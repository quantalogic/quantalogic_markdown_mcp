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
from .safe_editor import SafeMarkdownEditor
from .safe_editor_types import (
    SectionReference,
    EditOperation,
    EditResult,
    EditTransaction,
    ValidationLevel,
    ErrorCategory,
    DocumentStatistics,
    StructureAnalysis,
    LinkError,
    SafeParseError,
)
from .mcp_server import MarkdownMCPServer, server, mcp

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
    
    # Safe Editor
    "SafeMarkdownEditor",
    "SectionReference",
    "EditOperation",
    "EditResult",
    "EditTransaction",
    "ValidationLevel",
    "ErrorCategory",
    "DocumentStatistics",
    "StructureAnalysis",
    "LinkError",
    "SafeParseError",
    
    # MCP Server
    "MarkdownMCPServer",
    "server",
    "mcp",
]
