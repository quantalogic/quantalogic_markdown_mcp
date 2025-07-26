# Markdown Parser Specification

We want to create a markdown parser that will represent the parsed content as an AST (Abstract Syntax Tree) in Python.

The parser should be able to handle various markdown elements such as headings, paragraphs, lists, links, images, and code blocks. The goal is to create a flexible and extensible parser that can be used in different applications, such as static site generators or content management systems.

The parser should be able to detect and handle common markdown syntax errors gracefully, providing useful error messages to the user.

Brainstorm about the best ideas and approaches to implement this parser, considering the following aspects:

1. **AST Design**:

   - Define a clear and extensible AST structure that can represent all markdown elements.
   - Use classes for each element type (e.g., `Heading`, `Paragraph`, `List`, `Link`, `Image`, `CodeBlock`).
   - Include attributes for each class to store relevant data (e.g., text content, level of headings, list items).
   - Consider using a visitor pattern to traverse the AST for rendering or processing.
   - Implement methods for serialization to formats like JSON or XML if needed.

2. **Tokenization**:

   - Create a tokenizer that can break down markdown text into tokens (e.g., headings, lists, links).
   - Use regular expressions or a state machine to identify different markdown syntax.
   - Handle edge cases and variations in markdown syntax (e.g., different heading styles, inline code).
   - Ensure the tokenizer can handle escaped characters and special cases.

3. **Parsing**:

   - Implement a parser that can convert the stream of tokens into the AST.
   - Use a recursive descent parsing approach or a parser combinator library for flexibility.
   - Handle nested structures (e.g., lists within lists, code blocks within paragraphs).
   - Provide clear error handling for syntax errors, including line numbers and context.

4. **Error Handling**:

   - Implement robust error handling to catch syntax errors during parsing.
   - Provide meaningful error messages that include the type of error, line number, and context.
   - Consider implementing a recovery mechanism to continue parsing after an error.

5. **Rendering**:
   - Implement a renderer that can convert the AST back into markdown or other formats.
   - Support different output formats, such as HTML, LaTeX, or plain text.
   - Allow customization of the rendering process (e.g., custom styles for headings, lists).

## Detailed Specification

### 1. AST Design

#### Recommended Approach: Leverage Existing Libraries

Instead of building a completely custom AST from scratch, we should leverage battle-tested libraries like **markdown-it-py** or **mistletoe** as the foundation. This approach provides several advantages:

- **Standards Compliance**: Both libraries follow the CommonMark specification, ensuring compatibility and predictable behavior
- **Performance**: These libraries are optimized and benchmarked for speed
- **Extensibility**: Plugin systems allow for custom functionality without modifying core code
- **Maintenance**: Reduces the maintenance burden and avoids common parsing pitfalls

#### Primary Recommendation: markdown-it-py

##### Core Structure

Use markdown-it-py's `Token` objects as the foundation:

```python
from markdown_it import MarkdownIt
from markdown_it.token import Token

md = MarkdownIt()
tokens = md.parse(text)
```

##### Token Properties

- `type`: Element type (e.g., 'heading_open', 'paragraph_open', 'text', 'em_open', 'link_open')
- `tag`: HTML tag name (e.g., 'h1', 'p', 'em', 'a')
- `nesting`: Nesting level (1 for opening, -1 for closing, 0 for self-closing)
- `attrs`: Attributes dictionary (e.g., href for links, level for headings)
- `map`: Line number mapping [start, end] for error reporting
- `level`: Nesting depth in the document
- `children`: Inline tokens for block elements
- `content`: Raw text content
- `markup`: Original markdown syntax used
- `meta`: Additional metadata

##### Element Representation

