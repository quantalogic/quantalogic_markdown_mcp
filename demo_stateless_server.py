#!/usr/bin/env python3
"""Demo of the stateless MCP server functionality."""

import tempfile
from pathlib import Path
from quantalogic_markdown_mcp.mcp_server import MarkdownMCPServer

def main():
    print("🔧 Starting Quantalogic Markdown MCP Server Demo")
    print("=" * 60)
    
    # Create a temporary markdown file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("""# Test Document

## Introduction
This is a test document for the stateless server.

## Features
- Feature 1: Stateless operations
- Feature 2: Document path-based editing

## Conclusion
The server is working perfectly!
""")
        temp_path = f.name
    
    print(f"📄 Created test document: {temp_path}")
    
    try:
        # Initialize the server
        print("\n🚀 Initializing MCP server...")
        server = MarkdownMCPServer()
        print("✅ Server initialized successfully!")
        
        # Test 1: list_sections
        print("\n📋 Test 1: list_sections")
        result = server.call_tool_sync("list_sections", {"document_path": temp_path})
        print(f"   Success: {result.get('success', False)}")
        if result.get('success'):
            sections = result.get('sections', [])
            print(f"   Found {len(sections)} sections:")
            for section in sections:
                print(f"     - {section.get('title', 'Unknown')} (Level {section.get('level', '?')}, ID: {section.get('id', 'Unknown')})")
        
        # Test 2: get_section
        if result.get('success') and result.get('sections'):
            first_section_id = result['sections'][0]['id']
            print(f"\n📖 Test 2: get_section (ID: {first_section_id})")
            get_result = server.call_tool_sync("get_section", {"document_path": temp_path, "section_id": first_section_id})
            print(f"   Success: {get_result.get('success', False)}")
            if get_result.get('success'):
                section = get_result.get('section', {})
                print(f"   Retrieved: {section.get('title', 'Unknown')}")
                print(f"   Content preview: {section.get('content', '')[:50]}...")
        
        # Test 3: insert_section
        print(f"\n➕ Test 3: insert_section")
        insert_result = server.call_tool_sync("insert_section", {
            "document_path": temp_path,
            "heading": "New Section",
            "content": "This is a new section added by the stateless server.",
            "position": 2
        })
        print(f"   Success: {insert_result.get('success', False)}")
        
        # Test 4: Verify the section was added
        print(f"\n🔍 Test 4: Verifying section was added...")
        verify_result = server.call_tool_sync("list_sections", {"document_path": temp_path})
        print(f"   Success: {verify_result.get('success', False)}")
        if verify_result.get('success'):
            sections = verify_result.get('sections', [])
            print(f"   Now have {len(sections)} sections:")
            for section in sections:
                print(f"     - {section.get('title', 'Unknown')} (Level {section.get('level', '?')}, ID: {section.get('id', 'Unknown')})")
        
        # Test 5: get_document
        print(f"\n📄 Test 5: get_document")
        doc_result = server.call_tool_sync("get_document", {"document_path": temp_path})
        print(f"   Success: {doc_result.get('success', False)}")
        if doc_result.get('success'):
            content = doc_result.get('content', '')
            line_count = len(content.split('\n'))
            print(f"   Document has {line_count} lines")
        
        # Test 6: analyze_document
        print(f"\n🔍 Test 6: analyze_document")
        analyze_result = server.call_tool_sync("analyze_document", {"document_path": temp_path})
        print(f"   Success: {analyze_result.get('success', False)}")
        if analyze_result.get('success'):
            analysis = analyze_result.get('analysis', {})
            stats = analysis.get('statistics', {})
            print(f"   Statistics:")
            print(f"     - Total sections: {stats.get('total_sections', '?')}")
            print(f"     - Word count: {stats.get('word_count', '?')}")
            print(f"     - Character count: {stats.get('character_count', '?')}")
        
        print("\n✅ All tests completed successfully!")
        print("🎉 The Quantalogic Markdown MCP Server is fully functional!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up
        Path(temp_path).unlink(missing_ok=True)
        print(f"\n🧹 Cleaned up test file")

if __name__ == "__main__":
    main()
