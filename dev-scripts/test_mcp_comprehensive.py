#!/usr/bin/env python3
"""
Comprehensive MCP Server Testing
Tests all functionality including edge cases and error conditions.
"""

import pytest
import threading
import time
from fastmcp import FastMCP

# Import our MCP server
from src.quantalogic_markdown_mcp.mcp_server import MarkdownMCPServer


class TestMarkdownMCPServer:
    """Comprehensive test suite for MCP server functionality."""
    
    @pytest.fixture
    def server(self):
        """Create a fresh server instance for each test."""
        return MarkdownMCPServer()
    
    def test_server_initialization(self, server):
        """Test server initializes correctly."""
        assert isinstance(server, MarkdownMCPServer)
        assert hasattr(server, 'app')
        assert isinstance(server.app, FastMCP)
    
    def test_basic_document_operations(self, server):
        """Test basic document CRUD operations."""
        # Insert a section
        result = server.insert_section_after(
            section_id=None,
            title="Test Section",
            content="This is test content.",
            level=1
        )
        assert result["success"] is True
        assert "section_id" in result
        section_id = result["section_id"]
        
        # Get the section
        section = server.get_section(section_id)
        assert section["title"] == "Test Section"
        assert section["content"] == "This is test content."
        assert section["level"] == 1
        
        # Update the section
        update_result = server.update_section(
            section_id=section_id,
            title="Updated Test Section",
            new_content="This is updated content.",
            level=2
        )
        assert update_result["success"] is True
        
        # Verify update
        updated_section = server.get_section(section_id)
        assert updated_section["title"] == "Updated Test Section"
        assert updated_section["content"] == "This is updated content."
        assert updated_section["level"] == 2
        
        # Delete the section
        delete_result = server.delete_section(section_id)
        assert delete_result["success"] is True
        
        # Verify deletion
        with pytest.raises(Exception):  # Should raise an error for non-existent section
            server.get_section(section_id)
    
    def test_section_listing(self, server):
        """Test section listing functionality."""
        # Insert multiple sections
        sections = []
        for i in range(3):
            result = server.insert_section_after(
                section_id=None,
                title=f"Section {i+1}",
                content=f"Content for section {i+1}",
                level=1
            )
            sections.append(result["section_id"])
        
        # List all sections
        section_list = server.list_sections()
        assert len(section_list) >= 3
        
        # Verify section order and content
        titles = [s["title"] for s in section_list]
        assert "Section 1" in titles
        assert "Section 2" in titles
        assert "Section 3" in titles
    
    def test_section_moving(self, server):
        """Test section moving functionality."""
        # Create sections for moving
        section1 = server.insert_section_after(
            section_id=None,
            title="First Section",
            content="First content",
            level=1
        )["section_id"]
        
        section2 = server.insert_section_after(
            section_id=section1,
            title="Second Section", 
            content="Second content",
            level=1
        )["section_id"]
        
        section3 = server.insert_section_after(
            section_id=section2,
            title="Third Section",
            content="Third content", 
            level=1
        )["section_id"]
        
        # Move section 3 to position after section 1
        move_result = server.move_section(section3, section1)
        assert move_result["success"] is True
        
        # Verify new order
        sections = server.list_sections()
        section_titles = [s["title"] for s in sections]
        
        # Third section should now be between first and second
        first_idx = section_titles.index("First Section")
        third_idx = section_titles.index("Third Section") 
        second_idx = section_titles.index("Second Section")
        
        assert first_idx < third_idx < second_idx
    
    def test_undo_redo_functionality(self, server):
        """Test undo/redo operations."""
        # Insert a section
        result = server.insert_section_after(
            section_id=None,
            title="Undo Test Section",
            content="Original content",
            level=1
        )
        section_id = result["section_id"]
        
        # Update the section
        server.update_section(
            section_id=section_id,
            title="Updated Title",
            new_content="Updated content",
            level=1
        )
        
        # Verify update
        section = server.get_section(section_id)
        assert section["title"] == "Updated Title"
        assert section["content"] == "Updated content"
        
        # Undo the update
        undo_result = server.undo()
        assert undo_result["success"] is True
        
        # Verify undo worked
        section = server.get_section(section_id)
        assert section["title"] == "Undo Test Section"  # Should be back to original
        assert section["content"] == "Original content"
        
        # Redo the update
        redo_result = server.redo()
        assert redo_result["success"] is True
        
        # Verify redo worked
        section = server.get_section(section_id)
        assert section["title"] == "Updated Title"  # Should be updated again
        assert section["content"] == "Updated content"
    
    def test_document_resource(self, server):
        """Test document resource access."""
        # Add some content
        server.insert_section_after(
            section_id=None,
            title="Resource Test",
            content="Testing document resource",
            level=1
        )
        
        # Get document resource
        document = server.get_document()
        assert "content" in document
        assert "metadata" in document
        assert "Resource Test" in document["content"]
    
    def test_error_handling(self, server):
        """Test error handling for invalid operations."""
        # Test getting non-existent section
        with pytest.raises(Exception):
            server.get_section("non-existent-id")
        
        # Test updating non-existent section
        with pytest.raises(Exception):
            server.update_section(
                section_id="non-existent-id",
                title="Test",
                new_content="Test",
                level=1
            )
        
        # Test deleting non-existent section
        with pytest.raises(Exception):
            server.delete_section("non-existent-id")
        
        # Test moving non-existent section
        with pytest.raises(Exception):
            server.move_section("non-existent-id", None)
    
    def test_thread_safety(self, server):
        """Test thread safety of operations."""
        results = []
        errors = []
        
        def worker(worker_id):
            """Worker function for threading test."""
            try:
                # Each worker inserts a section
                result = server.insert_section_after(
                    section_id=None,
                    title=f"Thread {worker_id} Section",
                    content=f"Content from thread {worker_id}",
                    level=1
                )
                results.append(result)
                
                # Small delay to increase chance of race conditions
                time.sleep(0.01)
                
                # Each worker gets their section
                section = server.get_section(result["section_id"])
                assert section["title"] == f"Thread {worker_id} Section"
                
            except Exception as e:
                errors.append(f"Thread {worker_id}: {e}")
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Thread safety errors: {errors}"
        assert len(results) == 5, f"Expected 5 results, got {len(results)}"
        
        # Verify all sections were created
        all_sections = server.list_sections()
        thread_sections = [s for s in all_sections if "Thread" in s["title"]]
        assert len(thread_sections) >= 5  # At least 5 thread sections
    
    def test_complex_document_structure(self, server):
        """Test complex nested document structure."""
        # Create a hierarchical document structure
        h1_id = server.insert_section_after(
            section_id=None,
            title="Chapter 1",
            content="Chapter 1 introduction",
            level=1
        )["section_id"]
        
        h2_id = server.insert_section_after(
            section_id=h1_id,
            title="Section 1.1", 
            content="First subsection",
            level=2
        )["section_id"]
        
        h3_id = server.insert_section_after(
            section_id=h2_id,
            title="Subsection 1.1.1",
            content="Deep nested content",
            level=3
        )["section_id"]
        
        h2_2_id = server.insert_section_after(
            section_id=h3_id,
            title="Section 1.2",
            content="Second subsection", 
            level=2
        )["section_id"]
        
        # Verify structure
        sections = server.list_sections()
        
        # Find our sections in the list
        chapter1 = next(s for s in sections if s["title"] == "Chapter 1")
        section11 = next(s for s in sections if s["title"] == "Section 1.1")
        subsection111 = next(s for s in sections if s["title"] == "Subsection 1.1.1")
        section12 = next(s for s in sections if s["title"] == "Section 1.2")
        
        assert chapter1["level"] == 1
        assert section11["level"] == 2
        assert subsection111["level"] == 3
        assert section12["level"] == 2
        
        # Test document generation
        document = server.get_document()
        content = document["content"]
        
        # Verify hierarchical structure in markdown
        lines = content.split('\n')
        assert any("# Chapter 1" in line for line in lines)
        assert any("## Section 1.1" in line for line in lines)
        assert any("### Subsection 1.1.1" in line for line in lines)
        assert any("## Section 1.2" in line for line in lines)


