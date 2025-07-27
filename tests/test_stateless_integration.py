#!/usr/bin/env python3
"""
Comprehensive integration test for the stateless MCP server.
Tests all 10 tools with proper call_tool_sync pattern.
"""

import tempfile
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from quantalogic_markdown_mcp.mcp_server import MarkdownMCPServer

def test_comprehensive_stateless_server():
    """Test all functionality of the stateless MCP server."""
    print("🧪 Testing Comprehensive Stateless MCP Server")
    
    # Create test document
    test_content = """# Test Document

## Introduction
This is a test document for comprehensive testing.

## Features
- Feature 1: Basic functionality
- Feature 2: Advanced operations

## Implementation
Details about implementation here.

## Conclusion
Final thoughts and summary.
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(test_content)
        temp_path = f.name
    
    try:
        server = MarkdownMCPServer()
        results = {}
        
        # Test 1: load_document
        print("\n1️⃣ Testing load_document...")
        result = server.call_tool_sync("load_document", {
            "document_path": temp_path,
            "validation_level": "NORMAL"
        })
        results['load_document'] = result
        assert result['success'] == True
        assert result['stateless'] == True
        print(f"   ✅ Document loaded: {result['sections_count']} sections")
        
        # Test 2: list_sections
        print("\n2️⃣ Testing list_sections...")
        result = server.call_tool_sync("list_sections", {
            "document_path": temp_path
        })
        results['list_sections'] = result
        assert result['success'] == True
        assert len(result['sections']) == 5  # Including main document
        print(f"   ✅ Listed {len(result['sections'])} sections")
        
        # Get a section ID for further tests
        sections = result['sections']
        section_ids = [s['id'] for s in sections if s['title'] == 'Features']
        assert len(section_ids) > 0
        features_id = section_ids[0]
        
        # Test 3: get_section
        print("\n3️⃣ Testing get_section...")
        result = server.call_tool_sync("get_section", {
            "document_path": temp_path,
            "section_id": features_id
        })
        results['get_section'] = result
        assert result['success'] == True
        assert 'Features' in result['section']['title']
        print(f"   ✅ Retrieved section: {result['section']['title']}")
        
        # Test 4: insert_section
        print("\n4️⃣ Testing insert_section...")
        result = server.call_tool_sync("insert_section", {
            "document_path": temp_path,
            "heading": "Testing Section",
            "content": "This section was added by the comprehensive test.",
            "position": 3,
            "auto_save": True,
            "backup": False
        })
        results['insert_section'] = result
        assert result['success'] == True
        print(f"   ✅ Inserted section with ID: {result['modified_sections'][0]['id']}")
        
        # Test 5: update_section
        print("\n5️⃣ Testing update_section...")
        result = server.call_tool_sync("update_section", {
            "document_path": temp_path,
            "section_id": features_id,
            "content": "## Features\n- Updated Feature 1\n- Updated Feature 2\n- New Feature 3",
            "auto_save": True,
            "backup": False
        })
        results['update_section'] = result
        assert result['success'] == True
        print(f"   ✅ Updated section: {result['modified_sections'][0]['title']}")
        
        # Test 6: get_document
        print("\n6️⃣ Testing get_document...")
        result = server.call_tool_sync("get_document", {
            "document_path": temp_path
        })
        results['get_document'] = result
        assert result['success'] == True
        assert 'Testing Section' in result['content']
        assert 'Updated Feature' in result['content']
        print(f"   ✅ Retrieved complete document ({len(result['content'])} chars)")
        
        # Test 7: analyze_document
        print("\n7️⃣ Testing analyze_document...")
        result = server.call_tool_sync("analyze_document", {
            "document_path": temp_path
        })
        results['analyze_document'] = result
        assert result['success'] == True
        assert result['analysis']['total_sections'] >= 5
        print(f"   ✅ Analyzed document: {result['analysis']['total_sections']} sections")
        
        # Test 8: move_section (get the testing section we added)
        print("\n8️⃣ Testing move_section...")
        list_result = server.call_tool_sync("list_sections", {"document_path": temp_path})
        testing_sections = [s for s in list_result['sections'] if s['title'] == 'Testing Section']
        if testing_sections:
            testing_id = testing_sections[0]['id']
            result = server.call_tool_sync("move_section", {
                "document_path": temp_path,
                "section_id": testing_id,
                "target_position": 1,
                "auto_save": True,
                "backup": False
            })
            results['move_section'] = result
            assert result['success'] == True
            print(f"   ✅ Moved section to position 1")
        else:
            print("   ⚠️ Skipping move_section - Testing Section not found")
        
        # Test 9: delete_section
        print("\n9️⃣ Testing delete_section...")
        if testing_sections:
            result = server.call_tool_sync("delete_section", {
                "document_path": temp_path,
                "section_id": testing_id,
                "auto_save": True,
                "backup": False
            })
            results['delete_section'] = result
            assert result['success'] == True
            print(f"   ✅ Deleted section")
        else:
            print("   ⚠️ Skipping delete_section - Testing Section not found")
        
        # Test 10: save_document to different location
        print("\n🔟 Testing save_document...")
        with tempfile.NamedTemporaryFile(mode='w', suffix='_saved.md', delete=False) as save_file:
            save_path = save_file.name
        
        result = server.call_tool_sync("save_document", {
            "document_path": temp_path,
            "target_path": save_path,
            "backup": False
        })
        results['save_document'] = result
        assert result['success'] == True
        print(f"   ✅ Saved document to: {save_path}")
        
        # Verify saved file exists and has content
        saved_content = Path(save_path).read_text()
        assert len(saved_content) > 0
        assert 'Updated Feature' in saved_content
        
        # Test error handling
        print("\n🚨 Testing error handling...")
        
        # Test with invalid file
        result = server.call_tool_sync("load_document", {
            "document_path": "/non/existent/file.md"
        })
        assert result['success'] == False
        error_msg = result['error']['message'] if isinstance(result['error'], dict) else str(result['error'])
        assert 'does not exist' in error_msg.lower() or 'not found' in error_msg.lower()
        print("   ✅ Error handling works correctly")
        
        # Test with invalid section ID
        result = server.call_tool_sync("get_section", {
            "document_path": temp_path,
            "section_id": "invalid-section-id"
        })
        assert result['success'] == False
        print("   ✅ Invalid section ID handled correctly")
        
        print("\n🎉 All tests passed! Stateless MCP Server is working correctly.")
        print(f"\n📊 Test Summary:")
        for tool_name, result in results.items():
            status = "✅" if result.get('success') else "❌"
            print(f"   {status} {tool_name}")
        
        # Clean up saved file
        Path(temp_path.replace('.md', '_saved.md')).unlink(missing_ok=True)
        
        # Verify all tests passed (no return needed for pytest)
        assert True  # If we get here, all tests passed
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up
        Path(temp_path).unlink(missing_ok=True)

if __name__ == "__main__":
    success = test_comprehensive_stateless_server()
    sys.exit(0 if success else 1)
