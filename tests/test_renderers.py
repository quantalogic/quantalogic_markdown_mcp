"""Tests for rendering functionality."""

import pytest
import json

from quantalogic_markdown_mcp.renderers import (
    HTMLRenderer,
    LaTeXRenderer,
    JSONRenderer,
    MarkdownRenderer,
    MultiFormatRenderer,
)
from quantalogic_markdown_mcp.parsers import MarkdownItParser


class TestRenderers:
    """Test rendering implementations."""

    @pytest.fixture
    def sample_tokens(self):
        """Create sample tokens for testing."""
        parser = MarkdownItParser()
        result = parser.parse("# Test\n\nParagraph with *emphasis*.")
        return result.ast

    def test_html_renderer(self, sample_tokens):
        """Test HTML renderer."""
        renderer = HTMLRenderer()
        html = renderer.render(sample_tokens)
        
        assert '<h1>Test</h1>' in html
        assert '<em>emphasis</em>' in html
        assert renderer.get_output_format() == 'html'

    def test_latex_renderer(self, sample_tokens):
        """Test LaTeX renderer."""
        renderer = LaTeXRenderer()
        latex = renderer.render(sample_tokens)
        
        assert '\\documentclass{article}' in latex
        assert '\\section{' in latex
        assert 'Test' in latex
        assert renderer.get_output_format() == 'latex'

    def test_json_renderer(self, sample_tokens):
        """Test JSON renderer."""
        renderer = JSONRenderer()
        json_output = renderer.render(sample_tokens)
        
        # Should be valid JSON
        parsed = json.loads(json_output)
        assert isinstance(parsed, list)
        assert len(parsed) > 0
        assert renderer.get_output_format() == 'json'

    def test_markdown_renderer(self, sample_tokens):
        """Test Markdown renderer."""
        renderer = MarkdownRenderer()
        markdown = renderer.render(sample_tokens)
        
        assert '# Test' in markdown
        assert '*emphasis*' in markdown
        assert renderer.get_output_format() == 'markdown'

    def test_multi_format_renderer(self, sample_tokens):
        """Test multi-format renderer."""
        renderer = MultiFormatRenderer()
        
        # Test all supported formats
        for format_name in renderer.get_supported_formats():
            output = renderer.render(sample_tokens, format_name)
            assert isinstance(output, str)
            assert len(output) > 0

    def test_custom_renderer(self, sample_tokens):
        """Test adding custom renderer."""
        class CustomRenderer:
            def render(self, ast, options=None):
                return "CUSTOM OUTPUT"
            
            def get_output_format(self):
                return "custom"

        multi_renderer = MultiFormatRenderer()
        multi_renderer.add_renderer('custom', CustomRenderer())
        
        output = multi_renderer.render(sample_tokens, 'custom')
        assert output == "CUSTOM OUTPUT"

    def test_invalid_format(self, sample_tokens):
        """Test error handling for invalid format."""
        renderer = MultiFormatRenderer()
        
        with pytest.raises(ValueError, match="Unsupported format"):
            renderer.render(sample_tokens, 'invalid_format')