- **Headings**: `heading_open` tokens with `tag` indicating level (h1-h6) and `children` containing inline content
- **Paragraphs**: `paragraph_open`/`paragraph_close` pairs with `inline` children containing text and formatting
- **Lists**: `ordered_list_open`/`bullet_list_open` with nested `list_item_open` tokens
- **Links**: `link_open` tokens with `href` in `attrs` and text content in `children`
- **Images**: `image` tokens with `src`, `alt`, and `title` in `attrs`
- **Code Blocks**: `fence` tokens with `info` for language and `content` for code

##### Extensibility via Plugins

```python
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.front_matter import front_matter_plugin

md = MarkdownIt().use(footnote_plugin).use(front_matter_plugin)
```

##### Custom Wrapper Class (optional)

```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class MarkdownAST:
    tokens: List[Token]
    source: str

    def to_json(self) -> dict:
        return {
            'tokens': [token.as_dict() for token in self.tokens],
            'source': self.source
        }

    @classmethod
    def from_json(cls, data: dict) -> 'MarkdownAST':
        tokens = [Token.from_dict(token_dict) for token_dict in data['tokens']]
        return cls(tokens=tokens, source=data['source'])
```

#### Alternative: mistletoe

If a more traditional AST structure is preferred, **mistletoe** provides a tree-based approach:

```python
import mistletoe
from mistletoe import Document

with open('file.md', 'r') as f:
    doc = mistletoe.Document(f)
```

##### AST Node Structure

- **Base Node**: All elements inherit from `BlockToken` or `SpanToken`
- **Block Elements**: `Heading`, `Paragraph`, `List`, `CodeFence`, `BlockQuote`
- **Span Elements**: `Emphasis`, `Strong`, `Link`, `Image`, `InlineCode`
- **Attributes**: Each node has `children`, `content`, and element-specific properties

##### Traversal and Processing

```python
def walk_ast(node):
    # Process current node
    process_node(node)

    # Recursively process children
    if hasattr(node, 'children'):
        for child in node.children:
            walk_ast(child)
```

### 2. Tokenization

#### Recommended Approach: Use Library Tokenizers

Instead of implementing custom tokenization, leverage the robust tokenizers in existing libraries:

##### markdown-it-py Tokenization

```python
md = MarkdownIt('commonmark')
tokens = md.parse(text)

# Token stream provides flat list with nesting information
for token in tokens:
    print(f"{token.type}: {token.content[:50]}...")
```

##### Advantages

- Handles all CommonMark syntax correctly
- Manages escaped characters and edge cases
- Supports context-sensitive parsing (inline vs block)
- Extensible through plugins for custom syntax

##### Configuration Options

```python
# Strict CommonMark compliance
md = MarkdownIt('commonmark')

# GitHub Flavored Markdown
md = MarkdownIt('gfm-like')

# Custom configuration
md = MarkdownIt('zero').enable(['heading', 'paragraph', 'emphasis'])
```

##### mistletoe Tokenization

```python
from mistletoe import Document
from mistletoe.html_renderer import HTMLRenderer

# Parsing happens during Document creation
with HTMLRenderer() as renderer:
    doc = Document(lines)
```

##### Token Types

- **Block Tokens**: Handle block-level elements
- **Span Tokens**: Handle inline elements within blocks
- **Custom Tokens**: Easily extensible for domain-specific syntax

### 3. Parsing

#### Recommended Approach: Library-Based Parsing

##### markdown-it-py Parsing

```python
def parse_markdown(text: str) -> List[Token]:
    md = MarkdownIt('commonmark')
    return md.parse(text)

def create_syntax_tree(tokens: List[Token]) -> SyntaxTreeNode:
    from markdown_it.tree import SyntaxTreeNode
    return SyntaxTreeNode(tokens)
```

##### Features

- Handles nested structures automatically
- Maintains line number information for error reporting
- Supports incremental parsing for large documents
- Plugin system for custom elements

##### mistletoe Parsing

```python
def parse_markdown(text: str) -> Document:
    from mistletoe import Document
    from mistletoe.html_renderer import HTMLRenderer

    with HTMLRenderer() as renderer:
        return Document(text.splitlines())
```

