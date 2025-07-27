# Implementation Plan: Document Path Parameter Enhancement

## Overview

This document provides a detailed implementation plan for adding `document_path` as the first parameter to all MCP tools, transforming the SafeMarkdownEditor from a stateful to a stateless architecture while maintaining backward compatibility and ensuring comprehensive test coverage.

## Implementation Strategy

### Phase 1: Foundation and Preparation (Week 1-2)

#### 1.1 Create New Core Components

**A. Stateless Processor Engine**

Create `src/quantalogic_markdown_mcp/stateless_processor.py`:

```python
"""Stateless processor for Markdown operations."""

import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

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
```

**B. Enhanced MCP Server**

Create `src/quantalogic_markdown_mcp/enhanced_mcp_server.py`:

```python
"""Enhanced MCP Server with stateless operations and backward compatibility."""

import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

from .mcp_server import MarkdownMCPServer  # Legacy server
from .safe_editor import SafeMarkdownEditor
from .safe_editor_types import ValidationLevel
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
                return super().load_document(file_path, validation_level)
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
                return super().insert_section(heading, content, position)
            
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
                        from .safe_editor_types import EditResult, OperationType
                        return EditResult(
                            success=False,
                            operation=OperationType.INSERT,
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
                        from .safe_editor_types import EditResult, OperationType
                        return EditResult(
                            success=False,
                            operation=OperationType.INSERT,
                            errors=[f"Position {position} is out of range"]
                        )
            
            validation_map = {"STRICT": ValidationLevel.STRICT, "NORMAL": ValidationLevel.NORMAL, "PERMISSIVE": ValidationLevel.PERMISSIVE}
            validation_enum = validation_map.get(validation_level.upper(), ValidationLevel.NORMAL)
            
            return self.processor.execute_operation(document_path, operation, auto_save, backup, validation_enum)
        
        # Add similar enhanced implementations for other tools...
        # (This would continue for all tools following the same pattern)
```

#### 1.2 Test Infrastructure Setup

**A. Create Test Utilities**

Create `tests/test_utils/stateless_test_helpers.py`:

```python
"""Test utilities for stateless operations."""

import tempfile
from pathlib import Path
from typing import Dict, Any

from quantalogic_markdown_mcp.stateless_processor import StatelessMarkdownProcessor
from quantalogic_markdown_mcp.safe_editor_types import ValidationLevel


class StatelessTestHelper:
    """Helper class for testing stateless operations."""
    
    @staticmethod
    def create_temp_document(content: str) -> Path:
        """Create a temporary document for testing."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
        temp_file.write(content)
        temp_file.close()
        return Path(temp_file.name)
    
    @staticmethod
    def create_sample_document() -> str:
        """Create sample document content for testing."""
        return """# Test Document

## Introduction
This is a test document.

## Features
- Feature 1
- Feature 2

## Conclusion
End of document.
"""
    
    @staticmethod
    def assert_operation_success(result: Dict[str, Any], expected_message: str = None):
        """Assert that an operation was successful."""
        assert result["success"] is True, f"Operation failed: {result.get('error', 'Unknown error')}"
        if expected_message:
            assert expected_message in result.get("message", ""), f"Expected message not found: {result}"
    
    @staticmethod
    def assert_operation_failure(result: Dict[str, Any], expected_error: str = None):
        """Assert that an operation failed as expected."""
        assert result["success"] is False, f"Operation should have failed but succeeded: {result}"
        if expected_error:
            error_msg = result.get("error", {})
            if isinstance(error_msg, dict):
                error_msg = error_msg.get("message", str(error_msg))
            assert expected_error in str(error_msg), f"Expected error not found: {result}"
```

**B. Enhanced Test Configuration**

Update `pytest.ini`:

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --tb=short
    --cov=src/quantalogic_markdown_mcp
    --cov-report=html:htmlcov
    --cov-report=term-missing
    --cov-report=xml
    --cov-fail-under=95
markers =
    unit: Unit tests
    integration: Integration tests
    stateless: Tests for stateless operations
    legacy: Tests for legacy compatibility
    performance: Performance tests
    slow: Tests that take a long time to run
```

### Phase 2: Core Implementation (Week 3-4)

#### 2.1 Implement Enhanced Tools

**A. Complete Enhanced Server Implementation**

Finish implementing all tools in `enhanced_mcp_server.py` with the pattern:

1. Check for `document_path` parameter
2. If present, use stateless operation
3. If absent, fall back to legacy implementation
4. Add comprehensive error handling
5. Support new parameters (auto_save, backup, etc.)

**B. Tool Implementation Priority:**

1. **High Priority (Week 3):**
   - `load_document` ✓
   - `insert_section` ✓
   - `delete_section`
   - `update_section`
   - `get_section`
   - `list_sections`

2. **Medium Priority (Week 4):**
   - `move_section`
   - `get_document`
   - `save_document`
   - New advanced tools (batch_operations, analyze_document)

#### 2.2 Test Implementation Strategy

**A. Test Structure:**

```
tests/
├── unit/
│   ├── test_stateless_processor.py      # Core stateless functionality
│   ├── test_enhanced_mcp_server.py      # Enhanced server tests
│   └── test_backward_compatibility.py   # Legacy compatibility tests
├── integration/
│   ├── test_stateless_operations.py     # End-to-end stateless tests
│   ├── test_multi_document_ops.py       # Multi-document operations
│   └── test_concurrent_operations.py    # Concurrency tests
├── performance/
│   ├── test_memory_usage.py             # Memory efficiency tests
│   └── test_operation_latency.py        # Performance benchmarks
└── fixtures/
    ├── sample_documents/                 # Test document samples
    └── test_scenarios.py                # Common test scenarios
