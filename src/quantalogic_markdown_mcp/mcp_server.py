"""
Stateless MCP Server for SafeMarkdownEditor.

This module implements a Model Context Protocol (MCP) server that exposes
the SafeMarkdownEditor functionality as stateless MCP tools, where each
operation requires a document_path parameter.
"""

from typing import Any, Dict, Optional

from mcp.server.fastmcp import FastMCP

from .safe_editor import SafeMarkdownEditor
from .safe_editor_types import ValidationLevel
from .stateless_processor import StatelessMarkdownProcessor


class MarkdownMCPServer:
    """
    MCP Server for SafeMarkdownEditor with stateless operations.
    
    Provides MCP-compliant access to SafeMarkdownEditor functionality
    as stateless operations where each tool requires a document_path parameter.
    """
    
    def __init__(self, server_name: str = "SafeMarkdownEditor"):
        """Initialize the stateless MCP server."""
        self.mcp = FastMCP(server_name)
        self.processor = StatelessMarkdownProcessor()
        
        self._setup_tools()
        self._setup_resources()
        self._setup_prompts()
    
    def _setup_tools(self) -> None:
        """Register all stateless MCP tools."""
        
        @self.mcp.tool()
        def load_document(document_path: str, validation_level: str = "NORMAL") -> Dict[str, Any]:
            """
            Load and analyze a Markdown document from a file path.
            
            Args:
                document_path: Path to the Markdown file (supports absolute, relative, and ~ expansion)
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
                
                # Load document without server state
                editor = self.processor.load_document(document_path, validation_enum)
                sections = editor.get_sections()
                content_preview = editor.to_markdown()[:200] + "..." if len(editor.to_markdown()) > 200 else editor.to_markdown()
                
                return {
                    "success": True,
                    "message": f"Successfully analyzed document at {document_path}",
                    "document_path": document_path,
                    "sections_count": len(sections),
                    "content_preview": content_preview,
                    "file_size": len(editor.to_markdown()),
                    "stateless": True
                }
                
            except Exception as e:
                return self.processor.create_error_response(str(e), type(e).__name__)
        
        @self.mcp.tool()
        def insert_section(document_path: str, heading: str, content: str, position: int,
                          auto_save: bool = True, backup: bool = True,
                          validation_level: str = "NORMAL") -> Dict[str, Any]:
            """
            Insert a new section at a specified location.
            
            Args:
                document_path: Path to the Markdown file
                heading: The section heading/title
                content: The section content
                position: Position to insert (0-based index)
                auto_save: Whether to automatically save the document
                backup: Whether to create a backup before saving
                validation_level: Validation strictness - "STRICT", "NORMAL", or "PERMISSIVE"
            """
            def operation(editor):
                sections = editor.get_sections()
                
                if position == 0 or not sections:
                    if sections:
                        after_section = sections[0]
                        return editor.insert_section_after(
                            after_section=after_section,
                            level=2,
                            title=heading,
                            content=content
                        )
                    else:
                        # Handle empty document case
                        from .safe_editor_types import EditResult, OperationType
                        return EditResult(
                            success=False,
                            operation=OperationType.INSERT,
                            modified_sections=[],
                            errors=["Cannot insert into empty document"],
                            warnings=[]
                        )
                else:
                    if position-1 < len(sections):
                        after_section = sections[position-1]
                        return editor.insert_section_after(
                            after_section=after_section,
                            level=2,
                            title=heading,
                            content=content
                        )
                    else:
                        from .safe_editor_types import EditResult, OperationType
                        return EditResult(
                            success=False,
                            operation=OperationType.INSERT,
                            modified_sections=[],
                            errors=[f"Position {position} is out of range"],
                            warnings=[]
                        )
            
            validation_map = {"STRICT": ValidationLevel.STRICT, "NORMAL": ValidationLevel.NORMAL, "PERMISSIVE": ValidationLevel.PERMISSIVE}
            validation_enum = validation_map.get(validation_level.upper(), ValidationLevel.NORMAL)
            
            return self.processor.execute_operation(document_path, operation, auto_save, backup, validation_enum)
        
        @self.mcp.tool()
        def delete_section(document_path: str, section_id: Optional[str] = None, heading: Optional[str] = None,
                          auto_save: bool = True, backup: bool = True,
                          validation_level: str = "NORMAL") -> Dict[str, Any]:
            """
            Delete a section by ID or heading.
            
            Args:
                document_path: Path to the Markdown file
                section_id: The section ID to delete (optional)
                heading: The section heading to delete (optional)
                auto_save: Whether to automatically save the document
                backup: Whether to create a backup before saving
                validation_level: Validation strictness - "STRICT", "NORMAL", or "PERMISSIVE"
            """
            def operation(editor):
                if section_id:
                    # Find section by ID
                    section_ref = editor.get_section_by_id(section_id)
                    if not section_ref:
                        from .safe_editor_types import EditResult, OperationType
                        return EditResult(
                            success=False,
                            operation=OperationType.DELETE,
                            modified_sections=[],
                            errors=[f"Section with ID '{section_id}' not found"],
                            warnings=[]
                        )
                elif heading:
                    # Find section by heading
                    sections = editor.get_sections()
                    matching_sections = [s for s in sections if s.title == heading]
                    if not matching_sections:
                        from .safe_editor_types import EditResult, OperationType
                        return EditResult(
                            success=False,
                            operation=OperationType.DELETE,
                            modified_sections=[],
                            errors=[f"Section with heading '{heading}' not found"],
                            warnings=[]
                        )
                    section_ref = matching_sections[0]
                else:
                    from .safe_editor_types import EditResult, OperationType
                    return EditResult(
                        success=False,
                        operation=OperationType.DELETE,
                        modified_sections=[],
                        errors=["Either section_id or heading must be provided"],
                        warnings=[]
                    )
                
                return editor.delete_section(section_ref, preserve_subsections=False)
            
            validation_map = {"STRICT": ValidationLevel.STRICT, "NORMAL": ValidationLevel.NORMAL, "PERMISSIVE": ValidationLevel.PERMISSIVE}
            validation_enum = validation_map.get(validation_level.upper(), ValidationLevel.NORMAL)
            
            return self.processor.execute_operation(document_path, operation, auto_save, backup, validation_enum)
        
        @self.mcp.tool()
        def update_section(document_path: str, section_id: str, content: str,
                          auto_save: bool = True, backup: bool = True,
                          validation_level: str = "NORMAL") -> Dict[str, Any]:
            """
            Update the content of an existing section.
            
            Args:
                document_path: Path to the Markdown file
                section_id: The section ID to update
                content: New content for the section
                auto_save: Whether to automatically save the document
                backup: Whether to create a backup before saving
                validation_level: Validation strictness - "STRICT", "NORMAL", or "PERMISSIVE"
            """
            def operation(editor):
                section_ref = editor.get_section_by_id(section_id)
                if not section_ref:
                    from .safe_editor_types import EditResult, OperationType
                    return EditResult(
                        success=False,
                        operation=OperationType.UPDATE,
                        modified_sections=[],
                        errors=[f"Section with ID '{section_id}' not found"],
                        warnings=[]
                    )
                
                return editor.update_section_content(section_ref, content)
            
            validation_map = {"STRICT": ValidationLevel.STRICT, "NORMAL": ValidationLevel.NORMAL, "PERMISSIVE": ValidationLevel.PERMISSIVE}
            validation_enum = validation_map.get(validation_level.upper(), ValidationLevel.NORMAL)
            
            return self.processor.execute_operation(document_path, operation, auto_save, backup, validation_enum)
        
        @self.mcp.tool()
        def get_section(document_path: str, section_id: str, validation_level: str = "NORMAL") -> Dict[str, Any]:
            """
            Get a specific section by ID.
            
            Args:
                document_path: Path to the Markdown file
                section_id: The section ID to retrieve
                validation_level: Validation strictness - "STRICT", "NORMAL", or "PERMISSIVE"
            """
            try:
                validation_map = {"STRICT": ValidationLevel.STRICT, "NORMAL": ValidationLevel.NORMAL, "PERMISSIVE": ValidationLevel.PERMISSIVE}
                validation_enum = validation_map.get(validation_level.upper(), ValidationLevel.NORMAL)
                
                editor = self.processor.load_document(document_path, validation_enum)
                section_ref = editor.get_section_by_id(section_id)
                
                if not section_ref:
                    return {
                        "success": False,
                        "error": f"Section with ID '{section_id}' not found",
                        "suggestions": ["Use list_sections to see available sections"]
                    }
                
                # Extract section content using line ranges
                full_content = editor.to_markdown()
                lines = full_content.split('\n')
                section_lines = lines[section_ref.line_start:section_ref.line_end+1]
                section_content = '\n'.join(section_lines)
                
                return {
                    "success": True,
                    "section": {
                        "id": section_ref.id,
                        "title": section_ref.title,
                        "level": section_ref.level,
                        "content": section_content,
                        "line_start": section_ref.line_start,
                        "line_end": section_ref.line_end
                    }
                }
                
            except Exception as e:
                return self.processor.create_error_response(str(e), type(e).__name__)
        
        @self.mcp.tool()
        def list_sections(document_path: str, validation_level: str = "NORMAL") -> Dict[str, Any]:
            """
            List all sections in the document.
            
            Args:
                document_path: Path to the Markdown file
                validation_level: Validation strictness - "STRICT", "NORMAL", or "PERMISSIVE"  
            """
            try:
                validation_map = {"STRICT": ValidationLevel.STRICT, "NORMAL": ValidationLevel.NORMAL, "PERMISSIVE": ValidationLevel.PERMISSIVE}
                validation_enum = validation_map.get(validation_level.upper(), ValidationLevel.NORMAL)
                
                editor = self.processor.load_document(document_path, validation_enum)
                sections = editor.get_sections()
                
                # Get full content to extract section content
                full_content = editor.to_markdown()
                lines = full_content.split('\n')
                
                # Build section list with content preview
                section_list = []
                for section in sections:
                    # Extract section content using line ranges
                    try:
                        section_lines = lines[section.line_start:section.line_end+1]
                        section_content = '\n'.join(section_lines)
                        content_preview = section_content[:100] + "..." if len(section_content) > 100 else section_content
                    except (IndexError, AttributeError):
                        # Fallback if line extraction fails
                        content_preview = "Content preview not available"
                    
                    section_list.append({
                        "id": section.id,  
                        "title": section.title,
                        "level": section.level,
                        "line_start": section.line_start,
                        "line_end": section.line_end,
                        "content_preview": content_preview
                    })
                
                return {
                    "success": True,
                    "sections": section_list,
                    "total_sections": len(sections)
                }
                
            except Exception as e:
                return self.processor.create_error_response(str(e), type(e).__name__)
        
        @self.mcp.tool()
        def move_section(document_path: str, section_id: str, target_position: int,
                        auto_save: bool = True, backup: bool = True,
                        validation_level: str = "NORMAL") -> Dict[str, Any]:
            """
            Move a section to a different position.
            
            Args:
                document_path: Path to the Markdown file
                section_id: The section ID to move
                target_position: Target position (0-based index)
                auto_save: Whether to automatically save the document
                backup: Whether to create a backup before saving
                validation_level: Validation strictness - "STRICT", "NORMAL", or "PERMISSIVE"
            """
            def operation(editor):
                section_ref = editor.get_section_by_id(section_id)
                if not section_ref:
                    from .safe_editor_types import EditResult, OperationType
                    return EditResult(
                        success=False,
                        operation=OperationType.MOVE,
                        modified_sections=[],
                        errors=[f"Section with ID '{section_id}' not found"],
                        warnings=[]
                    )
                
                sections = editor.get_sections()
                if target_position >= len(sections) or target_position < 0:
                    from .safe_editor_types import EditResult, OperationType
                    return EditResult(
                        success=False,
                        operation=OperationType.MOVE,
                        modified_sections=[],
                        errors=[f"Target position {target_position} is out of range (0-{len(sections)-1})"],
                        warnings=[]
                    )
                
                target_section = sections[target_position]
                return editor.move_section(section_ref, target_section, "after")
            
            validation_map = {"STRICT": ValidationLevel.STRICT, "NORMAL": ValidationLevel.NORMAL, "PERMISSIVE": ValidationLevel.PERMISSIVE}
            validation_enum = validation_map.get(validation_level.upper(), ValidationLevel.NORMAL)
            
            return self.processor.execute_operation(document_path, operation, auto_save, backup, validation_enum)
        
        @self.mcp.tool()
        def get_document(document_path: str, validation_level: str = "NORMAL") -> Dict[str, Any]:
            """
            Get the complete document content and structure.
            
            Args:
                document_path: Path to the Markdown file
                validation_level: Validation strictness - "STRICT", "NORMAL", or "PERMISSIVE"
            """
            try:
                validation_map = {"STRICT": ValidationLevel.STRICT, "NORMAL": ValidationLevel.NORMAL, "PERMISSIVE": ValidationLevel.PERMISSIVE}
                validation_enum = validation_map.get(validation_level.upper(), ValidationLevel.NORMAL)
                
                editor = self.processor.load_document(document_path, validation_enum)
                sections = editor.get_sections()
                content = editor.to_markdown()
                
                return {
                    "success": True,
                    "document_path": document_path,
                    "content": content,
                    "sections": [
                        {
                            "id": section.id,
                            "title": section.title,
                            "level": section.level,
                            "line_start": section.line_start,
                            "line_end": section.line_end
                        }
                        for section in sections
                    ],
                    "metadata": {
                        "total_sections": len(sections),
                        "total_lines": len(content.split('\n')),
                        "file_size": len(content),
                        "validation_level": validation_level
                    }
                }
                
            except Exception as e:
                return self.processor.create_error_response(str(e), type(e).__name__)
        
        @self.mcp.tool()
        def save_document(document_path: str, target_path: Optional[str] = None,
                         backup: bool = True, validation_level: str = "NORMAL") -> Dict[str, Any]:
            """
            Save the document (mainly for validation purposes since auto_save handles most cases).
            
            Args:
                document_path: Path to the source Markdown file
                target_path: Path to save to (if different from source)
                backup: Whether to create a backup before saving
                validation_level: Validation strictness - "STRICT", "NORMAL", or "PERMISSIVE"
            """
            try:
                validation_map = {"STRICT": ValidationLevel.STRICT, "NORMAL": ValidationLevel.NORMAL, "PERMISSIVE": ValidationLevel.PERMISSIVE}
                validation_enum = validation_map.get(validation_level.upper(), ValidationLevel.NORMAL)
                
                editor = self.processor.load_document(document_path, validation_enum)
                
                # Determine save path
                save_path = target_path if target_path else document_path
                
                # Save the document
                save_result = self.processor.save_document(editor, save_path, backup)
                return save_result
                
            except Exception as e:
                return self.processor.create_error_response(str(e), type(e).__name__)
        
        @self.mcp.tool()
        def analyze_document(document_path: str, validation_level: str = "NORMAL") -> Dict[str, Any]:
            """
            Analyze document structure and provide insights.
            
            Args:
                document_path: Path to the Markdown file
                validation_level: Validation strictness - "STRICT", "NORMAL", or "PERMISSIVE"
            """
            try:
                validation_map = {"STRICT": ValidationLevel.STRICT, "NORMAL": ValidationLevel.NORMAL, "PERMISSIVE": ValidationLevel.PERMISSIVE}
                validation_enum = validation_map.get(validation_level.upper(), ValidationLevel.NORMAL)
                
                editor = self.processor.load_document(document_path, validation_enum)
                sections = editor.get_sections()
                content = editor.to_markdown()
                
                # Analyze heading levels
                heading_levels = {}
                for section in sections:
                    level = section.level
                    heading_levels[level] = heading_levels.get(level, 0) + 1
                
                # Content statistics
                lines = content.split('\n')
                words = len(content.split())
                
                return {
                    "success": True,
                    "document_path": document_path,
                    "analysis": {
                        "structure": {
                            "total_sections": len(sections),
                            "heading_levels": heading_levels,
                            "max_depth": max(heading_levels.keys()) if heading_levels else 0,
                            "min_depth": min(heading_levels.keys()) if heading_levels else 0
                        },
                        "content": {
                            "total_lines": len(lines),
                            "non_empty_lines": len([line for line in lines if line.strip()]),
                            "total_words": words,
                            "total_characters": len(content),
                            "average_section_length": words // len(sections) if sections else 0
                        },
                        "validation": {
                            "level": validation_level,
                            "is_valid": True  # If we got here, it loaded successfully
                        }
                    }
                }
                
            except Exception as e:
                return self.processor.create_error_response(str(e), type(e).__name__)
    
    def _setup_resources(self) -> None:
        """Register MCP resources (stateless version has no persistent resources)."""
        pass
    
    def _setup_prompts(self) -> None:
        """Register MCP prompts for common operations."""
        
        @self.mcp.prompt()
        def document_editing_guide() -> str:
            """Guide for using the stateless document editing tools."""
            return """