##### Nesting Handling

```python
def process_list(list_node):
    for item in list_node.children:
        if isinstance(item, List):
            # Handle nested list
            process_list(item)
        else:
            # Handle list item content
            process_item(item)
```

### 4. Error Handling

#### Comprehensive Error Management

##### Line Number Tracking

```python
def parse_with_error_handling(text: str) -> tuple[List[Token], List[str]]:
    md = MarkdownIt('commonmark')
    errors = []

    try:
        tokens = md.parse(text)

        # Validate token structure
        for i, token in enumerate(tokens):
            if token.map:
                line_start, line_end = token.map
                if line_start < 0 or line_end > len(text.splitlines()):
                    errors.append(f"Invalid line mapping at token {i}: {token.type}")

        return tokens, errors
    except Exception as e:
        errors.append(f"Parsing failed: {str(e)}")
        return [], errors
```

##### Validation and Recovery

```python
def validate_token_structure(tokens: List[Token]) -> List[str]:
    errors = []
    nesting_stack = []

    for i, token in enumerate(tokens):
        if token.nesting == 1:  # Opening token
            nesting_stack.append((token.type, i))
        elif token.nesting == -1:  # Closing token
            if not nesting_stack:
                errors.append(f"Unmatched closing token {token.type} at position {i}")
            else:
                opening_type, opening_pos = nesting_stack.pop()
                expected_closing = opening_type.replace('_open', '_close')
                if token.type != expected_closing:
                    errors.append(f"Mismatched tokens: {opening_type} at {opening_pos} closed by {token.type} at {i}")

    # Check for unclosed tokens
    for opening_type, pos in nesting_stack:
        errors.append(f"Unclosed token {opening_type} at position {pos}")

    return errors
```

##### User-Friendly Error Messages

```python
def format_error_message(error: str, text: str, line_num: int) -> str:
    lines = text.splitlines()
    if 0 <= line_num < len(lines):
        line_content = lines[line_num]
        return f"""
Error: {error}
Line {line_num + 1}: {line_content}
           {'~' * len(line_content)}
"""
    return f"Error: {error} (line {line_num + 1})"
```

### 5. Rendering

#### Multi-Format Rendering System

##### markdown-it-py Rendering

```python
class CustomRenderer:
    def __init__(self):
        self.md = MarkdownIt('commonmark')
        self._setup_custom_rules()

    def _setup_custom_rules(self):
        def custom_heading(self, tokens, idx, options, env):
            token = tokens[idx]
            level = token.tag[1]  # Extract number from h1, h2, etc.
            if token.nesting == 1:
                return f'<h{level} class="custom-heading">'
            else:
                return f'</h{level}>'

        self.md.add_render_rule("heading_open", custom_heading)
        self.md.add_render_rule("heading_close", custom_heading)

    def render_html(self, text: str) -> str:
        return self.md.render(text)

    def render_latex(self, text: str) -> str:
        tokens = self.md.parse(text)
        return self._tokens_to_latex(tokens)

    def _tokens_to_latex(self, tokens: List[Token]) -> str:
        latex_parts = []
        for token in tokens:
            if token.type == 'heading_open':
                level = token.tag[1]
                section_cmd = ['section', 'subsection', 'subsubsection'][int(level) - 1]
                latex_parts.append(f'\\{section_cmd}{{')
            elif token.type == 'heading_close':
                latex_parts.append('}')
            elif token.type == 'text':
                latex_parts.append(token.content)
            # Add more token type handlers...

        return ''.join(latex_parts)
```

##### mistletoe Rendering

```python
from mistletoe.latex_renderer import LaTeXRenderer
from mistletoe.html_renderer import HTMLRenderer

class CustomLatexRenderer(LaTeXRenderer):
    def render_heading(self, token):
        level_commands = ['section', 'subsection', 'subsubsection', 'paragraph', 'subparagraph']
        level = token.level
        if level <= len(level_commands):
            command = level_commands[level - 1]
            content = self.render_inner(token)
            return f'\\{command}{{{content}}}\n\n'
        return super().render_heading(token)

# Usage
with CustomLatexRenderer() as renderer:
    doc = Document(lines)
    latex_output = renderer.render(doc)
```