```

**B. Core Test Implementation**

Create `tests/unit/test_stateless_processor.py`:

```python
"""Unit tests for StatelessMarkdownProcessor."""

import pytest
import tempfile
from pathlib import Path

from quantalogic_markdown_mcp.stateless_processor import (
    StatelessMarkdownProcessor,
    DocumentNotFoundError,
    ValidationError
)
from quantalogic_markdown_mcp.safe_editor_types import ValidationLevel
from tests.test_utils.stateless_test_helpers import StatelessTestHelper


class TestStatelessMarkdownProcessor:
    """Test cases for StatelessMarkdownProcessor."""
    
    def setup_method(self):
        """Set up test environment."""
        self.processor = StatelessMarkdownProcessor()
        self.helper = StatelessTestHelper()
        self.sample_content = self.helper.create_sample_document()
    
    def test_resolve_path_absolute(self):
        """Test path resolution with absolute paths."""
        temp_file = self.helper.create_temp_document(self.sample_content)
        resolved = self.processor.resolve_path(str(temp_file))
        assert resolved == temp_file
        temp_file.unlink()  # Cleanup
    
    def test_resolve_path_relative(self):
        """Test path resolution with relative paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.md"
            test_file.write_text(self.sample_content)
            
            # Change to temp directory and test relative path
            import os
            old_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                resolved = self.processor.resolve_path("test.md")
                assert resolved.name == "test.md"
                assert resolved.exists()
            finally:
                os.chdir(old_cwd)
    
    def test_resolve_path_tilde_expansion(self):
        """Test path resolution with tilde expansion."""
        path_with_tilde = "~/test_document.md"
        resolved = self.processor.resolve_path(path_with_tilde)
        assert "~" not in str(resolved)
        assert str(resolved).startswith(str(Path.home()))
    
    def test_validate_file_path_exists(self):
        """Test file path validation for existing files."""
        temp_file = self.helper.create_temp_document(self.sample_content)
        
        # Should not raise exception
        self.processor.validate_file_path(temp_file, must_exist=True, must_be_file=True)
        
        temp_file.unlink()  # Cleanup
    
    def test_validate_file_path_not_exists(self):
        """Test file path validation for non-existing files."""
        non_existent = Path("/non/existent/file.md")
        
        with pytest.raises(DocumentNotFoundError):
            self.processor.validate_file_path(non_existent, must_exist=True)
    
    def test_validate_file_path_directory(self):
        """Test file path validation when path is a directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            with pytest.raises(IsADirectoryError):
                self.processor.validate_file_path(temp_path, must_exist=True, must_be_file=True)
    
    def test_load_document_success(self):
        """Test successful document loading."""
        temp_file = self.helper.create_temp_document(self.sample_content)
        
        editor = self.processor.load_document(str(temp_file), ValidationLevel.NORMAL)
        
        assert editor is not None
        assert len(editor.get_sections()) > 0
        assert "Test Document" in editor.to_markdown()
        
        temp_file.unlink()  # Cleanup
    
    def test_load_document_not_found(self):
        """Test loading non-existent document."""
        with pytest.raises(DocumentNotFoundError):
            self.processor.load_document("/non/existent/file.md")
    
    def test_save_document_success(self):
        """Test successful document saving."""
        # Load a document
        temp_file = self.helper.create_temp_document(self.sample_content)
        editor = self.processor.load_document(str(temp_file))
        
        # Save to a new location
        with tempfile.TemporaryDirectory() as temp_dir:
            new_file = Path(temp_dir) / "saved_document.md"
            result = self.processor.save_document(editor, str(new_file), backup=False)
            
            self.helper.assert_operation_success(result)
            assert new_file.exists()
            assert "Test Document" in new_file.read_text()
        
        temp_file.unlink()  # Cleanup
    
    def test_save_document_with_backup(self):
        """Test document saving with backup creation."""
        # Create original file
        temp_file = self.helper.create_temp_document(self.sample_content)
        editor = self.processor.load_document(str(temp_file))
        
        # Modify and save
        result = self.processor.save_document(editor, str(temp_file), backup=True)
        
        self.helper.assert_operation_success(result)
        assert result["backup_created"] is True
        
        backup_file = Path(str(temp_file) + ".bak")
        assert backup_file.exists()
        
        # Cleanup
        temp_file.unlink()
        backup_file.unlink()
    
    def test_execute_operation_success(self):
        """Test successful operation execution."""
        temp_file = self.helper.create_temp_document(self.sample_content)
        
        def test_operation(editor):
            sections = editor.get_sections()
            if sections:
                return editor.insert_section_after(
                    after_section=sections[0],
                    level=2,
                    title="New Section",
                    content="New content"
                )
        
        result = self.processor.execute_operation(
            str(temp_file), test_operation, auto_save=True, backup=False
        )
        
        self.helper.assert_operation_success(result)
        assert result["saved"] is True
        
        # Verify the change was saved
        saved_content = temp_file.read_text()
        assert "New Section" in saved_content
        
        temp_file.unlink()  # Cleanup
    
    def test_execute_operation_no_auto_save(self):
        """Test operation execution without auto-save."""
        temp_file = self.helper.create_temp_document(self.sample_content)
        original_content = temp_file.read_text()
        
        def test_operation(editor):
            sections = editor.get_sections()
            if sections:
                return editor.insert_section_after(
                    after_section=sections[0],
                    level=2,
                    title="New Section",
                    content="New content"
                )
        
        result = self.processor.execute_operation(
            str(temp_file), test_operation, auto_save=False
        )
        
        self.helper.assert_operation_success(result)
        assert result.get("saved", False) is False
        
        # Verify the change was NOT saved
        current_content = temp_file.read_text()
        assert current_content == original_content
        
        temp_file.unlink()  # Cleanup
    
    @pytest.mark.parametrize("validation_level", [
        ValidationLevel.STRICT,
        ValidationLevel.NORMAL,
        ValidationLevel.PERMISSIVE
    ])
    def test_different_validation_levels(self, validation_level):
        """Test loading with different validation levels."""
        temp_file = self.helper.create_temp_document(self.sample_content)
        
        editor = self.processor.load_document(str(temp_file), validation_level)
        
        assert editor is not None
        assert editor.validation_level == validation_level
        
        temp_file.unlink()  # Cleanup
