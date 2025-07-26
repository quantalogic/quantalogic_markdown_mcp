# Markdown Parser Implementation Guide

This document provides a step-by-step implementation guide for building a markdown parser based on the specification in `01-problem-markdown.md`. The implementation follows a focused approach using markdown-it-py as the foundation.

## Design Decision: Why markdown-it-py Only?

After extensive research, we chose to implement only markdown-it-py rather than supporting multiple parser backends (like mistletoe). Here's why:

### Key Advantages of markdown-it-py:
- **Ecosystem Dominance**: Used by 336k+ repositories vs mistletoe's smaller adoption
- **Active Maintenance**: Maintained by the Executable Books Project (part of Google's Assured OSS)
- **Rich Plugin System**: Extensive plugin ecosystem via `mdit-py-plugins`
- **Better Architecture**: Token-based parsing provides granular control and better error reporting
- **Specification Compliance**: Strict CommonMark compliance with predictable behavior
- **Performance**: Fast parsing with accurate results (mistletoe sacrifices correctness for speed)

### Problems with Supporting Multiple Parsers:
- **Complexity Without Benefit**: Different APIs require duplicate code paths
- **Maintenance Burden**: More dependencies and testing overhead  
- **User Confusion**: No clear guidance on which parser to choose
- **Quality Issues**: mistletoe makes parsing shortcuts that produce incorrect results

For example, mistletoe incorrectly parses this CommonMark:
```markdown
***foo** bar*
```
- **Correct**: `<p><em><strong>foo</strong> bar</em></p>`
- **Mistletoe**: `<p><strong>*foo</strong> bar*</p>`

## Overview

We'll build a Python markdown parser that:

- Leverages `markdown-it-py` as the parsing engine
- Supports multiple output formats (HTML, LaTeX, JSON, Markdown)
- Includes comprehensive error handling and validation
- Offers a plugin system for extensibility
- Maintains CommonMark compliance

## Phase 1: Project Setup

### Step 1.1: Initialize Project Structure

First, let's set up the proper Python project structure using modern best practices:

```bash
# Create project directory structure
mkdir -p src/quantalogic_markdown_mcp
mkdir -p tests
mkdir -p docs

# Create essential files
touch src/quantalogic_markdown_mcp/__init__.py
touch README.md
touch LICENSE
```

### Step 1.2: Configure pyproject.toml

Create the project configuration with all necessary dependencies:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "quantalogic-markdown-mcp"
version = "0.1.0"
description = "A flexible and extensible Markdown parser with AST support"
readme = "README.md"
requires-python = ">=3.11"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "your.email@example.com"},
]
keywords = ["markdown", "parser", "ast", "commonmark"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Text Processing :: Markup",
    "Topic :: Software Development :: Libraries :: Python Modules",
]

dependencies = [
    "markdown-it-py>=3.0.0",
    "mdit-py-plugins>=0.4.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
]
latex = [
    "Pygments>=2.0.0",
]
test = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
]

[project.urls]
Homepage = "https://github.com/yourusername/quantalogic-markdown-mcp"
Repository = "https://github.com/yourusername/quantalogic-markdown-mcp"
Documentation = "https://github.com/yourusername/quantalogic-markdown-mcp/docs"
Issues = "https://github.com/yourusername/quantalogic-markdown-mcp/issues"

[tool.hatch.build.targets.wheel]
packages = ["src/quantalogic_markdown_mcp"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]

[tool.black]
line-length = 88
target-version = ['py311']

[tool.ruff]
line-length = 88
target-version = "py311"

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

### Step 1.3: Set Up Development Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate environment (Linux/macOS)
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev,test,latex]"

