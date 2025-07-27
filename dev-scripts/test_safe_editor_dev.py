"""
Basic test for SafeMarkdownEditor functionality.
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from quantalogic_markdown_mcp import SafeMarkdownEditor, EditOperation

def test_basic_functionality():
    """Test basic SafeMarkdownEditor functionality."""
    
    # Test markdown content
    markdown_text = """# Introduction

This is the introduction section.

## Getting Started

Here's how to get started.

## Advanced Topics

Advanced content here.

### Subsection

More details.
"""
    
    print("=== Testing SafeMarkdownEditor ===")
    
    # Create editor
    try:
        editor = SafeMarkdownEditor(markdown_text)
        print("✓ SafeMarkdownEditor created successfully")
    except Exception as e:
        print(f"✗ Failed to create SafeMarkdownEditor: {e}")
        return
    
    # Test get_sections
    try:
        sections = editor.get_sections()
        print(f"✓ Found {len(sections)} sections:")
        for section in sections:
            print(f"  - {section.title} (Level {section.level}, Lines {section.line_start}-{section.line_end})")
    except Exception as e:
        print(f"✗ Failed to get sections: {e}")
        return
    
    # Test statistics
    try:
        stats = editor.get_statistics()
        print(f"✓ Document statistics:")
        print(f"  - Total sections: {stats.total_sections}")
        print(f"  - Word count: {stats.word_count}")
        print(f"  - Max depth: {stats.max_heading_depth}")
    except Exception as e:
        print(f"✗ Failed to get statistics: {e}")
        return
    
    # Test preview operation
    if sections:
        try:
            preview_result = editor.preview_operation(
                EditOperation.UPDATE_SECTION,
                section_ref=sections[0],
                content="This is updated introduction content with **bold** text."
            )
            print(f"✓ Preview operation: {'Success' if preview_result.success else 'Failed'}")
            if preview_result.success:
                print("  Preview generated successfully")
            else:
                print(f"  Errors: {[str(e) for e in preview_result.errors]}")
        except Exception as e:
            print(f"✗ Failed to preview operation: {e}")
            return
    
    # Test actual update
    if sections:
        try:
            update_result = editor.update_section_content(
                sections[0],
                "This is the **updated** introduction with *emphasis*."
            )
            print(f"✓ Update operation: {'Success' if update_result.success else 'Failed'}")
            if update_result.success:
                print("  Section updated successfully")
                print("  Final document:")
                print(editor.to_markdown()[:200] + "...")
            else:
                print(f"  Errors: {[str(e) for e in update_result.errors]}")
        except Exception as e:
            print(f"✗ Failed to update section: {e}")
            return
    
    print("\n=== All tests completed ===")

if __name__ == "__main__":
    test_basic_functionality()
