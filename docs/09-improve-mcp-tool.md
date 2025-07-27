# MCP Tools Improvement: Document Path Parameter

## Overview

This document outlines a comprehensive improvement plan for the SafeMarkdownEditor MCP tools by adding a `document_path` parameter as the first parameter to all document editing tools. This enhancement will enable:

- **Stateless operations**: Execute actions on documents without requiring persistent server state
- **Multi-document support**: Work with multiple documents simultaneously
- **Better scalability**: Reduce memory usage by avoiding persistent document loading
- **Improved reliability**: Eliminate race conditions from shared state

## Current Architecture Issues

### State Management Problems

1. **Shared State**: The current server maintains a single `self.editor` instance and `self.current_file_path`
2. **Threading Issues**: While the server uses locks, it creates potential bottlenecks
3. **Memory Usage**: Documents remain loaded in memory until replaced
4. **Concurrency Limitations**: Only one document can be active at a time per server instance

### Current Tool Categories

**File Operations (3 tools):**
- `load_document(file_path, validation_level)`
- `save_document(file_path?, backup)`
- `get_file_info()`
- `test_path_resolution(path)`

**Document Editing (8 tools):**
- `insert_section(heading, content, position)`
- `delete_section(section_id?, heading?)`
- `update_section(section_id, content)`
- `move_section(section_id, new_position)`
- `get_section(section_id)`
- `list_sections()`
- `get_document()`
- `undo()`

## Proposed Improvements

### Core Design Principle

Add `document_path: str` as the **first parameter** to all tools that operate on document content, making operations stateless and enabling one-call document manipulation.

### Tool-by-Tool Enhancement Plan

#### 1. File Operations Enhancement

**Current:**
```python
@mcp.tool()
def load_document(file_path: str, validation_level: str = "NORMAL") -> Dict[str, Any]:
    """Load a Markdown document from a file path."""
```

**Improved:**
```python
@mcp.tool()
def load_document(document_path: str, validation_level: str = "NORMAL") -> Dict[str, Any]:
    """Load and return information about a Markdown document.
    
    Args:
        document_path: Path to the Markdown document to analyze
        validation_level: Validation strictness - "STRICT", "NORMAL", or "PERMISSIVE"
    
    Returns:
        Document metadata, section count, validation results, and content preview
    """
```

**New Capabilities:**
- Returns document information without persistent loading
- Validates document structure
- Provides content preview and statistics
- No server state modification

#### 2. Document Editing Tools Enhancement

**A. Insert Section**

**Current:**
```python
def insert_section(heading: str, content: str, position: int) -> Dict[str, Any]:
```

**Improved:**
```python
def insert_section(document_path: str, heading: str, content: str, position: int, 
                  auto_save: bool = True, backup: bool = True, 
                  validation_level: str = "NORMAL") -> Dict[str, Any]:
    """Insert a new section into a document at the specified position.
    
    Args:
        document_path: Path to the target Markdown document
        heading: The section heading text
        content: The section content (supports Markdown)
        position: Insert position (0=beginning, -1=end, or after section N)
        auto_save: Whether to save changes automatically
        backup: Whether to create a backup before modifying
        validation_level: Document validation level
    
    Returns:
        Operation result with new section ID and updated document preview
    """
```

**B. Delete Section**

**Current:**
```python
def delete_section(section_id: Optional[str] = None, heading: Optional[str] = None) -> Dict[str, Any]:
```

**Improved:**
```python
def delete_section(document_path: str, section_id: Optional[str] = None, 
                  heading: Optional[str] = None, cascade: bool = True,
                  auto_save: bool = True, backup: bool = True) -> Dict[str, Any]:
    """Delete a section from a document by ID or heading.
    
    Args:
        document_path: Path to the target Markdown document
        section_id: Unique section identifier (optional)
        heading: Section heading text to match (optional)
        cascade: Whether to delete subsections as well
        auto_save: Whether to save changes automatically  
        backup: Whether to create a backup before modifying
    
    Note: Either section_id or heading must be provided
    """
```

**C. Update Section**

**Current:**
```python
def update_section(section_id: str, content: str) -> Dict[str, Any]:
```

