"""Enhanced MCP Server with stateless operations."""

from typing import Any, Dict, Optional

from .mcp_server import MarkdownMCPServer
from .safe_editor import SafeMarkdownEditor
from .safe_editor_types import EditOperation, ValidationLevel
from .stateless_processor import StatelessMarkdownProcessor


class EnhancedMarkdownMCPServer(MarkdownMCPServer):
    """Enhanced MCP Server with stateless operations."""
    
    def __init__(self, server_name: str = "SafeMarkdownEditor"):
        """Initialize the enhanced MCP server."""
        super().__init__(server_name)
        self.processor = StatelessMarkdownProcessor()
        self._setup_enhanced_tools()
    
    
    def _setup_enhanced_tools(self) -> None:
        """Register enhanced MCP tools."""
        
        @self.mcp.tool()
        def load_document(document_path: str, validation_level: str = "NORMAL") -> Dict[str, Any]:
            """Load a Markdown document from a file path (stateless only)."""
            try:
                validation_map = {
                    "STRICT": ValidationLevel.STRICT,
                    "NORMAL": ValidationLevel.NORMAL,
                    "PERMISSIVE": ValidationLevel.PERMISSIVE
                }
                validation_enum = validation_map.get(validation_level.upper(), ValidationLevel.NORMAL)
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
        
        # Document Editing Tools with Enhanced Capabilities
        @self.mcp.tool()
        def insert_section(document_path: str, heading: str, content: str, position: int,
                          auto_save: bool = True, backup: bool = True,
                          validation_level: str = "NORMAL") -> Dict[str, Any]:
            """Insert a new section (stateless only)."""
            def operation(editor: SafeMarkdownEditor):
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
                        from .safe_editor_types import EditResult
                        return EditResult(
                            success=False,
                            operation=EditOperation.INSERT_SECTION,
                            errors=["Cannot insert into empty document"]
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
                        from .safe_editor_types import EditResult
                        return EditResult(
                            success=False,
                            operation=EditOperation.INSERT_SECTION,
                            errors=[f"Position {position} is out of range"]
                        )
            validation_map = {"STRICT": ValidationLevel.STRICT, "NORMAL": ValidationLevel.NORMAL, "PERMISSIVE": ValidationLevel.PERMISSIVE}
            validation_enum = validation_map.get(validation_level.upper(), ValidationLevel.NORMAL)
            return self.processor.execute_operation(document_path, operation, auto_save, backup, validation_enum)
        
        @self.mcp.tool()
        def delete_section(document_path: str, section_id: Optional[str] = None,
                          heading: Optional[str] = None, auto_save: bool = True, backup: bool = True,
                          validation_level: str = "NORMAL") -> Dict[str, Any]:
            """Delete a section (stateless only)."""
            def operation(editor: SafeMarkdownEditor):
                if section_id:
                    section = editor.get_section_by_id(section_id)
                elif heading:
                    sections = editor.get_sections()
                    section = next((s for s in sections if s.title == heading), None)
                else:
                    from .safe_editor_types import EditResult
                    return EditResult(
                        success=False,
                        operation=EditOperation.DELETE_SECTION,
                        errors=["Either section_id or heading must be provided"]
                    )
                if section:
                    return editor.delete_section(section, preserve_subsections=False)
                else:
                    from .safe_editor_types import EditResult
                    return EditResult(
                        success=False,
                        operation=EditOperation.DELETE_SECTION,
                        errors=["Section not found"]
                    )
            validation_map = {"STRICT": ValidationLevel.STRICT, "NORMAL": ValidationLevel.NORMAL, "PERMISSIVE": ValidationLevel.PERMISSIVE}
            validation_enum = validation_map.get(validation_level.upper(), ValidationLevel.NORMAL)
            return self.processor.execute_operation(document_path, operation, auto_save, backup, validation_enum)
        
        @self.mcp.tool()
        def update_section(document_path: str, section_id: str, content: str,
                          auto_save: bool = True, backup: bool = True,
                          validation_level: str = "NORMAL") -> Dict[str, Any]:
            """Update a section's content (stateless only)."""
            def operation(editor: SafeMarkdownEditor):
                section = editor.get_section_by_id(section_id)
                if section:
                    return editor.update_section_content(
                        section_ref=section,
                        content=content
                    )
                else:
                    from .safe_editor_types import EditResult
                    return EditResult(
                        success=False,
                        operation=EditOperation.UPDATE_SECTION,
                        errors=["Section not found"]
                    )
            validation_map = {"STRICT": ValidationLevel.STRICT, "NORMAL": ValidationLevel.NORMAL, "PERMISSIVE": ValidationLevel.PERMISSIVE}
            validation_enum = validation_map.get(validation_level.upper(), ValidationLevel.NORMAL)
            return self.processor.execute_operation(document_path, operation, auto_save, backup, validation_enum)
        
        @self.mcp.tool()
        def get_section(document_path: str, section_id: str,
                       validation_level: str = "NORMAL") -> Dict[str, Any]:
            """Get a specific section (stateless only)."""
            try:
                validation_map = {"STRICT": ValidationLevel.STRICT, "NORMAL": ValidationLevel.NORMAL, "PERMISSIVE": ValidationLevel.PERMISSIVE}
                validation_enum = validation_map.get(validation_level.upper(), ValidationLevel.NORMAL)
                editor = self.processor.load_document(document_path, validation_enum)
                section = editor.get_section_by_id(section_id)
                if section:
                    return {
                        "success": True,
                        "section": {
                            "id": section.id,
                            "title": section.title,
                            "level": section.level,
                            "line_start": section.line_start,
                            "line_end": section.line_end,
                            "path": section.path
                        },
                        "stateless": True
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Section not found: {section_id}"
                    }
            except Exception as e:
                return self.processor.create_error_response(str(e), type(e).__name__)
        
        @self.mcp.tool()
        def list_sections(document_path: str, validation_level: str = "NORMAL") -> Dict[str, Any]:
            """List all sections (stateless only)."""
            try:
                validation_map = {"STRICT": ValidationLevel.STRICT, "NORMAL": ValidationLevel.NORMAL, "PERMISSIVE": ValidationLevel.PERMISSIVE}
                validation_enum = validation_map.get(validation_level.upper(), ValidationLevel.NORMAL)
                editor = self.processor.load_document(document_path, validation_enum)
                sections = editor.get_sections()
                return {
                    "success": True,
                    "sections": [
                        {
                            "section_id": section.id,
                            "heading": section.title,
                            "level": section.level,
                            "line_start": section.line_start,
                            "line_end": section.line_end,
                            "path": " > ".join(section.path)
                        }
                        for section in sections
                    ],
                    "total_sections": len(sections),
                    "stateless": True
                }
            except Exception as e:
                return self.processor.create_error_response(str(e), type(e).__name__)
        
        @self.mcp.tool()
        def get_document(document_path: str, validation_level: str = "NORMAL") -> Dict[str, Any]:
            """Get the complete document (stateless only)."""
            try:
                validation_map = {"STRICT": ValidationLevel.STRICT, "NORMAL": ValidationLevel.NORMAL, "PERMISSIVE": ValidationLevel.PERMISSIVE}
                validation_enum = validation_map.get(validation_level.upper(), ValidationLevel.NORMAL)
                editor = self.processor.load_document(document_path, validation_enum)
                content = editor.to_markdown()
                statistics = editor.get_statistics()
                return {
                    "success": True,
                    "document": content,
                    "statistics": {
                        "total_sections": statistics.total_sections,
                        "total_lines": statistics.total_lines,
                        "word_count": statistics.word_count,
                        "character_count": statistics.character_count
                    },
                    "document_path": document_path,
                    "stateless": True
                }
            except Exception as e:
                return self.processor.create_error_response(str(e), type(e).__name__)
        
        @self.mcp.tool()
        def save_document(document_path: str, backup: bool = True) -> Dict[str, Any]:
            """Save document to file (stateless only)."""
            try:
                editor = self.processor.load_document(document_path)
                return self.processor.save_document(editor, document_path, backup)
            except Exception as e:
                return self.processor.create_error_response(str(e), type(e).__name__)


# Global instances for direct usage
enhanced_server = EnhancedMarkdownMCPServer()
mcp = enhanced_server.mcp

if __name__ == "__main__":
    print("Starting SafeMarkdownEditor Enhanced MCP Server (Stateless Mode)...")
    mcp.run()
