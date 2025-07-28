#!/usr/bin/env python3
"""Comprehensive test for header duplication fix."""

import re
import sys
sys.path.insert(0, 'src')

from quantalogic_markdown_mcp.safe_editor import SafeMarkdownEditor
from quantalogic_markdown_mcp.safe_editor_types import ValidationLevel

def test_comprehensive_header_fix():
    """Test various edge cases for header duplication fix."""
    
    test_cases = [
        {
            "name": "Exact header match",
            "content": """## Chapter 1

New content with exact header match.""",
            "expected_headers": 1
        },
        {
            "name": "Header with extra spaces",
            "content": """##  Chapter 1  

Content with header that has extra spaces.""",
            "expected_headers": 2  # Should NOT be removed due to different spacing
        },
        {
            "name": "Wrong level header",
            "content": """### Chapter 1

Content with wrong level header.""",
            "expected_headers": 2  # Should NOT be removed due to different level
        },
        {
            "name": "Different title",
            "content": """## Different Title

Content with completely different title.""",
            "expected_headers": 1  # Only original header should remain
        },
        {
            "name": "Header in middle of content",
            "content": """Some content first.

## Chapter 1

More content after header.""",
            "expected_headers": 2  # Header in middle should NOT be removed
        },
        {
            "name": "Empty content with header",
            "content": """## Chapter 1""",
            "expected_headers": 1  # Should remove duplicate
        },
        {
            "name": "Header with empty lines after",
            "content": """## Chapter 1



Content after empty lines.""",
            "expected_headers": 1  # Should remove duplicate and empty lines
        }
    ]
    
    base_content = """# Main Document

## Chapter 1

Original content here.

## Chapter 2

Content for chapter 2.
"""
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n=== Test {i}: {test_case['name']} ===")
        
        # Create fresh editor for each test
        editor = SafeMarkdownEditor(base_content, ValidationLevel.NORMAL)
        sections = editor.get_sections()
        
        # Find Chapter 1
        chapter1 = None
        for section in sections:
            if section.title == "Chapter 1":
                chapter1 = section
                break
        
        if not chapter1:
            print("❌ Chapter 1 not found")
            all_passed = False
            continue
        
        # Update with test content
        result = editor.update_section_content(chapter1, test_case["content"])
        
        if not result.success:
            print("❌ Update failed")
            for error in result.errors:
                print(f"  Error: {error}")
            all_passed = False
            continue
        
        # Check result
        updated_content = editor.to_markdown()
        
        # Count headers more accurately using regex to catch all variants
        header_pattern = r'^##.*Chapter 1.*$'
        header_matches = re.findall(header_pattern, updated_content, re.MULTILINE)
        header_count = len(header_matches)
        
        print(f"Expected headers: {test_case['expected_headers']}, Found: {header_count}")
        
        if header_count == test_case["expected_headers"]:
            print("✅ Test passed")
        else:
            print("❌ Test failed")
            print("Updated content:")
            print(updated_content)
            print("-" * 50)
            all_passed = False
    
    return all_passed

def test_mcp_server_fix():
    """Test the fix through MCP server interface."""
    from quantalogic_markdown_mcp.mcp_server import MarkdownMCPServer
    
    # Create test document
    test_content = """# Test Document

## Introduction

Original intro content.

## Chapter 1

Original chapter 1 content.
"""
    
    # Write test document
    with open('test_mcp_fix.md', 'w') as f:
        f.write(test_content)
    
    print("\n" + "=" * 60)
    print("=== MCP Server Test ===")
    print("=" * 60)
    
    server = MarkdownMCPServer()
    
    # Get document sections (using the fixed MCP implementation)
    get_doc_result = server.call_tool_sync("get_document", {
        "document_path": "test_mcp_fix.md"
    })
    
    if not get_doc_result.get("success"):
        print("❌ Failed to get document")
        return False
    
    sections = get_doc_result.get("sections", [])
    print(f"Found {len(sections)} sections")
    
    # Find Chapter 1
    chapter1_id = None
    for section in sections:
        if section['title'] == 'Chapter 1':
            chapter1_id = section['id']
            break
    
    if not chapter1_id:
        print("❌ Chapter 1 not found")
        return False
    
    # Test update with duplicate header
    update_content = """## Chapter 1

This content includes the header and should not cause duplication.
Testing through MCP server interface."""
    
    update_result = server.call_tool_sync("update_section", {
        "document_path": "test_mcp_fix.md",
        "section_id": chapter1_id,
        "content": update_content
    })
    
    if not update_result.get("success"):
        print("❌ Update failed")
        print(update_result)
        return False
    
    # Check result
    with open('test_mcp_fix.md', 'r') as f:
        updated_content = f.read()
    
    header_count = updated_content.count("## Chapter 1")
    print(f"Header count after MCP update: {header_count}")
    
    # Cleanup
    import os
    try:
        os.remove('test_mcp_fix.md')
    except:
        pass
    
    if header_count == 1:
        print("✅ MCP server test passed")
        return True
    else:
        print("❌ MCP server test failed")
        print("Updated content:")
        print(updated_content)
        return False

if __name__ == "__main__":
    print("Running comprehensive header duplication tests...")
    
    direct_tests_passed = test_comprehensive_header_fix()
    mcp_tests_passed = test_mcp_server_fix()
    
    if direct_tests_passed and mcp_tests_passed:
        print("\n🎉 ALL TESTS PASSED! Header duplication issue is fixed.")
    else:
        print("\n❌ Some tests failed. Fix needs more work.")
        if not direct_tests_passed:
            print("  - Direct editor tests failed")
        if not mcp_tests_passed:
            print("  - MCP server tests failed")
