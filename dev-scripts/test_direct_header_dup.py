#!/usr/bin/env python3
"""Direct test of the header duplication issue."""

import sys
sys.path.insert(0, 'src')

from quantalogic_markdown_mcp.safe_editor import SafeMarkdownEditor
from quantalogic_markdown_mcp.safe_editor_types import ValidationLevel

def test_direct_header_duplication():
    """Test header duplication directly with the editor."""
    
    # Create test content
    test_content = """# Main Document

## Chapter 1

This is the original content for chapter 1.
Some content here.

## Chapter 2

Content for chapter 2.
"""
    
    print("=== Original Content ===")
    print(test_content)
    print("=" * 50)
    
    # Create editor
    editor = SafeMarkdownEditor(test_content, ValidationLevel.NORMAL)
    sections = editor.get_sections()
    
    print(f"Found {len(sections)} sections:")
    for section in sections:
        print(f"  {section.title} (level {section.level}, lines {section.line_start}-{section.line_end})")
    
    # Find Chapter 1
    chapter1 = None
    for section in sections:
        if section.title == "Chapter 1":
            chapter1 = section
            break
    
    if not chapter1:
        print("❌ Chapter 1 not found")
        return
    
    print(f"\n=== Chapter 1 Details ===")
    print(f"ID: {chapter1.id}")
    print(f"Title: {chapter1.title}")
    print(f"Level: {chapter1.level}")
    print(f"Lines: {chapter1.line_start}-{chapter1.line_end}")
    
    # Get current content to see what's happening
    current_content = editor.to_markdown()
    lines = current_content.split('\n')
    print(f"\nCurrent section content (lines {chapter1.line_start}-{chapter1.line_end}):")
    for i in range(chapter1.line_start, min(chapter1.line_end + 1, len(lines))):
        print(f"  {i}: {lines[i]}")
    
    # Test case 1: Update with content that includes the header (likely cause of duplication)
    print(f"\n=== Test 1: Update with header in content ===")
    content_with_header = """## Chapter 1

This is new content that includes the header.
This might cause duplication."""
    
    result1 = editor.update_section_content(chapter1, content_with_header)
    
    if result1.success:
        print("✅ Update 1 successful")
        updated_content = editor.to_markdown()
        print("\n=== Updated Document ===")
        print(updated_content)
        
        # Count occurrences of the header
        header_count = updated_content.count("## Chapter 1")
        print(f"\nHeader count: {header_count}")
        
        if header_count > 1:
            print("🔴 DUPLICATION DETECTED!")
            return True
        else:
            print("✅ No duplication in test 1")
    else:
        print("❌ Update 1 failed")
        for error in result1.errors:
            print(f"  Error: {error}")
    
    # Reset for test 2
    editor = SafeMarkdownEditor(test_content, ValidationLevel.NORMAL)
    sections = editor.get_sections()
    chapter1 = None
    for section in sections:
        if section.title == "Chapter 1":
            chapter1 = section
            break
    
    # Test case 2: Update with content WITHOUT header (should be correct)
    print(f"\n=== Test 2: Update without header in content ===")
    content_without_header = """This is new content WITHOUT the header.
The header should be preserved by the editor."""
    
    result2 = editor.update_section_content(chapter1, content_without_header)
    
    if result2.success:
        print("✅ Update 2 successful")
        updated_content = editor.to_markdown()
        print("\n=== Updated Document ===")
        print(updated_content)
        
        # Count occurrences of the header
        header_count = updated_content.count("## Chapter 1")
        print(f"\nHeader count: {header_count}")
        
        if header_count > 1:
            print("🔴 DUPLICATION DETECTED!")
            return True
        else:
            print("✅ No duplication in test 2")
    else:
        print("❌ Update 2 failed")
        for error in result2.errors:
            print(f"  Error: {error}")
    
    return False

if __name__ == "__main__":
    duplicated = test_direct_header_duplication()
    if duplicated:
        print("\n🔴 HEADER DUPLICATION ISSUE CONFIRMED!")
    else:
        print("\n✅ No header duplication detected in direct tests")
