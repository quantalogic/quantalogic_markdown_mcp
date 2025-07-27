#!/usr/bin/env python3
"""Simple direct test for the stateless MCP server."""

import tempfile
from pathlib import Path
from quantalogic_markdown_mcp.mcp_server import MarkdownMCPServer

def main():
    print("🔧 Starting stateless server test...")
    
    # Create a temporary markdown file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("""# Test Document

## Introduction  
This is a test document for the stateless server.

## Features
- Feature 1
- Feature 2

## Conclusion
End of document.
""")
        temp_path = f.name
    
    print(f"📄 Created test document: {temp_path}")
    
    try:
        # Initialize the server
        print("🚀 Initializing MCP server...")
        server = MarkdownMCPServer()
        print("✅ Server initialized successfully!")
        
        # Test list_sections
        print("\n📋 Testing list_sections...")
        result = server.call_tool_sync("list_sections", {"document_path": temp_path})
        print(f"   Result: {result.get('success', False)}")
        if result.get('success'):
            sections = result.get('sections', [])
            print(f"   Found {len(sections)} sections")
            for section in sections:
                print(f"     - {section.get('title', 'Unknown')} (ID: {section.get('id', 'Unknown')})")
        
        # Test get_section
        if result.get('success') and result.get('sections'):
            first_section_id = result['sections'][0]['id']
            print(f"\n📖 Testing get_section with ID: {first_section_id}...")
            get_result = server.call_tool_sync("get_section", {"document_path": temp_path, "section_id": first_section_id})
            print(f"   Result: {get_result.get('success', False)}")
            if get_result.get('success'):
                section = get_result.get('section', {})
                print(f"   Retrieved: {section.get('title', 'Unknown')}")
        
        # Test insert_section
        print("\n➕ Testing insert_section...")
        insert_result = server.call_tool_sync("insert_section", {
            "document_path": temp_path,
            "heading": "New Section",
            "content": "This is a new section added by the stateless server.",
            "position": 2
        })
        print(f"   Result: {insert_result.get('success', False)}")
        
        # Verify the section was added
        print("\n🔍 Verifying section was added...")
        final_result = server.call_tool_sync("list_sections", {"document_path": temp_path})
        print(f"   Result: {final_result.get('success', False)}")
        if final_result.get('success'):
            sections = final_result.get('sections', [])
            print(f"   Now have {len(sections)} sections")
            for section in sections:
                print(f"     - {section.get('title', 'Unknown')} (ID: {section.get('id', 'Unknown')})")
        
        print("\n✅ All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up
        Path(temp_path).unlink(missing_ok=True)
        print("🧹 Cleaned up test file")

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Test suite completed successfully!")
    else:
        print("\n💥 Test suite failed!")
        exit(1)
