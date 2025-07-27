# SafeMarkdownEditor MCP Server

A Model Context Protocol (MCP) server that provides powerful Markdown document editing capabilities with thread-safe operations, atomic transactions, and comprehensive validation.

## Features

✨ **Comprehensive Markdown Editing**

- Insert, update, delete, and move sections
- Thread-safe operations with atomic transactions
- Immutable section references that remain stable across edits
- Comprehensive validation with configurable strictness levels

🔧 **MCP Tools Available**

**File Operations:**

- `load_document` - Load a Markdown document from a file path (supports absolute, relative, and ~ expansion)
- `save_document` - Save the current document to a file path
- `get_file_info` - Get information about the currently loaded file
- `test_path_resolution` - Test and verify path resolution for different path formats

**Document Editing:**

- `insert_section` - Insert new sections at specified positions
- `delete_section` - Remove sections by ID or heading
- `update_section` - Modify section content while preserving structure
- `move_section` - Reorder sections within the document
- `get_section` - Retrieve individual section content and metadata
- `list_sections` - Get an overview of all document sections
- `get_document` - Export the complete Markdown document
- `undo` - Rollback the last operation

📊 **MCP Resources**

- `document://current` - Real-time access to the current document
- `document://history` - Transaction history for undo/redo operations
- `document://metadata` - Document metadata (title, author, timestamps)

🎯 **MCP Prompts**

- `summarize_section` - Generate section summaries
- `rewrite_section` - Improve section clarity and conciseness
- `generate_outline` - Create document outlines

## Installation

### Prerequisites

- Python 3.11 or higher
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Install with uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/raphaelmansuy/quantalogic-markdown-edit-mcp.git
cd quantalogic-markdown-edit-mcp

# Install dependencies
uv sync

# Install in development mode
uv pip install -e .
```

### Install with pip

```bash
# Clone the repository
git clone https://github.com/raphaelmansuy/quantalogic-markdown-edit-mcp.git
cd quantalogic-markdown-edit-mcp

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

## Quick Start

### Running the Server

#### Method 1: Direct Python Execution

```bash
# Using uv
uv run python -m quantalogic_markdown_mcp.mcp_server

# Or with regular Python
python -m quantalogic_markdown_mcp.mcp_server
```

#### Method 2: Using the Development Script

```bash
# Run the development server
python dev-scripts/run_mcp_server.py
```

#### Method 3: Using FastMCP CLI

```bash
# Install FastMCP CLI if not already installed
uv add fastmcp

# Run with FastMCP CLI
fastmcp run src/quantalogic_markdown_mcp/mcp_server.py:mcp
```

### Connecting to Claude Desktop

To use this MCP server with Claude Desktop, add the following configuration to your `claude_desktop_config.json`:

**macOS/Linux:**

```json
{
  "mcpServers": {
    "markdown-editor": {
      "command": "uv",
      "args": [
        "--directory",
        "/ABSOLUTE/PATH/TO/quantalogic-markdown-edit-mcp",
        "run",
        "python",
        "-m",
        "quantalogic_markdown_mcp.mcp_server"
      ]
    }
  }
}
```

**Windows:**

```json
{
  "mcpServers": {
    "markdown-editor": {
      "command": "uv.exe",
      "args": [
        "--directory",
        "C:\\ABSOLUTE\\PATH\\TO\\quantalogic-markdown-edit-mcp",
        "run",
        "python",
        "-m",
        "quantalogic_markdown_mcp.mcp_server"
      ]
    }
  }
}
```

**Configuration file locations:**

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

After adding the configuration, restart Claude Desktop.

## Working with Files

The MCP server supports loading and saving Markdown documents from various file path formats:

### Supported Path Formats

- **Absolute paths**: `/Users/username/documents/file.md`
- **Relative paths**: `./documents/file.md` or `documents/file.md`
- **Home directory expansion**: `~/Documents/file.md`
- **Environment variables**: `$HOME/documents/file.md`

### File Operations Examples

```text
"Load the document from ~/Documents/my-notes.md"
"Load the file at ./project-docs/README.md"
"Save this document to /Users/me/Desktop/backup.md"
"Get information about the current file"
"Test if the path ~/Documents/draft.md resolves correctly"
```

