"""
Test the new section operations: delete_section, move_section, change_heading_level
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from quantalogic_markdown_mcp import SafeMarkdownEditor, ValidationLevel

def test_new_section_operations():
    """Test the newly implemented section operations."""
    
    print("=== Testing New Section Operations ===\n")
    
    # Test markdown with multiple sections
    markdown_text = """# Main Document

This is the main document content.

## Section A

Content for section A.

### Subsection A1

Content for subsection A1.

### Subsection A2

Content for subsection A2.

## Section B

Content for section B.

## Section C

Content for section C.
"""
    
    editor = SafeMarkdownEditor(markdown_text, ValidationLevel.NORMAL)
    
    # Test 1: Change heading level
    print("1. Testing change_heading_level")
    sections = editor.get_sections()
    
    # Find "Section B" (should be level 2)
    section_b = None
    for section in sections:
        if section.title == "Section B":
            section_b = section
            break
    
    if section_b:
        print(f"   Found 'Section B' at level {section_b.level}")
        
        # Change it to level 3
        result = editor.change_heading_level(section_b, 3)
        print(f"   Change to level 3: {'Success' if result.success else 'Failed'}")
        
        if result.errors:
            for error in result.errors:
                print(f"     Error: {error.message}")
        
        # Verify the change
        updated_sections = editor.get_sections()
        for section in updated_sections:
            if section.title == "Section B":
                print(f"   New level for 'Section B': {section.level}")
                break
    
    # Test 2: Delete section
    print("\n2. Testing delete_section")
    current_sections = editor.get_sections()
    print(f"   Sections before deletion: {len(current_sections)}")
    
    # Find "Subsection A1" to delete
    subsection_a1 = None
    for section in current_sections:
        if section.title == "Subsection A1":
            subsection_a1 = section
            break
    
    if subsection_a1:
        result = editor.delete_section(subsection_a1)
        print(f"   Delete 'Subsection A1': {'Success' if result.success else 'Failed'}")
        
        if result.errors:
            for error in result.errors:
                print(f"     Error: {error.message}")
        
        # Verify deletion
        updated_sections = editor.get_sections()
        print(f"   Sections after deletion: {len(updated_sections)}")
        
        # Check if subsection A1 is gone
        a1_still_exists = any(s.title == "Subsection A1" for s in updated_sections)
        print(f"   'Subsection A1' still exists: {a1_still_exists}")
    
    # Test 3: Move section (simplified implementation)
    print("\n3. Testing move_section")
    current_sections = editor.get_sections()
    
    # Find "Section C" and "Section A"
    section_c = None
    section_a = None
    for section in current_sections:
        if section.title == "Section C":
            section_c = section
        elif section.title == "Section A":
            section_a = section
    
    if section_c and section_a:
        result = editor.move_section(section_c, section_a, "before")
        print(f"   Move 'Section C' before 'Section A': {'Success' if result.success else 'Failed'}")
        
        if result.warnings:
            for warning in result.warnings:
                print(f"     Warning: {warning.message}")
    
    # Test 4: Display final document structure
    print("\n4. Final Document Structure")
    final_sections = editor.get_sections()
    print(f"   Total sections: {len(final_sections)}")
    
    for section in final_sections:
        indent = "  " * (section.level - 1)
        print(f"     {indent}- {section.title} (L{section.level})")
    
    # Test 5: Show final document content
    print("\n5. Final Document Content")
    final_content = editor.to_markdown()
    print("   Document length:", len(final_content), "characters")
    print("   First 200 characters:")
    print("   " + repr(final_content[:200]))
    
    # Test 6: Transaction history
    print("\n6. Transaction History")
    history = editor.get_transaction_history()
    print(f"   Total transactions: {len(history)}")
    
    for i, txn in enumerate(history):
        print(f"   Transaction {i+1}: {txn.transaction_id} ({len(txn.operations)} operations)")
        for op in txn.operations:
            print(f"     - {op['operation'].value} on section {op.get('section_id', 'N/A')}")
    
    print("\n=== New Section Operations Test Complete ===")

if __name__ == "__main__":
    test_new_section_operations()