```

Create `tests/unit/test_enhanced_mcp_server.py`:

```python
"""Unit tests for EnhancedMarkdownMCPServer."""

import pytest
import tempfile
from pathlib import Path

from quantalogic_markdown_mcp.enhanced_mcp_server import EnhancedMarkdownMCPServer
from tests.test_utils.stateless_test_helpers import StatelessTestHelper


class TestEnhancedMarkdownMCPServer:
    """Test cases for EnhancedMarkdownMCPServer."""
    
    def setup_method(self):
        """Set up test environment."""
        self.server = EnhancedMarkdownMCPServer(legacy_mode=True)
        self.helper = StatelessTestHelper()
        self.sample_content = self.helper.create_sample_document()
    
    def test_load_document_stateless(self):
        """Test stateless document loading."""
        temp_file = self.helper.create_temp_document(self.sample_content)
        
        # Use new stateless API
        result = self.server.load_document(document_path=str(temp_file))
        
        self.helper.assert_operation_success(result)
        assert result["stateless"] is True
        assert result["sections_count"] > 0
        assert "content_preview" in result
        
        temp_file.unlink()  # Cleanup
    
    def test_load_document_legacy(self):
        """Test legacy document loading."""
        temp_file = self.helper.create_temp_document(self.sample_content)
        
        # Use legacy API
        result = self.server.load_document(file_path=str(temp_file))
        
        self.helper.assert_operation_success(result)
        assert "stateless" not in result or result["stateless"] is False
        
        temp_file.unlink()  # Cleanup
    
    def test_insert_section_stateless(self):
        """Test stateless section insertion."""
        temp_file = self.helper.create_temp_document(self.sample_content)
        
        result = self.server.insert_section(
            document_path=str(temp_file),
            heading="New Section",
            content="This is new content",
            position=1,
            auto_save=True
        )
        
        self.helper.assert_operation_success(result)
        assert result.get("saved", False) is True
        
        # Verify the change was saved
        saved_content = temp_file.read_text()
        assert "New Section" in saved_content
        
        temp_file.unlink()  # Cleanup
    
    def test_insert_section_legacy(self):
        """Test legacy section insertion."""
        temp_file = self.helper.create_temp_document(self.sample_content)
        
        # First load document in legacy mode
        self.server.load_document(file_path=str(temp_file))
        
        # Then insert section using legacy API
        result = self.server.insert_section(
            heading="Legacy Section",
            content="Legacy content",
            position=1
        )
        
        self.helper.assert_operation_success(result)
        
        temp_file.unlink()  # Cleanup
    
    def test_backward_compatibility_detection(self):
        """Test detection of legacy vs new API calls."""
        # Test legacy call detection
        assert self.server._is_legacy_call(heading="test", content="test") is True
        
        # Test new call detection
        assert self.server._is_legacy_call(document_path="/path/to/doc.md") is False
    
    def test_missing_parameters_error(self):
        """Test error handling for missing parameters."""
        # Call with neither document_path nor file_path
        result = self.server.load_document()
        
        self.helper.assert_operation_failure(result, "must be provided")
    
    def test_auto_save_parameter(self):
        """Test auto_save parameter functionality."""
        temp_file = self.helper.create_temp_document(self.sample_content)
        original_content = temp_file.read_text()
        
        # Test with auto_save=False
        result = self.server.insert_section(
            document_path=str(temp_file),
            heading="Temp Section",
            content="Temp content",
            position=1,
            auto_save=False
        )
        
        self.helper.assert_operation_success(result)
        assert result.get("saved", False) is False
        
        # Content should be unchanged
        current_content = temp_file.read_text()
        assert current_content == original_content
        
        temp_file.unlink()  # Cleanup
    
    def test_backup_parameter(self):
        """Test backup parameter functionality."""
        temp_file = self.helper.create_temp_document(self.sample_content)
        
        # Test with backup=True
        result = self.server.insert_section(
            document_path=str(temp_file),
            heading="Test Section",
            content="Test content", 
            position=1,
            auto_save=True,
            backup=True
        )
        
        self.helper.assert_operation_success(result)
        
        if result.get("saved") and result.get("save_info"):
            save_info = result["save_info"]
            assert save_info.get("backup_created", False) is True
        
        temp_file.unlink()  # Cleanup
        backup_file = Path(str(temp_file) + ".bak")
        if backup_file.exists():
            backup_file.unlink()