**Improved:**
```python
def update_section(document_path: str, section_id: str, content: str,
                  preserve_subsections: bool = True, auto_save: bool = True,
                  backup: bool = True, merge_strategy: str = "replace") -> Dict[str, Any]:
    """Update the content of an existing section.
    
    Args:
        document_path: Path to the target Markdown document
        section_id: Unique section identifier
        content: New content for the section
        preserve_subsections: Whether to keep existing subsections
        auto_save: Whether to save changes automatically
        backup: Whether to create a backup before modifying
        merge_strategy: How to handle content ("replace", "append", "prepend")
    """
```

**D. Move Section**

**Current:**
```python
def move_section(section_id: str, new_position: int) -> Dict[str, Any]:
```

**Improved:**
```python
def move_section(document_path: str, section_id: str, new_position: int,
                auto_save: bool = True, backup: bool = True,
                adjust_levels: bool = True) -> Dict[str, Any]:
    """Move a section to a new position within the document.
    
    Args:
        document_path: Path to the target Markdown document
        section_id: Unique section identifier
        new_position: Target position (0-based, -1 for end)
        auto_save: Whether to save changes automatically
        backup: Whether to create a backup before modifying
        adjust_levels: Whether to adjust heading levels for better structure
    """
```

**E. Get Section**

**Current:**
```python
def get_section(section_id: str) -> Dict[str, Any]:
```

**Improved:**
```python
def get_section(document_path: str, section_id: Optional[str] = None,
               heading: Optional[str] = None, include_subsections: bool = False,
               format: str = "markdown") -> Dict[str, Any]:
    """Retrieve a section's content and metadata from a document.
    
    Args:
        document_path: Path to the target Markdown document
        section_id: Unique section identifier (optional)
        heading: Section heading to match (optional)
        include_subsections: Whether to include nested subsections
        format: Output format ("markdown", "plain", "html")
    
    Note: Either section_id or heading must be provided
    """
```

**F. List Sections**

**Current:**
```python
def list_sections() -> Dict[str, Any]:
```

**Improved:**
```python
def list_sections(document_path: str, include_content_preview: bool = False,
                 max_depth: Optional[int] = None, filter_pattern: Optional[str] = None) -> Dict[str, Any]:
    """List all sections in a document with their metadata.
    
    Args:
        document_path: Path to the target Markdown document
        include_content_preview: Whether to include content preview for each section
        max_depth: Maximum heading depth to include (None for all)
        filter_pattern: Regex pattern to filter section headings
    """
```

**G. Get Document**

**Current:**
```python
def get_document() -> Dict[str, Any]:
```

**Improved:**
```python
def get_document(document_path: str, format: str = "markdown",
                include_metadata: bool = False, sections_only: bool = False) -> Dict[str, Any]:
    """Retrieve the complete document content and metadata.
    
    Args:
        document_path: Path to the target Markdown document
        format: Output format ("markdown", "html", "plain", "json")
        include_metadata: Whether to include document metadata
        sections_only: Whether to return only section structure
    """
```

#### 3. New Advanced Tools

**A. Batch Operations**

```python
def batch_operations(document_path: str, operations: List[Dict[str, Any]],
                    auto_save: bool = True, backup: bool = True,
                    atomic: bool = True) -> Dict[str, Any]:
    """Execute multiple operations on a document atomically.
    
    Args:
        document_path: Path to the target Markdown document
        operations: List of operations to execute
        auto_save: Whether to save changes automatically
        backup: Whether to create a backup before modifying
        atomic: Whether to rollback all changes if any operation fails
    
    Example operations:
    [
        {"action": "insert_section", "heading": "New Section", "content": "...", "position": 1},
        {"action": "update_section", "section_id": "sec_123", "content": "..."},
        {"action": "delete_section", "section_id": "sec_456"}
    ]
    """
```

**B. Document Analysis**

```python  
def analyze_document(document_path: str, analysis_types: List[str] = ["structure", "content", "links"]) -> Dict[str, Any]:
    """Perform comprehensive analysis of a document.
    
    Args:
        document_path: Path to the target Markdown document
        analysis_types: Types of analysis to perform
            - "structure": Heading hierarchy and document structure
            - "content": Word count, reading time, language detection
            - "links": Internal/external links analysis
            - "images": Image references and accessibility
            - "tables": Table structure and formatting
            - "code": Code blocks and syntax highlighting
    """
```

