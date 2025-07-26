"""Basic usage examples for Quantalogic Markdown Parser."""

from quantalogic_markdown_mcp import (
    QuantalogicMarkdownParser,
    parse_markdown,
    markdown_to_html,
    markdown_to_latex,
)


def basic_parsing_example():
    """Demonstrate basic parsing."""
    print("=== Basic Parsing Example ===")
    
    markdown_text = """
# Welcome to Markdown Parser

This is a **powerful** parser that supports:

- Multiple output formats
- *CommonMark* compliance
- Extensible architecture

Check out the [documentation](https://example.com) for more details.

```python
# Code blocks are supported too!
def hello():
    return "Hello, World!"
```
"""

    # Create parser instance
    parser = QuantalogicMarkdownParser()
    
    # Parse the markdown
    result = parser.parse(markdown_text)
    
    print(f"Parsed {len(result.ast)} tokens")
    print(f"Errors: {len(result.errors)}")
    print(f"Warnings: {len(result.warnings)}")
    print(f"Parser: {result.metadata['parser']}")
    
    # Get AST wrapper for analysis
    ast_wrapper = parser.get_ast_wrapper(result)
    headings = ast_wrapper.get_headings()
    
    print(f"Found {len(headings)} headings:")
    for heading in headings:
        print(f"  Level {heading['level']}: {heading['content']}")


def multi_format_rendering_example():
    """Demonstrate rendering to multiple formats."""
    print("\n=== Multi-Format Rendering Example ===")
    
    markdown_text = "# Hello\n\nThis is *emphasis* and **strong** text."
    
    parser = QuantalogicMarkdownParser()
    result = parser.parse(markdown_text)
    
    # Render to different formats
    html = parser.render(result, 'html')
    latex = parser.render(result, 'latex')
    json_output = parser.render(result, 'json')
    
    print("HTML Output:")
    print(html[:100] + "...")
    
    print("\nLaTeX Output:")
    print(latex[:200] + "...")
    
    print("\nJSON Output:")
    print(json_output[:150] + "...")


def convenience_functions_example():
    """Demonstrate convenience functions."""
    print("\n=== Convenience Functions Example ===")
    
    markdown_text = "# Quick Example\n\nUse **convenience functions** for *simple* tasks."
    
    # Quick parsing
    result = parse_markdown(markdown_text)
    print(f"Quick parse: {len(result.ast)} tokens")
    
    # Direct conversion to HTML
    html = markdown_to_html(markdown_text)
    print(f"HTML length: {len(html)} characters")
    print("HTML preview:", html[:60] + "...")
    
    # Direct conversion to LaTeX
    latex = markdown_to_latex(markdown_text)
    print(f"LaTeX length: {len(latex)} characters")


def error_handling_example():
    """Demonstrate error handling."""
    print("\n=== Error Handling Example ===")
    
    # Parse with potential issues
    problematic_text = """
# Heading

Some text with [unclosed link

Another paragraph.
"""

    parser = QuantalogicMarkdownParser()
    result = parser.parse(problematic_text)
    
    print(f"Errors found: {len(result.errors)}")
    print(f"Warnings found: {len(result.warnings)}")
    
    # Validate markdown
    issues = parser.validate_markdown(problematic_text)
    print(f"Validation issues: {len(issues)}")
    
    for issue in issues:
        print(f"  - {issue}")


def parser_features_example():
    """Demonstrate parser features and capabilities."""
    print("\n=== Parser Features Example ===")
    
    markdown_text = "# Test\n\n- Item 1\n- Item 2\n\n*Emphasis* text."
    
    # Parse with markdown-it-py
    parser = QuantalogicMarkdownParser()
    result = parser.parse(markdown_text)
    
    print(f"markdown-it-py: {len(result.ast)} tokens")
    
    # Show features
    features = parser.get_supported_features()
    print(f"Supported features: {', '.join(features)}")
    
    # Show formats
    formats = parser.get_supported_formats()
    print(f"Supported formats: {', '.join(formats)}")


if __name__ == "__main__":
    basic_parsing_example()
    multi_format_rendering_example()
    convenience_functions_example()
    error_handling_example()
    parser_features_example()
    
    print("\n=== All Examples Complete ===")
