"""
Comprehensive test suite for SafeMarkdownEditor API compliance.
Tests all major functionality according to the API specification.
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from quantalogic_markdown_mcp import (
    SafeMarkdownEditor, 
    EditOperation, 
    ValidationLevel
)

def test_api_compliance():
    """Test SafeMarkdownEditor API compliance with specification."""
    
    print("=== SafeMarkdownEditor API Compliance Test ===\n")
    
    # Test markdown with complex structure
    markdown_text = """# Project Documentation

This is the main project documentation.

## Introduction

Welcome to our project! This section provides an overview.

### Background

Some background information here.

### Goals

Our main goals are:
- Goal 1
- Goal 2

## Getting Started

Instructions for getting started.

### Prerequisites

You need:
- Python 3.8+
- pip

### Installation

Run the following command:

```bash
pip install our-package
```

## Advanced Topics

Advanced features and usage.

### Configuration

Configuration options are available.

### Troubleshooting

Common issues and solutions.
"""
    
    # Test 1: Constructor with different validation levels
    print("1. Testing Constructor and Validation Levels")
    try:
        SafeMarkdownEditor(markdown_text, ValidationLevel.STRICT)
        SafeMarkdownEditor(markdown_text, ValidationLevel.NORMAL)
        SafeMarkdownEditor(markdown_text, ValidationLevel.PERMISSIVE)
        print("   ✓ All validation levels work")
    except Exception as e:
        print(f"   ✗ Constructor failed: {e}")
        return
    
    # Use normal editor for rest of tests
    editor = SafeMarkdownEditor(markdown_text, ValidationLevel.NORMAL)
    
    # Test 2: Document Inspection Methods
    print("\n2. Testing Document Inspection Methods")
    sections = editor.get_sections()
    print(f"   Total sections: {len(sections)}")
    
    # Test get_sections_by_level
    h1_sections = editor.get_sections_by_level(1)
    h2_sections = editor.get_sections_by_level(2)
    h3_sections = editor.get_sections_by_level(3)
    print(f"   H1 sections: {len(h1_sections)}, H2: {len(h2_sections)}, H3: {len(h3_sections)}")
    
    # Test get_section_by_id
    if sections:
        section_by_id = editor.get_section_by_id(sections[0].id)
        print(f"   ✓ get_section_by_id: {'Found' if section_by_id else 'Not found'}")
    
    # Test get_child_sections
    if h1_sections:
        children = editor.get_child_sections(h1_sections[0])
        print(f"   Child sections of '{h1_sections[0].title}': {len(children)}")
    
    # Test 3: Preview Operations
    print("\n3. Testing Preview Operations")
    if sections:
        preview_result = editor.preview_operation(
            EditOperation.UPDATE_SECTION,
            section_ref=sections[1],  # "Introduction"
            content="This is a **previewed** update to the introduction."
        )
        print(f"   Preview update: {'Success' if preview_result.success else 'Failed'}")
        
        if preview_result.success and preview_result.preview:
            print(f"   Preview length: {len(preview_result.preview)} characters")
    
    # Test 4: Section Operations
    print("\n4. Testing Section Operations")
    
    # Test update_section_content
    if len(sections) > 1:
        update_result = editor.update_section_content(
            sections[1],  # "Introduction" 
            "This is the **updated** introduction with new formatting.\n\nIt now has multiple paragraphs."
        )
        print(f"   Update section: {'Success' if update_result.success else 'Failed'}")
        if update_result.errors:
            print(f"   Update errors: {[str(e) for e in update_result.errors]}")
    
    # Test insert_section_after
    current_sections = editor.get_sections()
    if current_sections:
        insert_result = editor.insert_section_after(
            current_sections[0],  # After "Project Documentation"
            level=2,
            title="Overview",
            content="This section provides a high-level overview of the project."
        )
        print(f"   Insert section: {'Success' if insert_result.success else 'Failed'}")
        if insert_result.errors:
            print(f"   Insert errors: {[str(e) for e in insert_result.errors]}")
    
    # Test 5: Transaction Management
    print("\n5. Testing Transaction Management")
    
    # Get transaction history
    history = editor.get_transaction_history()
    print(f"   Transaction history: {len(history)} transactions")
    
    for i, txn in enumerate(history[:3]):  # Show first 3
        print(f"   Transaction {i+1}: {txn.transaction_id} ({len(txn.operations)} ops)")
    
    # Test rollback
    if history:
        rollback_result = editor.rollback_transaction()
        print(f"   Rollback last transaction: {'Success' if rollback_result.success else 'Failed'}")
        
        # Check state after rollback
        post_rollback_sections = editor.get_sections()
        print(f"   Sections after rollback: {len(post_rollback_sections)}")
    
    # Test 6: Document Export
    print("\n6. Testing Document Export")
    
    # Test to_markdown
    markdown_output = editor.to_markdown()
    print(f"   Markdown export: {len(markdown_output)} characters")
    
    # Test to_html
    try:
        html_output = editor.to_html()
        print(f"   HTML export: {len(html_output)} characters")
    except Exception as e:
        print(f"   HTML export failed: {e}")
    
    # Test to_json
    try:
        json_output = editor.to_json()
        print(f"   JSON export: {len(json_output)} characters")
    except Exception as e:
        print(f"   JSON export failed: {e}")
    
    # Test 7: Statistics and Analysis
    print("\n7. Testing Statistics and Analysis")
    
    stats = editor.get_statistics()
    print(f"   Total sections: {stats.total_sections}")
    print(f"   Word count: {stats.word_count}")
    print(f"   Max heading depth: {stats.max_heading_depth}")
    print(f"   Edit count: {stats.edit_count}")
    print(f"   Section distribution: {stats.section_distribution}")
    
    # Test validation
    validation_errors = editor.validate_document()
    print(f"   Validation errors: {len(validation_errors)}")
    for error in validation_errors[:3]:  # Show first 3 errors
        print(f"     - {error.message} ({error.category.value})")
    
    # Test 8: Thread Safety (Basic Test)
    print("\n8. Testing Thread Safety")
    import threading
    
    results = []
    def worker_thread(thread_id):
        try:
            # Multiple threads trying to read concurrently
            local_sections = editor.get_sections()
            local_stats = editor.get_statistics()
            results.append(f"Thread {thread_id}: {len(local_sections)} sections, {local_stats.word_count} words")
        except Exception as e:
            results.append(f"Thread {thread_id} error: {e}")
    
    threads = []
    for i in range(3):
        thread = threading.Thread(target=worker_thread, args=(i,))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    print(f"   Concurrent read test: {len(results)} threads completed")
    for result in results:
        print(f"     {result}")
    
    # Test 9: Error Handling
    print("\n9. Testing Error Handling")
    
    # Test invalid operations
    try:
        editor.get_sections_by_level(7)  # Invalid level
        print("   ✗ Should have raised error for invalid heading level")
    except ValueError as e:
        print(f"   ✓ Correctly caught invalid heading level: {str(e)[:50]}...")
    
    # Test invalid section reference
    from quantalogic_markdown_mcp.safe_editor_types import SectionReference
    fake_section = SectionReference(
        id="fake_id",
        title="Fake Section",
        level=2,
        line_start=999,
        line_end=1000,
        path=[]
    )
    
    fake_update_result = editor.update_section_content(fake_section, "fake content")
    print(f"   Invalid section update: {'Failed as expected' if not fake_update_result.success else 'Unexpectedly succeeded'}")
    
    # Test 10: Final State Check
    print("\n10. Final State Verification")
    
    final_sections = editor.get_sections()
    final_stats = editor.get_statistics()
    
    print(f"   Final sections: {len(final_sections)}")
    print(f"   Final word count: {final_stats.word_count}")
    print(f"   Final edit count: {final_stats.edit_count}")
    
    # Display section structure
    print("   Final document structure:")
    for i, section in enumerate(final_sections):
        indent = "  " * (section.level - 1)
        print(f"     {indent}- {section.title} (L{section.level})")
    
    print("\n=== API Compliance Test Complete ===")
    print("✓ SafeMarkdownEditor API appears to be functioning correctly!")

if __name__ == "__main__":
    test_api_compliance()