# Or using uv (recommended)
uv venv
uv add --dev "pytest>=7.0.0" "pytest-cov>=4.0.0" "black>=23.0.0" "ruff>=0.1.0" "mypy>=1.0.0"
uv add "markdown-it-py>=3.0.0" "mdit-py-plugins>=0.4.0"
```

## Phase 2: Core AST Classes

### Step 2.1: Define Core Data Structures

Create `src/quantalogic_markdown_mcp/types.py`:

```python
"""Core data structures for the markdown parser."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, Union
from abc import ABC, abstractmethod
from enum import Enum


class ErrorLevel(Enum):
    """Error severity levels."""
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ParseError:
    """Represents a parsing error with context."""
    message: str
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    level: ErrorLevel = ErrorLevel.ERROR
    context: Optional[str] = None

    def __str__(self) -> str:
        """Format error message for display."""
        if self.line_number is not None:
            location = f"Line {self.line_number}"
            if self.column_number is not None:
                location += f", Column {self.column_number}"
            return f"{self.level.value.title()}: {self.message} ({location})"
        return f"{self.level.value.title()}: {self.message}"


@dataclass
class ParseResult:
    """Result of parsing markdown text."""
    ast: Any  # Token list from markdown-it-py or Document from mistletoe
    errors: List[ParseError]
    warnings: List[ParseError]
    metadata: Dict[str, Any]
    source_text: str

    @property
    def has_errors(self) -> bool:
        """Check if parsing resulted in errors."""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if parsing resulted in warnings."""
        return len(self.warnings) > 0

    def add_error(self, message: str, line_number: Optional[int] = None,
                  level: ErrorLevel = ErrorLevel.ERROR) -> None:
        """Add an error to the result."""
        error = ParseError(message=message, line_number=line_number, level=level)
        if level == ErrorLevel.WARNING:
            self.warnings.append(error)
        else:
            self.errors.append(error)


class MarkdownParser(Protocol):
    """Protocol for markdown parsers."""

    def parse(self, text: str) -> ParseResult:
        """Parse markdown text and return result with AST and errors."""
        ...

    def get_supported_features(self) -> List[str]:
        """Return list of supported markdown features."""
        ...


class Renderer(ABC):
    """Abstract base class for renderers."""

    @abstractmethod
    def render(self, ast: Any, options: Optional[Dict[str, Any]] = None) -> str:
        """Render AST to target format."""
        pass

    @abstractmethod
    def get_output_format(self) -> str:
        """Return the output format name."""
        pass
```

### Step 2.2: Implement MarkdownIt Parser

Create `src/quantalogic_markdown_mcp/parsers.py`:

```python
"""Markdown parser implementation using markdown-it-py."""

from typing import Dict, List, Optional, Any
import logging

from markdown_it import MarkdownIt
from markdown_it.token import Token
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.front_matter import front_matter_plugin

from .types import MarkdownParser, ParseResult, ParseError, ErrorLevel


logger = logging.getLogger(__name__)