```

### Phase 3: Advanced Features (Week 5-6)

#### 3.1 Implement New Advanced Tools

**A. Batch Operations Tool**

```python
@self.mcp.tool()
def batch_operations(document_path: str, operations: List[Dict[str, Any]],
                    auto_save: bool = True, backup: bool = True,
                    atomic: bool = True, validation_level: str = "NORMAL") -> Dict[str, Any]:
    """Execute multiple operations on a document atomically."""
    
    def batch_operation(editor):
        results = []
        original_state = None
        
        if atomic:
            # Store original state for potential rollback
            original_state = editor.to_markdown()
        
        try:
            for i, op in enumerate(operations):
                action = op.get("action")
                
                if action == "insert_section":
                    result = editor.insert_section_after(
                        after_section=editor.get_sections()[op.get("position", 0)],
                        level=op.get("level", 2),
                        title=op["heading"],
                        content=op["content"]
                    )
                elif action == "update_section":
                    section = editor.get_section_by_id(op["section_id"])
                    result = editor.update_section_content(
                        section_ref=section,
                        content=op["content"]
                    )
                elif action == "delete_section":
                    section = editor.get_section_by_id(op["section_id"])
                    result = editor.delete_section(section, cascade=True)
                else:
                    raise ValueError(f"Unknown operation: {action}")
                
                if not result.success:
                    if atomic:
                        # Rollback all changes
                        editor = SafeMarkdownEditor(original_state)
                        raise Exception(f"Operation {i} failed: {result.errors}")
                    else:
                        results.append({"operation": i, "success": False, "errors": result.errors})
                else:
                    results.append({"operation": i, "success": True})
            
            return EditResult(success=True, operation=OperationType.UPDATE, results=results)
            
        except Exception as e:
            return EditResult(success=False, operation=OperationType.UPDATE, errors=[str(e)])
    
    validation_map = {"STRICT": ValidationLevel.STRICT, "NORMAL": ValidationLevel.NORMAL, "PERMISSIVE": ValidationLevel.PERMISSIVE}
    validation_enum = validation_map.get(validation_level.upper(), ValidationLevel.NORMAL)
    
    return self.processor.execute_operation(document_path, batch_operation, auto_save, backup, validation_enum)
```

#### 3.2 Comprehensive Integration Tests

Create `tests/integration/test_stateless_operations.py`:

```python
"""Integration tests for stateless operations."""

import pytest
import tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from quantalogic_markdown_mcp.enhanced_mcp_server import EnhancedMarkdownMCPServer
from tests.test_utils.stateless_test_helpers import StatelessTestHelper