# Stateless Markdown Document Editing Guide

This MCP server provides stateless tools for editing Markdown documents. Each operation requires a `document_path` parameter.

## Core Operations

### Document Loading and Analysis
- `load_document(document_path, validation_level)` - Load and analyze a document
- `analyze_document(document_path, validation_level)` - Get detailed document analysis

### Section Operations
- `list_sections(document_path)` - List all sections
- `get_section(document_path, section_id)` - Get specific section
- `insert_section(document_path, heading, content, position)` - Insert new section
- `update_section(document_path, section_id, content)` - Update existing section
- `delete_section(document_path, section_id|heading)` - Delete section
- `move_section(document_path, section_id, target_position)` - Move section

### Document Operations
- `get_document(document_path)` - Get complete document content
- `save_document(document_path, target_path)` - Save document

## Key Features

1. **Stateless**: No server state, each operation works on the specified file
2. **Auto-save**: Most operations save automatically (configurable)  
3. **Backup**: Automatic backups created before modifications
4. **Validation**: Configurable validation levels (STRICT, NORMAL, PERMISSIVE)
5. **Path Resolution**: Supports absolute, relative, and tilde (~) paths

## Best Practices

1. Use absolute paths when possible for consistency
2. Enable backups for important documents
3. Use appropriate validation levels for your use case
4. Check operation results for success/failure status