class MarkdownItParser:
    """Parser implementation using markdown-it-py."""

    def __init__(
        self,
        preset: str = 'commonmark',
        plugins: Optional[List[str]] = None,
        options: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize parser with configuration.

        Args:
            preset: Parser preset ('commonmark', 'gfm-like', 'zero')
            plugins: List of plugin names to enable
            options: Additional parser options
        """
        self.preset = preset
        self.plugins = plugins or []
        self.options = options or {}

        self.md = MarkdownIt(preset, self.options)

        # Load plugins
        self._load_plugins()

    def _load_plugins(self) -> None:
        """Load and configure plugins."""
        plugin_map = {
            'footnote': footnote_plugin,
            'front_matter': front_matter_plugin,
        }

        for plugin_name in self.plugins:
            if plugin_name in plugin_map:
                self.md.use(plugin_map[plugin_name])
                logger.debug(f"Loaded plugin: {plugin_name}")
            else:
                logger.warning(f"Unknown plugin: {plugin_name}")

    def parse(self, text: str) -> ParseResult:
        """
        Parse markdown text.

        Args:
            text: Markdown text to parse

        Returns:
            ParseResult with tokens, errors, and metadata
        """
        result = ParseResult(
            ast=[],
            errors=[],
            warnings=[],
            metadata={
                'parser': 'markdown-it-py',
                'preset': self.preset,
                'plugins': self.plugins
            },
            source_text=text
        )

        try:
            # Parse text to tokens
            tokens = self.md.parse(text)
            result.ast = tokens
            result.metadata['token_count'] = len(tokens)

            # Validate token structure
            validation_errors = self._validate_tokens(tokens, text)
            result.errors.extend(validation_errors)

            logger.info(f"Parsed {len(tokens)} tokens with {len(result.errors)} errors")

        except Exception as e:
            error = ParseError(
                message=f"Parsing failed: {str(e)}",
                level=ErrorLevel.CRITICAL
            )
            result.errors.append(error)
            logger.error(f"Parse error: {e}")

        return result

    def _validate_tokens(self, tokens: List[Token], source_text: str) -> List[ParseError]:
        """
        Validate token structure and detect issues.

        Args:
            tokens: List of tokens to validate
            source_text: Original source text

        Returns:
            List of validation errors
        """
        errors = []
        nesting_stack = []
        source_lines = source_text.splitlines()

        for i, token in enumerate(tokens):
            # Check line mapping
            if token.map and len(token.map) >= 2:
                line_start, line_end = token.map[0], token.map[1]
                if line_start < 0 or line_end > len(source_lines):
                    errors.append(ParseError(
                        message=f"Invalid line mapping for token {token.type}",
                        line_number=line_start + 1 if line_start >= 0 else None,
                        level=ErrorLevel.WARNING
                    ))

            # Check nesting structure
            if token.nesting == 1:  # Opening token
                nesting_stack.append((token.type, i, token.map[0] if token.map else None))
            elif token.nesting == -1:  # Closing token
                if not nesting_stack:
                    errors.append(ParseError(
                        message=f"Unmatched closing token: {token.type}",
                        line_number=token.map[0] + 1 if token.map else None,
                        level=ErrorLevel.ERROR
                    ))
                else:
                    opening_type, opening_pos, opening_line = nesting_stack.pop()
                    expected_closing = opening_type.replace('_open', '_close')
                    if token.type != expected_closing:
                        errors.append(ParseError(
                            message=f"Mismatched tokens: {opening_type} (pos {opening_pos}) "
                                  f"closed by {token.type} (pos {i})",
                            line_number=opening_line + 1 if opening_line is not None else None,
                            level=ErrorLevel.ERROR
                        ))

        # Check for unclosed tokens
        for opening_type, pos, line_num in nesting_stack:
            errors.append(ParseError(
                message=f"Unclosed token: {opening_type}",
                line_number=line_num + 1 if line_num is not None else None,
                level=ErrorLevel.ERROR
            ))

        return errors

    def get_supported_features(self) -> List[str]:
        """Return list of supported markdown features."""
        active_rules = self.md.get_active_rules()
        features = []

        # Map rules to feature names
        rule_features = {
            'heading': 'headings',
            'paragraph': 'paragraphs',
            'list': 'lists',
            'emphasis': 'emphasis',
            'link': 'links',
            'image': 'images',
            'fence': 'code_blocks',
            'table': 'tables',
            'strikethrough': 'strikethrough',
            'blockquote': 'blockquotes',
        }

        for rule_type, rules in active_rules.items():
            for rule in rules:
                if rule in rule_features:
                    feature = rule_features[rule]
                    if feature not in features:
                        features.append(feature)

        return sorted(features)
```

## Phase 3: Token Processing and AST Manipulation

### Step 3.1: Create AST Utilities

Create `src/quantalogic_markdown_mcp/ast_utils.py`:

```python
"""AST manipulation and traversal utilities."""

from typing import Any, Callable, Iterator, List, Optional, Union
import json

from markdown_it.token import Token
from markdown_it.tree import SyntaxTreeNode

from .types import ParseResult


def walk_tokens(tokens: List[Token], callback: Callable[[Token, int], None]) -> None:
    """
    Walk through tokens and apply callback to each.

    Args:
        tokens: List of tokens to traverse
        callback: Function to call for each token
    """
    for i, token in enumerate(tokens):
        callback(token, i)
        if token.children:
            walk_tokens(token.children, callback)


def find_tokens_by_type(tokens: List[Token], token_type: str) -> List[Token]:
    """
    Find all tokens of a specific type.

    Args:
        tokens: List of tokens to search
        token_type: Type of token to find

    Returns:
        List of matching tokens
    """
    found_tokens = []

    def collector(token: Token, index: int) -> None:
        if token.type == token_type:
            found_tokens.append(token)

    walk_tokens(tokens, collector)
    return found_tokens


def token_to_dict(token: Token) -> dict:
    """
    Convert token to dictionary for serialization.

    Args:
        token: Token to convert

    Returns:
        Dictionary representation of token
    """
    return token.as_dict()


def tokens_to_json(tokens: List[Token], indent: int = 2) -> str:
    """
    Convert tokens to JSON string.

    Args:
        tokens: List of tokens to convert
        indent: JSON indentation

    Returns:
        JSON string representation
    """
    token_dicts = [token_to_dict(token) for token in tokens]
    return json.dumps(token_dicts, indent=indent, default=str)


def create_syntax_tree(tokens: List[Token]) -> SyntaxTreeNode:
    """
    Create a syntax tree from flat token list.

    Args:
        tokens: Flat list of tokens

    Returns:
        Root syntax tree node
    """
    return SyntaxTreeNode(tokens)


def extract_text_content(tokens: List[Token]) -> str:
    """
    Extract all text content from tokens.

    Args:
        tokens: List of tokens

    Returns:
        Concatenated text content
    """
    text_parts = []

    def text_collector(token: Token, index: int) -> None:
        if token.type == 'text' and token.content:
            text_parts.append(token.content)

    walk_tokens(tokens, text_collector)
    return ''.join(text_parts)


def get_headings(tokens: List[Token]) -> List[dict]:
    """
    Extract heading information from tokens.

    Args:
        tokens: List of tokens to analyze

    Returns:
        List of heading dictionaries with level and content
    """
    headings = []
    current_heading = None

    for token in tokens:
        if token.type == 'heading_open':
            level = int(token.tag[1]) if token.tag.startswith('h') else 1
            current_heading = {'level': level, 'content': '', 'line': None}
            if token.map:
                current_heading['line'] = token.map[0] + 1

        elif token.type == 'inline' and current_heading is not None:
            current_heading['content'] = token.content

        elif token.type == 'heading_close' and current_heading is not None:
            headings.append(current_heading)
            current_heading = None

    return headings


class ASTWrapper:
    """Wrapper class for AST manipulation."""

    def __init__(self, parse_result: ParseResult):
        """
        Initialize AST wrapper.

        Args:
            parse_result: Result from parsing operation
        """
        self.parse_result = parse_result
        self.tokens = parse_result.ast if isinstance(parse_result.ast, list) else []

    def to_json(self) -> str:
        """Convert AST to JSON."""
        if isinstance(self.parse_result.ast, list):
            return tokens_to_json(self.parse_result.ast)
        else:
            # Handle mistletoe documents or other AST types
            return json.dumps({
                'type': type(self.parse_result.ast).__name__,
                'content': str(self.parse_result.ast)
            }, indent=2)

    def get_headings(self) -> List[dict]:
        """Get all headings from the AST."""
        if isinstance(self.parse_result.ast, list):
            return get_headings(self.parse_result.ast)
        return []

    def get_text_content(self) -> str:
        """Extract all text content."""
        if isinstance(self.parse_result.ast, list):
            return extract_text_content(self.parse_result.ast)
        return str(self.parse_result.ast)

    def find_tokens(self, token_type: str) -> List[Token]:
        """Find tokens of specific type."""
        if isinstance(self.parse_result.ast, list):
            return find_tokens_by_type(self.parse_result.ast, token_type)
        return []

    def create_tree(self) -> Optional[SyntaxTreeNode]:
        """Create syntax tree if using markdown-it-py tokens."""
        if isinstance(self.parse_result.ast, list):
            return create_syntax_tree(self.parse_result.ast)
        return None
```

## Phase 4: Multi-Format Rendering

### Step 4.1: Implement Base Renderer Interface

Create `src/quantalogic_markdown_mcp/renderers.py`:

```python
"""Rendering implementations for different output formats."""

import json
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod

from markdown_it import MarkdownIt
from markdown_it.token import Token

from .types import Renderer


class HTMLRenderer(Renderer):
    """HTML renderer for markdown-it-py tokens."""

    def __init__(self, options: Optional[Dict[str, Any]] = None):
        """
        Initialize HTML renderer.

        Args:
            options: Rendering options
        """
        self.options = options or {}
        self.md = MarkdownIt('commonmark', self.options)

    def render(self, ast: Any, options: Optional[Dict[str, Any]] = None) -> str:
        """
        Render AST to HTML.

        Args:
            ast: AST to render (markdown-it-py tokens)
            options: Additional rendering options

        Returns:
            HTML string
        """
        if isinstance(ast, list):
            # markdown-it-py tokens
            return self._render_tokens(ast, options)
        else:
            # Handle other AST types as string representation
            return f"<pre>{str(ast)}</pre>"

    def _render_tokens(self, tokens: List[Token], options: Optional[Dict[str, Any]]) -> str:
        """Render markdown-it-py tokens to HTML."""
        # Use the markdown-it renderer
        return self.md.renderer.render(tokens, self.md.options, {})

    def get_output_format(self) -> str:
        """Return output format name."""
        return "html"


class LaTeXRenderer(Renderer):
    """LaTeX renderer for markdown AST."""

    def __init__(self, options: Optional[Dict[str, Any]] = None):
        """
        Initialize LaTeX renderer.

        Args:
            options: Rendering options
        """
        self.options = options or {}
        self.document_class = self.options.get('document_class', 'article')

    def render(self, ast: Any, options: Optional[Dict[str, Any]] = None) -> str:
        """
        Render AST to LaTeX.

        Args:
            ast: AST to render (markdown-it-py tokens)
            options: Additional rendering options

        Returns:
            LaTeX string
        """
        if isinstance(ast, list):
            return self._render_tokens(ast, options)
        else:
            # Handle other AST types as verbatim
            return f'\\begin{{verbatim}}\n{str(ast)}\n\\end{{verbatim}}'

    def _render_tokens(self, tokens: List[Token], options: Optional[Dict[str, Any]]) -> str:
        """Render markdown-it-py tokens to LaTeX."""
        latex_parts = []
        
        # Add document preamble
        latex_parts.append(f'\\documentclass{{{self.document_class}}}')
        latex_parts.append('\\usepackage[utf8]{inputenc}')
        latex_parts.append('\\usepackage{graphicx}')
        latex_parts.append('\\usepackage{hyperref}')
        latex_parts.append('\\begin{document}')
        latex_parts.append('')

        # Process tokens
        for token in tokens:
            latex_content = self._token_to_latex(token)
            if latex_content:
                latex_parts.append(latex_content)

        # End document
        latex_parts.append('')
        latex_parts.append('\\end{document}')

        return '\n'.join(latex_parts)

    def _token_to_latex(self, token: Token) -> str:
        """Convert a single token to LaTeX."""
        if token.type == 'heading_open':
            level = int(token.tag[1]) if token.tag.startswith('h') else 1
            commands = ['section', 'subsection', 'subsubsection', 'paragraph', 'subparagraph']
            if level <= len(commands):
                return f'\\{commands[level - 1]}{{'
            return '\\paragraph{'

        elif token.type == 'heading_close':
            return '}'

        elif token.type == 'paragraph_open':
            return ''

        elif token.type == 'paragraph_close':
            return '\n'

        elif token.type == 'text':
            # Escape LaTeX special characters
            text = token.content
            escapes = {
                '\\': '\\textbackslash{}',
                '{': '\\{',
                '}': '\\}',
                '$': '\\$',
                '&': '\\&',
                '%': '\\%',
                '#': '\\#',
                '^': '\\textasciicircum{}',
                '_': '\\_',
                '~': '\\textasciitilde{}'
            }
            for char, escape in escapes.items():
                text = text.replace(char, escape)
            return text

        elif token.type == 'em_open':
            return '\\textit{'

        elif token.type == 'em_close':
            return '}'

        elif token.type == 'strong_open':
            return '\\textbf{'

        elif token.type == 'strong_close':
            return '}'

        elif token.type == 'code_inline':
            return f'\\texttt{{{token.content}}}'

        elif token.type == 'fence':
            language = token.info or 'text'
            content = token.content.rstrip()
            return f'\\begin{{verbatim}}\n{content}\n\\end{{verbatim}}'

        return ''

    def get_output_format(self) -> str:
        """Return output format name."""
        return "latex"


class JSONRenderer(Renderer):
    """JSON renderer for AST serialization."""

    def __init__(self, options: Optional[Dict[str, Any]] = None):
        """
        Initialize JSON renderer.

        Args:
            options: Rendering options (indent, etc.)
        """
        self.options = options or {}
        self.indent = self.options.get('indent', 2)

    def render(self, ast: Any, options: Optional[Dict[str, Any]] = None) -> str:
        """
        Render AST to JSON.

        Args:
            ast: AST to render
            options: Additional rendering options

        Returns:
            JSON string
        """
        if isinstance(ast, list):
            # markdown-it-py tokens
            token_dicts = [token.as_dict() for token in ast]
            return json.dumps(token_dicts, indent=self.indent, default=str)
        else:
            # Other AST types
            return json.dumps({
                'type': type(ast).__name__,
                'content': str(ast)
            }, indent=self.indent, default=str)

    def get_output_format(self) -> str:
        """Return output format name."""
        return "json"


class MarkdownRenderer(Renderer):
    """Markdown renderer for round-trip conversion."""

    def __init__(self, options: Optional[Dict[str, Any]] = None):
        """
        Initialize Markdown renderer.

        Args:
            options: Rendering options
        """
        self.options = options or {}
        self.line_length = self.options.get('max_line_length', 80)

    def render(self, ast: Any, options: Optional[Dict[str, Any]] = None) -> str:
        """
        Render AST back to Markdown.

        Args:
            ast: AST to render (markdown-it-py tokens)
            options: Additional rendering options

        Returns:
            Markdown string
        """
        if isinstance(ast, list):
            return self._render_tokens(ast, options)
        else:
            # Handle other AST types as plain text
            return str(ast)

    def _render_tokens(self, tokens: List[Token], options: Optional[Dict[str, Any]]) -> str:
        """Render markdown-it-py tokens back to Markdown."""
        md_parts = []
        list_depth = 0

        for token in tokens:
            md_content = self._token_to_markdown(token, list_depth)
            if md_content is not None:
                md_parts.append(md_content)

        return ''.join(md_parts)

    def _token_to_markdown(self, token: Token, list_depth: int) -> Optional[str]:
        """Convert a token back to Markdown syntax."""
        if token.type == 'heading_open':
            level = int(token.tag[1]) if token.tag.startswith('h') else 1
            return '#' * level + ' '

        elif token.type == 'heading_close':
            return '\n\n'

        elif token.type == 'paragraph_open':
            return ''

        elif token.type == 'paragraph_close':
            return '\n\n'

        elif token.type == 'text':
            return token.content

        elif token.type == 'em_open':
            return '*'

        elif token.type == 'em_close':
            return '*'

        elif token.type == 'strong_open':
            return '**'

        elif token.type == 'strong_close':
            return '**'

        elif token.type == 'code_inline':
            return f'`{token.content}`'

        elif token.type == 'fence':
            info = token.info or ''
            content = token.content.rstrip()
            return f'```{info}\n{content}\n```\n\n'

        elif token.type == 'bullet_list_open':
            return ''

        elif token.type == 'bullet_list_close':
            return '\n'

        elif token.type == 'list_item_open':
            indent = '  ' * list_depth
            return f'{indent}- '

        elif token.type == 'list_item_close':
            return '\n'

        return None

    def get_output_format(self) -> str:
        """Return output format name."""
        return "markdown"


class MultiFormatRenderer:
    """Unified renderer supporting multiple output formats."""

    def __init__(self):
        """Initialize multi-format renderer."""
        self.renderers = {
            'html': HTMLRenderer(),
            'latex': LaTeXRenderer(),
            'json': JSONRenderer(),
            'markdown': MarkdownRenderer(),
        }

    def render(self, ast: Any, format_name: str, options: Optional[Dict[str, Any]] = None) -> str:
        """
        Render AST to specified format.

        Args:
            ast: AST to render
            format_name: Target format ('html', 'latex', 'json', 'markdown')
            options: Format-specific options

        Returns:
            Rendered content

        Raises:
            ValueError: If format is not supported
        """
        if format_name.lower() not in self.renderers:
            supported = ', '.join(self.renderers.keys())
            raise ValueError(f"Unsupported format '{format_name}'. Supported: {supported}")

        renderer = self.renderers[format_name.lower()]
        return renderer.render(ast, options)

    def get_supported_formats(self) -> List[str]:
        """Return list of supported output formats."""
        return list(self.renderers.keys())

    def add_renderer(self, format_name: str, renderer: Renderer) -> None:
        """
        Add a custom renderer.

        Args:
            format_name: Format name
            renderer: Renderer implementation
        """
        self.renderers[format_name.lower()] = renderer
```

## Phase 5: Main Parser Interface

### Step 5.1: Create Main Parser Class

Create `src/quantalogic_markdown_mcp/parser.py`:

```python
"""Main parser interface and factory."""

from typing import Any, Dict, List, Optional, Union
import logging

from .parsers import MarkdownItParser
from .renderers import MultiFormatRenderer
from .ast_utils import ASTWrapper
from .types import ParseResult, MarkdownParser


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

        logger.info(f"Initialized parser with markdown-it-py backend")

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
```

### Step 5.2: Create Package Init File

Update `src/quantalogic_markdown_mcp/__init__.py`:

```python
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
__author__ = "Your Name"
__email__ = "your.email@example.com"

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
```

## Phase 6: Testing and Validation

### Step 6.1: Create Comprehensive Test Suite

Create `tests/test_parser.py`:

```python
"""Tests for the main parser functionality."""

import pytest
from pathlib import Path

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
        assert '\\section{Test}' in latex
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
```

### Step 6.2: Create Additional Test Files

Create `tests/test_renderers.py`:

```python
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
        assert '\\section{Test}' in latex
        assert '\\textit{emphasis}' in latex
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
```

### Step 6.3: Create Usage Examples

Create `examples/basic_usage.py`:

```python
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


if __name__ == "__main__":
    basic_parsing_example()
    multi_format_rendering_example()
    convenience_functions_example()
    error_handling_example()
    parser_features_example()
    
    print("\n=== All Examples Complete ===")
```

## Final Steps

### Step 7.1: Create Documentation

Create `README.md`:

```markdown
# Quantalogic Markdown Parser

A flexible and extensible Markdown parser with AST support, built on top of battle-tested libraries like `markdown-it-py` and `mistletoe`.

## Features

- **Multiple Parser Backends**: Choose between `markdown-it-py` and `mistletoe`
- **CommonMark Compliance**: Follows the CommonMark specification
- **Multi-Format Output**: HTML, LaTeX, JSON, and Markdown
- **Comprehensive Error Handling**: Detailed error reporting with line numbers
- **Extensible Architecture**: Plugin system for custom functionality
- **AST Manipulation**: Rich API for working with parsed content

## Installation

```bash
pip install quantalogic-markdown-mcp
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
```

## Documentation

See the `examples/` directory for comprehensive usage examples and the `docs/` directory for detailed documentation.

## License

MIT License - see LICENSE file for details.
```

### Step 7.2: Run Tests and Validation

```bash
# Install in development mode
pip install -e ".[dev,test]"

# Run tests
pytest tests/ -v --cov=src/quantalogic_markdown_mcp

# Run linting
black src/
ruff check src/
mypy src/

# Run examples
python examples/basic_usage.py
```

This completes the step-by-step implementation of the markdown parser. The implementation provides a robust, extensible parser that leverages existing libraries while offering a clean, unified API for different use cases.

