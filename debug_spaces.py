#!/usr/bin/env python3
"""Debug the extra spaces case."""

import sys
sys.path.insert(0, 'src')

from quantalogic_markdown_mcp.safe_editor import SafeMarkdownEditor
from quantalogic_markdown_mcp.safe_editor_types import ValidationLevel

def debug_extra_spaces():
    """Debug the header with extra spaces case."""
    
    base_content = """# Main Document

## Chapter 1

Original content here.

## Chapter 2

Content for chapter 2.
"""
    
    editor = SafeMarkdownEditor(base_content, ValidationLevel.NORMAL)
    sections = editor.get_sections()
    
    # Find Chapter 1
    chapter1 = None
    for section in sections:
        if section.title == "Chapter 1":
            chapter1 = section
            break
    
    print(f"Chapter 1 section:")
    print(f"  Title: '{chapter1.title}'")
    print(f"  Level: {chapter1.level}")
    
    # Get the original header line
    lines = editor.to_markdown().split('\n')
    original_header = lines[chapter1.line_start]
    print(f"  Original header line: '{original_header}'")
    
    # Test content with extra spaces
    test_content = """##  Chapter 1  

Content with header that has extra spaces."""
    
    print(f"\nTest content first line: '{test_content.split(chr(10))[0]}'")
    
    # Expected header that our code generates
    expected_header = "#" * chapter1.level + " " + chapter1.title
    print(f"Expected header for comparison: '{expected_header}'")
    
    # Check if they match
    first_line = test_content.split('\n')[0]
    print(f"First line of test content: '{first_line}'")
    print(f"Match check: {first_line == expected_header}")
    
    # Update and see result
    result = editor.update_section_content(chapter1, test_content)
    
    if result.success:
        updated_content = editor.to_markdown()
        print(f"\nUpdated content:")
        print(updated_content)
        print(f"\nHeader count: {updated_content.count('## Chapter 1')}")
        
        # Show each line to debug
        updated_lines = updated_content.split('\n')
        for i, line in enumerate(updated_lines):
            if 'Chapter 1' in line:
                print(f"Line {i}: '{line}'")

if __name__ == "__main__":
    debug_extra_spaces()