class TestStatelessIntegration:
    """Integration tests for stateless operations."""
    
    def setup_method(self):
        """Set up test environment."""
        self.server = EnhancedMarkdownMCPServer(legacy_mode=True)
        self.helper = StatelessTestHelper()
    
    def test_full_document_workflow(self):
        """Test complete document manipulation workflow."""
        temp_file = self.helper.create_temp_document(self.helper.create_sample_document())
        
        # 1. Load and inspect document
        load_result = self.server.load_document(document_path=str(temp_file))
        self.helper.assert_operation_success(load_result)
        original_sections = load_result["sections_count"]
        
        # 2. Insert a new section
        insert_result = self.server.insert_section(
            document_path=str(temp_file),
            heading="Workflow Test Section",
            content="This section was added during workflow testing.",
            position=1,
            auto_save=True
        )
        self.helper.assert_operation_success(insert_result)
        
        # 3. Verify the change
        verify_result = self.server.load_document(document_path=str(temp_file))
        self.helper.assert_operation_success(verify_result)
        assert verify_result["sections_count"] == original_sections + 1
        
        # 4. List all sections
        sections_result = self.server.list_sections(document_path=str(temp_file))
        self.helper.assert_operation_success(sections_result)
        
        section_titles = [s["heading"] for s in sections_result["sections"]]
        assert "Workflow Test Section" in section_titles
        
        temp_file.unlink()  # Cleanup
    
    def test_concurrent_operations_different_documents(self):
        """Test concurrent operations on different documents."""
        # Create multiple test documents
        documents = []
        for i in range(5):
            content = f"# Document {i}\n\n## Section 1\nContent for document {i}."
            temp_file = self.helper.create_temp_document(content)
            documents.append(temp_file)
        
        # Define operations to perform concurrently
        def perform_operations(doc_path, doc_id):
            operations = []
            
            # Load document
            result = self.server.load_document(document_path=str(doc_path))
            operations.append(("load", result))
            
            # Insert section
            result = self.server.insert_section(
                document_path=str(doc_path),
                heading=f"Concurrent Section {doc_id}",
                content=f"Content added concurrently for doc {doc_id}",
                position=1,
                auto_save=True
            )
            operations.append(("insert", result))
            
            return operations
        
        # Execute operations concurrently
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(perform_operations, doc, i): i 
                for i, doc in enumerate(documents)
            }
            
            results = {}
            for future in as_completed(futures):
                doc_id = futures[future]
                try:
                    results[doc_id] = future.result()
                except Exception as e:
                    pytest.fail(f"Concurrent operation failed for document {doc_id}: {e}")
        
        # Verify all operations succeeded
        for doc_id, operations in results.items():
            for op_type, result in operations:
                self.helper.assert_operation_success(result, f"Document {doc_id} {op_type} failed")
        
        # Cleanup
        for doc in documents:
            doc.unlink()
    
    def test_batch_operations_integration(self):
        """Test batch operations functionality."""
        temp_file = self.helper.create_temp_document(self.helper.create_sample_document())
        
        # Prepare batch operations
        operations = [
            {
                "action": "insert_section",
                "heading": "Batch Section 1",
                "content": "First batch section",
                "position": 1
            },
            {
                "action": "insert_section", 
                "heading": "Batch Section 2",
                "content": "Second batch section",
                "position": 2
            }
        ]
        
        # Execute batch operations
        result = self.server.batch_operations(
            document_path=str(temp_file),
            operations=operations,
            atomic=True,
            auto_save=True
        )
        
        self.helper.assert_operation_success(result)
        
        # Verify both sections were added
        final_content = temp_file.read_text()
        assert "Batch Section 1" in final_content
        assert "Batch Section 2" in final_content
        
        temp_file.unlink()  # Cleanup
    
    def test_error_recovery_and_rollback(self):
        """Test error recovery in atomic batch operations."""
        temp_file = self.helper.create_temp_document(self.helper.create_sample_document())
        original_content = temp_file.read_text()
        
        # Prepare batch operations with one invalid operation
        operations = [
            {
                "action": "insert_section",
                "heading": "Valid Section",
                "content": "This should work",
                "position": 1
            },
            {
                "action": "invalid_action",  # This will fail
                "heading": "Invalid Section"
            }
        ]
        
        # Execute batch operations with atomic=True
        result = self.server.batch_operations(
            document_path=str(temp_file),
            operations=operations,
            atomic=True,
            auto_save=True
        )
        
        # Should fail due to invalid operation
        self.helper.assert_operation_failure(result)
        
        # Document should remain unchanged due to rollback
        current_content = temp_file.read_text()
        assert current_content == original_content
        assert "Valid Section" not in current_content
        
        temp_file.unlink()  # Cleanup
```

### Phase 4: Testing and Quality Assurance (Week 7-8)

#### 4.1 Comprehensive Test Suite

**A. Performance Tests**

Create `tests/performance/test_memory_usage.py`:

```python
"""Memory usage tests for stateless vs stateful operations."""

import pytest
import psutil
import tempfile
from pathlib import Path

from quantalogic_markdown_mcp.enhanced_mcp_server import EnhancedMarkdownMCPServer
from quantalogic_markdown_mcp.mcp_server import MarkdownMCPServer
from tests.test_utils.stateless_test_helpers import StatelessTestHelper


