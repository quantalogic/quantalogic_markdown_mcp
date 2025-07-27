"""Comprehensive tests for MCP server tools using direct tool calls."""

import pytest
import tempfile
from pathlib import Path
from quantalogic_markdown_mcp.mcp_server import MarkdownMCPServer


class TestMCPToolsComprehensive:
    """Test the actual MCP tools through the server interface."""
    
    @pytest.fixture
    def server(self):
        """Create a server instance for testing."""
        server = MarkdownMCPServer()
        # Initialize with test document  
        test_content = """# Test Document

## Introduction
This is the introduction section.

## Main Content
This section contains the main content.

### Subsection 1
Content for subsection 1.

### Subsection 2
Content for subsection 2.

## Conclusion
This is the conclusion.
"""
        server.initialize_document(test_content)
        return server
    
    def test_load_document_tool_success(self, server):
        """Test load_document tool with successful file loading."""
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Tool Test\n\n## Section A\nContent A")
            temp_file = Path(f.name)
        
        try:
            # Access the tool function directly 
            server._setup_tools()
            
            # Find and call the load_document tool
            found_tool = False
            for tool in server.mcp._tools:
                if tool.name == "load_document":
                    result = tool.handler(str(temp_file), "NORMAL")
                    found_tool = True
                    break
            
            assert found_tool, "load_document tool not found"
            assert result["success"] is True
            assert "Tool Test" in result["message"]
            
        finally:
            if temp_file.exists():
                temp_file.unlink()
    
    def test_load_document_tool_file_not_found(self, server):
        """Test load_document tool with non-existent file."""
        server._setup_tools()
        
        # Find and call the load_document tool with bad path
        for tool in server.mcp._tools:
            if tool.name == "load_document":
                result = tool.handler("/nonexistent/path.md", "NORMAL")
                break
        
        assert result["success"] is False
        assert "error" in result
    
    def test_save_document_tool_success(self, server):
        """Test save_document tool functionality."""
        server._setup_tools()
        
        # Create temp path
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=True) as f:
            temp_path = f.name
        
        # Find and call the save_document tool
        for tool in server.mcp._tools:
            if tool.name == "save_document":
                result = tool.handler(temp_path, True)
                break
        
        assert result["success"] is True
        assert Path(temp_path).exists()
        
        # Clean up
        Path(temp_path).unlink()
    
    def test_get_document_tool(self, server):
        """Test get_document tool."""
        server._setup_tools()
        
        for tool in server.mcp._tools:
            if tool.name == "get_document":
                result = tool.handler()
                break
        
        assert result["success"] is True
        assert "content" in result
        assert "# Test Document" in result["content"]
    
    def test_list_sections_tool(self, server):
        """Test list_sections tool."""
        server._setup_tools()
        
        for tool in server.mcp._tools:
            if tool.name == "list_sections":
                result = tool.handler()
                break
        
        assert result["success"] is True
        assert "sections" in result
        assert len(result["sections"]) > 0
        
        # Check for expected sections
        section_titles = [s["title"] for s in result["sections"]]
        assert "Test Document" in section_titles
        assert "Introduction" in section_titles
        assert "Main Content" in section_titles
    
    def test_get_section_tool_by_id(self, server):
        """Test get_section tool using section ID."""
        server._setup_tools()
        
        # First get sections to find an ID
        sections = server.ensure_editor().get_sections()
        test_section = sections[1]  # Get the "Introduction" section
        
        for tool in server.mcp._tools:
            if tool.name == "get_section":
                result = tool.handler(section_id=test_section.id)
                break
        
        assert result["success"] is True
        assert "section" in result
        assert result["section"]["title"] == test_section.title
    
    def test_get_section_tool_by_title(self, server):
        """Test get_section tool using section title."""
        server._setup_tools()
        
        for tool in server.mcp._tools:
            if tool.name == "get_section":
                result = tool.handler(title="Introduction")
                break
        
        assert result["success"] is True
        assert "section" in result
        assert result["section"]["title"] == "Introduction"
    
    def test_insert_section_tool(self, server):
        """Test insert_section tool."""
        server._setup_tools()
        
        # Get a section to insert after
        sections = server.ensure_editor().get_sections()
        intro_section = next(s for s in sections if s.title == "Introduction")
        
        for tool in server.mcp._tools:
            if tool.name == "insert_section":
                result = tool.handler(
                    after_section_id=intro_section.id,
                    level=2,
                    title="New Section",
                    content="This is new content."
                )
                break
        
        assert result["success"] is True
        assert "operation" in result
        
        # Verify section was added
        updated_sections = server.ensure_editor().get_sections()
        new_section_titles = [s.title for s in updated_sections]
        assert "New Section" in new_section_titles
    
    def test_update_section_tool(self, server):
        """Test update_section tool."""
        server._setup_tools()
        
        # Get a section to update
        sections = server.ensure_editor().get_sections()
        intro_section = next(s for s in sections if s.title == "Introduction")
        
        for tool in server.mcp._tools:
            if tool.name == "update_section":
                result = tool.handler(
                    section_id=intro_section.id,
                    content="Updated introduction content."
                )
                break
        
        assert result["success"] is True
        
        # Verify content was updated
        content = server.ensure_editor().to_markdown()
        assert "Updated introduction content" in content
    
    def test_delete_section_tool(self, server):
        """Test delete_section tool."""
        server._setup_tools()
        
        # Get a section to delete (use subsection to avoid hierarchy issues)
        sections = server.ensure_editor().get_sections()
        subsection = next(s for s in sections if s.title == "Subsection 1")
        
        for tool in server.mcp._tools:
            if tool.name == "delete_section":
                result = tool.handler(section_id=subsection.id)
                break
        
        assert result["success"] is True
        
        # Verify section was deleted
        updated_sections = server.ensure_editor().get_sections()
        section_titles = [s.title for s in updated_sections]
        assert "Subsection 1" not in section_titles
    
    def test_move_section_tool(self, server):
        """Test move_section tool."""
        server._setup_tools()
        
        # Get sections for moving
        sections = server.ensure_editor().get_sections()
        conclusion = next(s for s in sections if s.title == "Conclusion")
        main_content = next(s for s in sections if s.title == "Main Content")
        
        for tool in server.mcp._tools:
            if tool.name == "move_section":
                result = tool.handler(
                    section_id=conclusion.id,
                    target_section_id=main_content.id,
                    position="before"
                )
                break
        
        assert result["success"] is True
        
        # Verify section was moved (check order)
        updated_sections = server.ensure_editor().get_sections()
        titles = [s.title for s in updated_sections]
        conclusion_idx = titles.index("Conclusion")
        main_content_idx = titles.index("Main Content")
        assert conclusion_idx < main_content_idx
    
    def test_undo_tool(self, server):
        """Test undo tool."""
        server._setup_tools()
        
        # First make a change to undo
        sections = server.ensure_editor().get_sections()
        intro_section = next(s for s in sections if s.title == "Introduction")
        
        # Update a section
        for tool in server.mcp._tools:
            if tool.name == "update_section":
                tool.handler(
                    section_id=intro_section.id,
                    content="Content to be undone."
                )
                break
        
        # Now test undo
        for tool in server.mcp._tools:
            if tool.name == "undo":
                result = tool.handler()
                break
        
        assert result["success"] is True
        
        # Verify change was undone
        content = server.ensure_editor().to_markdown()
        assert "Content to be undone" not in content
    
    def test_resources_functionality(self, server):
        """Test MCP resources."""
        server._setup_resources()
        
        # Test that resources are set up
        assert len(server.mcp._resources) > 0
        
        # Find and test document resource
        for resource in server.mcp._resources:
            if resource.name == "document":
                result = resource.handler()
                assert "content" in result
                assert "# Test Document" in result["content"]
                break
    
    def test_prompts_functionality(self, server):
        """Test MCP prompts."""
        server._setup_prompts()
        
        # Test that prompts are set up
        assert len(server.mcp._prompts) > 0
        
        # Find and test summarize prompt
        for prompt in server.mcp._prompts:
            if prompt.name == "summarize_section":
                result = prompt.handler(section_title="Introduction")
                assert "prompt" in result
                assert "Introduction" in result["prompt"]
                break
    
    def test_validation_level_handling(self, server):
        """Test different validation levels in tools."""
        server._setup_tools()
        
        # Test with different validation levels
        for validation in ["STRICT", "NORMAL", "PERMISSIVE"]:
            for tool in server.mcp._tools:
                if tool.name == "load_document":
                    # Create temp file for each test
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
                        f.write(f"# Test {validation}\nContent")
                        temp_file = Path(f.name)
                    
                    try:
                        result = tool.handler(str(temp_file), validation)
                        assert result["success"] is True
                    finally:
                        if temp_file.exists():
                            temp_file.unlink()
                    break
    
    def test_error_handling_in_tools(self, server):
        """Test error handling in various tools."""
        server._setup_tools()
        
        # Test get_section with invalid ID
        for tool in server.mcp._tools:
            if tool.name == "get_section":
                result = tool.handler(section_id="invalid_id")
                assert result["success"] is False
                break
        
        # Test update_section with invalid ID
        for tool in server.mcp._tools:
            if tool.name == "update_section":
                result = tool.handler(section_id="invalid_id", content="test")
                assert result["success"] is False
                break
    
    def test_tool_count_completeness(self, server):
        """Verify all expected tools are registered."""
        server._setup_tools()
        
        expected_tools = {
            "load_document", "save_document", "get_document", "list_sections", 
            "get_section", "insert_section", "update_section", "delete_section",
            "move_section", "undo"
        }
        
        actual_tools = {tool.name for tool in server.mcp._tools}
        assert expected_tools.issubset(actual_tools), f"Missing tools: {expected_tools - actual_tools}"
