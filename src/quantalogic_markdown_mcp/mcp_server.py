"""
MCP Server for SafeMarkdownEditor.

This module implements a Model Context Protocol (MCP) server that exposes
the SafeMarkdownEditor functionality as MCP tools, resources, and prompts.
"""

import threading
from datetime import datetime
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
                "message": result.message or "Operation completed successfully"
            }
            if result.section_ref:
                response["section_id"] = result.section_ref.id
            if result.changes_made:
                response["changes_made"] = result.changes_made
                self.document_metadata["modified"] = datetime.now().isoformat()
            return response
        else:
            # Return error information but don't raise exception
            # Let MCP handle the error response format
            return {
                "success": False,
                "error": result.error_message or "Operation failed",
                "suggestions": result.suggestions
            }
    
    def _setup_tools(self) -> None:
        """Register all MCP tools."""
        
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
                    
                    result = editor.delete_section(section_ref, cascade=True)
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
