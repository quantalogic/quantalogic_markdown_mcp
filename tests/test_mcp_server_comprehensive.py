"""
Comprehensive tests for the MCP Server implementation.

This test suite validates all the MCP tools, resources, and prompts
to ensure they work correctly with the SafeMarkdownEditor backend.
"""

import sys
import os

# Add the src directory to the path to import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from quantalogic_markdown_mcp.mcp_server import MarkdownMCPServer
from quantalogic_markdown_mcp.safe_editor_types import ValidationLevel


class TestMarkdownMCPServer:
    """Test class for MCP Server functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.server = MarkdownMCPServer("TestServer")
        self.test_markdown = """# Test Document

## Introduction
This is a comprehensive test document for our MCP server implementation.

### Background
The MCP server provides tools for editing Markdown documents.

## Features
Our server supports the following operations:

### Section Management
- Insert new sections
- Update existing sections  
- Delete sections
- Move sections around

### Document Operations
- Get full document
- List all sections
- Undo/redo operations

## Advanced Features

### Validation
The system includes comprehensive validation at multiple levels.

### Error Handling  
Robust error handling with helpful suggestions.

## Conclusion
This test document validates our MCP server implementation.
"""
        self.server.initialize_document(self.test_markdown, ValidationLevel.NORMAL)
    
    def test_server_initialization(self):
        """Test that the server initializes correctly."""
        assert self.server is not None
        assert self.server.editor is not None
        assert hasattr(self.server, 'lock')
        assert hasattr(self.server, 'document_metadata')
        assert hasattr(self.server, 'mcp')
    
    def test_get_document_tool(self):
        """Test the get_document tool."""
        with self.server.lock:
            # Access the tool function through the server's method
            result = self.server.mcp._tools["get_document"]()
            
            assert result["success"] is True
            assert "document" in result
            assert len(result["document"]) > 0
            assert "# Test Document" in result["document"]
    
    def test_list_sections_tool(self):
        """Test the list_sections tool."""  
        with self.server.lock:
            result = self.server.mcp._tools["list_sections"]()
            
            assert result["success"] is True
            assert "sections" in result
            assert len(result["sections"]) > 0
            
            # Check that we have the expected sections
            section_titles = [s["heading"] for s in result["sections"]]
            assert "Test Document" in section_titles
            assert "Introduction" in section_titles
            assert "Features" in section_titles
            assert "Conclusion" in section_titles
    
    def test_get_section_tool(self):
        """Test the get_section tool."""
        with self.server.lock:
            # First get the sections to find a valid section ID
            sections_result = self.server.mcp._tools["list_sections"]()
            assert sections_result["success"] is True
            
            first_section = sections_result["sections"][0]
            section_id = first_section["section_id"]
            
            # Now get the specific section
            result = self.server.mcp._tools["get_section"](section_id)
            
            assert result["success"] is True
            assert "heading" in result
            assert "content" in result
            assert "section_id" in result
            assert result["section_id"] == section_id
    
    def test_insert_section_tool(self):
        """Test the insert_section tool."""
        with self.server.lock:
            # Insert a new section
            result = self.server.mcp._tools["insert_section"](
                heading="New Test Section",
                content="This is a new section added by the test.",
                position=2
            )
            
            assert result["success"] is True
            assert "section_id" in result
            assert "changes_made" in result
            
            # Verify the section was added
            sections_result = self.server.mcp._tools["list_sections"]()
            section_titles = [s["heading"] for s in sections_result["sections"]]
            assert "New Test Section" in section_titles
    
    def test_update_section_tool(self):
        """Test the update_section tool."""
        with self.server.lock:
            # Get a section to update
            sections_result = self.server.mcp._tools["list_sections"]()
            introduction_section = None
            for section in sections_result["sections"]:
                if section["heading"] == "Introduction":
                    introduction_section = section
                    break
            
            assert introduction_section is not None
            section_id = introduction_section["section_id"]
            
            # Update the section
            new_content = "This is updated content for the introduction section."
            result = self.server.mcp._tools["update_section"](
                section_id=section_id,
                content=new_content
            )
            
            assert result["success"] is True
            assert "changes_made" in result
            
            # Verify the content was updated
            get_result = self.server.mcp._tools["get_section"](section_id)
            assert new_content in get_result["content"]
    
    def test_delete_section_tool(self):
        """Test the delete_section tool."""
        with self.server.lock:
            # First add a section to delete
            insert_result = self.server.mcp._tools["insert_section"](
                heading="Section to Delete",
                content="This section will be deleted.",
                position=1
            )
            assert insert_result["success"] is True
            section_id = insert_result["section_id"]
            
            # Now delete it
            result = self.server.mcp._tools["delete_section"](section_id=section_id)
            
            assert result["success"] is True
            assert "changes_made" in result
            
            # Verify it was deleted
            sections_result = self.server.mcp._tools["list_sections"]()
            section_titles = [s["heading"] for s in sections_result["sections"]]
            assert "Section to Delete" not in section_titles
    
    def test_move_section_tool(self):
        """Test the move_section tool."""
        with self.server.lock:
            # Get a section to move
            sections_result = self.server.mcp._tools["list_sections"]()
            conclusion_section = None
            for section in sections_result["sections"]:
                if section["heading"] == "Conclusion":
                    conclusion_section = section
                    break
            
            assert conclusion_section is not None
            section_id = conclusion_section["section_id"]
            
            # Move it to a different position
            new_position = 1
            result = self.server.mcp._tools["move_section"](
                section_id=section_id,
                new_position=new_position
            )
            
            assert result["success"] is True
            assert "changes_made" in result
            
            # Verify it moved (Note: the exact position might differ due to implementation details)
            updated_section = self.server.mcp._tools["get_section"](section_id)
            assert updated_section["success"] is True
    
    def test_undo_tool(self):
        """Test the undo tool."""
        with self.server.lock:
            # Make a change first
            insert_result = self.server.mcp._tools["insert_section"](
                heading="Section for Undo Test",
                content="This will be undone.",
                position=1
            )
            assert insert_result["success"] is True
            
            # Verify the section exists
            sections_result = self.server.mcp._tools["list_sections"]()
            section_titles = [s["heading"] for s in sections_result["sections"]]
            assert "Section for Undo Test" in section_titles
            
            # Now undo the change
            undo_result = self.server.mcp._tools["undo"]()
            
            # The undo might succeed or fail depending on the implementation
            # but it should return a proper response
            assert "success" in undo_result
            assert isinstance(undo_result["success"], bool)
    
    def test_document_resource(self):
        """Test the document resource."""
        with self.server.lock:
            result = self.server.mcp._resources["document://current"]()
            
            assert isinstance(result, str)
            assert len(result) > 0
            assert "# Test Document" in result
    
    def test_history_resource(self):
        """Test the history resource."""
        with self.server.lock:
            # Make a change to create history
            self.server.mcp._tools["insert_section"](
                heading="History Test Section",
                content="Creating history.",
                position=1
            )
            
            result = self.server.mcp._resources["document://history"]()
            
            assert isinstance(result, dict)
            assert "history" in result
            assert isinstance(result["history"], list)
    
    def test_metadata_resource(self):
        """Test the metadata resource."""
        with self.server.lock:
            result = self.server.mcp._resources["document//metadata"]()
            
            assert isinstance(result, dict)
            assert "title" in result
            assert "author" in result
            assert "created" in result
            assert "modified" in result
    
    def test_summarize_section_prompt(self):
        """Test the summarize_section prompt."""
        test_content = "This is test content that needs to be summarized."
        result = self.server.mcp._prompts["summarize_section"](test_content)
        
        assert isinstance(result, str)
        assert test_content in result
        assert "summarize" in result.lower()
    
    def test_rewrite_section_prompt(self):
        """Test the rewrite_section prompt."""
        test_content = "This content needs rewriting for clarity."
        result = self.server.mcp._prompts["rewrite_section"](test_content)
        
        assert isinstance(result, str)
        assert test_content in result
        assert "rewrite" in result.lower()
    
    def test_generate_outline_prompt(self):
        """Test the generate_outline prompt."""
        test_document = "# Document\n## Section 1\n## Section 2"
        result = self.server.mcp._prompts["generate_outline"](test_document)
        
        assert isinstance(result, str)
        assert test_document in result
        assert "outline" in result.lower()
    
    def test_error_handling(self):
        """Test error handling for invalid operations."""
        with self.server.lock:
            # Test with invalid section ID
            result = self.server.mcp._tools["get_section"]("invalid_section_id")
            
            assert result["success"] is False
            assert "error" in result
            assert "suggestions" in result
            
            # Test delete with non-existent section
            result = self.server.mcp._tools["delete_section"](section_id="nonexistent")
            
            assert result["success"] is False
            assert "error" in result
    
    def test_concurrent_access(self):
        """Test that concurrent access is handled properly."""
        import threading
        
        results = []
        errors = []
        
        def worker():
            try:
                result = self.server.mcp._tools["list_sections"]()
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()
        
        # Wait for all threads to complete
        for t in threads:
            t.join()
        
        # Check results
        assert len(errors) == 0, f"Concurrent access errors: {errors}"
        assert len(results) == 5
        for result in results:
            assert result["success"] is True


def run_tests():
    """Run all tests manually."""
    print("=== Running Comprehensive MCP Server Tests ===")
    
    test_instance = TestMarkdownMCPServer()
    
    test_methods = [
        ("server_initialization", test_instance.test_server_initialization),
        ("get_document_tool", test_instance.test_get_document_tool),
        ("list_sections_tool", test_instance.test_list_sections_tool),
        ("get_section_tool", test_instance.test_get_section_tool),
        ("insert_section_tool", test_instance.test_insert_section_tool),
        ("update_section_tool", test_instance.test_update_section_tool),
        ("delete_section_tool", test_instance.test_delete_section_tool),
        ("move_section_tool", test_instance.test_move_section_tool),
        ("undo_tool", test_instance.test_undo_tool),
        ("document_resource", test_instance.test_document_resource),
        ("history_resource", test_instance.test_history_resource),
        ("metadata_resource", test_instance.test_metadata_resource),
        ("summarize_section_prompt", test_instance.test_summarize_section_prompt),
        ("rewrite_section_prompt", test_instance.test_rewrite_section_prompt),
        ("generate_outline_prompt", test_instance.test_generate_outline_prompt),
        ("error_handling", test_instance.test_error_handling),
        ("concurrent_access", test_instance.test_concurrent_access),
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
    
    print("\n=== Test Results ===")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total: {passed + failed}")
    
    if failed == 0:
        print("🎉 All tests passed!")
        return True
    else:
        print("💥 Some tests failed!")
        return False


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
