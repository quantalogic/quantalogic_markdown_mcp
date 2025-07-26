"""Main parser interface and factory."""

from typing import Any, Dict, List, Optional, Union
import logging

from .parsers import MarkdownItParser
from .renderers import MultiFormatRenderer
from .ast_utils import ASTWrapper
from .types import ParseResult


logger = logging.getLogger(__name__)


class QuantalogicMarkdownParser:
    """Main parser interface for markdown-it-py."""

    def __init__(
        self,
        preset: str = 'commonmark',
        plugins: Optional[List[str]] = None,
        options: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize parser with markdown-it-py backend.

        Args:
            preset: Parser preset for markdown-it-py
            plugins: List of plugins to enable
            options: Parser-specific options
        """
        self.preset = preset
        self.plugins = plugins or []
        self.options = options or {}

        # Initialize parser
        self.parser = self._create_parser()
        
        # Initialize renderer
        self.renderer = MultiFormatRenderer()

        logger.info("Initialized parser with markdown-it-py backend")

    def _create_parser(self) -> MarkdownItParser:
        """Create markdown-it-py parser instance."""
        return MarkdownItParser(
            preset=self.preset,
            plugins=self.plugins,
            options=self.options
        )

    def parse(self, text: str) -> ParseResult:
        """
        Parse markdown text.

        Args:
            text: Markdown text to parse

        Returns:
            ParseResult with AST, errors, and metadata
        """
        return self.parser.parse(text)

    def parse_file(self, filepath: str, encoding: str = 'utf-8') -> ParseResult:
        """
        Parse markdown file.

        Args:
            filepath: Path to markdown file
            encoding: File encoding

        Returns:
            ParseResult with AST, errors, and metadata
        """
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                text = f.read()
            
            result = self.parse(text)
            result.metadata['source_file'] = filepath
            result.metadata['encoding'] = encoding
            
            return result
            
        except IOError as e:
            # Create error result for file I/O issues
            from .types import ParseError, ErrorLevel
            result = ParseResult(
                ast=[],
                errors=[ParseError(f"File error: {str(e)}", level=ErrorLevel.CRITICAL)],
                warnings=[],
                metadata={'source_file': filepath, 'encoding': encoding},
                source_text=""
            )
            return result

    def render(
        self,
        ast_or_result: Union[Any, ParseResult],
        format_name: str = 'html',
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Render AST to specified format.

        Args:
            ast_or_result: AST or ParseResult to render
            format_name: Output format
            options: Format-specific options

        Returns:
            Rendered content
        """
        if isinstance(ast_or_result, ParseResult):
            ast = ast_or_result.ast
        else:
            ast = ast_or_result

        return self.renderer.render(ast, format_name, options)

    def parse_and_render(
        self,
        text: str,
        format_name: str = 'html',
        options: Optional[Dict[str, Any]] = None
    ) -> tuple[str, ParseResult]:
        """
        Parse text and render to format in one step.

        Args:
            text: Markdown text to parse
            format_name: Output format
            options: Format-specific options

        Returns:
            Tuple of (rendered_content, parse_result)
        """
        result = self.parse(text)
        rendered = self.render(result, format_name, options)
        return rendered, result

    def get_ast_wrapper(self, result: ParseResult) -> ASTWrapper:
        """
        Get AST wrapper for advanced manipulation.

        Args:
            result: Parse result

        Returns:
            AST wrapper instance
        """
        return ASTWrapper(result)

    def get_supported_features(self) -> List[str]:
        """Get list of supported markdown features."""
        return self.parser.get_supported_features()

    def get_supported_formats(self) -> List[str]:
        """Get list of supported output formats."""
        return self.renderer.get_supported_formats()

    def add_renderer(self, format_name: str, renderer) -> None:
        """
        Add custom renderer.

        Args:
            format_name: Format name
            renderer: Renderer implementation
        """
        self.renderer.add_renderer(format_name, renderer)

    def validate_markdown(self, text: str) -> List[str]:
        """
        Validate markdown and return list of issues.

        Args:
            text: Markdown text to validate

        Returns:
            List of validation messages
        """
        result = self.parse(text)
        issues = []
        
        for error in result.errors:
            issues.append(str(error))
        
        for warning in result.warnings:
            issues.append(str(warning))
            
        return issues


# Convenience functions for common use cases

def parse_markdown(
    text: str,
    preset: str = 'commonmark'
) -> ParseResult:
    """
    Quick parse function.

    Args:
        text: Markdown text
        preset: Parser preset

    Returns:
        Parse result
    """
    parser = QuantalogicMarkdownParser(preset=preset)
    return parser.parse(text)


def markdown_to_html(text: str, **kwargs) -> str:
    """
    Convert markdown to HTML.

    Args:
        text: Markdown text
        **kwargs: Parser options

    Returns:
        HTML string
    """
    parser = QuantalogicMarkdownParser(**kwargs)
    rendered, _ = parser.parse_and_render(text, 'html')
    return rendered


def markdown_to_latex(text: str, **kwargs) -> str:
    """
    Convert markdown to LaTeX.

    Args:
        text: Markdown text
        **kwargs: Parser options

    Returns:
        LaTeX string
    """
    parser = QuantalogicMarkdownParser(**kwargs)
    rendered, _ = parser.parse_and_render(text, 'latex')
    return rendered
