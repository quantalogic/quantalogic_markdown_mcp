#!/usr/bin/env python3
"""Test script to reproduce header duplication through MCP tools."""

import sys
sys.path.insert(0, 'src')

from quantalogic_markdown_mcp.mcp_server import MarkdownMCPServer

def test_mcp_header_duplication():
    """Test header duplication through MCP tools."""
    
    # Create test document
    test_content = """# Test Document

This is a test document.

## Introduction

This is the introduction section with some content.
More content here.

## Chapter 1

This is chapter 1 with original content.
Some more text in chapter 1.

## Chapter 2

This is chapter 2.
"""
    
    # Write test document
    with open('test_mcp_duplication.md', 'w') as f:
        f.write(test_content)
    
    print("=== Original Document ===")
    print(test_content)
    print("=" * 50)
    
    # Initialize MCP server
    server = MarkdownMCPServer()
    
    # List sections to get section IDs
    list_result = server.call_tool_sync("list_sections", {
        "document_path": "test_mcp_duplication.md"
    })
    
    if not list_result.get("success"):
        print("❌ Failed to list sections")
        print(list_result)
        return
    
    sections = list_result.get("metadata", {}).get("sections", [])
    print(f"Found {len(sections)} sections:")
    for section in sections:
        print(f"  ID: {section['id']}, Title: {section['title']}, Level: {section['level']}")
    
    # Find Chapter 1 section
    chapter1_section = None
    for section in sections:
        if section['title'] == 'Chapter 1':
            chapter1_section = section
            break
    
    if not chapter1_section:
        print("❌ Chapter 1 not found")
        return
    
    print(f"\n=== Updating Chapter 1 via MCP ===")
    print(f"Section ID: {chapter1_section['id']}")
    print(f"Title: {chapter1_section['title']}")
    
    # Update using MCP tool
    new_content = """## Chapter 1

This is completely new content for Chapter 1.
Updated through MCP server.
Let's see what happens to the header."""
    
    update_result = server.call_tool_sync("update_section", {
        "document_path": "test_mcp_duplication.md",
        "section_id": chapter1_section['id'],
        "content": new_content
    })
    
    print(f"Update result: {update_result}")
    
    if update_result.get("success"):
        print("✅ Update successful")
        
        # Read the updated document
        with open('test_mcp_duplication.md', 'r') as f:
            updated_content = f.read()
        
        print("\n=== Updated Document ===")
        print(updated_content)
        print("=" * 50)
        
        # Check for header duplication
        lines = updated_content.split('\n')
        chapter1_lines = []
        for i, line in enumerate(lines):
            if 'Chapter 1' in line and line.strip().startswith('#'):
                chapter1_lines.append((i, line))
        
        print(f"\nHeader lines containing 'Chapter 1': {len(chapter1_lines)}")
        for line_num, line in chapter1_lines:
            print(f"  Line {line_num}: {line}")
            
        if len(chapter1_lines) > 1:
            print("🔴 ISSUE DETECTED: Header duplication found!")
            return True
        else:
            print("✅ No header duplication detected")
            return False
    else:
        print("❌ Update failed")
        for error in update_result.get("errors", []):
            print(f"  Error: {error}")
        return False

def test_with_header_in_content():
    """Test specifically with header included in the content."""
    
    # Create test document
    test_content = """# Test Document

## Chapter 1

Original content here.
"""
    
    # Write test document
    with open('test_header_in_content.md', 'w') as f:
        f.write(test_content)
    
    print("\n" + "=" * 60)
    print("=== Test 2: Header in Content ===")
    print("=" * 60)
    print(test_content)
    
    server = MarkdownMCPServer()
    
    # List sections
    list_result = server.call_tool_sync("list_sections", {
        "document_path": "test_header_in_content.md"
    })
    
    sections = list_result.get("metadata", {}).get("sections", [])
    chapter1_section = None
    for section in sections:
        if section['title'] == 'Chapter 1':
            chapter1_section = section
            break
    
    if not chapter1_section:
        print("❌ Chapter 1 not found")
        return False
    
    # Update with content that includes a header - this might cause duplication
    new_content_with_header = """## Chapter 1

This new content includes the header.
This might cause duplication!"""
    
    print(f"Updating with content that includes header:\n{new_content_with_header}")
    
    update_result = server.call_tool_sync("update_section", {
        "document_path": "test_header_in_content.md", 
        "section_id": chapter1_section['id'],
        "content": new_content_with_header
    })
    
    if update_result.get("success"):
        with open('test_header_in_content.md', 'r') as f:
            updated_content = f.read()
        
        print("\n=== Updated Document ===")
        print(updated_content)
        print("=" * 50)
        
        # Check for duplication
        chapter1_count = updated_content.count('## Chapter 1')
        print(f"Number of '## Chapter 1' headers: {chapter1_count}")
        
        if chapter1_count > 1:
            print("🔴 ISSUE DETECTED: Header duplication found!")
            return True
        else:
            print("✅ No header duplication detected")
            return False
    else:
        print("❌ Update failed")
        return False

if __name__ == "__main__":
    issue1 = test_mcp_header_duplication()
    issue2 = test_with_header_in_content()
    
    if issue1 or issue2:
        print("\n🔴 HEADER DUPLICATION ISSUE FOUND!")
    else:
        print("\n✅ No header duplication issues detected")
        
    # Cleanup
    import os
    try:
        os.remove('test_mcp_duplication.md')
        os.remove('test_header_in_content.md')
    except:
        pass
