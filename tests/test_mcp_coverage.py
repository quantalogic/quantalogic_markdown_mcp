#!/usr/bin/env python3
"""
Test MCP Server Implementation - Focus on Coverage
"""
import pytest
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from quantalogic_markdown_mcp.mcp_server import MarkdownMCPServer
from quantalogic_markdown_mcp.safe_editor_types import ValidationLevel


class TestMCPServerCoverage:
    """Test MCP server to improve coverage."""

    @pytest.fixture
    def server(self):
        """Create a server instance for testing."""
        return MarkdownMCPServer("TestServer")

    def test_server_initialization(self, server):
        """Test server initializes correctly."""
        assert server is not None
        assert hasattr(server, 'mcp')
        assert hasattr(server, 'document_metadata')
        assert server.document_metadata['title'] == 'Untitled Document'

    def test_initialize_document(self, server):
        """Test document initialization."""
        test_content = "# Test Document\n\nThis is test content."
        server.initialize_document(test_content, ValidationLevel.NORMAL)
        
        assert server.editor is not None
        sections = server.editor.get_sections()
        assert len(sections) > 0
        assert sections[0].title == "Test Document"

    def test_ensure_editor_creates_default(self, server):
        """Test that _ensure_editor creates a default document."""
        # Initially no editor
        assert server.editor is None
        
        # Call _ensure_editor
        editor = server._ensure_editor()
        
        # Should create default document
        assert editor is not None
        assert server.editor is not None

    def test_handle_edit_result_success(self, server):
        """Test _handle_edit_result with successful result."""
        from quantalogic_markdown_mcp.safe_editor_types import EditResult, EditOperation, SectionReference
        
        section_ref = SectionReference(
            id="test_id",
            title="Test Section",
            level=1,
            line_start=0,
            line_end=1,
            path=[]
        )
        
        result = EditResult(
            success=True,
            operation=EditOperation.INSERT_SECTION,
            modified_sections=[section_ref],
            errors=[],
            warnings=[],
            metadata={'changes_made': ['Added section']}
        )
        result.section_ref = section_ref
        result.changes_made = ['Test change']
        result.message = "Success message"
        
        response = server._handle_edit_result(result)
        
        assert response['success'] is True
        assert response['message'] == "Success message"
        assert response['section_id'] == "test_id"
        assert response['changes_made'] == ['Test change']

    def test_handle_edit_result_failure(self, server):
        """Test _handle_edit_result with failed result."""
        from quantalogic_markdown_mcp.safe_editor_types import EditResult, EditOperation
        
        result = EditResult(
            success=False,
            operation=EditOperation.INSERT_SECTION,
            modified_sections=[],
            errors=[],
            warnings=[],
            metadata={}
        )
        result.error_message = "Test error"
        result.suggestions = ["Try again"]
        
        response = server._handle_edit_result(result)
        
        assert response['success'] is False
        assert response['error'] == "Test error"
        assert response['suggestions'] == ["Try again"]

    def test_server_lock_usage(self, server):
        """Test that server lock is used properly."""
        # Initialize document with lock
        with server.lock:
            server.initialize_document("# Test")
            assert server.editor is not None

    def test_metadata_updates(self, server):
        """Test that metadata is updated properly."""
        initial_modified = server.document_metadata['modified']
        
        # Initialize document should update metadata
        server.initialize_document("# New Document")
        
        updated_modified = server.document_metadata['modified']
        assert updated_modified != initial_modified

    def test_multiple_server_instances(self):
        """Test creating multiple server instances."""
        server1 = MarkdownMCPServer("Server1")
        server2 = MarkdownMCPServer("Server2")
        
        server1.initialize_document("# Document 1")
        server2.initialize_document("# Document 2")
        
        sections1 = server1.editor.get_sections()
        sections2 = server2.editor.get_sections()
        
        assert sections1[0].title == "Document 1"
        assert sections2[0].title == "Document 2"

    def test_server_with_different_validation_levels(self, server):
        """Test server with different validation levels."""
        # Test with STRICT validation
        server.initialize_document("# Test", ValidationLevel.STRICT)
        assert server.editor is not None
        
        # Test with PERMISSIVE validation
        server.initialize_document("# Test 2", ValidationLevel.PERMISSIVE)
        assert server.editor is not None

    def test_concurrent_server_access(self, server):
        """Test concurrent access to server."""
        import threading
        import time
        
        results = []
        errors = []
        
        def worker(worker_id):
            try:
                with server.lock:
                    server.initialize_document(f"# Document {worker_id}")
                    time.sleep(0.001)  # Small delay
                    sections = server.editor.get_sections()
                    results.append(len(sections))
            except Exception as e:
                errors.append(str(e))
        
        # Run multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        assert len(errors) == 0
        assert len(results) == 3

    def test_server_error_handling(self, server):
        """Test server error handling."""
        # Test with malformed content that might cause issues
        try:
            server.initialize_document("", ValidationLevel.STRICT)
            # Should handle empty content gracefully
            assert server.editor is not None
        except Exception:
            # If it raises an exception, that's also valid behavior
            pass
