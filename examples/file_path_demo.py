#!/usr/bin/env python3
"""
Example script demonstrating file path operations with the SafeMarkdownEditor MCP server.

This script shows how to:
1. Load documents from various path formats
2. Work with absolute, relative, and tilde-expanded paths
3. Test path resolution
4. Save documents to different locations
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from fastmcp import Client
from quantalogic_markdown_mcp.mcp_server import server

async def demonstrate_path_operations():
    """Demonstrate various file path operations."""
    print("🚀 SafeMarkdownEditor MCP Server - File Path Demo")
    print("=" * 50)
    
    async with Client(server.mcp) as client:
        # 1. Test path resolution with different formats
        print("\n🔍 Testing Path Resolution:")
        
        paths_to_test = [
            "~/Documents/test.md",          # Tilde expansion
            "./README.md",                  # Relative path
            "/tmp/absolute_test.md",        # Absolute path
            "$HOME/env_test.md"            # Environment variable
        ]
        
        for path in paths_to_test:
            result = await client.call_tool("test_path_resolution", {"path": path})
            content = result.content[0].text
            import json
            parsed = json.loads(content)
            
            print(f"  Path: {path}")
            print(f"    Resolves to: {parsed['resolved_path']}")
            print(f"    Exists: {parsed['exists']}")
            print(f"    Tilde expanded: {parsed['expansion_info']['tilde_expanded']}")
            print()
        
        # 2. Create a sample document and save it
        print("📝 Creating and Saving Document:")
        
        # Initialize with sample content
        server.initialize_document("""# Demo Document

## Introduction
This document demonstrates file path operations.

## Examples
Here are some examples of what you can do:

- Load documents from various paths
- Save to different locations
- Work with relative and absolute paths

## Conclusion
File path handling works great!
""")
        
        # Save to different locations
        save_locations = [
            "~/Desktop/mcp_demo.md",       # Home directory
            "./examples/demo_output.md",   # Relative path
            "/tmp/mcp_temp_demo.md"        # Absolute path
        ]
        
        for location in save_locations:
            try:
                # Create parent directory if needed
                parent = Path(location).expanduser().parent
                parent.mkdir(parents=True, exist_ok=True)
                
                result = await client.call_tool("save_document", {
                    "file_path": location,
                    "backup": True
                })
                content = result.content[0].text
                parsed = json.loads(content)
                
                if parsed['success']:
                    print(f"  ✅ Saved to: {location}")
                    print(f"      Actual path: {parsed['file_path']}")
                else:
                    print(f"  ❌ Failed to save to: {location}")
                    print(f"      Error: {parsed['error']}")
                    
            except Exception as e:
                print(f"  ❌ Error saving to {location}: {e}")
        
        # 3. Load a document and get file info
        print("\n📂 Loading Document and Getting Info:")
        
        # Load the README.md file
        result = await client.call_tool("load_document", {"file_path": "./README.md"})
        content = result.content[0].text
        parsed = json.loads(content)
        
        if parsed['success']:
            print(f"  ✅ Loaded: {parsed['file_path']}")
            print(f"      Sections: {parsed['sections_count']}")
            print(f"      Size: {parsed['file_size']} bytes")
            
            # Get detailed file info
            info_result = await client.call_tool("get_file_info", {})
            info_content = info_result.content[0].text
            info_parsed = json.loads(info_content)
            
            print(f"      File name: {info_parsed['file_name']}")
            print(f"      Readable: {info_parsed['is_readable']}")
            print(f"      Writable: {info_parsed['is_writable']}")
        
        print("\n🎉 Demo completed successfully!")
        print("\nKey takeaways:")
        print("  • Absolute paths: /full/path/to/file.md")
        print("  • Relative paths: ./docs/file.md")
        print("  • Tilde expansion: ~/Documents/file.md")
        print("  • Environment variables: $HOME/file.md")
        print("  • All path types are fully supported!")

if __name__ == "__main__":
    try:
        asyncio.run(demonstrate_path_operations())
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
