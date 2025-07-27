#!/usr/bin/env python3
"""
Test MCP Server Direct Functionality
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from quantalogic_markdown_mcp.mcp_server import MarkdownMCPServer

def main():
    print("Creating MCP server...")
    server = MarkdownMCPServer()
    print("✅ MCP server created successfully!")
    print(f"Server has FastMCP instance: {server.mcp}")
    
    print("Testing document initialization...")
    server.initialize_document("# Test Document\n\nThis is a test document.")
    print("✅ Document initialized successfully!")
    
    sections = server.editor.get_sections()
    print(f"Document has {len(sections)} sections")
    for i, section in enumerate(sections):
        print(f"  Section {i+1}: {section.title}")
    
    print("🎉 MCP server is fully functional!")

if __name__ == "__main__":
    main()