class TestMemoryUsage:
    """Test memory usage patterns."""
    
    def setup_method(self):
        """Set up test environment."""
        self.helper = StatelessTestHelper()
        
    def measure_memory_usage(self, operation):
        """Measure memory usage during operation."""
        process = psutil.Process()
        memory_before = process.memory_info().rss
        
        operation()
        
        memory_after = process.memory_info().rss
        return memory_after - memory_before
    
    def test_stateless_vs_stateful_memory_usage(self):
        """Compare memory usage between stateless and stateful operations."""
        # Create test documents
        large_content = "# Large Document\n\n" + ("## Section\nContent\n\n" * 100)
        documents = []
        for i in range(10):
            temp_file = self.helper.create_temp_document(large_content)
            documents.append(temp_file)
        
        # Test stateful server (legacy)
        def test_stateful():
            legacy_server = MarkdownMCPServer()
            for doc in documents:
                legacy_server.load_document_from_file(str(doc))
                # Simulate keeping documents in memory
        
        # Test stateless server
        def test_stateless():
            stateless_server = EnhancedMarkdownMCPServer()
            for doc in documents:
                stateless_server.load_document(document_path=str(doc))
                # Documents are not kept in memory
        
        stateful_memory = self.measure_memory_usage(test_stateful)
        stateless_memory = self.measure_memory_usage(test_stateless)
        
        # Stateless should use significantly less memory
        assert stateless_memory < stateful_memory * 0.5, f"Stateless: {stateless_memory}, Stateful: {stateful_memory}"
        
        # Cleanup
        for doc in documents:
            doc.unlink()
    
    def test_concurrent_memory_efficiency(self):
        """Test memory efficiency under concurrent load."""
        # This test would measure memory usage during concurrent operations
        # Implementation details would depend on specific performance requirements
        pass
```

**B. Compatibility Tests**

Create `tests/unit/test_backward_compatibility.py`:

```python
"""Backward compatibility tests."""

import pytest
import tempfile

from quantalogic_markdown_mcp.enhanced_mcp_server import EnhancedMarkdownMCPServer
from quantalogic_markdown_mcp.mcp_server import MarkdownMCPServer
from tests.test_utils.stateless_test_helpers import StatelessTestHelper


class TestBackwardCompatibility:
    """Test backward compatibility with legacy API."""
    
    def setup_method(self):
        """Set up test environment."""
        self.legacy_server = MarkdownMCPServer()
        self.enhanced_server = EnhancedMarkdownMCPServer(legacy_mode=True)
        self.helper = StatelessTestHelper()
    
    def test_all_legacy_calls_work(self):
        """Test that all legacy API calls still work."""
        temp_file = self.helper.create_temp_document(self.helper.create_sample_document())
        
        # Test all legacy operations on both servers
        legacy_operations = [
            ("load_document", {"file_path": str(temp_file)}),
            ("insert_section", {"heading": "Test", "content": "Test content", "position": 1}),
            ("list_sections", {}),
            ("get_document", {}),
            ("save_document", {})
        ]
        
        for op_name, params in legacy_operations:
            # Test legacy server
            legacy_method = getattr(self.legacy_server, op_name)
            legacy_result = legacy_method(**params)
            
            # Test enhanced server with same parameters
            enhanced_method = getattr(self.enhanced_server, op_name)
            enhanced_result = enhanced_method(**params)
            
            # Results should be similar (accounting for enhancements)
            assert legacy_result["success"] == enhanced_result["success"]
            
        temp_file.unlink()  # Cleanup
    
    def test_mixed_api_usage(self):
        """Test mixing legacy and new API calls."""
        temp_file = self.helper.create_temp_document(self.helper.create_sample_document())
        
        # Load with legacy API
        load_result = self.enhanced_server.load_document(file_path=str(temp_file))
        self.helper.assert_operation_success(load_result)
        
        # Insert with new API
        insert_result = self.enhanced_server.insert_section(
            document_path=str(temp_file),
            heading="Mixed API Section",
            content="Added with new API",
            position=1,
            auto_save=True
        )
        self.helper.assert_operation_success(insert_result)
        
        # List with legacy API
        sections_result = self.enhanced_server.list_sections()
        self.helper.assert_operation_success(sections_result)
        
        temp_file.unlink()  # Cleanup
```

#### 4.2 Documentation and Migration Guide

**A. Update API Documentation**

Update `README.md` with new API examples:

```markdown
### New Stateless API (Recommended)

```python
# Single call operations - no state management required
await client.call_tool("insert_section", {
    "document_path": "~/Documents/my-notes.md",
    "heading": "New Section",
    "content": "Section content here",
    "position": 1,
    "auto_save": True,
    "backup": True
})

await client.call_tool("batch_operations", {
    "document_path": "~/Documents/complex-doc.md",
    "operations": [
        {"action": "insert_section", "heading": "Intro", "content": "...", "position": 0},
        {"action": "update_section", "section_id": "sec_123", "content": "Updated"},
        {"action": "delete_section", "section_id": "sec_456"}
    ],
    "atomic": True,
    "auto_save": True
})
```

### Legacy API (Still Supported)

```python
# Multi-step operations with state management
await client.call_tool("load_document", {"file_path": "~/Documents/my-notes.md"})
await client.call_tool("insert_section", {"heading": "New Section", "content": "...", "position": 1})
await client.call_tool("save_document", {})
```
```

**B. Create Migration Script**

Create `scripts/migrate_to_stateless.py`:

```python
#!/usr/bin/env python3
"""Migration script to help users adopt the new stateless API."""

import re
import sys
from pathlib import Path


