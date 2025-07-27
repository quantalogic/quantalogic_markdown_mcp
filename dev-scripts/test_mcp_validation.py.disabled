#!/usr/bin/env python3
"""
Simple MCP Server Testing
Basic validation of MCP server functionality.
"""

import sys
import os

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from quantalogic_markdown_mcp.mcp_server import MarkdownMCPServer
from quantalogic_markdown_mcp.safe_editor import SafeMarkdownEditor


def test_server_creation():
    """Test that the MCP server can be created successfully."""
    print("🔧 Testing MCP server creation...")
    
    server = MarkdownMCPServer()
    assert server is not None
    assert hasattr(server, 'mcp')
    assert server.mcp is not None
    
    print("✅ Server creation test passed!")


def test_editor_initialization():
    """Test that the editor can be initialized."""
    print("🔧 Testing editor initialization...")
    
    server = MarkdownMCPServer()
    server.initialize_document("# Test Document\n\nThis is a test.")
    
    assert server.editor is not None
    assert isinstance(server.editor, SafeMarkdownEditor)
    
    print("✅ Editor initialization test passed!")


def test_safe_editor_functionality():
    """Test that the underlying SafeMarkdownEditor works correctly."""
    print("🔧 Testing SafeMarkdownEditor functionality...")
    
    # Create a SafeMarkdownEditor directly
    editor = SafeMarkdownEditor("# Test Document\n\nThis is test content.")
    
    # Test section listing
    sections = editor.get_sections()
    assert len(sections) > 0
    assert sections[0].title == "Test Document"
    
    # Test section insertion
    result = editor.insert_section_after(
        after_section=sections[0],
        level=2,
        title="New Section",
        content="New section content"
    )
    assert result.success
    
    # Verify insertion
    updated_sections = editor.get_sections()
    assert len(updated_sections) == 2
    assert updated_sections[1].title == "New Section"
    
    print("✅ SafeMarkdownEditor functionality test passed!")


def test_mcp_structure():
    """Test that the MCP server has the expected structure."""
    print("🔧 Testing MCP server structure...")
    
    server = MarkdownMCPServer()
    
    # Check that FastMCP instance exists
    assert hasattr(server, 'mcp')
    
    # Check that tools are registered (we can't easily test this without
    # running the actual MCP protocol, but we can verify the structure exists)
    assert server.mcp is not None
    
    print("✅ MCP server structure test passed!")


def test_document_metadata():
    """Test document metadata functionality."""
    print("🔧 Testing document metadata...")
    
    server = MarkdownMCPServer()
    
    # Check initial metadata
    assert 'title' in server.document_metadata
    assert 'author' in server.document_metadata
    assert 'created' in server.document_metadata
    assert 'modified' in server.document_metadata
    
    # Initialize document and check metadata updates
    initial_modified = server.document_metadata['modified']
    server.initialize_document("# New Document\n\nContent here.")
    
    # Modified time should have changed
    assert server.document_metadata['modified'] != initial_modified
    
    print("✅ Document metadata test passed!")


def test_thread_safety_basic():
    """Test basic thread safety of server creation."""
    print("🔧 Testing basic thread safety...")
    
    import threading
    import time
    
    servers = []
    errors = []
    
    def create_server(server_id):
        try:
            server = MarkdownMCPServer(f"TestServer{server_id}")
            server.initialize_document(f"# Document {server_id}\n\nContent for server {server_id}")
            servers.append(server)
            time.sleep(0.01)  # Small delay to test concurrency
            
            # Verify server is functional
            assert server.editor is not None
            sections = server.editor.get_sections()
            assert len(sections) > 0
            assert f"Document {server_id}" in sections[0].title
            
        except Exception as e:
            errors.append(f"Server {server_id}: {e}")
    
    # Create multiple servers in parallel
    threads = []
    for i in range(3):
        thread = threading.Thread(target=create_server, args=(i,))
        threads.append(thread)
    
    # Start all threads
    for thread in threads:
        thread.start()
    
    # Wait for completion
    for thread in threads:
        thread.join()
    
    # Check results
    assert len(errors) == 0, f"Thread safety errors: {errors}"
    assert len(servers) == 3, f"Expected 3 servers, got {len(servers)}"
    
    print("✅ Basic thread safety test passed!")


def main():
    """Run all tests."""
    print("🧪 Running MCP Server validation tests...\n")
    
    try:
        test_server_creation()
        test_editor_initialization()
        test_safe_editor_functionality()
        test_mcp_structure()
        test_document_metadata()
        test_thread_safety_basic()
        
        print("\n🎉 All MCP Server validation tests passed!")
        print("✅ The MCP server implementation is working correctly!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