**C. Document Transformation**

```python
def transform_document(document_path: str, transformations: List[Dict[str, Any]],
                      output_path: Optional[str] = None, backup: bool = True) -> Dict[str, Any]:
    """Apply structural transformations to a document.
    
    Args:
        document_path: Path to the source Markdown document
        transformations: List of transformation rules
        output_path: Path for the transformed document (None to overwrite)
        backup: Whether to create a backup before modifying
    
    Example transformations:
    [
        {"action": "normalize_headings", "start_level": 1},
        {"action": "add_toc", "position": 1, "max_depth": 3},
        {"action": "auto_number_sections", "format": "1.1.1"},
        {"action": "reorder_sections", "order": ["introduction", "methods", "results"]}
    ]
    """
```

#### 4. Multi-Document Operations

**A. Document Comparison**

```python
def compare_documents(document_path_1: str, document_path_2: str,
                     comparison_type: str = "structure", output_format: str = "diff") -> Dict[str, Any]:
    """Compare two documents and return differences.
    
    Args:
        document_path_1: Path to the first document
        document_path_2: Path to the second document  
        comparison_type: Type of comparison ("structure", "content", "both")
        output_format: Format for differences ("diff", "json", "markdown")
    """
```

**B. Document Merging**

```python
def merge_documents(document_paths: List[str], output_path: str,
                   merge_strategy: str = "sequential", conflict_resolution: str = "manual") -> Dict[str, Any]:
    """Merge multiple documents into one.
    
    Args:
        document_paths: List of paths to documents to merge
        output_path: Path for the merged document
        merge_strategy: How to merge ("sequential", "interleaved", "by_section")
        conflict_resolution: How to handle conflicts ("manual", "first_wins", "last_wins")
    """
```

### Implementation Architecture

#### 1. Core Engine Modification

**Current State Manager:**
```python
class MarkdownMCPServer:
    def __init__(self):
        self.editor: Optional[SafeMarkdownEditor] = None
        self.current_file_path: Optional[Path] = None
        self.lock = threading.RLock()
```

**Proposed Stateless Engine:**
```python
class StatelessMarkdownProcessor:
    """Stateless processor for Markdown operations."""
    
    @staticmethod
    def load_and_process(document_path: str, 
                        operation: Callable,
                        validation_level: ValidationLevel = ValidationLevel.NORMAL,
                        **kwargs) -> Dict[str, Any]:
        """Load a document, perform an operation, and optionally save."""
        
    @staticmethod
    def create_editor(document_path: str, validation_level: ValidationLevel) -> SafeMarkdownEditor:
        """Create a temporary editor instance for a document."""
        
    @staticmethod
    def save_if_requested(editor: SafeMarkdownEditor, document_path: str,
                         auto_save: bool, backup: bool) -> Dict[str, Any]:
        """Save document if auto_save is enabled."""
```

#### 2. Backward Compatibility

**Legacy Mode Support:**
```python
class MarkdownMCPServer:
    def __init__(self, legacy_mode: bool = True):
        self.legacy_mode = legacy_mode
        if legacy_mode:
            # Keep existing stateful behavior for backward compatibility
            self.editor = None
            self.current_file_path = None
```

**Parameter Detection:**
```python
def _is_legacy_call(self, **kwargs) -> bool:
    """Detect if this is a legacy call without document_path."""
    return 'document_path' not in kwargs

def _handle_legacy_operation(self, operation_name: str, **kwargs):
    """Handle operations in legacy mode with shared state."""
```

#### 3. Enhanced Error Handling

**Comprehensive Error Types:**
```python
class DocumentOperationError(Exception):
    """Base class for document operation errors."""
    
class DocumentNotFoundError(DocumentOperationError):
    """Document file not found or not accessible."""
    
class ValidationError(DocumentOperationError):
    """Document validation failed."""
    
class SectionNotFoundError(DocumentOperationError):
    """Requested section not found in document."""
    
class PermissionError(DocumentOperationError):
    """Insufficient permissions for operation."""
```