##### Output Format Support

```python
class MultiFormatRenderer:
    def __init__(self):
        self.md = MarkdownIt('commonmark')

    def render(self, text: str, format: str) -> str:
        if format.lower() == 'html':
            return self.md.render(text)
        elif format.lower() == 'latex':
            return self._render_latex(text)
        elif format.lower() == 'markdown':
            return self._render_markdown(text)
        elif format.lower() == 'json':
            tokens = self.md.parse(text)
            return json.dumps([token.as_dict() for token in tokens], indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _render_latex(self, text: str) -> str:
        # Implementation for LaTeX conversion
        pass

    def _render_markdown(self, text: str) -> str:
        # For markdown round-trip (formatting, etc.)
        tokens = self.md.parse(text)
        return self._tokens_to_markdown(tokens)
```

### 6. Architecture and Integration

#### Modular Design

```python
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

@dataclass
class ParseResult:
    ast: Any  # Token list or Document
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]

class MarkdownParser(ABC):
    @abstractmethod
    def parse(self, text: str) -> ParseResult:
        pass

class MarkdownItParser(MarkdownParser):
    def __init__(self, preset: str = 'commonmark', plugins: List[str] = None):
        self.md = MarkdownIt(preset)
        if plugins:
            for plugin in plugins:
                self.md.use(plugin)

    def parse(self, text: str) -> ParseResult:
        try:
            tokens = self.md.parse(text)
            errors = validate_token_structure(tokens)

            return ParseResult(
                ast=tokens,
                errors=errors,
                warnings=[],
                metadata={'parser': 'markdown-it-py', 'token_count': len(tokens)}
            )
        except Exception as e:
            return ParseResult(
                ast=[],
                errors=[str(e)],
                warnings=[],
                metadata={'parser': 'markdown-it-py'}
            )

class MistletoeParser(MarkdownParser):
    def parse(self, text: str) -> ParseResult:
        try:
            from mistletoe import Document
            from mistletoe.html_renderer import HTMLRenderer

            with HTMLRenderer() as renderer:
                doc = Document(text.splitlines())

            return ParseResult(
                ast=doc,
                errors=[],
                warnings=[],
                metadata={'parser': 'mistletoe'}
            )
        except Exception as e:
            return ParseResult(
                ast=None,
                errors=[str(e)],
                warnings=[],
                metadata={'parser': 'mistletoe'}
            )
```

### 7. Testing and Validation

#### Comprehensive Test Suite

```python
import pytest
from pathlib import Path

class TestMarkdownParser:
    @pytest.fixture
    def parser(self):
        return MarkdownItParser()

    def test_basic_elements(self, parser):
        text = """
# Heading 1
## Heading 2

This is a paragraph with *emphasis* and **strong** text.

- List item 1
- List item 2
  - Nested item

[Link](https://example.com)

![Image](image.png "Title")

Code block example here

"""
        result = parser.parse(text)
        assert not result.errors
        assert len(result.ast) > 0

    def test_error_handling(self, parser):
        # Test malformed markdown
        text = "# Unclosed [link"
        result = parser.parse(text)
        # Should parse without errors (markdown is forgiving)
        assert isinstance(result.ast, list)

    def test_commonmark_compliance(self, parser):
        # Test against CommonMark test suite
        test_cases = load_commonmark_tests()
        for test_case in test_cases:
            result = parser.parse(test_case.markdown)
            rendered = render_html(result.ast)
            assert rendered == test_case.expected_html
```

This specification provides a robust foundation for building a markdown parser that leverages existing, battle-tested libraries while maintaining flexibility for customization and extension.