All operations return structured responses with success status, error details, and helpful suggestions.
"""

        @self.mcp.prompt()
        def section_operations_examples() -> str:
            """Examples of common section operations."""
            return """
# Section Operations Examples

## Insert a new section
```
insert_section(
    document_path="/path/to/document.md",
    heading="New Section",
    content="This is the content of the new section.",
    position=1,
    auto_save=True,
    backup=True
)
```

## Update existing section content  
```
update_section(
    document_path="/path/to/document.md",
    section_id="section-123",
    content="Updated content for this section.",
    auto_save=True,
    backup=True
)
```

## Move a section to different position
```
move_section(
    document_path="/path/to/document.md", 
    section_id="section-123",
    target_position=3,
    auto_save=True,
    backup=True
)
```

## Delete a section
```
delete_section(
    document_path="/path/to/document.md",
    section_id="section-123",
    auto_save=True,
    backup=True
)
```

All operations support both section IDs and heading-based lookups where appropriate.
"""
    
    def call_tool_sync(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronously call a tool for testing purposes."""
        # Get the tool function from the mcp instance
        tools = {
            "load_document": self._load_document_impl,
            "list_sections": self._list_sections_impl,
            "get_section": self._get_section_impl,
            "insert_section": self._insert_section_impl,
            "update_section": self._update_section_impl,
            "delete_section": self._delete_section_impl,
            "move_section": self._move_section_impl,
            "get_document": self._get_document_impl,
            "save_document": self._save_document_impl,
            "analyze_document": self._analyze_document_impl,
        }
        
        if tool_name not in tools:
            return {"success": False, "error": f"Tool '{tool_name}' not found"}
        
        try:
            return tools[tool_name](**arguments)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Implementation methods for testing
    def _load_document_impl(self, document_path: str, validation_level: str = "NORMAL") -> Dict[str, Any]:
        """Implementation for load_document tool."""
        try:
            # Convert string validation level to enum
            validation_map = {
                "STRICT": ValidationLevel.STRICT,
                "NORMAL": ValidationLevel.NORMAL,
                "PERMISSIVE": ValidationLevel.PERMISSIVE
            }
            validation_enum = validation_map.get(validation_level, ValidationLevel.NORMAL)
            
            # Load document content first
            from pathlib import Path
            doc_path = Path(document_path).expanduser().resolve()
            
            if not doc_path.exists():
                return self.processor.create_error_response(f"Path does not exist: {doc_path}", "DocumentNotFoundError")
            
            content = doc_path.read_text(encoding='utf-8')
            
            # Create editor with content and validation level
            editor = SafeMarkdownEditor(content, validation_level=validation_enum)
            
            sections = editor.get_sections()
            
            return {
                "success": True,
                "message": f"Successfully loaded document from {document_path}",
                "document_path": document_path,
                "sections_count": len(sections),
                "stateless": True,
                "validation_level": validation_level
            }
        except Exception as e:
            return self.processor.create_error_response(str(e), type(e).__name__)

    def _list_sections_impl(self, document_path: str) -> Dict[str, Any]:
        """Implementation for list_sections tool."""
        def operation(editor):
            from .safe_editor_types import EditResult, EditOperation
            
            sections = editor.get_sections()
            
            section_list = []
            for section in sections:
                # Extract content for the section by using line ranges
                content = ""
                try:
                    markdown_text = editor.to_markdown()
                    lines = markdown_text.split('\n')
                    
                    # Extract section content from line_start to line_end
                    if section.line_start < len(lines) and section.line_end < len(lines):
                        content_lines = lines[section.line_start:section.line_end + 1]
                        content = '\n'.join(content_lines)
                except Exception:
                    content = ""
                
                section_list.append({
                    "id": section.id,
                    "title": section.title,
                    "level": section.level,
                    "start_line": section.line_start,
                    "end_line": section.line_end,
                    "content": content
                })
            
            return EditResult(
                success=True,
                operation=EditOperation.BATCH_OPERATIONS,  # Or a custom operation
                modified_sections=[],
                errors=[],
                warnings=[],
                metadata={"sections": section_list}
            )
        
        return self.processor.execute_operation(document_path, operation, auto_save=False)
    
    def _get_section_impl(self, document_path: str, section_id: str) -> Dict[str, Any]:
        """Implementation for get_section tool."""
        def operation(editor):
            from .safe_editor_types import EditResult, EditOperation, SafeParseError, ErrorCategory
            
            section = editor.get_section_by_id(section_id)
            
            if not section:
                return EditResult(
                    success=False,
                    operation=EditOperation.BATCH_OPERATIONS,
                    modified_sections=[],
                    errors=[SafeParseError(
                        message=f"Section '{section_id}' not found",
                        error_code="SECTION_NOT_FOUND",
                        category=ErrorCategory.VALIDATION
                    )],
                    warnings=[]
                )
            
            # Extract content for the section
            content = ""
            try:
                markdown_text = editor.to_markdown()
                lines = markdown_text.split('\n')
                
                # Extract section content from line_start to line_end
                if section.line_start < len(lines) and section.line_end < len(lines):
                    content_lines = lines[section.line_start:section.line_end + 1]
                    content = '\n'.join(content_lines)
            except Exception:
                content = ""
            
            section_data = {
                "id": section.id,
                "title": section.title,
                "level": section.level,
                "start_line": section.line_start,
                "end_line": section.line_end,
                "content": content
            }
            
            return EditResult(
                success=True,
                operation=EditOperation.BATCH_OPERATIONS,
                modified_sections=[],
                errors=[],
                warnings=[],
                metadata={"section": section_data}
            )
        
        return self.processor.execute_operation(document_path, operation, auto_save=False)
    
    def _insert_section_impl(self, document_path: str, heading: str, content: str = "", position: Optional[int] = None, auto_save: bool = True, backup: bool = True) -> Dict[str, Any]:
        """Implementation for insert_section tool."""
        def operation(editor):
            sections = editor.get_sections()
            
            # Handle position parameter
            if position is None or position >= len(sections):
                # Insert at the end
                if sections:
                    last_section = sections[-1]
                    return editor.insert_section_after(last_section, 1, heading, content)
                else:
                    # Document is empty - create a simple document with the new section
                    return {"success": False, "error": "Cannot insert into empty document - use save_document first"}
            
            elif position == 0:
                # Insert at the beginning - insert before first section
                if sections:
                    # Since we can't insert "before", we need to manipulate this differently
                    # For now, let's insert at level 1 after a dummy section or return error
                    return {"success": False, "error": "Inserting at position 0 not supported - use position >= 1"}
                else:
                    return {"success": False, "error": "Cannot insert into empty document"}
            else:
                # Insert after the section at position-1
                after_section = sections[position - 1]
                level = after_section.level if after_section.level < 6 else 1
                return editor.insert_section_after(after_section, level, heading, content)
            
        validation_enum = ValidationLevel.NORMAL
        return self.processor.execute_operation(document_path, operation, auto_save, backup, validation_enum)
    
    def _update_section_impl(self, document_path: str, section_id: str, content: str, auto_save: bool = True, backup: bool = True) -> Dict[str, Any]:
        """Implementation for update_section tool."""
        def operation(editor):
            section = editor.get_section_by_id(section_id)
            if not section:
                return {"success": False, "error": f"Section '{section_id}' not found"}
            return editor.update_section_content(section, content)
            
        validation_enum = ValidationLevel.NORMAL
        return self.processor.execute_operation(document_path, operation, auto_save, backup, validation_enum)
    
    def _delete_section_impl(self, document_path: str, section_id: str, auto_save: bool = True, backup: bool = True) -> Dict[str, Any]:
        """Implementation for delete_section tool."""
        def operation(editor):
            section = editor.get_section_by_id(section_id)
            if not section:
                return {"success": False, "error": f"Section '{section_id}' not found"}
            return editor.delete_section(section)
            
        validation_enum = ValidationLevel.NORMAL
        return self.processor.execute_operation(document_path, operation, auto_save, backup, validation_enum)
    
    def _move_section_impl(self, document_path: str, section_id: str, target_position: int, auto_save: bool = True, backup: bool = True) -> Dict[str, Any]:
        """Implementation for move_section tool."""
        def operation(editor):
            section = editor.get_section_by_id(section_id)
            if not section:
                return {"success": False, "error": f"Section '{section_id}' not found"}
                
            sections = editor.get_sections()
            if target_position < 0 or target_position >= len(sections):
                return {"success": False, "error": f"Invalid target position: {target_position}"}
                
            target_section = sections[target_position]
            return editor.move_section(section, target_section, "after")
            
        validation_enum = ValidationLevel.NORMAL
        return self.processor.execute_operation(document_path, operation, auto_save, backup, validation_enum)
    
    def _get_document_impl(self, document_path: str) -> Dict[str, Any]:
        """Implementation for get_document tool."""
        def operation(editor):
            from .safe_editor_types import EditResult, EditOperation
            
            content = editor.to_markdown()
            sections = editor.get_sections()
            
            document_data = {
                "content": content,
                "sections": [
                    {
                        "id": section.id,
                        "title": section.title,
                        "level": section.level,
                        "start_line": section.line_start,
                        "end_line": section.line_end
                    }
                    for section in sections
                ],
                "word_count": len(content.split()),
                "character_count": len(content)
            }
            
            return EditResult(
                success=True,
                operation=EditOperation.BATCH_OPERATIONS,
                modified_sections=[],
                errors=[],
                warnings=[],
                metadata=document_data
            )
        
        return self.processor.execute_operation(document_path, operation, auto_save=False)
    
    def _save_document_impl(self, document_path: str, target_path: Optional[str] = None, backup: bool = True, validation_level: str = "NORMAL") -> Dict[str, Any]:
        """Implementation for save_document tool."""
        try:
            validation_map = {"STRICT": ValidationLevel.STRICT, "NORMAL": ValidationLevel.NORMAL, "PERMISSIVE": ValidationLevel.PERMISSIVE}
            validation_enum = validation_map.get(validation_level.upper(), ValidationLevel.NORMAL)
            
            editor = self.processor.load_document(document_path, validation_enum)
            
            # Determine save path
            save_path = target_path if target_path else document_path
            
            return self.processor.save_document(editor, save_path, backup)
        except Exception as e:
            return self.processor.create_error_response(str(e), type(e).__name__)
    
    def _analyze_document_impl(self, document_path: str) -> Dict[str, Any]:
        """Implementation for analyze_document tool."""
        def operation(editor):
            from .safe_editor_types import EditResult, EditOperation
            
            content = editor.to_markdown()
            sections = editor.get_sections()
            
            # Basic document analysis
            lines = content.split('\n')
            word_count = len(content.split())
            char_count = len(content)
            
            # Section analysis
            section_levels = {}
            for section in sections:
                level = section.level
                section_levels[level] = section_levels.get(level, 0) + 1
            
            analysis_data = {
                "analysis": {
                    "total_sections": len(sections),
                    "section_levels": section_levels,
                    "word_count": word_count,
                    "character_count": char_count,
                    "line_count": len(lines),
                    "heading_structure": [
                        {
                            "id": section.id,
                            "title": section.title,
                            "level": section.level
                        }
                        for section in sections
                    ]
                }
            }
            
            return EditResult(
                success=True,
                operation=EditOperation.BATCH_OPERATIONS,
                modified_sections=[],
                errors=[],
                warnings=[],
                metadata=analysis_data
            )
        
        return self.processor.execute_operation(document_path, operation, auto_save=False)


# Global instances for backward compatibility and direct usage
server = MarkdownMCPServer()
mcp = server.mcp

if __name__ == "__main__":
    # Initialize with an empty document for stateless operations
    server.initialize_document(
        markdown_text="# Welcome\n\nThis is a stateless MCP server.\n",
        validation_level=ValidationLevel.NORMAL
    )
    
    print("Starting SafeMarkdownEditor MCP Server (Stateless Mode)...")
    mcp.run()