## Usage Examples

### Basic Document Operations

Once connected to Claude Desktop (or another MCP client), you can use natural language commands:

```text
"Load the document from ~/Documents/my-project.md"
"Create a new section called 'Getting Started' with some basic instructions"
"Move the 'Installation' section to be the second section"
"Update the 'Features' section to include the new functionality"
"Delete the 'Deprecated' section"
"Save the document to ./backups/project-backup.md"
"Show me all the sections in this document"
"Get the current document as Markdown"
```

### Working with Different Path Types

```text
"Load /Users/me/Documents/important-notes.md"
"Load the file at ./project-docs/specification.md"
"Load ~/Desktop/meeting-notes.md"
"Test if the path $HOME/Documents/draft.md exists"
"Save to /tmp/quick-backup.md with backup enabled"
```

### Programmatic Usage

You can also use the server programmatically with FastMCP clients:

```python
import asyncio
from fastmcp import Client

async def demo():
    # Connect to the server
    async with Client("src/quantalogic_markdown_mcp/mcp_server.py") as client:
        # List available tools
        tools = await client.list_tools()
        print(f"Available tools: {[tool.name for tool in tools]}")
        
        # Load a document from file
        result = await client.call_tool("load_document", {
            "file_path": "~/Documents/my-notes.md",
            "validation_level": "NORMAL"
        })
        print(f"Load result: {result.content}")
        
        # Get file information
        file_info = await client.call_tool("get_file_info", {})
        print(f"File info: {file_info.content}")
        
        # Test path resolution
        path_test = await client.call_tool("test_path_resolution", {
            "path": "~/Documents/test.md"
        })
        print(f"Path resolution: {path_test.content}")
        
        # Insert a new section
        result = await client.call_tool("insert_section", {
            "heading": "Introduction",
            "content": "Welcome to our documentation!",
            "position": 0
        })
        print(f"Insert result: {result.content}")
        
        # List all sections
        sections = await client.call_tool("list_sections", {})
        print(f"Document sections: {sections.content}")
        
        # Save the modified document
        save_result = await client.call_tool("save_document", {
            "file_path": "./modified-notes.md",
            "backup": True
        })
        print(f"Save result: {save_result.content}")

# Run the demo
asyncio.run(demo())
```

## Tool Reference

### File Operation Tools

### `load_document(file_path: str, validation_level: str = "NORMAL")`

Load a Markdown document from a file path with support for various path formats.

**Parameters:**

- `file_path`: Path to the Markdown file (supports absolute, relative, ~, and $ENV expansion)
- `validation_level`: Validation strictness - "STRICT", "NORMAL", or "PERMISSIVE"

**Returns:** Success status with file information and document statistics

**Examples:**

- `load_document("/Users/me/notes.md")`
- `load_document("./docs/README.md")`
- `load_document("~/Documents/project.md")`

### `save_document(file_path?: str, backup: bool = True)`

Save the current document to a file path.

**Parameters:**

- `file_path`: Target path to save to (optional, uses current file if not provided)
- `backup`: Whether to create a .bak backup of existing files

**Returns:** Success status with save location information

### `get_file_info()`

Get detailed information about the currently loaded file.

**Returns:** File metadata including path, size, permissions, and timestamps

### `test_path_resolution(path: str)`

Test and validate path resolution for different path formats.

**Parameters:**

- `path`: The path to test and resolve

**Returns:** Detailed path resolution information including expansion details

### Document Editing Tools

### `insert_section(heading: str, content: str, position: int)`

Insert a new section at the specified position.

**Parameters:**

- `heading`: The section heading text
- `content`: The section content (can include Markdown)
- `position`: Where to insert (0 = beginning, or after existing section)

**Returns:** Success/failure status with section ID if successful

### `delete_section(section_id?: str, heading?: str)`

Delete a section by ID or heading.

**Parameters:**

- `section_id`: Unique section identifier (optional)
- `heading`: Section heading text (optional)

**Note:** Either `section_id` or `heading` must be provided.

### `update_section(section_id: str, content: str)`

Update the content of an existing section.

**Parameters:**

- `section_id`: Unique section identifier
- `content`: New content for the section