def migrate_code_file(file_path: Path) -> bool:
    """Migrate a Python file to use the new stateless API."""
    content = file_path.read_text()
    original_content = content
    
    # Migration patterns
    migrations = [
        # Convert load_document calls
        (
            r'call_tool\("load_document",\s*\{\s*"file_path":\s*([^}]+)\}\)',
            r'call_tool("load_document", {"document_path": \1})'
        ),
        # Convert insert_section calls to include document_path
        (
            r'call_tool\("insert_section",\s*\{\s*"heading":\s*([^,]+),\s*"content":\s*([^,]+),\s*"position":\s*([^}]+)\}\)',
            r'call_tool("insert_section", {"document_path": "YOUR_DOCUMENT_PATH", "heading": \1, "content": \2, "position": \3, "auto_save": True})'
        ),
        # Add more migration patterns as needed
    ]
    
    for pattern, replacement in migrations:
        content = re.sub(pattern, replacement, content)
    
    if content != original_content:
        # Create backup
        backup_path = file_path.with_suffix(file_path.suffix + '.backup')
        backup_path.write_text(original_content)
        
        # Write migrated content
        file_path.write_text(content)
        print(f"Migrated {file_path} (backup created at {backup_path})")
        return True
    
    return False


def main():
    """Main migration function."""
    if len(sys.argv) != 2:
        print("Usage: python migrate_to_stateless.py <directory_or_file>")
        sys.exit(1)
    
    path = Path(sys.argv[1])
    
    if path.is_file():
        files = [path]
    elif path.is_dir():
        files = list(path.rglob("*.py"))
    else:
        print(f"Error: {path} is not a valid file or directory")
        sys.exit(1)
    
    migrated_count = 0
    for file_path in files:
        if migrate_code_file(file_path):
            migrated_count += 1
    
    print(f"Migration complete. {migrated_count} files were modified.")
    print("Please review the changes and update document_path placeholders with actual paths.")


if __name__ == "__main__":
    main()
```

### Phase 5: Deployment and Monitoring (Week 9-10)

#### 5.1 Final Integration and Testing

**A. End-to-End Testing**

Create comprehensive end-to-end tests that simulate real-world usage:

```python
# tests/e2e/test_real_world_scenarios.py
"""End-to-end tests simulating real-world usage scenarios."""

import pytest
import tempfile
from pathlib import Path

