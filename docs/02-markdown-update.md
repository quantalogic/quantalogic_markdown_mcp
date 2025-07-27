
# Markdown Editing API: Specification & Best Practices

## Overview

Design an API that enables robust, programmatic editing of Markdown documents. The API should support granular, version-controlled, and collaborative editing, while enforcing clarity, consistency, and accessibility.

## Supported Operations

The API must support the following operations:

1. **Update Section Content**
   - Update the text or content of a specific section, identified by heading or unique ID.
   - Support partial updates (e.g., only a paragraph or list within a section).

2. **Add Section**
   - Insert a new section at a specified location (before/after another section, or as a child of a heading).
   - Specify heading level, title, and optional initial content.

3. **Delete Section**
   - Remove a section and all its content, including nested subsections.
   - Optionally support soft-delete (move to trash/undo).

4. **Indent/Unindent Section**
   - Change the nesting level of a section (promote/demote heading level).
   - Update all child sections accordingly.

5. **Move Section**
   - Move a section (and its children) up/down or to a new parent section.
   - Maintain document structure and update heading levels as needed.

6. **Change Heading Level**
   - Change the heading level of a section (e.g., H2 to H3).
   - Ensure heading hierarchy remains valid.

7. **Add/Remove Code Block**
   - Insert or delete code blocks within a section.
   - Specify language for syntax highlighting.

8. **Add/Remove List Item**
   - Add or remove items from ordered/unordered lists.
   - Support nested lists and maintain proper indentation.

9. **Add/Remove Table**
   - Insert or delete tables, rows, or columns.
   - Ensure Markdown table syntax is valid.

10. **Add/Remove Blockquote**
    - Insert or delete blockquotes for notes, warnings, or tips.

11. **Add/Remove Link or Image**
    - Insert or remove hyperlinks and images, with support for alt text and reference links.

## API Design Principles

- **Consistency:** Enforce a style guide for headings, lists, code blocks, and links. Use linting tools to maintain style.
- **Clarity:** Require explicit parameters for all operations (e.g., section ID, position, content, type).
- **Version Control:** Integrate with Git or similar systems to track changes, support undo/redo, and enable collaborative editing.
- **Accessibility:** Require alt text for images, logical heading order, and semantic structure.
- **Extensibility:** Allow for future operations (e.g., table of contents generation, metadata editing).
- **Validation:** Validate Markdown syntax after each operation. Provide clear error messages for invalid edits.
- **Atomicity:** Each operation should be atomic and reversible.

## Implementation Architecture

The API will leverage the existing `QuantalogicMarkdownParser` infrastructure:

### Core Components

- **QuantalogicMarkdownParser**: Main parser interface using markdown-it-py
- **ASTWrapper**: Provides token manipulation and analysis utilities
- **ParseResult**: Contains parsed tokens, errors, and metadata
- **Token-based editing**: Operations work directly on markdown-it-py tokens

### Token-Based Editing Approach

```python
from quantalogic_markdown_mcp import QuantalogicMarkdownParser, ASTWrapper

# Parse document
parser = QuantalogicMarkdownParser()
result = parser.parse(markdown_text)
wrapper = ASTWrapper(result)

# Find sections by heading content
headings = wrapper.get_headings()
target_section = next(h for h in headings if h['content'] == 'Installation')

# Manipulate tokens directly
tokens = wrapper.tokens
# ... perform token-level operations
```

## Example API Operations

```python
class MarkdownEditor:
    def __init__(self, markdown_text: str):
        self.parser = QuantalogicMarkdownParser()
        self.result = self.parser.parse(markdown_text)
        self.wrapper = ASTWrapper(self.result)
    
    def update_section_content(self, section_id: str, content: str) -> ParseResult:
        """Update content of a specific section."""
        # Find section tokens by heading content or line number
        headings = self.wrapper.get_headings()
        # ... token manipulation logic
        return self._rebuild_document()
    
    def add_section(self, after_section_id: str, heading_level: int, 
                   title: str, content: str = "") -> ParseResult:
        """Add new section after specified section."""
        # Create new heading tokens
        # Insert at appropriate position
        return self._rebuild_document()
    
    def move_section(self, section_id: str, direction: str) -> ParseResult:
        """Move section up or down."""
        # Find section token range
        # Reorder tokens
        return self._rebuild_document()
```

## Token Manipulation Utilities

The API will extend the existing `ASTWrapper` with editing capabilities:

### Extended ASTWrapper Methods

```python
class EditableASTWrapper(ASTWrapper):
    def find_section_tokens(self, section_identifier: str) -> List[Token]:
        """Find all tokens belonging to a section."""
        # Use existing get_headings() and token analysis
        pass
    
    def insert_tokens_at_position(self, tokens: List[Token], position: int) -> None:
        """Insert tokens at specific position."""
        pass
    
    def delete_token_range(self, start_idx: int, end_idx: int) -> None:
        """Delete range of tokens."""
        pass
    
    def create_heading_tokens(self, level: int, content: str) -> List[Token]:
        """Create heading tokens programmatically."""
        pass
    
    def create_paragraph_tokens(self, content: str) -> List[Token]:
        """Create paragraph tokens."""
        pass
    
    def validate_token_structure(self) -> List[ParseError]:
        """Validate token nesting and structure."""
        pass
```

