"""
Test transaction and rollback functionality for SafeMarkdownEditor.
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from quantalogic_markdown_mcp import SafeMarkdownEditor

def test_transaction_rollback():
    """Test transaction history and rollback functionality."""
    
    # Test markdown content
    markdown_text = """# Introduction

This is the introduction section.

## Getting Started

Here's how to get started.
"""
    
    print("=== Testing Transaction Rollback ===")
    
    # Create editor
    editor = SafeMarkdownEditor(markdown_text)
    print("✓ SafeMarkdownEditor created")
    
    print(f"Initial version: {editor._version}")
    
    # Get initial sections and make first change
    sections = editor.get_sections()
    print(f"Initial sections: {len(sections)}")
    
    # First operation: Update introduction
    print("\n--- Operation 1: Update Introduction ---")
    result1 = editor.update_section_content(
        sections[0],
        "This is the **UPDATED** introduction with new content."
    )
    print(f"Update 1: {'Success' if result1.success else 'Failed'}")
    
    # Check transaction history
    history1 = editor.get_transaction_history()
    print(f"Transaction history length: {len(history1)}")
    
    # Second operation: Insert new section
    print("\n--- Operation 2: Insert New Section ---")
    updated_sections = editor.get_sections()
    print(f"Sections after update: {len(updated_sections)}")
    for i, section in enumerate(updated_sections):
        print(f"  {i}: {section.title}")
    
    if len(updated_sections) > 1:
        target_section = updated_sections[1]  # After "Getting Started"
    else:
        target_section = updated_sections[0]  # After first section if only one exists
        
    result2 = editor.insert_section_after(
        target_section,
        level=2,
        title="Troubleshooting",
        content="Common issues and solutions."
    )
    print(f"Insert: {'Success' if result2.success else 'Failed'}")
    if result2.errors:
        print(f"Insert errors: {[str(e) for e in result2.errors]}")
    
    # Check state after two operations
    current_sections = editor.get_sections()
    print(f"Current sections: {len(current_sections)}")
    for i, section in enumerate(current_sections):
        print(f"  {i}: {section.title}")
    
    # Check transaction history
    history2 = editor.get_transaction_history()
    print(f"Transaction history length: {len(history2)}")
    
    print("\n--- Current Document ---")
    print(editor.to_markdown()[:300] + "...")
    
    # Test rollback to previous state
    print("\n--- Testing Rollback ---")
    if history2:
        last_txn_id = history2[0].transaction_id  # Most recent
        print(f"Rolling back transaction: {last_txn_id}")
        
        rollback_result = editor.rollback_transaction(last_txn_id)
        print(f"Rollback: {'Success' if rollback_result.success else 'Failed'}")
        
        if rollback_result.success:
            print(f"Rollback metadata: {rollback_result.metadata}")
            
            # Check sections after rollback
            rollback_sections = editor.get_sections()
            print(f"Sections after rollback: {len(rollback_sections)}")
            for i, section in enumerate(rollback_sections):
                print(f"  {i}: {section.title}")
            
            print("\n--- Document After Rollback ---")
            print(editor.to_markdown())
            
            # Check transaction history after rollback
            history3 = editor.get_transaction_history()
            print(f"Transaction history after rollback: {len(history3)}")
        else:
            print(f"Rollback errors: {rollback_result.errors}")
    
    # Test document validation
    print("\n--- Document Validation ---")
    validation_errors = editor.validate_document()
    print(f"Validation errors: {len(validation_errors)}")
    for error in validation_errors:
        print(f"  - {error.message}")
    
    # Test export functions
    print("\n--- Export Functions ---")
    try:
        html_output = editor.to_html()
        print(f"✓ HTML export: {len(html_output)} characters")
    except Exception as e:
        print(f"✗ HTML export failed: {e}")
    
    try:
        json_output = editor.to_json()
        print(f"✓ JSON export: {len(json_output)} characters")
    except Exception as e:
        print(f"✗ JSON export failed: {e}")
    
    print("\n=== Transaction Rollback Test Complete ===")

if __name__ == "__main__":
    test_transaction_rollback()
