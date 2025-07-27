# Quantalogic Markdown Parser

A flexible and extensible Markdown parser with AST support, built on top of the battle-tested `markdown-it-py` library.

[![Tests](https://img.shields.io/badge/tests-passing-green)](https://github.com/raphaelmansuy/quantalogic-markdown-edit-mcp)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

## Features

- **CommonMark Compliance**: Follows the CommonMark specification for consistent parsing
- **Multi-Format Output**: Render to HTML, LaTeX, JSON, and Markdown
- **Comprehensive Error Handling**: Detailed error reporting with line numbers and context
- **Extensible Architecture**: Plugin system for custom functionality
- **AST Manipulation**: Rich API for working with parsed content
- **High Performance**: Built on `markdown-it-py` for fast, accurate parsing

## Installation

```bash
pip install quantalogic-markdown-mcp
```

Or using uv:

```bash
uv add quantalogic-markdown-mcp
```

## Quick Start

```python
from quantalogic_markdown_mcp import QuantalogicMarkdownParser

# Create parser
parser = QuantalogicMarkdownParser()

# Parse markdown
result = parser.parse("# Hello\n\nThis is **bold** text.")

# Render to HTML
html = parser.render(result, 'html')
print(html)
# Output: <h1>Hello</h1>\n<p>This is <strong>bold</strong> text.</p>

# Render to LaTeX
latex = parser.render(result, 'latex')
print(latex)
# Output: Full LaTeX document with proper formatting

# Get AST analysis
wrapper = parser.get_ast_wrapper(result)
headings = wrapper.get_headings()
print(headings)
# Output: [{'level': 1, 'content': 'Hello', 'line': 1}]
```

## Convenience Functions

For simple use cases, you can use the convenience functions:

```python
from quantalogic_markdown_mcp import parse_markdown, markdown_to_html, markdown_to_latex

# Quick parsing
result = parse_markdown("# Hello World")

# Direct HTML conversion
html = markdown_to_html("# Hello\n\nParagraph with *emphasis*.")

# Direct LaTeX conversion
latex = markdown_to_latex("# Hello\n\nParagraph with **bold** text.")
```

## Supported Output Formats

| Format | Description | Use Case |
|--------|-------------|----------|
| `html` | HTML output | Web pages, documentation |
| `latex` | LaTeX document | Academic papers, PDFs |
| `json` | JSON serialization | Data processing, APIs |
| `markdown` | Markdown (round-trip) | Formatting, normalization |

## Advanced Usage

### Plugin Support

```python
from quantalogic_markdown_mcp import QuantalogicMarkdownParser

# Enable plugins
parser = QuantalogicMarkdownParser(
    preset='commonmark',
    plugins=['footnote', 'front_matter']
)
```

### Custom Rendering Options

```python
# LaTeX with custom document class
latex_options = {'document_class': 'report'}
latex = parser.render(result, 'latex', latex_options)

# JSON with custom indentation
json_options = {'indent': 4}
json_output = parser.render(result, 'json', json_options)
```

### AST Manipulation

```python
# Get AST wrapper for advanced operations
wrapper = parser.get_ast_wrapper(result)

# Extract all headings
headings = wrapper.get_headings()

# Get plain text content
text = wrapper.get_text_content()

# Convert to JSON
json_ast = wrapper.to_json()

# Find specific token types
emphasis_tokens = wrapper.find_tokens('em_open')
```

### Error Handling

```python
# Parse with error checking
result = parser.parse(markdown_text)

if result.has_errors:
    for error in result.errors:
        print(f"Error: {error}")

if result.has_warnings:
    for warning in result.warnings:
        print(f"Warning: {warning}")

# Validate markdown
issues = parser.validate_markdown(markdown_text)
for issue in issues:
    print(issue)
```

## Examples

See the `examples/` directory for comprehensive usage examples:

- `basic_usage.py` - Basic parsing and rendering examples
- More examples coming soon!

## Development

### Setting up for development

```bash
# Clone the repository
git clone https://github.com/raphaelmansuy/quantalogic-markdown-edit-mcp.git
cd quantalogic-markdown-edit-mcp

# Install with development dependencies
uv venv
uv add --dev "pytest>=7.0.0" "pytest-cov>=4.0.0" "black>=23.0.0" "ruff>=0.1.0" "mypy>=1.0.0"
uv pip install -e .
```

### Running tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src/quantalogic_markdown_mcp

# Run specific test file
pytest tests/test_parser.py -v
```

### Code quality

```bash
# Format code
black src/

# Lint code
ruff check src/

# Type checking
mypy src/
```

## Architecture

The parser is built with a modular architecture:

- **Core Types** (`types.py`): Data structures and protocols
- **Parsers** (`parsers.py`): Markdown-it-py integration
- **Renderers** (`renderers.py`): Multi-format output generation
- **AST Utils** (`ast_utils.py`): AST manipulation utilities
- **Main Parser** (`parser.py`): High-level interface

## Why markdown-it-py?

We chose `markdown-it-py` over other alternatives because:

- **Ecosystem Dominance**: Used by 336k+ repositories
- **Active Maintenance**: Part of Google's Assured OSS program
- **Rich Plugin System**: Extensive plugin ecosystem
- **Better Architecture**: Token-based parsing with granular control
- **Specification Compliance**: Strict CommonMark compliance
- **Performance**: Fast parsing with accurate results

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built on top of [markdown-it-py](https://github.com/executablebooks/markdown-it-py)
- Inspired by the [markdown-it](https://github.com/markdown-it/markdown-it) JavaScript library
- Thanks to the CommonMark specification authors for standardizing Markdown

## Support

If you encounter any issues or have questions, please:

1. Check the [documentation](docs/)
2. Search existing [issues](https://github.com/raphaelmansuy/quantalogic-markdown-edit-mcp/issues)
3. Create a new issue with a minimal reproducible example

## Changelog

### v0.1.0 (2025-07-26)

- Initial release
- Core parsing functionality with markdown-it-py
- Multi-format rendering (HTML, LaTeX, JSON, Markdown)
- Comprehensive test suite
- AST manipulation utilities
- Error handling and validation
