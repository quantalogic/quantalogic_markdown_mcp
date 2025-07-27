# SafeMarkdownEditor API: Detailed Technical Specification

## Table of Contents

1. [Overview](#overview)
2. [Core Data Types](#core-data-types)
3. [API Interface](#api-interface)
4. [Operation Semantics](#operation-semantics)
5. [Error Handling](#error-handling)
6. [Thread Safety](#thread-safety)
7. [Performance Characteristics](#performance-characteristics)
8. [Usage Examples](#usage-examples)
9. [Migration Guide](#migration-guide)
10. [Implementation Notes](#implementation-notes)

## Overview

The `SafeMarkdownEditor` API provides atomic, thread-safe operations for editing Markdown documents with comprehensive validation, error recovery, and transaction support. It is built on top of the `QuantalogicMarkdownParser` and provides a high-level, semantic interface that abstracts away the complexity of token manipulation.

### Design Principles

1. **Safety First**: All operations are atomic with automatic rollback on failure
2. **Immutable References**: Section references remain stable across document modifications
3. **Rich Feedback**: Comprehensive error reporting with actionable suggestions
4. **Preview-Driven**: All operations support preview before application
5. **Thread Safety**: Concurrent access protection with proper synchronization
6. **Validation-Centric**: Structural integrity maintained at all times

### Version Information

- **API Version**: 2.0.0
- **Compatibility**: Backward compatible with legacy `MarkdownEditor` via deprecation layer
- **Dependencies**: `quantalogic-markdown-mcp >= 0.1.0`

## Core Data Types

### SectionReference

Immutable reference to a document section that remains stable across edits.

```python
@dataclass(frozen=True)
class SectionReference:
    """Immutable reference to a document section."""
    
    id: str                    # Stable hash-based identifier
    title: str                 # Section heading text
    level: int                 # Heading level (1-6)
    line_start: int           # Starting line number (0-indexed)
    line_end: int             # Ending line number (0-indexed)
    path: List[str]           # Hierarchical path from root
    
    def __hash__(self) -> int:
        """Hash based on immutable properties."""
        return hash((self.id, self.title, self.level, self.line_start))
    
    def __eq__(self, other) -> bool:
        """Equality based on ID and position."""
        return (isinstance(other, SectionReference) and
                self.id == other.id and
                self.line_start == other.line_start)
```

**Properties:**

- `id`: Unique identifier computed from `hash(title + level + content_hash) % 100000`
- `title`: Exact heading text without markup (e.g., "Introduction")
- `level`: Heading level from 1 (H1) to 6 (H6)
- `line_start`: Zero-indexed line where section begins
- `line_end`: Zero-indexed line where section ends (exclusive)
- `path`: Hierarchical navigation path (e.g., `["Chapter 1", "Introduction"]`)

### EditOperation

Enumeration of supported editing operations.

```python
class EditOperation(Enum):
    """Supported editing operations."""
    
    INSERT_SECTION = "insert_section"
    UPDATE_SECTION = "update_section"
    DELETE_SECTION = "delete_section"
    MOVE_SECTION = "move_section"
    CHANGE_HEADING_LEVEL = "change_heading_level"
    INSERT_CONTENT = "insert_content"
    DELETE_CONTENT = "delete_content"
    BATCH_OPERATIONS = "batch_operations"
```

### EditResult

Comprehensive result object for all editing operations.

```python
@dataclass
class EditResult:
    """Result of an edit operation with comprehensive feedback."""
    
    success: bool                           # Operation success status
    operation: EditOperation               # Type of operation performed
    modified_sections: List[SectionReference]  # Sections affected by operation
    errors: List[ParseError]              # Validation or execution errors
    warnings: List[ParseError]            # Non-critical issues
    preview: Optional[str] = None         # Markdown preview of changes
    metadata: Dict[str, Any] = field(default_factory=dict)  # Operation metadata
    
    @property
    def has_errors(self) -> bool:
        """Check if operation encountered errors."""
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        """Check if operation generated warnings."""
        return len(self.warnings) > 0
    
    def get_error_summary(self) -> str:
        """Get formatted summary of all errors."""
        if not self.has_errors:
            return "No errors"
        return "\n".join(f"- {error}" for error in self.errors)
```

### EditTransaction

Container for atomic transaction operations with rollback capability.

```python
@dataclass
class EditTransaction:
    """Atomic transaction with rollback capability."""
    
    transaction_id: str                    # Unique transaction identifier
    operations: List[Dict[str, Any]]      # List of operations in transaction
    rollback_data: str                    # Document state for rollback
    timestamp: datetime                   # Transaction creation time
    metadata: Dict[str, Any] = field(default_factory=dict)  # Transaction metadata
    
    def can_rollback(self) -> bool:
        """Check if transaction supports rollback."""
        return bool(self.rollback_data)
```

## API Interface

### Constructor

```python
class SafeMarkdownEditor:
    def __init__(self, 
                 markdown_text: str,
                 validation_level: ValidationLevel = ValidationLevel.STRICT,
                 max_transaction_history: int = 100) -> None:
        """
        Initialize safe markdown editor.
        
        Args:
            markdown_text: Initial markdown document content
            validation_level: Strictness of validation (STRICT, NORMAL, PERMISSIVE)
            max_transaction_history: Maximum number of transactions to retain
            
        Raises:
            ValueError: If markdown_text contains critical parsing errors
            DocumentStructureError: If document structure is invalid
        """
```

### Core Operations

#### Document Inspection

```python
def get_sections(self) -> List[SectionReference]:
    """
    Get immutable references to all document sections.
    
    Returns:
        List of SectionReference objects in document order
        
    Complexity: O(n) where n is number of headings
    Thread Safety: Safe for concurrent access
    """

def get_section_by_id(self, section_id: str) -> Optional[SectionReference]:
    """
    Find section by stable identifier.
    
    Args:
        section_id: Stable section identifier
        
    Returns:
        SectionReference if found, None otherwise
        
    Complexity: O(n) where n is number of sections
    """

def get_sections_by_level(self, level: int) -> List[SectionReference]:
    """
    Get all sections at specified heading level.
    
    Args:
        level: Heading level (1-6)
        
    Returns:
        List of sections at specified level
        
    Raises:
        ValueError: If level not in range 1-6
    """

def get_child_sections(self, parent: SectionReference) -> List[SectionReference]:
    """
    Get all direct child sections of a parent section.
    
    Args:
        parent: Parent section reference
        
    Returns:
        List of immediate child sections
    """
```

#### Preview Operations

```python
def preview_operation(self, 
                     operation: EditOperation, 
                     **params) -> EditResult:
    """
    Preview an operation without applying changes.
    
    Args:
        operation: Type of operation to preview
        **params: Operation-specific parameters
        
    Returns:
        EditResult with preview content and validation results
        
    Example:
        preview = editor.preview_operation(
            EditOperation.UPDATE_SECTION,
            section_ref=section,
            content="New content"
        )
    """

def preview_batch_operations(self, 
                           operations: List[Dict[str, Any]]) -> EditResult:
    """
    Preview multiple operations as atomic batch.
    
    Args:
        operations: List of operation dictionaries
        
    Returns:
        EditResult with combined preview and validation
    """
```

#### Section Operations

```python
def update_section_content(self, 
                         section_ref: SectionReference, 
                         content: str,
                         preserve_subsections: bool = True) -> EditResult:
    """
    Update content of a specific section.
    
    Args:
        section_ref: Immutable reference to target section
        content: New content (markdown text without heading)
        preserve_subsections: Whether to keep existing subsections
        
    Returns:
        EditResult with operation status and details
        
    Validation:
        - Validates content is valid markdown
        - Ensures no heading conflicts
        - Checks document structure integrity
        
    Atomicity:
        - Operation is fully atomic
        - Automatic rollback on any failure
        - Document state preserved on error
    """

def insert_section_after(self, 
                        after_section: SectionReference,
                        level: int,
                        title: str,
                        content: str = "",
                        auto_adjust_level: bool = True) -> EditResult:
    """
    Insert new section after specified section.
    
    Args:
        after_section: Reference section for insertion point
        level: Heading level for new section (1-6)
        title: Section title (plain text)
        content: Section content (markdown)
        auto_adjust_level: Auto-adjust level to maintain hierarchy
        
    Returns:
        EditResult with new section reference in modified_sections
        
    Validation:
        - Ensures valid heading hierarchy
        - Validates title is non-empty
        - Checks content for structural issues
    """

def insert_section_before(self, 
                         before_section: SectionReference,
                         level: int,
                         title: str,
                         content: str = "") -> EditResult:
    """Insert new section before specified section."""

def delete_section(self, 
                  section_ref: SectionReference,
                  cascade_children: bool = True,
                  soft_delete: bool = False) -> EditResult:
    """
    Delete section and optionally its children.
    
    Args:
        section_ref: Section to delete
        cascade_children: Whether to delete child sections
        soft_delete: Mark for deletion without removing (future feature)
        
    Returns:
        EditResult with list of deleted sections
        
    Behavior:
        - If cascade_children=True: Deletes section and all subsections
        - If cascade_children=False: Promotes children to parent level
        - Maintains document structure integrity
    """

def move_section(self, 
                section_ref: SectionReference,
                target_position: int,
                adjust_level: bool = True) -> EditResult:
    """
    Move section to new position in document.
    
    Args:
        section_ref: Section to move
        target_position: New position (0-based index)
        adjust_level: Auto-adjust heading level for new context
        
    Returns:
        EditResult with updated section reference
    """

def change_heading_level(self, 
                        section_ref: SectionReference,
                        new_level: int,
                        cascade_children: bool = True) -> EditResult:
    """
    Change heading level of section.
    
    Args:
        section_ref: Section to modify
        new_level: New heading level (1-6)
        cascade_children: Adjust child section levels proportionally
        
    Returns:
        EditResult with updated section hierarchy
        
    Validation:
        - Ensures valid heading hierarchy after change
        - Prevents invalid nesting structures
    """
```

#### Content Operations

```python
def insert_content_at_line(self, 
                          line_number: int, 
                          content: str) -> EditResult:
    """Insert content at specific line number."""

def delete_content_range(self, 
                        start_line: int, 
                        end_line: int) -> EditResult:
    """Delete content in specified line range."""

def replace_content_range(self, 
                         start_line: int, 
                         end_line: int, 
                         new_content: str) -> EditResult:
    """Replace content in specified range."""
```

#### Batch Operations

```python
def execute_batch_operations(self, 
                           operations: List[Dict[str, Any]],
                           stop_on_error: bool = True) -> EditResult:
    """
    Execute multiple operations atomically.
    
    Args:
        operations: List of operation specifications
        stop_on_error: Whether to halt on first error
        
    Returns:
        EditResult with combined results
        
    Atomicity:
        - All operations succeed or all are rolled back
        - No partial state changes
        - Transaction logged for rollback
        
    Example:
        operations = [
            {
                'operation': EditOperation.UPDATE_SECTION,
                'section_ref': section1,
                'content': 'New content 1'
            },
            {
                'operation': EditOperation.INSERT_SECTION,
                'after_section': section2,
                'level': 2,
                'title': 'New Section',
                'content': 'Section content'
            }
        ]
        result = editor.execute_batch_operations(operations)
    """
```

#### Transaction Management

```python
def get_transaction_history(self, 
                          limit: Optional[int] = None) -> List[EditTransaction]:
    """
    Get transaction history.
    
    Args:
        limit: Maximum number of transactions to return
        
    Returns:
        List of transactions in reverse chronological order
    """

def rollback_transaction(self, 
                        transaction_id: Optional[str] = None) -> EditResult:
    """
    Rollback to state before specified transaction.
    
    Args:
        transaction_id: Transaction to rollback (defaults to last)
        
    Returns:
        EditResult indicating rollback success
        
    Behavior:
        - Rolls back to document state before transaction
        - Removes rolled-back transactions from history
        - Validates document integrity after rollback
    """

def create_checkpoint(self, 
                     name: str, 
                     description: str = "") -> str:
    """
    Create named checkpoint for manual rollback.
    
    Args:
        name: Checkpoint name
        description: Optional description
        
    Returns:
        Checkpoint identifier
    """

def rollback_to_checkpoint(self, checkpoint_id: str) -> EditResult:
    """Rollback to named checkpoint."""
```

#### Document Export

```python
def to_markdown(self) -> str:
    """Get current document as markdown string."""

def to_html(self) -> str:
    """Convert document to HTML."""

def to_json(self) -> str:
    """Export document structure as JSON."""

def get_statistics(self) -> DocumentStatistics:
    """Get comprehensive document statistics."""
```

### Validation and Analysis

```python
def validate_document(self) -> List[ParseError]:
    """
    Perform comprehensive document validation.
    
    Returns:
        List of validation errors and warnings
        
    Checks:
        - Heading hierarchy consistency  
        - Link integrity
        - Markdown syntax validity
        - Document structure coherence
    """

def analyze_structure(self) -> StructureAnalysis:
    """
    Analyze document structure and provide insights.
    
    Returns:
        StructureAnalysis with metrics and recommendations
    """

def find_broken_links(self) -> List[LinkError]:
    """Find broken internal and external links."""

def get_word_count(self, 
                  sections: Optional[List[SectionReference]] = None) -> int:
    """Get word count for entire document or specific sections."""
```

## Operation Semantics

### Atomicity Guarantees

All operations in the SafeMarkdownEditor API are **strictly atomic**:

1. **Success State**: Operation completes fully, document is in valid state
2. **Failure State**: Operation rolls back completely, document unchanged
3. **No Partial States**: Never leaves document in inconsistent intermediate state

### Section Identification Stability

Section references remain stable across most operations:

- **Stable Across**: Content updates, section moves, level changes
- **Invalidated By**: Section deletion, major structural changes
- **Refresh Strategy**: Call `get_sections()` after structural changes

### Validation Levels

```python
class ValidationLevel(Enum):
    STRICT = "strict"      # Full validation, strict compliance
    NORMAL = "normal"      # Standard validation, some flexibility  
    PERMISSIVE = "permissive"  # Minimal validation, maximum flexibility
```

**STRICT Mode:**

- Enforces perfect heading hierarchy (no level skipping)
- Validates all links and references
- Requires valid markdown syntax throughout
- Prevents any structural inconsistencies

**NORMAL Mode** (Default):

- Allows minor heading hierarchy issues (with warnings)
- Validates critical structural elements
- Permits some markdown syntax flexibility
- Balances safety with usability

**PERMISSIVE Mode:**

- Minimal structural validation
- Allows heading level jumps
- Tolerates markdown syntax variations
- Prioritizes operation success over strict compliance

## Error Handling

### Error Categories

1. **ValidationError**: Document structure or content validation failures
2. **OperationError**: Operation-specific failures (e.g., section not found)
3. **ParseError**: Markdown parsing failures
4. **ConcurrencyError**: Thread safety violations
5. **SystemError**: Underlying system or library failures

### Error Context

All errors include:

```python
@dataclass
class ParseError:
    message: str                    # Human-readable error description
    error_code: str                # Machine-readable error code
    line_number: Optional[int]     # Line number where error occurred
    column_number: Optional[int]   # Column number (if available)
    context: Optional[str]         # Surrounding content for context
    suggestions: List[str]         # Actionable suggestions for resolution
    severity: ErrorLevel           # ERROR, WARNING, INFO
    category: ErrorCategory        # Categorization for handling
```

### Error Recovery Patterns

```python
# Pattern 1: Simple error checking
result = editor.update_section_content(section, new_content)
if not result.success:
    print(f"Operation failed: {result.get_error_summary()}")
    return

# Pattern 2: Detailed error handling
result = editor.insert_section_after(section, 2, "New Section", content)
if result.has_errors:
    for error in result.errors:
        if error.category == ErrorCategory.VALIDATION:
            print(f"Validation error: {error.message}")
            for suggestion in error.suggestions:
                print(f"  Suggestion: {suggestion}")
        elif error.category == ErrorCategory.STRUCTURE:
            print(f"Structure error at line {error.line_number}: {error.message}")

# Pattern 3: Preview-first error prevention
preview = editor.preview_operation(EditOperation.DELETE_SECTION, 
                                  section_ref=section, cascade_children=True)
if preview.has_errors:
    print("Operation would fail:", preview.errors)
else:
    result = editor.delete_section(section, cascade_children=True)
```

## Thread Safety

### Concurrency Model

The SafeMarkdownEditor uses a **multi-reader, single-writer** concurrency model:

- **Read Operations**: Multiple threads can safely read simultaneously
- **Write Operations**: Exclusive access required, automatic synchronization
- **Transaction Isolation**: Each transaction has isolated workspace

### Thread Safety Guarantees

```python
# Safe concurrent usage example
import threading

editor = SafeMarkdownEditor(markdown_text)

def worker_thread(thread_id: int):
    # Safe: Multiple threads can read concurrently
    sections = editor.get_sections()
    stats = editor.get_statistics()
    
    # Safe: Writes are automatically synchronized
    result = editor.update_section_content(
        sections[thread_id % len(sections)], 
        f"Updated by thread {thread_id}"
    )

# Start multiple worker threads
threads = [threading.Thread(target=worker_thread, args=(i,)) for i in range(5)]
for thread in threads:
    thread.start()
for thread in threads:
    thread.join()
```

### Deadlock Prevention

- **Lock Ordering**: Consistent lock acquisition order
- **Timeout Mechanisms**: Automatic timeout for lock acquisition
- **Deadlock Detection**: Runtime detection and recovery

## Performance Characteristics

### Time Complexity

| Operation | Best Case | Average Case | Worst Case |
|-----------|-----------|--------------|------------|
| `get_sections()` | O(h) | O(h) | O(h) |
| `update_section_content()` | O(1) | O(n) | O(n) |
| `insert_section_after()` | O(1) | O(n) | O(n) |
| `delete_section()` | O(1) | O(n) | O(n) |
| `move_section()` | O(1) | O(n) | O(n) |
| `validate_document()` | O(n) | O(n) | O(n²) |

Where:

- `h` = number of headings
- `n` = document size (lines or tokens)

### Memory Usage

- **Base Memory**: O(n) for document storage
- **Transaction History**: O(t×n) where t = number of transactions
- **Section References**: O(h) for heading metadata
- **Temporary Buffers**: O(n) during operations

### Optimization Strategies

1. **Lazy Validation**: Validation only when necessary
2. **Incremental Updates**: Minimize document reconstruction
3. **Reference Caching**: Cache section references between operations
4. **Transaction Compression**: Compress old transaction data

## Usage Examples

### Basic Document Editing

```python
from quantalogic_markdown_mcp import SafeMarkdownEditor, EditOperation

# Initialize editor
markdown_text = """# Project Documentation

## Introduction
This is the introduction.

## Getting Started
Installation instructions here.

### Prerequisites
List of requirements.
"""

editor = SafeMarkdownEditor(markdown_text)

# Get document structure
sections = editor.get_sections()
print(f"Document has {len(sections)} sections")

# Update section content
intro_section = sections[1]  # "Introduction" section
result = editor.update_section_content(
    intro_section,
    "This is the **updated** introduction with more details."
)

if result.success:
    print("Introduction updated successfully")
else:
    print(f"Update failed: {result.get_error_summary()}")
```

### Preview-Driven Editing

```python
# Preview changes before applying
preview = editor.preview_operation(
    EditOperation.INSERT_SECTION,
    after_section=sections[2],  # After "Getting Started"
    level=2,
    title="Configuration",
    content="Configuration options and examples."
)

if preview.success:
    print("Preview:")
    print(preview.preview[:200] + "...")
    
    # Apply the change
    result = editor.insert_section_after(
        sections[2], 2, "Configuration", 
        "Configuration options and examples."
    )
    print(f"Section added: {result.success}")
else:
    print("Operation would fail:", preview.errors)
```

### Atomic Batch Operations

```python
# Execute multiple operations atomically
operations = [
    {
        'operation': EditOperation.UPDATE_SECTION,
        'section_ref': sections[0],
        'content': 'Updated project overview'
    },
    {
        'operation': EditOperation.INSERT_SECTION,
        'after_section': sections[-1],
        'level': 2,
        'title': 'Conclusion',
        'content': 'Summary and next steps.'
    },
    {
        'operation': EditOperation.CHANGE_HEADING_LEVEL,
        'section_ref': sections[3],  # "Prerequisites"
        'new_level': 2,
        'cascade_children': True
    }
]

result = editor.execute_batch_operations(operations)
if result.success:
    print(f"Batch operation completed, {len(result.modified_sections)} sections modified")
else:
    print("Batch operation failed, rolling back...")
```

### Error Handling and Recovery

```python
# Comprehensive error handling
result = editor.delete_section(sections[1], cascade_children=True)

if result.has_errors:
    print("Errors encountered:")
    for error in result.errors:
        print(f"  {error.severity.value}: {error.message}")
        if error.line_number:
            print(f"    At line {error.line_number}")
        for suggestion in error.suggestions:
            print(f"    Suggestion: {suggestion}")

if result.has_warnings:
    print("Warnings:")
    for warning in result.warnings:
        print(f"  {warning.message}")

# Rollback if needed
if result.success:
    print("Section deleted successfully")
else:
    print("Operation failed, document unchanged")
    
    # Manual rollback to previous state
    history = editor.get_transaction_history(limit=1)
    if history:
        rollback_result = editor.rollback_transaction()
        print(f"Rollback successful: {rollback_result.success}")
```

### Advanced Structure Analysis

```python
# Document analysis and validation
validation_errors = editor.validate_document()
if validation_errors:
    print("Document issues found:")
    for error in validation_errors:
        print(f"  {error}")

# Structure analysis
analysis = editor.analyze_structure()
print(f"Document depth: {analysis.max_heading_depth}")
print(f"Section balance: {analysis.section_balance_score}")

# Statistics
stats = editor.get_statistics()
print(f"Total sections: {stats.total_sections}")
print(f"Word count: {stats.word_count}")
print(f"Edit history: {stats.edit_count} transactions")
```

## Migration Guide

### From Legacy MarkdownEditor

The legacy `MarkdownEditor` API is deprecated but supported through a compatibility layer:

```python
# OLD: Unsafe legacy API
editor = MarkdownEditor(markdown_text)
sections = editor.get_sections()  # Returns dict objects
editor.update_section_content("section_0", content)  # String ID

# NEW: Safe modern API  
editor = SafeMarkdownEditor(markdown_text)
sections = editor.get_sections()  # Returns SectionReference objects
result = editor.update_section_content(sections[0], content)  # Immutable reference
```

### Migration Checklist

1. **Replace Constructor**:

   ```python
   # Before
   editor = MarkdownEditor(text)
   
   # After
   editor = SafeMarkdownEditor(text)
   ```

2. **Update Section References**:

   ```python
   # Before
   sections = editor.get_sections()
   section_id = sections[0]['id']  # String ID
   
   # After  
   sections = editor.get_sections()
   section_ref = sections[0]  # SectionReference object
   ```

3. **Handle Return Values**:

   ```python
   # Before
   result = editor.update_section_content(section_id, content)
   # result is ParseResult
   
   # After
   result = editor.update_section_content(section_ref, content)
   if result.success:
       # Handle success
   else:
       # Handle errors: result.errors
   ```

4. **Add Error Handling**:

   ```python
   # Before
   editor.add_section(after_id, level, title, content)  # No error checking
   
   # After
   result = editor.insert_section_after(after_ref, level, title, content)
   if not result.success:
       print(f"Failed: {result.get_error_summary()}")
   ```

### Automated Migration Tools

A migration script is provided to automatically convert legacy usage:

```bash
python -m quantalogic_markdown_mcp.migrate --input legacy_code.py --output safe_code.py
```

## Implementation Notes

### Internal Architecture

```text
SafeMarkdownEditor
├── DocumentState (immutable snapshot)
├── TransactionManager (rollback support)  
├── ValidationEngine (document integrity)
├── ConcurrencyController (thread safety)
└── OperationExecutor (atomic operations)
```

### Extension Points

The API supports extension through:

1. **Custom Validators**: Add domain-specific validation rules
2. **Operation Plugins**: Implement custom editing operations  
3. **Export Formats**: Add new output formats
4. **Analysis Tools**: Custom document analysis functions

### Testing Strategy

The API includes comprehensive test coverage:

- **Unit Tests**: Individual operation testing
- **Integration Tests**: Multi-operation scenarios
- **Concurrency Tests**: Thread safety validation
- **Performance Tests**: Scalability benchmarks
- **Regression Tests**: Backward compatibility

### Dependencies

- `quantalogic-markdown-mcp >= 0.1.0`: Core parsing infrastructure
- `markdown-it-py >= 3.0.0`: Markdown parsing engine
- `typing-extensions >= 4.0.0`: Enhanced type annotations

---

*This specification represents the definitive API contract for SafeMarkdownEditor v2.0.0. All implementations must conform to the behaviors and guarantees described in this document.*
