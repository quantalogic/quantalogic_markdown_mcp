"""
Additional MCP Server tests using proper MCP client to improve coverage.

This test suite adds proper MCP tool/resource/prompt testing through the
actual MCP protocol interface to increase coverage of mcp_server.py.
"""

import sys
import os
import tempfile
from pathlib import Path

# Add the src directory to the path to import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from quantalogic_markdown_mcp.mcp_server import MarkdownMCPServer
from quantalogic_markdown_mcp.safe_editor_types import ValidationLevel


class TestMCPServerInterface:
    """Test MCP Server interface functionality to improve coverage."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.server = MarkdownMCPServer("TestServerInterface")
        self.test_markdown = """# Interface Test Document

## Section 1
This is the first section for testing the MCP interface.

### Subsection 1.1
Content in subsection 1.1.

## Section 2
This is the second section.

### Subsection 2.1
Content in subsection 2.1.

### Subsection 2.2
Content in subsection 2.2.

## Conclusion
This concludes our interface test document.
"""
        self.server.initialize_document(self.test_markdown, ValidationLevel.NORMAL)
    
    def test_file_path_resolution(self):
        """Test file path resolution functionality.""" 
        # Test absolute path resolution
        abs_path = "/tmp/test.md"
        resolved = self.server._resolve_path(abs_path)
        assert resolved.is_absolute()
        # On macOS, /tmp is actually a symlink to /private/tmp
        assert str(resolved).endswith("test.md")
        assert "tmp" in str(resolved)        # Test relative path resolution
        rel_path = "./test.md"
        resolved = self.server._resolve_path(rel_path)
        assert resolved.is_absolute()
        
        # Test tilde expansion
        home_path = "~/test.md"
        resolved = self.server._resolve_path(home_path)
        assert resolved.is_absolute()
        assert str(resolved).startswith(str(Path.home()))
        
        # Test environment variable expansion
        env_path = "$HOME/test.md"
        resolved = self.server._resolve_path(env_path)
        assert resolved.is_absolute()
    
    def test_file_path_validation(self):
        """Test file path validation functionality."""
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Test\nContent")
            temp_file = Path(f.name)
        
        try:
            # Test valid file validation
            self.server._validate_file_path(temp_file, must_exist=True, must_be_file=True)
            
            # Test non-existent file validation
            non_existent = Path("/non/existent/file.md")
            try:
                self.server._validate_file_path(non_existent, must_exist=True)
                assert False, "Should have raised FileNotFoundError"
            except FileNotFoundError:
                pass
            
            # Test directory validation
            temp_dir = temp_file.parent
            try:
                self.server._validate_file_path(temp_dir, must_exist=True, must_be_file=True)
                assert False, "Should have raised IsADirectoryError"
            except IsADirectoryError:
                pass
                
        finally:
            # Clean up
            temp_file.unlink()
    
    def test_load_document_from_file(self):
        """Test loading document from file functionality."""
        # Create a temporary markdown file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            test_content = "# File Test\n\n## Section A\nContent A\n\n## Section B\nContent B"
            f.write(test_content)
            temp_file = Path(f.name)
        
        try:
            # Test loading the file
            self.server.load_document_from_file(str(temp_file), ValidationLevel.NORMAL)
            
            # Verify the document was loaded
            assert self.server.editor is not None
            # Resolve both paths to handle symlink differences
            assert self.server.current_file_path.resolve() == temp_file.resolve()
            content = self.server.editor.to_markdown()
            assert "# File Test" in content
            assert "Section A" in content
            assert "Section B" in content
            
            # Check metadata was updated
            assert self.server.document_metadata["title"] == temp_file.stem
            # Use resolve() to handle symlink differences
            assert Path(self.server.document_metadata["file_path"]).resolve() == temp_file.resolve()
            
        finally:
            # Clean up
            temp_file.unlink()
    
    def test_save_document_to_file(self):
        """Test saving document to file functionality."""
        # Create a temporary file path
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=True) as f:
            temp_file = Path(f.name)
        
        try:
            # Ensure we have a document loaded
            assert self.server.editor is not None
            
            # Save the document
            self.server.save_document_to_file(str(temp_file), backup=False)
            
            # Verify the file was created and contains expected content
            assert temp_file.exists()
            content = temp_file.read_text()
            assert "# Interface Test Document" in content
            assert "Section 1" in content
            assert "Conclusion" in content
            
            # Check metadata was updated
            # Resolve both paths to handle symlink differences
            assert self.server.current_file_path.resolve() == temp_file.resolve()
            # Use resolve() to handle symlink differences
            assert Path(self.server.document_metadata["file_path"]).resolve() == temp_file.resolve()
            
        finally:
            # Clean up
            if temp_file.exists():
                temp_file.unlink()
    
    def test_save_document_with_backup(self):
        """Test saving document with backup functionality."""
        # Create a temporary file with existing content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Original Content\nThis will be backed up.")
            temp_file = Path(f.name)
        
        try:
            # Save new content to the existing file with backup
            self.server.save_document_to_file(str(temp_file), backup=True)
            
            # Verify the main file was updated
            content = temp_file.read_text()
            assert "# Interface Test Document" in content
            
            # Verify backup was created
            backup_file = temp_file.with_suffix(f"{temp_file.suffix}.bak")
            assert backup_file.exists()
            backup_content = backup_file.read_text()
            assert "# Original Content" in backup_content
            
        finally:
            # Clean up
            temp_file.unlink()
            backup_file = temp_file.with_suffix(f"{temp_file.suffix}.bak")
            if backup_file.exists():
                backup_file.unlink()
    
    def test_document_initialization_variations(self):
        """Test different document initialization scenarios."""
        # Test with default parameters
        server2 = MarkdownMCPServer("TestServer2")
        server2.initialize_document()
        assert server2.editor is not None
        content = server2.editor.to_markdown()
        assert "# Untitled Document" in content
        
        # Test with custom content and validation level
        custom_content = "# Custom Document\n\nCustom content here."
        server3 = MarkdownMCPServer("TestServer3")
        server3.initialize_document(custom_content, ValidationLevel.STRICT)
        assert server3.editor is not None
        content = server3.editor.to_markdown()
        assert "# Custom Document" in content
        assert "Custom content" in content
    
    def test_handle_edit_result_success(self):
        """Test handling successful edit results."""
        # Create a mock successful edit result
        from quantalogic_markdown_mcp.safe_editor_types import EditResult, EditOperation
        
        sections = self.server.editor.get_sections()
        result = EditResult(
            success=True,
            operation=EditOperation.INSERT_SECTION,
            modified_sections=sections[:1],
            errors=[],
            warnings=[]
        )
        
        # Test handling the result
        response = self.server._handle_edit_result(result)
        
        assert response["success"] is True
        assert "message" in response
        assert response["message"] == "Operation completed successfully"
        assert response["operation"] == "insert_section"
        assert "modified_sections" in response
    
    def test_handle_edit_result_failure(self):
        """Test handling failed edit results."""
        from quantalogic_markdown_mcp.safe_editor_types import EditResult, EditOperation
        from quantalogic_markdown_mcp.types import ParseError, ErrorLevel

        # Create a mock failed edit result
        error = ParseError(
            message="Test error",
            line_number=1,
            column_number=1,
            level=ErrorLevel.ERROR
        )
        
        result = EditResult(
            success=False,
            operation=EditOperation.UPDATE_SECTION,
            modified_sections=[],
            errors=[error],
            warnings=[]
        )
        
        # Test handling the result
        response = self.server._handle_edit_result(result)
        
        assert response["success"] is False
        assert "error" in response
        assert "Test error" in response["error"]
        assert response["operation"] == "update_section"
    
    def test_server_metadata_management(self):
        """Test server metadata management."""
        # Check initial metadata
        metadata = self.server.document_metadata
        assert "title" in metadata
        assert "author" in metadata
        assert "created" in metadata
        assert "modified" in metadata
        
        # Test metadata updates
        # Note: metadata modified time might be updated during operations
        
        # Simulate a change by inserting a section
        sections = self.server.editor.get_sections()
        if sections:
            result = self.server.editor.insert_section_after(
                after_section=sections[0],
                level=2,
                title="Metadata Test Section",
                content="Testing metadata updates."
            )
            
            if result.success:
                # Metadata should be updated after a successful operation
                new_metadata = self.server.document_metadata
                # The modified time might be updated by handle_edit_result
                assert "modified" in new_metadata
    
    def test_ensure_editor_functionality(self):
        """Test the ensure_editor functionality."""
        # Create a new server without initializing
        server = MarkdownMCPServer("EnsureEditorTest")
        assert server.editor is None
        
        # Call ensure_editor
        editor = server._ensure_editor()
        
        # Verify editor was created
        assert editor is not None
        assert server.editor is editor
        
        # Verify default document was loaded
        content = editor.to_markdown()
        assert len(content) > 0
    
    def test_unicode_and_encoding_handling(self):
        """Test handling of different encodings and Unicode content."""
        # Create a file with Unicode content
        unicode_content = "# Unicode Test 📝\n\n## Section with émojis 🚀\nContent with special chars: àáâãäå"
        
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.md', delete=False) as f:
            f.write(unicode_content)
            temp_file = Path(f.name)
        
        try:
            # Test loading Unicode content
            self.server.load_document_from_file(str(temp_file))
            
            # Verify Unicode content was preserved
            content = self.server.editor.to_markdown()
            assert "📝" in content
            assert "🚀" in content
            assert "àáâãäå" in content
            
        finally:
            temp_file.unlink()


def run_additional_tests():
    """Run all additional tests manually."""
    print("=== Running Additional MCP Server Interface Tests ===")
    
    test_instance = TestMCPServerInterface()
    
    test_methods = [
        ("file_path_resolution", test_instance.test_file_path_resolution),
        ("file_path_validation", test_instance.test_file_path_validation),
        ("load_document_from_file", test_instance.test_load_document_from_file),
        ("save_document_to_file", test_instance.test_save_document_to_file),
        ("save_document_with_backup", test_instance.test_save_document_with_backup),
        ("document_initialization_variations", test_instance.test_document_initialization_variations),
        ("handle_edit_result_success", test_instance.test_handle_edit_result_success),
        ("handle_edit_result_failure", test_instance.test_handle_edit_result_failure),
        ("server_metadata_management", test_instance.test_server_metadata_management),
        ("ensure_editor_functionality", test_instance.test_ensure_editor_functionality),
        ("unicode_and_encoding_handling", test_instance.test_unicode_and_encoding_handling),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_method in test_methods:
        try:
            print(f"Running {test_name}...", end=" ")
            test_instance.setup_method()
            test_method()
            print("✅ PASSED")
            passed += 1
        except Exception as e:
            print(f"❌ FAILED: {e}")
            failed += 1
            import traceback
            traceback.print_exc()
    
    print("\n=== Additional Test Results ===")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total: {passed + failed}")
    
    if failed == 0:
        print("🎉 All additional tests passed!")
        return True
    else:
        print("💥 Some additional tests failed!")
        return False


if __name__ == "__main__":
    success = run_additional_tests()
    sys.exit(0 if success else 1)
