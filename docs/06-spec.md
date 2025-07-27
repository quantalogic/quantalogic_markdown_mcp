
# MCP API Specification for SafeMarkdownEditor

## Protocol Version
This API targets MCP protocol version: `2025-06-18`. The server negotiates protocol version during initialization.

## Overview
This specification describes how to expose the SafeMarkdownEditor as an MCP-compliant API, enabling safe, structured, and AI-driven interaction with Markdown documents.

## Goals
- Provide a secure, robust, and discoverable API for Markdown editing via MCP.
- Support all SafeMarkdownEditor operations as MCP tools/resources.
- Ensure compatibility with official MCP clients and LLMs.

## Architecture
- **Server:** Python, using the official `mcp` SDK (`FastMCP`).
- **Transport:** Prefer stdio for local, HTTP for remote.
- **Primitives:**
  - **Tools:** Expose editor operations (insert, delete, update, move, etc.) as callable tools.
  - **Resources:** Expose document state, metadata, and history as resources.
  - **Prompts:** Provide reusable prompt templates for common editing tasks.


## API Endpoints (Tools)

### insert_section
**Description:** Insert a new section at a specified location.
**Input Schema:**
```json
{
  "heading": "string",
  "content": "string",
  "position": "integer (0-based index)"
}
```
**Output:**
```json
{
  "section_id": "string",
  "message": "Section inserted."
}
```
**Example Call:**
```json
{
  "heading": "Introduction",
  "content": "This is the intro.",
  "position": 0
}
```

### delete_section
**Description:** Delete a section by ID or heading.
**Input Schema:**
```json
{
  "section_id": "string (optional)",
  "heading": "string (optional)"
}
```
**Output:**
```json
{
  "message": "Section deleted."
}
```

### update_section
**Description:** Update the content of a section.
**Input Schema:**
```json
{
  "section_id": "string",
  "content": "string"
}
```
**Output:**
```json
{
  "message": "Section updated."
}
```

### move_section
**Description:** Move a section to a new location.
**Input Schema:**
```json
{
  "section_id": "string",
  "new_position": "integer"
}
```
**Output:**
```json
{
  "message": "Section moved."
}
```

### get_section
**Description:** Retrieve a section's content.
**Input Schema:**
```json
{
  "section_id": "string"
}
```
**Output:**
```json
{
  "heading": "string",
  "content": "string",
  "position": "integer"
}
```

### list_sections
**Description:** List all sections and their metadata.
**Input Schema:** `{}`
**Output:**
```json
{
  "sections": [
    {"section_id": "string", "heading": "string", "position": "integer"}
  ]
}
```

### undo / redo
**Description:** Undo/redo the last operation.
**Input Schema:** `{}`
**Output:**
```json
{
  "message": "Undo successful."
}
```

### get_document
**Description:** Retrieve the full Markdown document.
**Input Schema:** `{}`
**Output:**
```json
{
  "document": "string (full markdown)"
}
```


## Resources

### document
**Description:** The current Markdown document.
**Schema:**
```json
{
  "document": "string (full markdown)"
}
```

### history
**Description:** List of past operations (for undo/redo).
**Schema:**
```json
{
  "history": [
    {"operation": "string", "timestamp": "ISO8601", "details": "object"}
  ]
}
```

### metadata
**Description:** Document metadata (title, author, etc.).
**Schema:**
```json
{
  "title": "string",
  "author": "string",
  "created": "ISO8601",
  "modified": "ISO8601"
}
```


## Prompts

### summarize_section
**Template:**
```
Summarize the following section:
{section_content}
```

### rewrite_section
**Template:**
```
Rewrite the following section for clarity and conciseness:
{section_content}
```

### generate_outline
**Template:**
```
Generate an outline for the following document:
{document}
```


## Error Handling
- Use standard MCP error codes and messages.
- Validate all input using JSON Schema (auto-generated from type hints).
- Return meaningful error messages for invalid operations.

### Common Error Codes
| Code | Message | Description |
|------|---------|-------------|
| -32600 | Invalid Request | The request is not a valid MCP/JSON-RPC request. |
| -32601 | Method not found | The requested tool/resource does not exist. |
| -32602 | Invalid params | Input validation failed (e.g., missing/invalid fields). |
| -32000 | Application error | Editor-specific error (e.g., section not found). |

**Example Error Response:**
```json
{
  "code": -32000,
  "message": "Section not found.",
  "data": {"section_id": "abc123"}
}
```


## Security
- Authenticate clients if using HTTP transport. Supported methods: API keys (via header), OAuth2 bearer tokens.
- Document how to configure authentication in server settings.
- Validate all requests and sanitize inputs.


## Example Tool Definitions (Python)
```python
@mcp.tool()
async def insert_section(heading: str, content: str, position: int) -> dict:
    """Insert a new section at the specified position."""
    # Implementation here
    return {"section_id": "abc123", "message": "Section inserted."}

@mcp.tool()
async def delete_section(section_id: str = None, heading: str = None) -> dict:
    """Delete a section by ID or heading."""
    # Implementation here
    return {"message": "Section deleted."}

@mcp.resource()
async def document() -> dict:
    """Return the current markdown document."""
    # Implementation here
    return {"document": "# Title\n..."}
```


## Extensibility
- New tools/resources can be added by defining new `@mcp.tool()` or `@mcp.resource()` functions.
- Clients should ignore unknown primitives for forward compatibility.

## Compliance & Testing
- Use the [MCP Inspector](https://github.com/modelcontextprotocol/inspector) and official test suites to verify protocol compliance.
- Validate schemas and error handling with real MCP clients.

## References
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP Official Docs](https://modelcontextprotocol.io/)


## Next Steps
- Implement the MCP server using this spec.
- Test with official MCP clients and LLMs.
- Iterate and refine based on feedback.
