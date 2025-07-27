"""Unit tests for StatelessMarkdownProcessor."""

import pytest
import tempfile
from pathlib import Path

from quantalogic_markdown_mcp.stateless_processor import (
    StatelessMarkdownProcessor,
    DocumentNotFoundError
)
from quantalogic_markdown_mcp.safe_editor_types import ValidationLevel
from test_utils.stateless_test_helpers import StatelessTestHelper


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
        # Both paths should resolve to the same file, but one may have /private prefix on macOS
        assert resolved.samefile(temp_file)
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
        assert editor._validation_level == validation_level
        
        temp_file.unlink()  # Cleanup
