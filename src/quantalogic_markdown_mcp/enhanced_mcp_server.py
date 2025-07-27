"""Enhanced MCP Server with stateless operations and backward compatibility."""

from typing import Any, Dict, Optional

from .mcp_server import MarkdownMCPServer  # Legacy server
from .safe_editor import SafeMarkdownEditor
from .safe_editor_types import EditOperation, ValidationLevel
from .stateless_processor import StatelessMarkdownProcessor


class EnhancedMarkdownMCPServer(MarkdownMCPServer):
    """Enhanced MCP Server with stateless operations and backward compatibility."""
    
    def __init__(self, server_name: str = "SafeMarkdownEditor", legacy_mode: bool = True):
        """Initialize the enhanced MCP server."""
        super().__init__(server_name)
        self.legacy_mode = legacy_mode
        self.processor = StatelessMarkdownProcessor()
        
        # Override tool setup to include enhanced tools
        self._setup_enhanced_tools()
    
    def _is_legacy_call(self, **kwargs) -> bool:
        """Detect if this is a legacy call without document_path."""
        return 'document_path' not in kwargs
    
    def _setup_enhanced_tools(self) -> None:
        """Register enhanced MCP tools with backward compatibility."""
        
        # File Operations
        @self.mcp.tool()
        def load_document(document_path: Optional[str] = None, file_path: Optional[str] = None,
                         validation_level: str = "NORMAL") -> Dict[str, Any]:
            """Load a Markdown document from a file path (enhanced with stateless support)."""
            
            # Handle backward compatibility
            if document_path is None and file_path is not None:
                # Legacy call
                return super(EnhancedMarkdownMCPServer, self).load_document(file_path, validation_level)
            elif document_path is not None:
                # New stateless call
                try:
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
            else:
                return {
                    "success": False,
                    "error": "Either document_path or file_path must be provided",
                    "suggestions": ["Use document_path for new stateless operations", "Use file_path for legacy compatibility"]
                }
        
        # Document Editing Tools with Enhanced Capabilities
        @self.mcp.tool()
        def insert_section(document_path: Optional[str] = None, heading: Optional[str] = None,
                          content: Optional[str] = None, position: Optional[int] = None,
                          auto_save: bool = True, backup: bool = True,
                          validation_level: str = "NORMAL") -> Dict[str, Any]:
            """Insert a new section (enhanced with stateless support)."""
            
            if document_path is None:
                # Legacy call - use existing implementation
                if heading is None or content is None or position is None:
                    return {"success": False, "error": "Missing required parameters for legacy call"}
                return super(EnhancedMarkdownMCPServer, self).insert_section(heading, content, position)
            
            # New stateless implementation
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
                        # Handle empty document case
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
        def delete_section(document_path: Optional[str] = None, section_id: Optional[str] = None,
                          heading: Optional[str] = None, auto_save: bool = True, backup: bool = True,
                          validation_level: str = "NORMAL") -> Dict[str, Any]:
            """Delete a section (enhanced with stateless support)."""
            
            if document_path is None:
                # Legacy call
                return super(EnhancedMarkdownMCPServer, self).delete_section(section_id, heading)
            
            # New stateless implementation
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
        def update_section(document_path: Optional[str] = None, section_id: Optional[str] = None,
                          content: Optional[str] = None, auto_save: bool = True, backup: bool = True,
                          validation_level: str = "NORMAL") -> Dict[str, Any]:
            """Update a section's content (enhanced with stateless support)."""
            
            if document_path is None:
                # Legacy call
                return super(EnhancedMarkdownMCPServer, self).update_section(section_id, content)
            
            # New stateless implementation
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
        def get_section(document_path: Optional[str] = None, section_id: Optional[str] = None,
                       validation_level: str = "NORMAL") -> Dict[str, Any]:
            """Get a specific section (enhanced with stateless support)."""
            
            if document_path is None:
                # Legacy call
                return super(EnhancedMarkdownMCPServer, self).get_section(section_id)
            
            # New stateless implementation
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
        def list_sections(document_path: Optional[str] = None, validation_level: str = "NORMAL") -> Dict[str, Any]:
            """List all sections (enhanced with stateless support)."""
            
            if document_path is None:
                # Legacy call
                return super(EnhancedMarkdownMCPServer, self).list_sections()
            
            # New stateless implementation
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
        def get_document(document_path: Optional[str] = None, validation_level: str = "NORMAL") -> Dict[str, Any]:
            """Get the complete document (enhanced with stateless support)."""
            
            if document_path is None:
                # Legacy call
                return super(EnhancedMarkdownMCPServer, self).get_document()
            
            # New stateless implementation
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
            """Save document to file (stateless - requires source document to load and save)."""
            # This is a bit different - we need to know where to get the content from
            # For true stateless operation, this would be used after other operations
            # For now, we'll provide a simple implementation that assumes the document exists
            try:
                # Load, then immediately save (essentially a copy operation for stateless mode)
                editor = self.processor.load_document(document_path)
                return self.processor.save_document(editor, document_path, backup)
            except Exception as e:
                return self.processor.create_error_response(str(e), type(e).__name__)
