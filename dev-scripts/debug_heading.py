"""
Debug the heading level change issue
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from quantalogic_markdown_mcp import SafeMarkdownEditor, ValidationLevel

def debug_heading_change():
    """Debug why heading level change is failing."""
    
    markdown_text = """# Main Document

This is the main document content.

## Section A

Content for section A.

## Section B

Content for section B.
"""
    
    editor = SafeMarkdownEditor(markdown_text, ValidationLevel.NORMAL)
    sections = editor.get_sections()
    
    # Find "Section B"
    section_b = None
    for section in sections:
        if section.title == "Section B":
            section_b = section
            break
    
    if section_b:
        print(f"Section B found:")
        print(f"  Title: {section_b.title}")
        print(f"  Level: {section_b.level}")
        print(f"  Line start: {section_b.line_start}")
        print(f"  Line end: {section_b.line_end}")
        
        # Check the actual line content
        lines = editor._current_text.split('\n')
        line_index = section_b.line_start - 1  # Convert to 0-based
        
        print(f"\nDocument lines around Section B:")
        for i in range(max(0, line_index - 2), min(len(lines), line_index + 3)):
            marker = " -> " if i == line_index else "    "
            print(f"{marker}Line {i+1}: {repr(lines[i])}")
        
        print(f"\nLine content at index {line_index}:")
        if line_index < len(lines):
            actual_line = lines[line_index]
            print(f"  Raw: {repr(actual_line)}")
            print(f"  Stripped: {repr(actual_line.strip())}")
            
            # Test the regex
            import re
            heading_match = re.match(r'^(#+)\s*(.*)$', actual_line.strip())
            if heading_match:
                print("  Regex match found:")
                print(f"    Level: {len(heading_match.group(1))}")
                print(f"    Title: {heading_match.group(2)}")
            else:
                print("  Regex match failed!")
                
                # Try a few lines around to find the actual heading
                for offset in [-1, 0, 1, 2]:
                    test_idx = line_index + offset
                    if 0 <= test_idx < len(lines):
                        test_line = lines[test_idx]
                        test_match = re.match(r'^(#+)\s*(.*)$', test_line.strip())
                        if test_match and "Section B" in test_match.group(2):
                            print(f"  Found Section B heading at line {test_idx + 1}: {repr(test_line)}")
                            break
                
        else:
            print(f"  Line index {line_index} is out of bounds (total lines: {len(lines)})")

if __name__ == "__main__":
    debug_heading_change()
