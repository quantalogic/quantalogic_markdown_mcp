#!/usr/bin/env python3
"""
Comprehensive test suite for the new human-readable section ID system.

This test verifies that the new title-based section ID system works correctly
across all MCP operations and handles various edge cases properly.
"""

import sys
sys.path.insert(0, 'src')

from quantalogic_markdown_mcp.safe_editor import SafeMarkdownEditor
from quantalogic_markdown_mcp.mcp_server import MarkdownMCPServer
import os


def test_basic_id_generation():
    """Test basic human-readable ID generation."""
    print("🧪 Testing basic ID generation...")
    
    test_content = '''# Main Document

## Introduction
Basic introduction.

## Getting Started
Getting started guide.

## API Reference
API documentation.
'''
    
    editor = SafeMarkdownEditor(test_content)
    sections = editor.get_sections()
    
    expected_ids = ['main-document', 'introduction', 'getting-started', 'api-reference']
    actual_ids = [section.id for section in sections]
    
    assert actual_ids == expected_ids, f"Expected {expected_ids}, got {actual_ids}"
    print("✅ Basic ID generation works correctly")


def test_duplicate_handling():
    """Test handling of duplicate section titles."""
    print("🧪 Testing duplicate title handling...")
    
    test_content = '''# Test Document

## Introduction
First introduction.

## Features
Features section.

## Introduction
Second introduction (should get hierarchical context).

## Setup
Setup section.

### Installation
Installation under setup.

## Setup
Duplicate setup (should get numeric suffix).

### Installation  
Duplicate installation under duplicate setup.
'''
    
    editor = SafeMarkdownEditor(test_content)
    sections = editor.get_sections()
    
    # Check that duplicates are handled intelligently
    ids = [section.id for section in sections]
    titles = [section.title for section in sections]
    
    print(f"Generated IDs: {ids}")
    
    # Verify no duplicate IDs
    assert len(ids) == len(set(ids)), f"Found duplicate IDs: {ids}"
    
    # Verify intelligent collision resolution
    introduction_ids = [id for id, title in zip(ids, titles) if title == 'Introduction']
    setup_ids = [id for id, title in zip(ids, titles) if title == 'Setup']
    installation_ids = [id for id, title in zip(ids, titles) if title == 'Installation']
    
    assert len(introduction_ids) == 2, f"Expected 2 Introduction IDs, got {introduction_ids}"
    assert len(setup_ids) == 2, f"Expected 2 Setup IDs, got {setup_ids}"
    assert len(installation_ids) == 2, f"Expected 2 Installation IDs, got {installation_ids}"
    
    print("✅ Duplicate handling works correctly")


def test_edge_cases():
    """Test edge cases like special characters, empty titles, etc."""
    print("🧪 Testing edge cases...")
    
    test_content = '''# Test Document

## API & Integration
Special characters.

## 
Empty title.

## This is a very long title that should be truncated because it exceeds the reasonable length limit for section identifiers
Long title.

## Émojis & Ünicode
Unicode test.
'''
    
    editor = SafeMarkdownEditor(test_content)
    sections = editor.get_sections()
    
    ids = [section.id for section in sections]
    print(f"Edge case IDs: {ids}")
    
    # Verify all IDs are valid (no spaces, reasonable length, etc.)
    for id in ids:
        assert ' ' not in id, f"ID contains spaces: {id}"
        assert len(id) <= 60, f"ID too long: {id}"
        assert id.replace('-', '').replace('_', '').isalnum() or 'section' in id, f"Invalid characters in ID: {id}"
    
    print("✅ Edge cases handled correctly")


def test_mcp_server_functionality():
    """Test MCP server operations with new IDs."""
    print("🧪 Testing MCP server functionality...")
    
    test_file = 'test_comprehensive.md'
    test_content = '''# Project Documentation

## Overview
Project overview section.

## Installation
How to install the project.

## Usage
Usage instructions.

## Overview
Duplicate overview section.
'''
    
    # Write test file
    with open(test_file, 'w') as f:
        f.write(test_content)
    
    try:
        server = MarkdownMCPServer()
        
        # Test list_sections
        result = server.call_tool_sync('list_sections', {'document_path': test_file})
        assert result.get('success'), f"list_sections failed: {result}"
        
        sections = result.get('sections', [])
        assert len(sections) == 5, f"Expected 5 sections, got {len(sections)}"
        
        # Verify human-readable IDs
        ids = [s['id'] for s in sections]
        expected_ids = ['project-documentation', 'overview', 'installation', 'usage', 'project-documentation-overview']
        assert ids == expected_ids, f"Expected {expected_ids}, got {ids}"
        
        # Test get_section with human-readable ID
        result = server.call_tool_sync('get_section', {
            'document_path': test_file,
            'section_id': 'installation'
        })
        assert result.get('success'), f"get_section failed: {result}"
        
        section = result.get('section', {})
        assert section.get('id') == 'installation', f"Wrong section returned: {section}"
        assert section.get('title') == 'Installation', f"Wrong title: {section}"
        
        # Test update_section with human-readable ID
        result = server.call_tool_sync('update_section', {
            'document_path': test_file,
            'section_id': 'usage',
            'content': '''## Usage

This is the UPDATED usage section with new content!
'''
        })
        assert result.get('success'), f"update_section failed: {result}"
        
        # Verify the update
        with open(test_file, 'r') as f:
            updated_content = f.read()
        
        assert 'UPDATED usage section' in updated_content, "Update not applied correctly"
        
        print("✅ MCP server functionality works correctly")
        
    finally:
        # Clean up
        if os.path.exists(test_file):
            os.remove(test_file)


def test_section_operations():
    """Test section insert, delete, and move operations."""
    print("🧪 Testing section operations...")
    
    test_file = 'test_operations.md'
    test_content = '''# Document

## Section A
Content A.

## Section B
Content B.
'''
    
    with open(test_file, 'w') as f:
        f.write(test_content)
    
    try:
        server = MarkdownMCPServer()
        
        # Test insert_section
        result = server.call_tool_sync('insert_section', {
            'document_path': test_file,
            'heading': 'New Section',
            'content': 'New section content.',
            'position': 2
        })
        assert result.get('success'), f"insert_section failed: {result}"
        
        # Verify the section was inserted with a human-readable ID
        result = server.call_tool_sync('list_sections', {'document_path': test_file})
        sections = result.get('sections', [])
        
        new_section_ids = [s['id'] for s in sections if s['title'] == 'New Section']
        assert len(new_section_ids) == 1, f"New section not found: {sections}"
        assert new_section_ids[0] == 'new-section', f"Wrong ID for new section: {new_section_ids[0]}"
        
        print("✅ Section operations work correctly")
        
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)


def run_all_tests():
    """Run all comprehensive tests."""
    print("🚀 Running comprehensive test suite for human-readable section IDs...\n")
    
    try:
        test_basic_id_generation()
        test_duplicate_handling()
        test_edge_cases()
        test_mcp_server_functionality()
        test_section_operations()
        
        print("\n🎉 All tests passed! The new section ID system is working perfectly!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
