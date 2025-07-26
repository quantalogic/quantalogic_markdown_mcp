"""Markdown parser implementation using markdown-it-py."""

from typing import Dict, List, Optional, Any
import logging

from markdown_it import MarkdownIt
from markdown_it.token import Token
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.front_matter import front_matter_plugin

from .types import ParseResult, ParseError, ErrorLevel


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
