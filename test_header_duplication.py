#!/usr/bin/env python3
"""Test script to reproduce the header duplication issue."""

import sys
import os
sys.path.insert(0, 'src')

from quantalogic_markdown_mcp.safe_editor import SafeMarkdownEditor
from quantalogic_markdown_mcp.safe_editor_types import ValidationLevel

def test_header_duplication():
    """Test to reproduce header duplication issue."""
    
    # Create a simple test document
    markdown_content = """# Main Title

This is the introduction section.

## Chapter 1

This is the content of chapter 1.
Some more content here.

## Chapter 2  

This is the content of chapter 2.
More content for chapter 2.
"""

    print("=== Original Document ===")
    print(markdown_content)
    print("=" * 50)
    
    # Initialize editor
    editor = SafeMarkdownEditor(markdown_content, ValidationLevel.NORMAL)
    
    # Get sections
    sections = editor.get_sections()
    print(f"Found {len(sections)} sections:")
    for i, section in enumerate(sections):
        print(f"  {i}: {section.title} (level {section.level}, lines {section.line_start}-{section.line_end})")
    
    # Find "Chapter 1" section
    chapter1_section = None
    for section in sections:
        if section.title == "Chapter 1":
            chapter1_section = section
            break
    
    if not chapter1_section:
        print("ERROR: Chapter 1 section not found!")
        return
    
    print(f"\n=== Updating Chapter 1 ===")
    print(f"Section: {chapter1_section.title}")
    print(f"Lines: {chapter1_section.line_start}-{chapter1_section.line_end}")
    
    # Update the content
    new_content = """This is completely new content for chapter 1.
I'm replacing the old content with this new text.
Let's see if the header gets duplicated."""
    
    result = editor.update_section_content(chapter1_section, new_content)
    
    if result.success:
        print("✅ Update successful")
        print("\n=== Updated Document ===")
        updated_content = editor.to_markdown()
        print(updated_content)
        print("=" * 50)
        
        # Check for duplication
        lines = updated_content.split('\n')
        chapter1_lines = []
        for i, line in enumerate(lines):
            if 'Chapter 1' in line:
                chapter1_lines.append((i, line))
        
        print(f"\nLines containing 'Chapter 1': {len(chapter1_lines)}")
        for line_num, line in chapter1_lines:
            print(f"  Line {line_num}: {line}")
            
        if len(chapter1_lines) > 1:
            print("🔴 ISSUE DETECTED: Header duplication found!")
        else:
            print("✅ No header duplication detected")
            
    else:
        print("❌ Update failed")
        for error in result.errors:
            print(f"  Error: {error.message}")

if __name__ == "__main__":
    test_header_duplication()
