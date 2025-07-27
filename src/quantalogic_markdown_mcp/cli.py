"""CLI entry point for quantalogic-markdown-mcp."""

def main():
    """Main entry point for the MCP server."""
    from quantalogic_markdown_mcp.mcp_server import mcp
    mcp.run()

if __name__ == "__main__":
    main()