**Error Response Format:**
```python
{
    "success": False,
    "error": {
        "type": "DocumentNotFoundError",
        "message": "Document not found: /path/to/file.md",
        "code": "DOC_NOT_FOUND",
        "details": {
            "path": "/path/to/file.md",
            "resolved_path": "/absolute/path/to/file.md",
            "exists": False,
            "parent_exists": True
        }
    },
    "suggestions": [
        "Check that the file path is correct",
        "Ensure you have read permissions for the file",
        "Use test_path_resolution to verify path expansion"
    ],
    "recovery_options": [
        {
            "action": "create_document",
            "description": "Create a new document at this path",
            "parameters": {"document_path": "/path/to/file.md"}
        }
    ]
}
```

### Benefits of the Proposed Changes

#### 1. **Scalability Improvements**

- **Memory Efficiency**: Documents are loaded only during operations
- **Concurrency**: Multiple documents can be processed simultaneously
- **Resource Management**: Automatic cleanup after operations

#### 2. **Developer Experience**

- **Simpler API**: One call to perform any operation on any document
- **Better Debugging**: Each operation is self-contained and traceable
- **Flexibility**: Choose between stateful and stateless operations

#### 3. **Use Case Examples**

**Before (Current):**
```python
# Multi-step process with state management
await client.call_tool("load_document", {"file_path": "doc1.md"})
await client.call_tool("insert_section", {"heading": "New Section", "content": "...", "position": 1})
await client.call_tool("save_document", {})

# Need to load another document
await client.call_tool("load_document", {"file_path": "doc2.md"})
await client.call_tool("delete_section", {"heading": "Old Section"})
await client.call_tool("save_document", {})
```

**After (Improved):**
```python
# Single call per operation, no state management
await client.call_tool("insert_section", {
    "document_path": "doc1.md",
    "heading": "New Section", 
    "content": "...", 
    "position": 1,
    "auto_save": True
})

await client.call_tool("delete_section", {
    "document_path": "doc2.md",
    "heading": "Old Section",
    "auto_save": True
})
```

**Batch Operations:**
```python
# Process multiple operations atomically
await client.call_tool("batch_operations", {
    "document_path": "complex_doc.md",
    "operations": [
        {"action": "insert_section", "heading": "Introduction", "content": "...", "position": 0},
        {"action": "update_section", "section_id": "sec_123", "content": "Updated content"},
        {"action": "move_section", "section_id": "sec_456", "new_position": 2}
    ],
    "atomic": True,
    "auto_save": True
})
```

### Migration Strategy

#### Phase 1: Add New Parameters (Non-Breaking)
- Add `document_path` as an optional first parameter to all tools
- Maintain backward compatibility with existing stateful behavior
- Default to legacy mode when `document_path` is not provided

#### Phase 2: Encourage New Pattern
- Update documentation to showcase new stateless approach
- Add deprecation warnings for stateful operations
- Provide migration examples and tools

#### Phase 3: Full Transition
- Make `document_path` required parameter
- Remove stateful server instance variables
- Provide legacy compatibility layer for existing users

### Testing Strategy

#### 1. **Compatibility Testing**
- Ensure all existing tests pass with legacy mode enabled
- Test new parameter handling with and without `document_path`
- Verify error handling for mixed old/new calling patterns

#### 2. **Performance Testing**
- Compare memory usage between stateful and stateless operations
- Measure operation latency for repeated document access
- Test concurrent operations on multiple documents

#### 3. **Integration Testing**
- Test with Claude Desktop using new parameter format
- Verify VSCode MCP integration works with enhanced tools
- Test batch operations and error recovery scenarios

### Conclusion

Adding `document_path` as the first parameter to all MCP tools represents a significant architectural improvement that:

1. **Eliminates State Management Complexity**: No more shared state or threading concerns
2. **Enables True Concurrency**: Multiple documents can be processed simultaneously  
3. **Improves Reliability**: Each operation is self-contained and atomic
4. **Enhances User Experience**: One call to perform any operation on any document
5. **Supports Advanced Features**: Batch operations, document analysis, and multi-document workflows

The proposed changes maintain backward compatibility while providing a clear migration path to a more scalable and reliable architecture. This improvement positions the SafeMarkdownEditor MCP server as a powerful tool for complex document manipulation workflows.

---

**Next Steps:**
1. Review and refine the proposed API changes
2. Implement Phase 1 with backward compatibility
3. Create comprehensive test suite for new functionality
4. Update documentation with examples and migration guide
5. Gather user feedback and iterate on the design