def test_performance_benchmark():
    """Basic performance test - not a unit test but useful for validation."""
    server = MarkdownMCPServer()
    
    start_time = time.time()
    
    # Insert 100 sections
    section_ids = []
    for i in range(100):
        result = server.insert_section_after(
            section_id=None,
            title=f"Performance Test Section {i}",
            content=f"Content for performance test section {i}",
            level=1
        )
        section_ids.append(result["section_id"])
    
    insert_time = time.time() - start_time
    
    # Read all sections
    start_read = time.time()
    for section_id in section_ids:
        server.get_section(section_id)
    read_time = time.time() - start_read
    
    # Get full document
    start_doc = time.time()
    server.get_document()
    doc_time = time.time() - start_doc
    
    print(f"\nPerformance Results:")
    print(f"  Insert 100 sections: {insert_time:.3f}s ({insert_time/100*1000:.1f}ms per section)")
    print(f"  Read 100 sections: {read_time:.3f}s ({read_time/100*1000:.1f}ms per section)")
    print(f"  Generate document: {doc_time:.3f}s")
    
    # Basic performance assertions
    assert insert_time < 5.0, f"Insert too slow: {insert_time}s"
    assert read_time < 2.0, f"Read too slow: {read_time}s"  
    assert doc_time < 1.0, f"Document generation too slow: {doc_time}s"


if __name__ == "__main__":
    # Run all tests
    print("🧪 Running comprehensive MCP server tests...")
    
    # Run pytest
    pytest.main([__file__, "-v", "--tb=short"])
    
    # Run performance test separately
    print("\n🚀 Running performance benchmark...")
    test_performance_benchmark()
    
    print("\n✅ All comprehensive tests completed!")
