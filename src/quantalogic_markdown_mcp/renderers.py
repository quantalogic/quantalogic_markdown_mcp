"""Rendering implementations for different output formats."""

import json
from typing import Any, Dict, List, Optional

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
        latex_parts.extend(self._process_tokens(tokens))

        # End document
        latex_parts.append('')
        latex_parts.append('\\end{document}')

        return '\n'.join(latex_parts)

    def _process_tokens(self, tokens: List[Token]) -> List[str]:
        """Process tokens recursively."""
        parts = []
        for token in tokens:
            latex_content = self._token_to_latex(token)
            if latex_content:
                parts.append(latex_content)
            
            # Process children if they exist
            if token.children:
                child_parts = self._process_tokens(token.children)
                parts.extend(child_parts)
        
        return parts

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

        elif token.type == 'inline':
            # Don't process inline tokens directly - their children will be processed
            return ''

        elif token.type == 'text':
            # Escape LaTeX special characters
            return self._escape_latex(token.content)

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
            content = token.content.rstrip()
            return f'\\begin{{verbatim}}\n{content}\n\\end{{verbatim}}'

        return ''

    def _escape_latex(self, text: str) -> str:
        """Escape LaTeX special characters."""
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
        return ''.join(self._process_tokens_for_markdown(tokens, 0))

    def _process_tokens_for_markdown(self, tokens: List[Token], list_depth: int) -> List[str]:
        """Process tokens recursively for markdown rendering."""
        parts = []
        for token in tokens:
            md_content = self._token_to_markdown(token, list_depth)
            if md_content is not None:
                parts.append(md_content)
            
            # Process children if they exist
            if token.children:
                child_parts = self._process_tokens_for_markdown(token.children, list_depth)
                parts.extend(child_parts)
        
        return parts

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

        elif token.type == 'inline':
            # Don't process inline tokens directly - their children will be processed
            return ''

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
