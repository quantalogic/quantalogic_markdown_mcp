# MCP Research and Implementation Notes (Scratchpad)

## Protocol Overview
- MCP (Model Context Protocol) is a standard for connecting AI applications (LLMs, agents) to external tools, data, and prompts.
- Uses JSON-RPC 2.0 for message exchange.
- Two layers: Data (protocol, primitives) and Transport (stdio, HTTP).

## Core Concepts
- **Primitives:**
  - Tools: Executable functions (e.g., file ops, API calls).
  - Resources: Data sources (e.g., file contents, API responses).
  - Prompts: Templates for LLM interactions.
- **Lifecycle:** Initialization, capability negotiation, identity exchange.
- **Notifications:** Real-time updates (e.g., tool list changes).

## Architecture
- **MCP Host:** AI app managing one or more MCP clients.
- **MCP Client:** Connects to a server, obtains context.
- **MCP Server:** Provides context (tools/resources/prompts).

## Python SDK
- Official SDK: https://github.com/modelcontextprotocol/python-sdk
- Install with: `uv add "mcp[cli]" httpx`
- Use `FastMCP` for server, `ClientSession` for client.
- Logging: Use `logging` to stderr, not stdout (for stdio servers).

## Server Example
- Define tools with `@mcp.tool()` decorator.
- Expose resources and prompts as needed.
- Run with `mcp.run(transport='stdio')` or HTTP.

## Client Example
- Use `ClientSession` and `stdio_client` to connect.
- Discover tools with `tools/list`.
- Call tools with `tools/call`.

## Best Practices
- Use type hints and docstrings for auto-generated schemas.
- Handle errors gracefully, provide meaningful messages.
- Secure API keys and sensitive data.
- Use notifications for real-time updates.

## References
- Official docs: https://modelcontextprotocol.io/
- Architecture: https://modelcontextprotocol.io/docs/learn/architecture
- Server quickstart: https://modelcontextprotocol.io/quickstart/server
- Client quickstart: https://modelcontextprotocol.io/quickstart/client
- SDKs: https://modelcontextprotocol.io/docs/sdk
- Example servers: https://github.com/modelcontextprotocol/servers

## Next Steps
- Draft actionable MCP API spec for SafeMarkdownEditor.
- Track progress in 07-progress.md.
