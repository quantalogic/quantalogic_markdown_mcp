"""Safe Markdown Editor - Core data types and enumerations."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from .types import ParseError


class ValidationLevel(Enum):
    """Validation strictness levels."""
    STRICT = "strict"      # Full validation, strict compliance
    NORMAL = "normal"      # Standard validation, some flexibility  
    PERMISSIVE = "permissive"  # Minimal validation, maximum flexibility


class ErrorCategory(Enum):
    """Categories for error classification."""
    VALIDATION = "validation"
    STRUCTURE = "structure"
    OPERATION = "operation"
    PARSE = "parse"
    CONCURRENCY = "concurrency"
    SYSTEM = "system"


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


class OperationType(Enum):
    """Operation types for edit results."""
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    MOVE = "move"
    ANALYZE = "analyze"
    LOAD = "load"
    SAVE = "save"


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


@dataclass
class DocumentStatistics:
    """Comprehensive document statistics."""
    
    total_sections: int
    word_count: int
    character_count: int
    line_count: int
    max_heading_depth: int
    edit_count: int
    section_distribution: Dict[int, int]  # heading level -> count
    last_modified: Optional[datetime] = None


@dataclass
class StructureAnalysis:
    """Document structure analysis results."""
    
    max_heading_depth: int
    section_balance_score: float  # 0.0 to 1.0, higher is better balanced
    heading_hierarchy_valid: bool
    orphaned_sections: List[SectionReference]
    recommendations: List[str]


@dataclass
class LinkError:
    """Broken link information."""
    
    link_text: str
    target: str
    line_number: int
    error_type: str  # "broken_internal", "broken_external", "malformed"
    suggestion: Optional[str] = None


# Enhanced ParseError with additional SafeMarkdownEditor fields
@dataclass
class SafeParseError(ParseError):
    """Extended ParseError with additional fields for SafeMarkdownEditor."""
    
    error_code: str = ""                # Machine-readable error code
    context: Optional[str] = None       # Surrounding content for context
    suggestions: List[str] = field(default_factory=list)  # Actionable suggestions
    category: ErrorCategory = ErrorCategory.PARSE  # Error categorization
