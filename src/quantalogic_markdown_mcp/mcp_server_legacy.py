"""
MCP Server for SafeMarkdownEditor.

This module implements a Model Context Protocol (MCP) server that exposes
the SafeMarkdownEditor functionality as MCP tools, resources, and prompts.
"""

import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from mcp.server.fastmcp import FastMCP

from .safe_editor import SafeMarkdownEditor
from .safe_editor_types import (
    EditResult,
    ValidationLevel,
)


class MarkdownMCPServer:
    """
    MCP Server for SafeMarkdownEditor.
    
    Provides MCP-compliant access to SafeMarkdownEditor functionality
    including tools for document manipulation, resources for document state,
    and prompts for common editing tasks.
    """
    
    def __init__(self, server_name: str = "SafeMarkdownEditor"):
        """Initialize the MCP server."""
        self.mcp = FastMCP(server_name)
        self.editor: Optional[SafeMarkdownEditor] = None
        self.current_file_path: Optional[Path] = None
        self.lock = threading.RLock()
        self.document_metadata = {
            "title": "Untitled Document",
            "author": "Unknown",
            "created": datetime.now().isoformat(),
            "modified": datetime.now().isoformat()
        }
        
        self._setup_tools()
        self._setup_resources()
        self._setup_prompts()
    
    def _resolve_path(self, path_str: str) -> Path:
        """
        Resolve a path string to an absolute Path object.
        
        Handles:
        - Absolute paths
        - Relative paths (relative to current working directory)
        - Tilde expansion for home directory
        - Environment variable expansion
        
        Args:
            path_str: The path string to resolve
            
        Returns:
            Resolved absolute Path object
            
        Raises:
            ValueError: If the path cannot be resolved
        """
        try:
            # Expand environment variables and user home directory
            expanded_path = os.path.expandvars(os.path.expanduser(path_str))
            
            # Create Path object and resolve to absolute path
            path = Path(expanded_path).resolve()
            
            return path
        except Exception as e:
            raise ValueError(f"Could not resolve path '{path_str}': {e}")
    
    def _validate_file_path(self, path: Path, must_exist: bool = True, must_be_file: bool = True) -> None:
        """
        Validate a file path for various conditions.
        
        Args:
            path: The path to validate
            must_exist: Whether the path must exist
            must_be_file: Whether the path must be a file (not directory)
            
        Raises:
            FileNotFoundError: If must_exist=True and path doesn't exist
            IsADirectoryError: If must_be_file=True and path is a directory
            PermissionError: If path is not readable/writable
        """
        if must_exist and not path.exists():
            raise FileNotFoundError(f"Path does not exist: {path}")
        
        if path.exists():
            if must_be_file and path.is_dir():
                raise IsADirectoryError(f"Path is a directory, not a file: {path}")
            
            if not os.access(path, os.R_OK):
                raise PermissionError(f"No read permission for path: {path}")
    
    def load_document_from_file(self, file_path: str, validation_level: ValidationLevel = ValidationLevel.NORMAL) -> None:
        """
        Load a Markdown document from a file path.
        
        Args:
            file_path: Path to the Markdown file (supports absolute, relative, and ~ expansion)
            validation_level: Validation level for the editor
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            PermissionError: If the file can't be read
            ValueError: If the path is invalid
        """
        with self.lock:
            # Resolve and validate the path
            resolved_path = self._resolve_path(file_path)
            self._validate_file_path(resolved_path, must_exist=True, must_be_file=True)
            
            # Read the file content
            try:
                content = resolved_path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                # Try with different encodings
                for encoding in ['utf-8-sig', 'latin1', 'cp1252']:
                    try:
                        content = resolved_path.read_text(encoding=encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    raise ValueError(f"Could not decode file {resolved_path} with any supported encoding")
            
            # Initialize the editor with the content
            self.editor = SafeMarkdownEditor(
                markdown_text=content,
                validation_level=validation_level
            )
            
            # Update metadata
            self.current_file_path = resolved_path
            self.document_metadata.update({
                "title": resolved_path.stem,
                "file_path": str(resolved_path),
                "modified": datetime.now().isoformat(),
                "file_size": len(content),
                "encoding": "utf-8"
            })
    
    def save_document_to_file(self, file_path: Optional[str] = None, backup: bool = True) -> None:
        """
        Save the current document to a file.
        
        Args:
            file_path: Path to save to (if None, uses current file path)
            backup: Whether to create a backup of existing file
            
        Raises:
            ValueError: If no file path is specified and no current file is set
            PermissionError: If the file can't be written
        """
        with self.lock:
            if self.editor is None:
                raise ValueError("No document loaded")
            
            # Determine the target path
            if file_path is not None:
                target_path = self._resolve_path(file_path)
            elif self.current_file_path is not None:
                target_path = self.current_file_path
            else:
                raise ValueError("No file path specified and no current file loaded")
            
            # Create parent directories if they don't exist
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create backup if requested and file exists
            if backup and target_path.exists():
                backup_path = target_path.with_suffix(f"{target_path.suffix}.bak")
                backup_path.write_bytes(target_path.read_bytes())
            
            # Save the document
            content = self.editor.to_markdown()
            target_path.write_text(content, encoding='utf-8')
            
            # Update metadata
            self.current_file_path = target_path
            self.document_metadata.update({
                "file_path": str(target_path),
                "modified": datetime.now().isoformat(),
                "file_size": len(content)
            })
    
    def initialize_document(self, 
                           markdown_text: str = "# Untitled Document\n\nStart writing your content here.",
                           validation_level: ValidationLevel = ValidationLevel.NORMAL) -> None:
        """Initialize or replace the current document."""
        with self.lock:
            self.editor = SafeMarkdownEditor(
                markdown_text=markdown_text,
                validation_level=validation_level
            )
            self.document_metadata["modified"] = datetime.now().isoformat()
    
    def _ensure_editor(self) -> SafeMarkdownEditor:
        """Ensure an editor instance exists, creating one if necessary."""
        if self.editor is None:
            self.initialize_document()
        return self.editor
    
    def _handle_edit_result(self, result: EditResult) -> Dict[str, Any]:
        """Convert an EditResult to MCP response format."""
        if result.success:
            response = {
                "success": True,
                "message": "Operation completed successfully"
            }
            # Add information about modified sections
            if result.modified_sections:
                response["modified_sections"] = [
                    {"id": section.id, "title": section.title, "level": section.level}
                    for section in result.modified_sections
                ]
                self.document_metadata["modified"] = datetime.now().isoformat()
            
            # Include operation type
            response["operation"] = result.operation.value
            
            # Add preview if available
            if result.preview:
                response["preview"] = result.preview
                
            return response
        else:
            # Return error information but don't raise exception
            # Let MCP handle the error response format
            error_messages = [str(error) for error in result.errors]
            return {
                "success": False,  
                "error": "; ".join(error_messages) if error_messages else "Operation failed",
                "operation": result.operation.value
            }
    
    def _setup_tools(self) -> None:
        """Register all MCP tools."""
        
        @self.mcp.tool()
        def load_document(file_path: str, validation_level: str = "NORMAL") -> Dict[str, Any]:
            """
            Load a Markdown document from a file path.
            
            Supports absolute paths, relative paths, and tilde (~) expansion.
            
            Args:
                file_path: Path to the Markdown file (e.g., "/path/to/file.md", "./docs/readme.md", "~/Documents/notes.md")
                validation_level: Validation strictness - "STRICT", "NORMAL", or "PERMISSIVE"
            """
            try:
                # Convert string validation level to enum
                validation_map = {
                    "STRICT": ValidationLevel.STRICT,
                    "NORMAL": ValidationLevel.NORMAL,
                    "PERMISSIVE": ValidationLevel.PERMISSIVE
                }
                validation_enum = validation_map.get(validation_level.upper(), ValidationLevel.NORMAL)
                
                # Load the document
                self.load_document_from_file(file_path, validation_enum)
                
                # Get document info
                sections = self.editor.get_sections()
                content_preview = self.editor.to_markdown()[:200] + "..." if len(self.editor.to_markdown()) > 200 else self.editor.to_markdown()
                
                return {
                    "success": True,
                    "message": f"Successfully loaded document from {self.current_file_path}",
                    "file_path": str(self.current_file_path),
                    "sections_count": len(sections),
                    "content_preview": content_preview,
                    "file_size": self.document_metadata.get("file_size", 0)
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "suggestions": [
                        "Check that the file path exists and is readable",
                        "Ensure the file is a valid Markdown document",
                        "Try using an absolute path if relative path fails"
                    ]
                }
        
        @self.mcp.tool()
        def save_document(file_path: Optional[str] = None, backup: bool = True) -> Dict[str, Any]:
            """
            Save the current document to a file.
            
            Args:
                file_path: Path to save to (if not provided, saves to current file)
                backup: Whether to create a backup of existing file
            """
            try:
                self.save_document_to_file(file_path, backup)
                
                return {
                    "success": True,
                    "message": f"Successfully saved document to {self.current_file_path}",
                    "file_path": str(self.current_file_path),
                    "backup_created": backup and Path(str(self.current_file_path) + ".bak").exists()
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "suggestions": [
                        "Ensure you have write permissions for the target directory",
                        "Check that the parent directory exists",
                        "Load a document first if none is currently loaded"
                    ]
                }
        
        @self.mcp.tool()
        def get_file_info() -> Dict[str, Any]:
            """Get information about the currently loaded file."""
            with self.lock:
                if self.current_file_path is None:
                    return {
                        "success": False,
                        "error": "No file currently loaded",
                        "suggestions": ["Use load_document to load a file first"]
                    }
                
                try:
                    path = self.current_file_path
                    stat = path.stat()
                    
                    return {
                        "success": True,
                        "file_path": str(path),
                        "absolute_path": str(path.resolve()),
                        "file_name": path.name,
                        "file_stem": path.stem,
                        "file_suffix": path.suffix,
                        "file_size": stat.st_size,
                        "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "is_writable": os.access(path, os.W_OK),
                        "is_readable": os.access(path, os.R_OK)
                    }
                    
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Could not get file info: {e}",
                        "suggestions": ["Check that the file still exists"]
                    }
        
        @self.mcp.tool()
        def test_path_resolution(path: str) -> Dict[str, Any]:
            """
            Test path resolution to verify absolute, relative, and tilde expansion works.
            
            Args:
                path: The path to test (can be absolute, relative, or use ~ for home)
            """
            try:
                resolved_path = self._resolve_path(path)
                
                return {
                    "success": True,
                    "original_path": path,
                    "resolved_path": str(resolved_path),
                    "absolute_path": str(resolved_path.resolve()),
                    "exists": resolved_path.exists(),
                    "is_file": resolved_path.is_file() if resolved_path.exists() else None,
                    "is_directory": resolved_path.is_dir() if resolved_path.exists() else None,
                    "is_readable": os.access(resolved_path, os.R_OK) if resolved_path.exists() else None,
                    "is_writable": os.access(resolved_path, os.W_OK) if resolved_path.exists() else None,
                    "parent_exists": resolved_path.parent.exists(),
                    "expansion_info": {
                        "tilde_expanded": os.path.expanduser(path) != path,
                        "env_vars_expanded": os.path.expandvars(os.path.expanduser(path)) != os.path.expanduser(path),
                        "is_absolute": Path(path).is_absolute(),
                        "is_relative": not Path(path).is_absolute()
                    }
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "original_path": path,
                    "suggestions": [
                        "Check the path syntax",
                        "Ensure environment variables exist if used",
                        "Verify parent directories exist for relative paths"
                    ]
                }
        
        @self.mcp.tool()
        def insert_section(heading: str, content: str, position: int) -> Dict[str, Any]:
            """Insert a new section at a specified location."""
            with self.lock:
                try:
                    editor = self._ensure_editor()
                    
                    # Get all sections to find the insertion point
                    sections = editor.get_sections()
                    
                    if position == 0 or not sections:
                        # Insert at the beginning is tricky - we'd need insert_section_before
                        # For now, we'll insert after the first section if it exists
                        if sections:
                            after_section = sections[0]
                            result = editor.insert_section_after(
                                after_section=after_section,
                                level=2,  # Default to H2
                                title=heading,
                                content=content
                            )
                        else:
                            return {
                                "success": False,
                                "error": "Cannot insert into empty document",
                                "suggestions": ["Initialize document first"]
                            }
                    else:
                        # Insert after the section at position-1 (if it exists)
                        if position-1 < len(sections):
                            after_section = sections[position-1]
                            result = editor.insert_section_after(
                                after_section=after_section,
                                level=2,  # Default to H2
                                title=heading,
                                content=content
                            )
                        else:
                            return {
                                "success": False,
                                "error": f"Position {position} is out of range",
                                "suggestions": [f"Use position between 0 and {len(sections)}"]
                            }
                    
                    return self._handle_edit_result(result)
                    
                except Exception as e:
                    return {
                        "success": False,
                        "error": str(e),
                        "suggestions": ["Check that the position is valid", "Ensure heading format is correct"]
                    }
        
        @self.mcp.tool()
        def delete_section(section_id: Optional[str] = None, heading: Optional[str] = None) -> Dict[str, Any]:
            """Delete a section by ID or heading."""
            with self.lock:
                try:
                    editor = self._ensure_editor()
                    
                    if section_id:
                        # Find section by ID
                        section_ref = editor.get_section_by_id(section_id)
                        if not section_ref:
                            return {
                                "success": False,
                                "error": f"Section with ID '{section_id}' not found",
                                "suggestions": ["Use list_sections to see available sections"]
                            }
                    elif heading:
                        # Find section by heading
                        sections = editor.get_sections()
                        matching_sections = [s for s in sections if s.title == heading]
                        if not matching_sections:
                            return {
                                "success": False,
                                "error": f"Section with heading '{heading}' not found",
                                "suggestions": ["Use list_sections to see available sections"]
                            }
                        section_ref = matching_sections[0]
                    else:
                        return {
                            "success": False,
                            "error": "Either section_id or heading must be provided",
                            "suggestions": ["Provide section_id or heading parameter"]
                        }
                    
                    result = editor.delete_section(section_ref, preserve_subsections=False)
                    return self._handle_edit_result(result)
                    
                except Exception as e:
                    return {
                        "success": False,
                        "error": str(e),
                        "suggestions": ["Check that the section exists", "Ensure section ID is valid"]
                    }
        
        @self.mcp.tool()
        def update_section(section_id: str, content: str) -> Dict[str, Any]:
            """Update the content of a section."""
            with self.lock:
                try:
                    editor = self._ensure_editor()
                    
                    section_ref = editor.get_section_by_id(section_id)
                    if not section_ref:
                        return {
                            "success": False,
                            "error": f"Section with ID '{section_id}' not found",
                            "suggestions": ["Use list_sections to see available sections"]
                        }
                    
                    result = editor.update_section_content(
                        section_ref=section_ref,
                        content=content,
                        preserve_subsections=True
                    )
                    
                    return self._handle_edit_result(result)
                    
                except Exception as e:
                    return {
                        "success": False,
                        "error": str(e),
                        "suggestions": ["Check that the section ID is valid", "Ensure content is properly formatted"]
                    }
        
        @self.mcp.tool()
        def move_section(section_id: str, new_position: int) -> Dict[str, Any]:
            """Move a section to a new location."""
            with self.lock:
                try:
                    editor = self._ensure_editor()
                    
                    section_ref = editor.get_section_by_id(section_id)
                    if not section_ref:
                        return {
                            "success": False,
                            "error": f"Section with ID '{section_id}' not found",
                            "suggestions": ["Use list_sections to see available sections"]
                        }
                    
                    result = editor.move_section(
                        section_ref=section_ref,
                        target_position=new_position
                    )
                    
                    return self._handle_edit_result(result)
                    
                except Exception as e:
                    return {
                        "success": False,
                        "error": str(e),
                        "suggestions": ["Check that the section ID is valid", "Ensure new position is within bounds"]
                    }
        
        @self.mcp.tool()
        def get_section(section_id: str) -> Dict[str, Any]:
            """Retrieve a section's content."""
            with self.lock:
                try:
                    editor = self._ensure_editor()
                    
                    section_ref = editor.get_section_by_id(section_id)
                    if not section_ref:
                        return {
                            "success": False,
                            "error": f"Section with ID '{section_id}' not found",
                            "suggestions": ["Use list_sections to see available sections"]
                        }
                    
                    # Get the actual content from the document
                    document_lines = editor.to_markdown().split('\n')
                    section_lines = document_lines[section_ref.line_start:section_ref.line_end]
                    section_content = '\n'.join(section_lines)
                    
                    return {
                        "success": True,
                        "heading": section_ref.title,
                        "content": section_content,
                        "position": section_ref.line_start,
                        "level": section_ref.level,
                        "section_id": section_ref.id
                    }
                    
                except Exception as e:
                    return {
                        "success": False,
                        "error": str(e),
                        "suggestions": ["Check that the section ID is valid"]
                    }
        
        @self.mcp.tool()
        def list_sections() -> Dict[str, Any]:
            """List all sections and their metadata."""
            with self.lock:
                try:
                    editor = self._ensure_editor()
                    sections = editor.get_sections()
                    
                    sections_data = []
                    for section in sections:
                        sections_data.append({
                            "section_id": section.id,
                            "heading": section.title,
                            "position": section.line_start,
                            "level": section.level,
                            "path": section.path
                        })
                    
                    return {
                        "success": True,
                        "sections": sections_data
                    }
                    
                except Exception as e:
                    return {
                        "success": False,
                        "error": str(e),
                        "suggestions": ["Ensure document is properly initialized"]
                    }
        
        @self.mcp.tool()
        def undo() -> Dict[str, Any]:
            """Undo the last operation."""
            with self.lock:
                try:
                    editor = self._ensure_editor()
                    
                    # Get current transaction history
                    history = editor.get_transaction_history()
                    if not history:
                        return {
                            "success": False,
                            "error": "No operations to undo",
                            "suggestions": ["Make some changes first"]
                        }
                    
                    # Rollback the last transaction
                    last_transaction = history[-1]
                    result = editor.rollback_transaction(last_transaction.id)
                    
                    if result.success:
                        self.document_metadata["modified"] = datetime.now().isoformat()
                    
                    return self._handle_edit_result(result)
                    
                except Exception as e:
                    return {
                        "success": False,
                        "error": str(e),
                        "suggestions": ["Ensure there are operations to undo"]
                    }
        
        @self.mcp.tool()
        def redo() -> Dict[str, Any]:
            """Redo the last undone operation."""
            # Note: Current SafeMarkdownEditor doesn't have explicit redo
            # This is a placeholder implementation
            return {
                "success": False,
                "error": "Redo functionality not yet implemented",
                "suggestions": ["Use undo to reverse changes"]
            }
        
        @self.mcp.tool()
        def get_document() -> Dict[str, Any]:
            """Retrieve the full Markdown document."""
            with self.lock:
                try:
                    editor = self._ensure_editor()
                    document_text = editor.to_markdown()
                    
                    return {
                        "success": True,
                        "document": document_text
                    }
                    
                except Exception as e:
                    return {
                        "success": False,
                        "error": str(e),
                        "suggestions": ["Ensure document is properly initialized"]
                    }
    
    def _setup_resources(self) -> None:
        """Register all MCP resources."""
        
        @self.mcp.resource("document://current")
        def get_current_document() -> str:
            """The current Markdown document."""
            with self.lock:
                editor = self._ensure_editor()
                return editor.to_markdown()
        
        @self.mcp.resource("document://history")  
        def get_document_history() -> Dict[str, Any]:
            """List of past operations (for undo/redo)."""
            with self.lock:
                editor = self._ensure_editor()
                history = editor.get_transaction_history()
                
                history_data = []
                for transaction in history:
                    history_data.append({
                        "operation": transaction.operation.value,
                        "timestamp": transaction.timestamp.isoformat(),
                        "details": {
                            "message": transaction.description,
                            "success": transaction.success
                        }
                    })
                
                return {"history": history_data}
        
        @self.mcp.resource("document://metadata")
        def get_document_metadata() -> Dict[str, Any]:
            """Document metadata (title, author, etc.)."""
            with self.lock:
                return self.document_metadata.copy()
    
    def _setup_prompts(self) -> None:
        """Register all MCP prompts."""
        
        @self.mcp.prompt()
        def summarize_section(section_content: str) -> str:
            """Generate a prompt to summarize a section."""
            return f"""Summarize the following section:

{section_content}

Please provide a concise summary that captures the main points and key information."""
        
        @self.mcp.prompt()
        def rewrite_section(section_content: str) -> str:
            """Generate a prompt to rewrite a section for clarity and conciseness."""
            return f"""Rewrite the following section for clarity and conciseness:

{section_content}

Please improve the writing while maintaining the original meaning and key information."""
        
        @self.mcp.prompt()
        def generate_outline(document: str) -> str:
            """Generate a prompt to create an outline for the document."""
            return f"""Generate an outline for the following document:

{document}

Please create a hierarchical outline that shows the main sections and subsections."""
    
    def run(self, **kwargs) -> None:
        """Run the MCP server."""
        # Initialize with default document if none exists
        if self.editor is None:
            self.initialize_document()
        
        # Run the FastMCP server
        self.mcp.run(**kwargs)


# Create a global server instance
server = MarkdownMCPServer()

# Expose the FastMCP instance for direct access if needed
mcp = server.mcp

# Main entry point
def main():
    """Main entry point for running the MCP server."""
    server.run()


if __name__ == "__main__":
    main()
