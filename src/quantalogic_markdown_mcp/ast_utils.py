"""AST manipulation and traversal utilities."""

from typing import Callable, List, Optional
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
