"""Stateless processor for Markdown operations."""

import os
from pathlib import Path
from typing import Any, Callable, Dict

from .safe_editor import SafeMarkdownEditor
from .safe_editor_types import EditResult, ValidationLevel


class DocumentOperationError(Exception):
    """Base class for document operation errors."""
    pass


class DocumentNotFoundError(DocumentOperationError):
    """Document file not found or not accessible."""
    pass


class ValidationError(DocumentOperationError):
    """Document validation failed."""
    pass


class SectionNotFoundError(DocumentOperationError):
    """Requested section not found in document."""
    pass


class StatelessMarkdownProcessor:
    """Stateless processor for Markdown operations."""
    
    @staticmethod
    def resolve_path(path_str: str) -> Path:
        """Resolve a path string to an absolute Path object."""
        try:
            expanded_path = os.path.expandvars(os.path.expanduser(path_str))
            path = Path(expanded_path).resolve()
            return path
        except Exception as e:
            raise ValueError(f"Could not resolve path '{path_str}': {e}")
    
    @staticmethod
    def validate_file_path(path: Path, must_exist: bool = True, must_be_file: bool = True) -> None:
        """Validate a file path for various conditions."""
        if must_exist and not path.exists():
            raise DocumentNotFoundError(f"Path does not exist: {path}")
        
        if path.exists():
            if must_be_file and path.is_dir():
                raise IsADirectoryError(f"Path is a directory, not a file: {path}")
            
            if not os.access(path, os.R_OK):
                raise PermissionError(f"No read permission for path: {path}")
    
    @staticmethod
    def load_document(document_path: str, validation_level: ValidationLevel = ValidationLevel.NORMAL) -> SafeMarkdownEditor:
        """Load a document and create a SafeMarkdownEditor instance."""
        resolved_path = StatelessMarkdownProcessor.resolve_path(document_path)
        StatelessMarkdownProcessor.validate_file_path(resolved_path, must_exist=True, must_be_file=True)
        
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
        
        # Create editor instance
        editor = SafeMarkdownEditor(
            markdown_text=content,
            validation_level=validation_level
        )
        
        return editor
    
    @staticmethod
    def save_document(editor: SafeMarkdownEditor, document_path: str, backup: bool = True) -> Dict[str, Any]:
        """Save a document to the specified path."""
        target_path = StatelessMarkdownProcessor.resolve_path(document_path)
        
        # Create parent directories if they don't exist
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create backup if requested and file exists
        if backup and target_path.exists():
            backup_path = target_path.with_suffix(f"{target_path.suffix}.bak")
            backup_path.write_bytes(target_path.read_bytes())
        
        # Save the document
        content = editor.to_markdown()
        target_path.write_text(content, encoding='utf-8')
        
        return {
            "success": True,
            "message": f"Successfully saved document to {target_path}",
            "file_path": str(target_path),
            "backup_created": backup and Path(str(target_path) + ".bak").exists(),
            "file_size": len(content)
        }
    
    @staticmethod
    def execute_operation(document_path: str, operation: Callable[[SafeMarkdownEditor], EditResult],
                         auto_save: bool = True, backup: bool = True,
                         validation_level: ValidationLevel = ValidationLevel.NORMAL) -> Dict[str, Any]:
        """Execute an operation on a document."""
        try:
            # Load the document
            editor = StatelessMarkdownProcessor.load_document(document_path, validation_level)
            
            # Execute the operation
            result = operation(editor)
            
            # Handle the result
            response = StatelessMarkdownProcessor.handle_edit_result(result)
            
            # Save if requested and operation was successful
            if auto_save and result.success:
                save_result = StatelessMarkdownProcessor.save_document(editor, document_path, backup)
                response.update({
                    "saved": True,
                    "save_info": save_result
                })
            
            return response
            
        except Exception as e:
            return StatelessMarkdownProcessor.create_error_response(str(e), type(e).__name__)
    
    @staticmethod
    def handle_edit_result(result: EditResult) -> Dict[str, Any]:
        """Convert an EditResult to response format."""
        if result.success:
            response = {
                "success": True,
                "message": "Operation completed successfully",
                "operation": result.operation.value
            }
            
            if result.modified_sections:
                response["modified_sections"] = [
                    {"id": section.id, "title": section.title, "level": section.level}
                    for section in result.modified_sections
                ]
            
            if result.preview:
                response["preview"] = result.preview
            
            # Include metadata if present
            if hasattr(result, 'metadata') and result.metadata:
                response.update(result.metadata)
                
            return response
        else:
            error_messages = [str(error) for error in result.errors]
            return {
                "success": False,
                "error": "; ".join(error_messages) if error_messages else "Operation failed",
                "operation": result.operation.value
            }
    
    @staticmethod
    def create_error_response(error_message: str, error_type: str = "Error") -> Dict[str, Any]:
        """Create a standardized error response."""
        return {
            "success": False,
            "error": {
                "type": error_type,
                "message": error_message
            },
            "suggestions": [
                "Check that the file path is correct",
                "Ensure you have appropriate permissions",
                "Verify the document format is valid"
            ]
        }
