#!/usr/bin/env python3
"""Final verification of the header duplication fix through MCP."""

import sys
sys.path.insert(0, 'src')

from quantalogic_markdown_mcp.mcp_server import MarkdownMCPServer

def final_verification():
    """Final test of the header duplication fix."""
    
    # Create test document
    test_content = """# Test Document for Header Duplication Fix

## Introduction

This is a test document to verify the header duplication fix.

## Chapter 1

This is the original content for Chapter 1.

## Chapter 2

This is content for Chapter 2.
"""
    
    # Write test document
    with open('test_final_verification.md', 'w') as f:
        f.write(test_content)
    
    print("=== Final Verification Test ===")
    print("Original document:")
    print(test_content)
    print("=" * 60)
    
    server = MarkdownMCPServer()
    
    # Get document sections
    doc_result = server.call_tool_sync("get_document", {
        "document_path": "test_final_verification.md"
    })
    
    if not doc_result.get("success"):
        print("❌ Failed to get document")
        return False
    
    sections = doc_result.get("sections", [])
    print(f"Found {len(sections)} sections:")
    for section in sections:
        print(f"  - {section['title']} (ID: {section['id']})")
    
    # Find Chapter 1
    chapter1_id = None
    for section in sections:
        if section['title'] == 'Chapter 1':
            chapter1_id = section['id']
            break
    
    if not chapter1_id:
        print("❌ Chapter 1 not found")
        return False
    
    # Test 1: Update with content that includes duplicate header
    print(f"\n=== Test 1: Update with duplicate header ===")
    content_with_header = """## Chapter 1

This is NEW content for Chapter 1 that includes the header.
This should NOT cause duplication."""
    
    update_result = server.call_tool_sync("update_section", {
        "document_path": "test_final_verification.md",
        "section_id": chapter1_id,
        "content": content_with_header
    })
    
    if not update_result.get("success"):
        print("❌ Update failed")
        print(update_result)
        return False
    
    # Check result
    with open('test_final_verification.md', 'r') as f:
        updated_content = f.read()
    
    print("Updated document:")
    print(updated_content)
    
    # Count Chapter 1 headers
    import re
    chapter1_headers = re.findall(r'^##.*Chapter 1.*$', updated_content, re.MULTILINE)
    print(f"\nChapter 1 headers found: {len(chapter1_headers)}")
    for i, header in enumerate(chapter1_headers, 1):
        print(f"  {i}: '{header}'")
    
    if len(chapter1_headers) == 1:
        print("✅ Test 1 PASSED - No header duplication!")
    else:
        print("❌ Test 1 FAILED - Header duplication detected!")
        return False
    
    # Test 2: Update with normal content (no header)
    print(f"\n=== Test 2: Update with normal content ===")
    normal_content = """This is updated content WITHOUT a header.
The header should be preserved by the editor."""
    
    update_result2 = server.call_tool_sync("update_section", {
        "document_path": "test_final_verification.md",
        "section_id": chapter1_id,
        "content": normal_content
    })
    
    if not update_result2.get("success"):
        print("❌ Update 2 failed")
        return False
    
    # Check result
    with open('test_final_verification.md', 'r') as f:
        updated_content2 = f.read()
    
    print("Updated document:")
    print(updated_content2)
    
    chapter1_headers2 = re.findall(r'^##.*Chapter 1.*$', updated_content2, re.MULTILINE)
    print(f"\nChapter 1 headers found: {len(chapter1_headers2)}")
    
    if len(chapter1_headers2) == 1:
        print("✅ Test 2 PASSED - Header preserved correctly!")
        test2_passed = True
    else:
        print("❌ Test 2 FAILED - Header not preserved correctly!")
        test2_passed = False
    
    # Cleanup
    import os
    try:
        os.remove('test_final_verification.md')
    except:
        pass
    
    return test2_passed

if __name__ == "__main__":
    success = final_verification()
    if success:
        print("\n🎉 HEADER DUPLICATION FIX VERIFIED SUCCESSFULLY!")
        print("The MCP markdown editor now correctly handles header duplication.")
    else:
        print("\n❌ Verification failed. Fix needs more work.")
