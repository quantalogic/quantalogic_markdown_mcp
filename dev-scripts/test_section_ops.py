"""
Extended test for SafeMarkdownEditor functionality including section insertion.
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from quantalogic_markdown_mcp import SafeMarkdownEditor, EditOperation

def test_section_operations():
    """Test section insertion and other operations."""
    
    # Test markdown content
    markdown_text = """# Introduction

This is the introduction section.

## Getting Started

Here's how to get started.

## Advanced Topics

Advanced content here.
"""
    
    print("=== Testing SafeMarkdownEditor Section Operations ===")
    
    # Create editor
    try:
        editor = SafeMarkdownEditor(markdown_text)
        print("✓ SafeMarkdownEditor created successfully")
    except Exception as e:
        print(f"✗ Failed to create SafeMarkdownEditor: {e}")
        return
    
    # Get initial sections
    sections = editor.get_sections()
    print(f"✓ Initial sections: {len(sections)}")
    for i, section in enumerate(sections):
        print(f"  {i}: {section.title} (Level {section.level})")
    
    # Test section insertion
    try:
        # Insert a new section after "Getting Started"
        getting_started = sections[1]  # "Getting Started" section
        insert_result = editor.insert_section_after(
            getting_started,
            level=2,
            title="Configuration",
            content="This section covers configuration options.\n\n- Option 1\n- Option 2"
        )
        
        print(f"✓ Insert operation: {'Success' if insert_result.success else 'Failed'}")
        if insert_result.success:
            print(f"  New section added at level {insert_result.metadata.get('final_level', 'unknown')}")
            print(f"  Transaction ID: {insert_result.metadata.get('transaction_id', 'none')}")
        else:
            print(f"  Errors: {[str(e) for e in insert_result.errors]}")
    except Exception as e:
        print(f"✗ Failed to insert section: {e}")
        return
    
    # Show updated sections
    updated_sections = editor.get_sections()
    print(f"✓ Updated sections: {len(updated_sections)}")
    for i, section in enumerate(updated_sections):
        print(f"  {i}: {section.title} (Level {section.level}, Lines {section.line_start}-{section.line_end})")
    
    # Test update of the new section
    try:
        # Find the Configuration section
        config_section = None
        for section in updated_sections:
            if section.title == "Configuration":
                config_section = section
                break
        
        if config_section:
            update_result = editor.update_section_content(
                config_section,
                "Updated configuration content with **bold** text and more details."
            )
            print(f"✓ Update new section: {'Success' if update_result.success else 'Failed'}")
        else:
            print("✗ Could not find Configuration section")
    except Exception as e:
        print(f"✗ Failed to update new section: {e}")
    
    # Show final document
    print("\n=== Final Document ===")
    final_doc = editor.to_markdown()
    print(final_doc)
    
    # Show statistics
    stats = editor.get_statistics()
    print(f"\n=== Statistics ===")
    print(f"Total sections: {stats.total_sections}")
    print(f"Word count: {stats.word_count}")
    print(f"Edit count: {stats.edit_count}")
    print(f"Section distribution: {stats.section_distribution}")
    
    print("\n=== Test completed ===")

if __name__ == "__main__":
    test_section_operations()