### `move_section(section_id: str, new_position: int)`

Move a section to a new position in the document.

**Parameters:**

- `section_id`: Unique section identifier
- `new_position`: Target position (0-based)

### `get_section(section_id: str)`

Retrieve detailed information about a specific section.

**Returns:** Section heading, content, position, level, and ID

### `list_sections()`

Get metadata for all sections in the document.

**Returns:** Array of section metadata (ID, heading, position, level, path)

### `get_document()`

Export the complete Markdown document.

**Returns:** Full document as Markdown text

### `undo()`

Undo the last operation performed on the document.

**Returns:** Success/failure status

## Configuration Options

The server supports several configuration options through environment variables:

```bash
# Validation level (STRICT, NORMAL, PERMISSIVE)
export MARKDOWN_VALIDATION_LEVEL=NORMAL

# Maximum transaction history size
export MAX_TRANSACTION_HISTORY=100

# Server name
export MCP_SERVER_NAME="SafeMarkdownEditor"
```

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test files
uv run pytest tests/test_mcp_server.py
```

### Code Quality

```bash
# Format code
uv run black src tests

# Lint code
uv run ruff check src tests

# Type checking
uv run mypy src
```

### Development Server

For development, you can run the server with additional debugging:

```python
# In dev-scripts/run_mcp_server.py
from quantalogic_markdown_mcp.mcp_server import server

if __name__ == "__main__":
    # Initialize with debug document
    server.initialize_document(
        markdown_text="""# Sample Document

## Introduction
This is a sample document for testing.

## Features  
- Feature 1
- Feature 2

## Conclusion
Thank you for reading!
""",
        validation_level=ValidationLevel.NORMAL
    )
    
    print("Starting SafeMarkdownEditor MCP Server...")
    print("Debug mode enabled with sample document")
    server.run()
```

## Troubleshooting

### Common Issues

**Server not appearing in Claude Desktop:**

1. Check that the path in `claude_desktop_config.json` is absolute
2. Verify that `uv` is in your PATH (`which uv` on macOS/Linux, `where uv` on Windows)
3. Restart Claude Desktop after configuration changes
4. Check Claude Desktop logs for error messages

**Tool execution errors:**

1. Ensure the document is initialized (the server auto-initializes if needed)
2. Check section IDs are valid using `list_sections` first
3. Verify that section references haven't changed after edits

**Performance issues:**

1. Large documents may take time to process
2. Consider using section-level operations instead of full document operations
3. Monitor transaction history size

### Debug Mode

Enable debug logging by setting:

```bash
export PYTHONPATH=$PWD/src
export MCP_DEBUG=1
python -m quantalogic_markdown_mcp.mcp_server
```

### Logging

The server uses Python's logging module and writes to stderr to avoid interfering with MCP's stdio transport. To see debug logs:

```bash
# Run with debug logging
PYTHONPATH=$PWD/src python -m quantalogic_markdown_mcp.mcp_server 2>debug.log
```

## Architecture

The server is built on several key components:

- **SafeMarkdownEditor**: Core thread-safe editing engine with atomic operations
- **MarkdownMCPServer**: MCP server wrapper that exposes editing capabilities
- **FastMCP**: Modern MCP framework for Python with automatic schema generation
- **Transaction System**: Atomic operations with rollback support
- **Validation Engine**: Configurable document structure validation

## Contributing

Contributions are welcome! Please read our contributing guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Ensure all tests pass and code is formatted
5. Submit a pull request

### Development Setup

```bash
# Clone and setup
git clone https://github.com/raphaelmansuy/quantalogic-markdown-edit-mcp.git
cd quantalogic-markdown-edit-mcp

# Install with development dependencies
uv sync --group dev

# Install pre-commit hooks
uv run pre-commit install
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Related Projects

- [Model Context Protocol](https://modelcontextprotocol.io/) - The protocol specification
- [FastMCP](https://gofastmcp.com/) - Python framework for building MCP servers
- [Claude Desktop](https://claude.ai/download) - AI assistant with MCP support

---

**Need help?** Open an issue on [GitHub](https://github.com/raphaelmansuy/quantalogic-markdown-edit-mcp/issues) or check the [documentation](docs/).
