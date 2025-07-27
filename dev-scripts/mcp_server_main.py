#!/usr/bin/env python3
"""
SafeMarkdownEditor MCP Server Entry Point

This is the main entry point for running the SafeMarkdownEditor MCP server.
It can be used directly with the MCP Inspector or other MCP clients.
"""

if __name__ == "__main__":
    from quantalogic_markdown_mcp.mcp_server import main
    main()