from quantalogic_markdown_mcp.enhanced_mcp_server import EnhancedMarkdownMCPServer


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""
    
    def test_documentation_editing_workflow(self):
        """Test a typical documentation editing workflow."""
        # Simulate editing a project README
        server = EnhancedMarkdownMCPServer()
        
        # Create initial README
        readme_content = """# My Project

## Overview
This is a sample project.

## Installation
Coming soon.

## Usage
Coming soon.
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(readme_content)
            readme_path = f.name
        
        try:
            # 1. Analyze existing structure
            analysis = server.load_document(document_path=readme_path)
            assert analysis["success"]
            
            # 2. Add a features section
            server.insert_section(
                document_path=readme_path,
                heading="Features",
                content="- Feature 1\n- Feature 2\n- Feature 3",
                position=1,
                auto_save=True
            )
            
            # 3. Update installation section
            sections = server.list_sections(document_path=readme_path)
            install_section = next(s for s in sections["sections"] if s["heading"] == "Installation")
            
            server.update_section(
                document_path=readme_path,
                section_id=install_section["section_id"],
                content="```bash\nnpm install my-project\n```",
                auto_save=True
            )
            
            # 4. Verify final document
            final_doc = server.get_document(document_path=readme_path)
            final_content = final_doc["document"]
            
            assert "Features" in final_content
            assert "npm install" in final_content
            assert final_content.count("#") >= 4  # At least 4 sections
            
        finally:
            Path(readme_path).unlink()
    
    def test_multi_document_project_management(self):
        """Test managing multiple documents in a project."""
        # Simulate managing documentation for a multi-file project
        server = EnhancedMarkdownMCPServer()
        
        # Create multiple documents
        documents = {
            "README.md": "# Project\n\n## Overview\nMain project file.",
            "CONTRIBUTING.md": "# Contributing\n\n## Guidelines\nHow to contribute.",
            "API.md": "# API Documentation\n\n## Endpoints\nAPI reference."
        }
        
        temp_files = {}
        try:
            # Create temporary files
            for name, content in documents.items():
                with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
                    f.write(content)
                    temp_files[name] = f.name
            
            # Batch operations across multiple documents
            for doc_name, file_path in temp_files.items():
                # Add a "Status" section to each document
                server.insert_section(
                    document_path=file_path,
                    heading="Status",
                    content=f"This document is part of the {doc_name} project documentation.",
                    position=1,
                    auto_save=True
                )
            
            # Verify all documents were updated
            for doc_name, file_path in temp_files.items():
                doc_content = server.get_document(document_path=file_path)
                assert "Status" in doc_content["document"]
                assert doc_name in doc_content["document"]
            
        finally:
            # Cleanup
            for file_path in temp_files.values():
                Path(file_path).unlink()
```

#### 5.2 Performance Benchmarking

Create performance benchmarks to ensure the new architecture meets performance requirements:

```python
# tests/performance/test_benchmarks.py
"""Performance benchmarks for the enhanced MCP server."""

import time
import statistics
import tempfile
from pathlib import Path

from quantalogic_markdown_mcp.enhanced_mcp_server import EnhancedMarkdownMCPServer
from quantalogic_markdown_mcp.mcp_server import MarkdownMCPServer


class TestPerformanceBenchmarks:
    """Performance benchmarks and comparisons."""
    
    def benchmark_operation(self, operation, iterations=100):
        """Benchmark an operation over multiple iterations."""
        times = []
        
        for _ in range(iterations):
            start_time = time.time()
            operation()
            end_time = time.time()
            times.append(end_time - start_time)
        
        return {
            "mean": statistics.mean(times),
            "median": statistics.median(times),
            "stdev": statistics.stdev(times) if len(times) > 1 else 0,
            "min": min(times),
            "max": max(times)
        }
    
    def test_load_document_performance(self):
        """Benchmark document loading performance."""
        # Create test document
        large_content = "# Large Document\n\n" + ("## Section\n" + "Content line\n" * 50 + "\n") * 20
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(large_content)
            temp_path = f.name
        
        try:
            # Benchmark stateless loading
            stateless_server = EnhancedMarkdownMCPServer()
            
            def stateless_load():
                result = stateless_server.load_document(document_path=temp_path)
                assert result["success"]
            
            stateless_stats = self.benchmark_operation(stateless_load, iterations=50)
            
            # Benchmark legacy loading
            legacy_server = MarkdownMCPServer()
            
            def legacy_load():
                result = legacy_server.load_document(file_path=temp_path)
                assert result["success"]
            
            legacy_stats = self.benchmark_operation(legacy_load, iterations=50)
            
            print(f"Stateless loading: {stateless_stats['mean']:.4f}s ± {stateless_stats['stdev']:.4f}s")
            print(f"Legacy loading: {legacy_stats['mean']:.4f}s ± {legacy_stats['stdev']:.4f}s")
            
            # Stateless should be competitive (within 50% of legacy performance)
            assert stateless_stats['mean'] < legacy_stats['mean'] * 1.5
            
        finally:
            Path(temp_path).unlink()
```

## Testing Strategy Summary

### Test Coverage Requirements

- **Unit Tests**: 95%+ coverage for all new components
- **Integration Tests**: Cover all tool interactions and workflows
- **Performance Tests**: Ensure stateless operations meet performance requirements
- **Compatibility Tests**: Verify 100% backward compatibility with legacy API
- **End-to-End Tests**: Simulate real-world usage scenarios

### Test Categories and Priorities

1. **Critical (Must Pass)**:
   - All legacy functionality still works
   - New stateless operations work correctly
   - No memory leaks or performance regressions
   - Thread safety maintained

2. **Important (Should Pass)**:
   - Advanced features (batch operations, analysis tools)
   - Error handling and recovery
   - Concurrent operations
   - File system edge cases

3. **Nice to Have (May Pass)**:
   - Performance optimizations beyond baseline
   - Advanced analysis features
   - Complex transformation operations

### Continuous Integration Setup

Update `.github/workflows/test.yml`:

```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: [3.11, 3.12]
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install uv
        uv sync --group dev
    
    - name: Run unit tests
      run: uv run pytest tests/unit/ -v --cov=src --cov-report=xml
      
    - name: Run integration tests
      run: uv run pytest tests/integration/ -v
      
    - name: Run compatibility tests
      run: uv run pytest tests/unit/test_backward_compatibility.py -v
      
    - name: Run performance benchmarks
      run: uv run pytest tests/performance/ -v --benchmark-only
      
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

## Deployment Checklist

### Pre-Deployment

- [ ] All tests passing (unit, integration, compatibility)
- [ ] Performance benchmarks meet requirements
- [ ] Documentation updated with new API examples
- [ ] Migration guide and script tested
- [ ] Backward compatibility verified
- [ ] Security review completed (if applicable)

### Deployment

- [ ] Version bump in `pyproject.toml`
- [ ] Release notes prepared
- [ ] PyPI package built and tested
- [ ] GitHub release created
- [ ] Documentation deployed

### Post-Deployment

- [ ] Monitor for issues in real-world usage
- [ ] Collect user feedback on new features
- [ ] Performance monitoring in production environments
- [ ] Plan deprecation timeline for legacy features (if applicable)

## Success Metrics

### Technical Metrics

- **Test Coverage**: Maintain >95% test coverage
- **Performance**: Stateless operations within 150% of legacy performance
- **Memory Usage**: 50%+ reduction in memory usage for multi-document workflows
- **Concurrency**: Support 10+ concurrent document operations without degradation

### User Experience Metrics

- **API Adoption**: Track usage of new vs legacy API calls
- **Error Rates**: Monitor error rates in production deployments
- **User Feedback**: Collect feedback on ease of migration and new features
- **Documentation**: Ensure comprehensive examples and migration guides

This implementation plan provides a structured approach to delivering the enhanced MCP tools while maintaining reliability, performance, and backward compatibility. The phased approach ensures steady progress with regular validation points, while the comprehensive testing strategy ensures quality and reliability throughout the development process.
