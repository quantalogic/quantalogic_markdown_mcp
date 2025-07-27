#!/usr/bin/env python3
"""
Test script for the MCP server.

This script can be used to run the MCP server directly for testing purposes.
"""

import sys
import os

# Add the src directory to the path to import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from quantalogic_markdown_mcp.mcp_server import main

if __name__ == "__main__":
    print("Starting SafeMarkdownEditor MCP Server...")
    print("Use Ctrl+C to stop the server")
    try:
        main()
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