### Integration with Existing Parser Features

- **Error Handling**: Leverage existing `ParseError` and `ErrorLevel` for validation
- **Metadata Tracking**: Use `ParseResult.metadata` to track edit history
- **Multi-format Output**: Use existing renderers to output edited markdown
- **Plugin Support**: Maintain compatibility with markdown-it-py plugins

## Implementation Strategy

1. **Extend ASTWrapper**: Add editing methods to existing `ASTWrapper` class
2. **Token Factory**: Create utility methods for generating new tokens
3. **Section Detection**: Enhance existing `get_headings()` for better section identification  
4. **Validation Layer**: Use existing error handling for operation validation
5. **Undo/Redo**: Track token changes using `ParseResult` metadata

## Edge Cases & Error Handling

Leveraging existing `ParseError` and validation infrastructure:

- **Invalid Token Structure**: Use existing token validation in `MarkdownItParser`
- **Heading Hierarchy**: Extend existing heading detection for hierarchy validation
- **Token Integrity**: Ensure opening/closing token pairs remain balanced
- **Line Mapping**: Maintain `token.map` information for accurate error reporting
- **Plugin Compatibility**: Ensure edits don't break plugin-generated tokens

```python
def validate_edit_operation(self, operation: dict) -> List[ParseError]:
    """Validate edit using existing error handling."""
    errors = []
    
    # Use existing ParseError structure
    if not self._valid_section_id(operation.get('section_id')):
        errors.append(ParseError(
            message="Invalid section identifier",
            level=ErrorLevel.ERROR,
            context=operation.get('section_id')
        ))
    
    return errors
```

## Testing & Automation

Building on existing test infrastructure:

- **Token-level Tests**: Extend existing `test_parser.py` for editing operations
- **AST Validation**: Use existing `ASTWrapper` tests as foundation
- **Renderer Integration**: Test edited documents render correctly in all formats
- **Plugin Compatibility**: Ensure edits work with footnote, front_matter plugins

## Documentation & Examples

Extending existing documentation patterns:

```python
# Example leveraging existing convenience functions
from quantalogic_markdown_mcp import parse_markdown, markdown_to_html

# Parse document
result = parse_markdown(markdown_text)

# Edit using new API
editor = MarkdownEditor(result)
editor.add_section("introduction", 2, "Getting Started", "Welcome content")

# Render back to HTML using existing renderer
html_output = markdown_to_html(editor.to_markdown())
```

## References

- [Google Markdown Style Guide](https://google.github.io/styleguide/docguide/style.html)
- [Best Practices for Creating Markdown Documentation](https://thenewstack.io/best-practices-for-creating-markdown-documentation-for-your-apps/)
- [Efficiently Document APIs with Markdown](https://zuplo.com/blog/2025/04/14/document-apis-with-markdown)
- **Implementation Example**: See `/examples/markdown_editor_example.py` for a complete working implementation

## Implementation Roadmap

1. **Phase 1**: Extend `ASTWrapper` with basic editing methods
2. **Phase 2**: Implement `MarkdownEditor` class with core operations
3. **Phase 3**: Add validation and error handling using existing infrastructure
4. **Phase 4**: Integrate with existing renderers for multi-format output
5. **Phase 5**: Add advanced features (undo/redo, collaborative editing)

---

## Summary

This specification provides a comprehensive design for a Markdown editing API that leverages the existing `QuantalogicMarkdownParser` infrastructure. The key advantages of this approach are:

### Leveraging Existing Infrastructure

- **Token-based editing**: Direct manipulation of markdown-it-py tokens for precise control
- **Robust parsing**: Built on proven `QuantalogicMarkdownParser` with error handling
- **Multi-format output**: Automatic support for HTML, LaTeX, JSON, and Markdown rendering
- **Extensible architecture**: Easy to add new operations and validation rules

### Production-Ready Features

- **Comprehensive validation**: Uses existing `ParseError` and `ErrorLevel` infrastructure
- **Edit history tracking**: Full audit trail of document modifications
- **Structure validation**: Maintains heading hierarchy and document integrity
- **Plugin compatibility**: Works with existing markdown-it-py plugins

### Developer Experience

- **Familiar patterns**: Follows existing codebase conventions and patterns
- **Rich tooling**: Integrates with existing AST utilities and renderers
- **Complete examples**: Working implementation demonstrating all concepts
- **Extensive testing**: Built on solid test foundation with 100% test coverage

The implementation example in `/examples/markdown_editor_example.py` demonstrates a fully functional Markdown editor that successfully integrates with the existing parser infrastructure, providing all the operations specified in this document while maintaining the robustness and extensibility of the original system.

This spec is designed to ensure your Markdown editing API is robust, user-friendly, and maintainable. Follow these guidelines to maximize clarity, consistency, and developer adoption.
