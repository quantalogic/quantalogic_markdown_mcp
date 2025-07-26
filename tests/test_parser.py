"""Tests for the main parser functionality."""

import pytest

from quantalogic_markdown_mcp import (
    QuantalogicMarkdownParser,
    parse_markdown,
    markdown_to_html,
    markdown_to_latex,
    ParseResult,
    ErrorLevel,
)


class TestQuantalogicMarkdownParser:
    """Test suite for the main parser."""

    @pytest.fixture
    def parser(self):
        """Create parser instance for testing."""
        return QuantalogicMarkdownParser()

    @pytest.fixture
    def sample_markdown(self):
        """Sample markdown text for testing."""
        return """# Heading 1

This is a paragraph with *emphasis* and **strong** text.

## Heading 2

- List item 1
- List item 2
  - Nested item

[Link](https://example.com)

![Image](image.png "Title")

```python
def hello_world():
    print("Hello, World!")
```

> This is a blockquote
"""

    def test_basic_parsing(self, parser, sample_markdown):
        """Test basic parsing functionality."""
        result = parser.parse(sample_markdown)
        
        assert isinstance(result, ParseResult)
        assert not result.has_errors
        assert result.ast is not None
        assert len(result.ast) > 0
        assert result.metadata['parser'] == 'markdown-it-py'

    def test_parse_file(self, parser, tmp_path):
        """Test parsing from file."""
        # Create temporary markdown file
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test\n\nContent here")
        
        result = parser.parse_file(str(md_file))
        
        assert not result.has_errors
        assert result.metadata['source_file'] == str(md_file)

    def test_html_rendering(self, parser, sample_markdown):
        """Test HTML rendering."""
        result = parser.parse(sample_markdown)
        html = parser.render(result, 'html')
        
        assert '<h1>' in html
        assert '<p>' in html
        assert '<em>' in html
        assert '<strong>' in html
        assert '<ul>' in html
        assert '<a href=' in html

    def test_latex_rendering(self, parser, sample_markdown):
        """Test LaTeX rendering."""
        result = parser.parse(sample_markdown)
        latex = parser.render(result, 'latex')
        
        assert '\\documentclass' in latex
        assert '\\section{' in latex
        assert '\\textit{' in latex
        assert '\\textbf{' in latex

    def test_json_rendering(self, parser, sample_markdown):
        """Test JSON rendering."""
        result = parser.parse(sample_markdown)
        json_output = parser.render(result, 'json')
        
        import json
        parsed_json = json.loads(json_output)
        assert isinstance(parsed_json, list)
        assert len(parsed_json) > 0

    def test_markdown_rendering(self, parser, sample_markdown):
        """Test Markdown round-trip rendering."""
        result = parser.parse(sample_markdown)
        md_output = parser.render(result, 'markdown')
        
        assert '# Heading 1' in md_output
        assert '*emphasis*' in md_output
        assert '**strong**' in md_output

    def test_parse_and_render(self, parser, sample_markdown):
        """Test combined parse and render."""
        html, result = parser.parse_and_render(sample_markdown, 'html')
        
        assert '<h1>' in html
        assert not result.has_errors

    def test_ast_wrapper(self, parser, sample_markdown):
        """Test AST wrapper functionality."""
        result = parser.parse(sample_markdown)
        wrapper = parser.get_ast_wrapper(result)
        
        headings = wrapper.get_headings()
        assert len(headings) >= 2
        assert headings[0]['level'] == 1
        assert 'Heading 1' in headings[0]['content']

    def test_supported_features(self, parser):
        """Test feature detection."""
        features = parser.get_supported_features()
        
        expected_features = ['headings', 'paragraphs', 'lists', 'emphasis', 'links']
        for feature in expected_features:
            assert feature in features

    def test_validation(self, parser):
        """Test markdown validation."""
        invalid_md = "# Heading\n\n[unclosed link"
        issues = parser.validate_markdown(invalid_md)
        
        # Note: markdown-it-py is forgiving, so this might not produce errors
        assert isinstance(issues, list)

    def test_plugins(self):
        """Test plugin loading."""
        parser = QuantalogicMarkdownParser(plugins=['footnote'])
        assert 'footnote' in parser.plugins

    def test_error_handling(self, parser):
        """Test error handling for edge cases."""
        # Empty input
        result = parser.parse("")
        assert not result.has_errors
        assert result.ast == []

        # Very large input (should not crash)
        large_text = "# Heading\n" + "Text paragraph. " * 10000
        result = parser.parse(large_text)
        assert not result.has_errors


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_parse_markdown(self):
        """Test parse_markdown function."""
        result = parse_markdown("# Test")
        assert isinstance(result, ParseResult)
        assert not result.has_errors

    def test_markdown_to_html(self):
        """Test markdown_to_html function."""
        html = markdown_to_html("# Test\n\nParagraph with *emphasis*.")
        assert '<h1>Test</h1>' in html
        assert '<em>emphasis</em>' in html

    def test_markdown_to_latex(self):
        """Test markdown_to_latex function."""
        latex = markdown_to_latex("# Test\n\nParagraph.")
        assert '\\section{' in latex
        assert 'Test' in latex
        assert '\\documentclass' in latex


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_file_not_found(self):
        """Test handling of non-existent files."""
        parser = QuantalogicMarkdownParser()
        result = parser.parse_file("nonexistent.md")
        
        assert result.has_errors
        assert result.errors[0].level == ErrorLevel.CRITICAL

    def test_invalid_format(self):
        """Test invalid output format."""
        parser = QuantalogicMarkdownParser()
        result = parser.parse("# Test")
        
        with pytest.raises(ValueError):
            parser.render(result, 'invalid_format')

    def test_malformed_input(self):
        """Test handling of potentially problematic input."""
        parser = QuantalogicMarkdownParser()
        
        # Test with null bytes
        result = parser.parse("# Test\x00content")
        # Should not crash, markdown-it-py handles this gracefully
        assert isinstance(result, ParseResult)


if __name__ == "__main__":
    pytest.main([__file__])
