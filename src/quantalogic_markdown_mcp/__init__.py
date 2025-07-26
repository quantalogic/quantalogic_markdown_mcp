"""Quantalogic Markdown Parser - A flexible and extensible Markdown parser with AST support.""" 

from .parser import (
    QuantalogicMarkdownParser,
    parse_markdown,
    markdown_to_html,
    markdown_to_latex,
)
from .parsers import MarkdownItParser
from .renderers import (
    HTMLRenderer,
    LaTeXRenderer,
    JSONRenderer,
    MarkdownRenderer,
    MultiFormatRenderer,
)
from .ast_utils import ASTWrapper
from .types import ParseResult, ParseError, ErrorLevel

__version__ = "0.1.0"
__author__ = "Raphael Mansuy"
__email__ = "raphael.mansuy@example.com"

__all__ = [
    # Main interface
    "QuantalogicMarkdownParser",
    "parse_markdown",
    "markdown_to_html",
    "markdown_to_latex",
    
    # Parsers
    "MarkdownItParser",
    
    # Renderers
    "HTMLRenderer",
    "LaTeXRenderer",
    "JSONRenderer",
    "MarkdownRenderer",
    "MultiFormatRenderer",
    
    # Utilities
    "ASTWrapper",
    
    # Types
    "ParseResult",
    "ParseError",
    "ErrorLevel",
]
