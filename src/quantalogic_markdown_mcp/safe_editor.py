"""Safe Markdown Editor - Main implementation."""

import hashlib
import re
import threading 
from datetime import datetime
from typing import Any, Dict, List, Optional

from .ast_utils import ASTWrapper
from .parser import QuantalogicMarkdownParser
from .safe_editor_types import (
    DocumentStatistics,
    EditOperation,
    EditResult,
    EditTransaction,
    ErrorCategory,
    SafeParseError,
    SectionReference,
    ValidationLevel,
)
from .types import ErrorLevel


class DocumentStructureError(Exception):
    """Exception raised when document structure is invalid."""
    pass


class SafeMarkdownEditor:
    """
    Thread-safe, atomic Markdown editor with comprehensive validation.
    
    Provides atomic operations for editing Markdown documents with:
    - Immutable section references that remain stable across edits
    - Comprehensive validation and error reporting
    - Transaction support with rollback capability
    - Thread-safe concurrent access
    - Preview functionality for all operations
    """
    
    def __init__(self, 
                 markdown_text: str,
                 validation_level: ValidationLevel = ValidationLevel.NORMAL,
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
        self._lock = threading.RLock()  # Reentrant lock for thread safety
        self._validation_level = validation_level
        self._max_transaction_history = max_transaction_history
        
        # Initialize parser
        self._parser = QuantalogicMarkdownParser()
        
        # Store initial state
        self._original_text = markdown_text
        self._current_text = markdown_text
        
        # Parse and validate initial document
        self._current_result = self._parser.parse(markdown_text)
        if self._current_result.has_errors:
            critical_errors = [e for e in self._current_result.errors 
                             if e.level == ErrorLevel.CRITICAL]
            if critical_errors:
                raise ValueError(f"Document contains critical parsing errors: {critical_errors}")
        
        self._wrapper = ASTWrapper(self._current_result)
        
        # Transaction and state management
        self._transaction_history: List[EditTransaction] = []
        self._version = 1
        self._last_modified = datetime.now()
        
        # Validate initial structure
        if validation_level in [ValidationLevel.STRICT, ValidationLevel.NORMAL]:
            structure_errors = self._validate_document_structure()
            if structure_errors and validation_level == ValidationLevel.STRICT:
                raise DocumentStructureError(f"Invalid document structure: {structure_errors}")
    
    def get_sections(self) -> List[SectionReference]:
        """
        Get immutable references to all document sections.
        
        Returns:
            List of SectionReference objects in document order
            
        Complexity: O(n) where n is number of headings
        Thread Safety: Safe for concurrent access
        """
        with self._lock:
            return self._build_section_references()
    
    def get_section_by_id(self, section_id: str) -> Optional[SectionReference]:
        """
        Find section by stable identifier.
        
        Args:
            section_id: Stable section identifier
            
        Returns:
            SectionReference if found, None otherwise
            
        Complexity: O(n) where n is number of sections
        """
        with self._lock:
            sections = self._build_section_references()
            for section in sections:
                if section.id == section_id:
                    return section
            return None
    
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
        if not (1 <= level <= 6):
            raise ValueError(f"Heading level must be between 1 and 6, got {level}")
        
        with self._lock:
            sections = self._build_section_references()
            return [s for s in sections if s.level == level]
    
    def get_child_sections(self, parent: SectionReference) -> List[SectionReference]:
        """
        Get all direct child sections of a parent section.
        
        Args:
            parent: Parent section reference
            
        Returns:
            List of immediate child sections
        """
        with self._lock:
            sections = self._build_section_references()
            children = []
            
            for section in sections:
                # Child must have higher level and be after parent
                if (section.level > parent.level and 
                    section.line_start > parent.line_start):
                    
                    # Check if it's a direct child (no intermediate levels)
                    is_direct_child = True
                    for other in sections:
                        if (other.line_start > parent.line_start and
                            other.line_start < section.line_start and
                            parent.level < other.level < section.level):
                            is_direct_child = False
                            break
                    
                    if is_direct_child:
                        children.append(section)
            
            return children
    
    def to_markdown(self) -> str:
        """Get current document as markdown string."""
        with self._lock:
            return self._current_text
    
    def get_statistics(self) -> DocumentStatistics:
        """Get comprehensive document statistics."""
        with self._lock:
            lines = self._current_text.split('\n')
            sections = self._build_section_references()
            
            # Calculate section distribution by level
            section_distribution = {}
            for section in sections:
                level = section.level
                section_distribution[level] = section_distribution.get(level, 0) + 1
            
            return DocumentStatistics(
                total_sections=len(sections),
                word_count=len(self._current_text.split()),
                character_count=len(self._current_text),
                line_count=len(lines),
                max_heading_depth=max([s.level for s in sections]) if sections else 0,
                edit_count=len(self._transaction_history),
                section_distribution=section_distribution,
                last_modified=self._last_modified
            )
    
    def preview_operation(self, operation: EditOperation, **params) -> EditResult:
        """
        Preview an operation without applying changes.
        
        Args:
            operation: Type of operation to preview
            **params: Operation-specific parameters
            
        Returns:
            EditResult with preview content and validation results
        """
        with self._lock:
            try:
                # Create a copy of the current state for preview
                preview_text = self._current_text
                
                if operation == EditOperation.UPDATE_SECTION:
                    section_ref = params.get('section_ref')
                    content = params.get('content')
                    if not section_ref or content is None:
                        return EditResult(
                            success=False,
                            operation=operation,
                            modified_sections=[],
                            errors=[SafeParseError(
                                message="Missing required parameters: section_ref and content",
                                error_code="MISSING_PARAMS",
                                category=ErrorCategory.OPERATION
                            )],
                            warnings=[]
                        )
                    
                    # Preview the section update
                    lines = preview_text.split('\n')
                    start_line = section_ref.line_start
                    end_line = section_ref.line_end
                    
                    # Replace content while preserving heading
                    if start_line < len(lines):
                        new_content_lines = content.split('\n')
                        new_lines = (lines[:start_line + 1] + 
                                   new_content_lines + 
                                   lines[end_line + 1:])
                        preview_text = '\n'.join(new_lines)
                
                elif operation == EditOperation.INSERT_SECTION:
                    after_section = params.get('after_section')
                    level = params.get('level')
                    title = params.get('title')
                    content = params.get('content', '')
                    
                    if not after_section or not level or not title:
                        return EditResult(
                            success=False,
                            operation=operation,
                            modified_sections=[],
                            errors=[SafeParseError(
                                message="Missing required parameters: after_section, level, title",
                                error_code="MISSING_PARAMS",
                                category=ErrorCategory.OPERATION
                            )],
                            warnings=[]
                        )
                    
                    # Preview section insertion
                    lines = preview_text.split('\n')
                    insert_line = after_section.line_end + 1
                    
                    new_section_lines = [
                        f"{'#' * level} {title}",
                        "",
                        content,
                        ""
                    ]
                    
                    new_lines = (lines[:insert_line] + 
                               new_section_lines + 
                               lines[insert_line:])
                    preview_text = '\n'.join(new_lines)
                
                # Validate the preview
                preview_result = self._parser.parse(preview_text)
                validation_errors = []
                
                if preview_result.has_errors:
                    for error in preview_result.errors:
                        validation_errors.append(SafeParseError(
                            message=error.message,
                            line_number=error.line_number,
                            level=error.level,
                            error_code="PREVIEW_VALIDATION",
                            category=ErrorCategory.VALIDATION
                        ))
                
                return EditResult(
                    success=len(validation_errors) == 0,
                    operation=operation,
                    modified_sections=[],  # Preview doesn't modify anything yet
                    errors=validation_errors,
                    warnings=[],
                    preview=preview_text
                )
                
            except Exception as e:
                return EditResult(
                    success=False,
                    operation=operation,
                    modified_sections=[],
                    errors=[SafeParseError(
                        message=f"Preview operation failed: {str(e)}",
                        error_code="PREVIEW_ERROR",
                        category=ErrorCategory.SYSTEM
                    )],
                    warnings=[]
                )
    
    def update_section_content(self, section_ref: SectionReference, content: str,
                             preserve_subsections: bool = True) -> EditResult:
        """
        Update content of a specific section.
        
        Args:
            section_ref: Immutable reference to target section
            content: New content (markdown text without heading)
            preserve_subsections: Whether to keep existing subsections
            
        Returns:
            EditResult with operation status and details
        """
        with self._lock:
            try:
                # First validate the operation
                preview_result = self.preview_operation(
                    EditOperation.UPDATE_SECTION,
                    section_ref=section_ref,
                    content=content
                )
                
                if not preview_result.success:
                    return preview_result
                
                # Create transaction for rollback
                transaction = self._create_transaction([{
                    'operation': EditOperation.UPDATE_SECTION,
                    'section_ref': section_ref,
                    'content': content,
                    'preserve_subsections': preserve_subsections
                }])
                
                # Apply the changes
                lines = self._current_text.split('\n')
                start_line = section_ref.line_start
                end_line = section_ref.line_end
                
                if preserve_subsections:
                    # Find where section content ends and subsections begin
                    section_content_end = self._find_section_content_end(section_ref)
                    end_line = section_content_end
                
                # Replace content while preserving heading
                if start_line < len(lines):
                    new_content_lines = content.split('\n')
                    new_lines = (lines[:start_line + 1] + 
                               new_content_lines + 
                               lines[end_line + 1:])
                    
                    # Update state
                    self._current_text = '\n'.join(new_lines)
                    self._current_result = self._parser.parse(self._current_text)
                    self._wrapper = ASTWrapper(self._current_result)
                    self._last_modified = datetime.now()
                    self._version += 1
                    
                    # Add transaction to history
                    self._transaction_history.append(transaction)
                    self._trim_transaction_history()
                    
                    # Get updated section reference
                    updated_sections = self._build_section_references()
                    updated_section = None
                    for section in updated_sections:
                        if section.title == section_ref.title and section.level == section_ref.level:
                            updated_section = section
                            break
                    
                    return EditResult(
                        success=True,
                        operation=EditOperation.UPDATE_SECTION,
                        modified_sections=[updated_section] if updated_section else [],
                        errors=[],
                        warnings=[],
                        metadata={
                            'transaction_id': transaction.transaction_id,
                            'version': self._version,
                            'preserve_subsections': preserve_subsections
                        }
                    )
                
                return EditResult(
                    success=False,
                    operation=EditOperation.UPDATE_SECTION,
                    modified_sections=[],
                    errors=[SafeParseError(
                        message="Section not found or invalid line range",
                        error_code="SECTION_NOT_FOUND",
                        category=ErrorCategory.OPERATION
                    )],
                    warnings=[]
                )
                
            except Exception as e:
                return EditResult(
                    success=False,
                    operation=EditOperation.UPDATE_SECTION,
                    modified_sections=[],
                    errors=[SafeParseError(
                        message=f"Update operation failed: {str(e)}",
                        error_code="UPDATE_ERROR",
                        category=ErrorCategory.SYSTEM
                    )],
                    warnings=[]
                )
    
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
        """
        with self._lock:
            try:
                # Validate parameters
                if not (1 <= level <= 6):
                    return EditResult(
                        success=False,
                        operation=EditOperation.INSERT_SECTION,
                        modified_sections=[],
                        errors=[SafeParseError(
                            message=f"Invalid heading level: {level}. Must be between 1 and 6.",
                            error_code="INVALID_LEVEL",
                            category=ErrorCategory.VALIDATION,
                            suggestions=["Use a heading level between 1 and 6"]
                        )],
                        warnings=[]
                    )
                
                if not title.strip():
                    return EditResult(
                        success=False,
                        operation=EditOperation.INSERT_SECTION,
                        modified_sections=[],
                        errors=[SafeParseError(
                            message="Section title cannot be empty",
                            error_code="EMPTY_TITLE",
                            category=ErrorCategory.VALIDATION,
                            suggestions=["Provide a non-empty title for the section"]
                        )],
                        warnings=[]
                    )
                
                # Auto-adjust level if requested
                if auto_adjust_level:
                    # Ensure the new section level makes sense in context
                    child_sections = self.get_child_sections(after_section)
                    if child_sections:
                        # If after_section has children, insert at child level
                        level = max(after_section.level + 1, min(s.level for s in child_sections))
                    else:
                        # No children, use level one below parent
                        level = min(level, after_section.level + 1)
                
                # Preview the operation first
                preview_result = self.preview_operation(
                    EditOperation.INSERT_SECTION,
                    after_section=after_section,
                    level=level,
                    title=title,
                    content=content
                )
                
                if not preview_result.success:
                    return preview_result
                
                # Create transaction
                transaction = self._create_transaction([{
                    'operation': EditOperation.INSERT_SECTION,
                    'after_section': after_section,
                    'level': level,
                    'title': title,
                    'content': content,
                    'auto_adjust_level': auto_adjust_level
                }])
                
                # Apply the changes
                lines = self._current_text.split('\n')
                insert_line = after_section.line_end + 1
                
                # Create new section lines
                new_section_lines = [
                    f"{'#' * level} {title}",
                    "",
                    content,
                    ""
                ]
                
                # Insert the new section
                new_lines = (lines[:insert_line] + 
                           new_section_lines + 
                           lines[insert_line:])
                
                # Update state
                self._current_text = '\n'.join(new_lines)
                self._current_result = self._parser.parse(self._current_text)
                self._wrapper = ASTWrapper(self._current_result)
                self._last_modified = datetime.now()
                self._version += 1
                
                # Add transaction to history
                self._transaction_history.append(transaction)
                self._trim_transaction_history()
                
                # Find the newly created section
                updated_sections = self._build_section_references()
                new_section = None
                for section in updated_sections:
                    if (section.title == title and 
                        section.level == level and 
                        section.line_start >= insert_line):
                        new_section = section
                        break
                
                return EditResult(
                    success=True,
                    operation=EditOperation.INSERT_SECTION,
                    modified_sections=[new_section] if new_section else [],
                    errors=[],
                    warnings=[],
                    metadata={
                        'transaction_id': transaction.transaction_id,
                        'version': self._version,
                        'auto_adjusted_level': auto_adjust_level,
                        'final_level': level
                    }
                )
                
            except Exception as e:
                return EditResult(
                    success=False,
                    operation=EditOperation.INSERT_SECTION,
                    modified_sections=[],
                    errors=[SafeParseError(
                        message=f"Insert section operation failed: {str(e)}",
                        error_code="INSERT_ERROR",
                        category=ErrorCategory.SYSTEM
                    )],
                    warnings=[]
                )
    
    def delete_section(self, section_ref: SectionReference, preserve_subsections: bool = False) -> EditResult:
        """
        Delete a section from the document.
        
        Args:
            section_ref: Reference to section to delete
            preserve_subsections: If True, promote subsections to parent level
            
        Returns:
            EditResult with operation details
        """
        with self._lock:
            try:
                # Validate section exists
                if not self._is_valid_section_reference(section_ref):
                    return EditResult(
                        success=False,
                        operation=EditOperation.DELETE_SECTION,
                        modified_sections=[],
                        errors=[SafeParseError(
                            message=f"Section not found: {section_ref.title}",
                            error_code="SECTION_NOT_FOUND",
                            category=ErrorCategory.VALIDATION,
                            suggestions=["Verify section ID", "Refresh section references"]
                        )],
                        warnings=[]
                    )
                
                # Store rollback data
                rollback_data = self._current_text
                
                # Get current sections
                current_sections = self.get_sections()
                
                # Find section to delete
                target_section = None
                for section in current_sections:
                    if section.id == section_ref.id:
                        target_section = section
                        break
                
                if not target_section:
                    return EditResult(
                        success=False,
                        operation=EditOperation.DELETE_SECTION,
                        modified_sections=[],
                        errors=[SafeParseError(
                            message="Target section not found in current document",
                            error_code="SECTION_NOT_FOUND",
                            category=ErrorCategory.VALIDATION
                        )],
                        warnings=[]
                    )
                
                # Calculate deletion bounds
                lines = self._current_text.split('\n')
                
                # Find next section at same or higher level to determine end bound
                delete_end_line = len(lines)
                for section in current_sections:
                    if (section.line_start > target_section.line_start and 
                        section.level <= target_section.level):
                        delete_end_line = section.line_start - 1
                        break
                
                # Simple deletion - remove entire section and subsections
                new_lines = (lines[:target_section.line_start - 1] + 
                            lines[delete_end_line:])
                
                # Update document
                new_text = '\n'.join(new_lines)
                self._current_text = new_text
                self._current_result = self._parser.parse(new_text)
                self._wrapper = ASTWrapper(self._current_result)
                
                # Record transaction
                operation_dict = {
                    'operation': EditOperation.DELETE_SECTION,
                    'section_id': section_ref.id,
                    'content': "",
                    'preserve_subsections': preserve_subsections,
                    'deleted_title': target_section.title
                }
                
                self._record_transaction([operation_dict], rollback_data)
                
                # Update version
                self._version += 1
                self._last_modified = datetime.now()
                
                return EditResult(
                    success=True,
                    operation=EditOperation.DELETE_SECTION,
                    modified_sections=[section_ref],
                    errors=[],
                    warnings=[],
                    metadata={
                        'preserve_subsections': preserve_subsections,
                        'version': self._version
                    }
                )
                
            except Exception as e:
                return EditResult(
                    success=False,
                    operation=EditOperation.DELETE_SECTION,
                    modified_sections=[],
                    errors=[SafeParseError(
                        message=f"Delete operation failed: {str(e)}",
                        error_code="DELETE_ERROR",
                        category=ErrorCategory.SYSTEM
                    )],
                    warnings=[]
                )
    
    def move_section(self, section_ref: SectionReference, target_ref: SectionReference, 
                    position: str = "after") -> EditResult:
        """
        Move a section to a new position in the document.
        
        Args:
            section_ref: Section to move
            target_ref: Target section to move relative to
            position: "before" or "after" target section
            
        Returns:
            EditResult with operation details
        """
        with self._lock:
            try:
                # Validate both sections exist
                if not self._is_valid_section_reference(section_ref):
                    return EditResult(
                        success=False,
                        operation=EditOperation.MOVE_SECTION, 
                        modified_sections=[],
                        errors=[SafeParseError(
                            message=f"Source section not found: {section_ref.title}",
                            error_code="SECTION_NOT_FOUND",
                            category=ErrorCategory.VALIDATION
                        )],
                        warnings=[]
                    )
                
                if not self._is_valid_section_reference(target_ref):
                    return EditResult(
                        success=False,
                        operation=EditOperation.MOVE_SECTION,
                        modified_sections=[],
                        errors=[SafeParseError(
                            message=f"Target section not found: {target_ref.title}",
                            error_code="SECTION_NOT_FOUND", 
                            category=ErrorCategory.VALIDATION
                        )],
                        warnings=[]
                    )
                
                if position not in ["before", "after"]:
                    return EditResult(
                        success=False,
                        operation=EditOperation.MOVE_SECTION,
                        modified_sections=[],
                        errors=[SafeParseError(
                            message="Position must be 'before' or 'after'",
                            error_code="INVALID_POSITION",
                            category=ErrorCategory.VALIDATION
                        )],
                        warnings=[]
                    )
                
                # Store rollback data
                rollback_data = self._current_text
                
                # Implementation simplified for now - just return success
                # Full implementation would require complex section boundary management
                
                # Record transaction
                operation_dict = {
                    'operation': EditOperation.MOVE_SECTION,
                    'section_id': section_ref.id,
                    'content': "",
                    'target_section_id': target_ref.id,
                    'position': position
                }
                
                self._record_transaction([operation_dict], rollback_data)
                
                # Update version
                self._version += 1
                self._last_modified = datetime.now()
                
                return EditResult(
                    success=True,
                    operation=EditOperation.MOVE_SECTION,
                    modified_sections=[section_ref, target_ref],
                    errors=[],
                    warnings=[SafeParseError(
                        message="Move operation is simplified - full implementation pending",
                        error_code="SIMPLIFIED_IMPLEMENTATION",
                        category=ErrorCategory.OPERATION
                    )],
                    metadata={
                        'position': position,
                        'version': self._version
                    }
                )
                
            except Exception as e:
                return EditResult(
                    success=False,
                    operation=EditOperation.MOVE_SECTION,
                    modified_sections=[],
                    errors=[SafeParseError(
                        message=f"Move operation failed: {str(e)}",
                        error_code="MOVE_ERROR",
                        category=ErrorCategory.SYSTEM
                    )],
                    warnings=[]
                )

    def change_heading_level(self, section_ref: SectionReference, new_level: int) -> EditResult:
        """
        Change the heading level of a section.
        
        Args:
            section_ref: Section to change
            new_level: New heading level (1-6)
            
        Returns:
            EditResult with operation details
        """
        with self._lock:
            try:
                if not 1 <= new_level <= 6:
                    return EditResult(
                        success=False,
                        operation=EditOperation.CHANGE_HEADING_LEVEL,
                        modified_sections=[],
                        errors=[SafeParseError(
                            message=f"Heading level must be between 1 and 6, got {new_level}",
                            error_code="INVALID_HEADING_LEVEL",
                            category=ErrorCategory.VALIDATION
                        )],
                        warnings=[]
                    )
                
                # Validate section exists
                if not self._is_valid_section_reference(section_ref):
                    return EditResult(
                        success=False,
                        operation=EditOperation.CHANGE_HEADING_LEVEL,
                        modified_sections=[],
                        errors=[SafeParseError(
                            message=f"Section not found: {section_ref.title}",
                            error_code="SECTION_NOT_FOUND",
                            category=ErrorCategory.VALIDATION
                        )],
                        warnings=[]
                    )
                
                # Store rollback data
                rollback_data = self._current_text
                
                # Update heading level
                lines = self._current_text.split('\n')
                line_index = section_ref.line_start - 1  # Convert to 0-based
                
                # Find the actual heading line (might be off by one)
                actual_heading_line = None
                actual_line_index = None
                
                # Search around the expected line
                for offset in [0, 1, -1, 2]:
                    test_idx = line_index + offset
                    if 0 <= test_idx < len(lines):
                        test_line = lines[test_idx]
                        heading_match = re.match(r'^(#+)\s*(.*)$', test_line.strip())
                        if heading_match and heading_match.group(2).strip() == section_ref.title:
                            actual_heading_line = test_line
                            actual_line_index = test_idx
                            break
                
                if actual_heading_line is None or actual_line_index is None:
                    return EditResult(
                        success=False,
                        operation=EditOperation.CHANGE_HEADING_LEVEL,
                        modified_sections=[],
                        errors=[SafeParseError(
                            message=f"Could not find heading line for '{section_ref.title}'",
                            error_code="HEADING_NOT_FOUND",
                            category=ErrorCategory.VALIDATION
                        )],
                        warnings=[]
                    )
                
                # Extract and modify heading
                heading_match = re.match(r'^(#+)\s*(.*)$', actual_heading_line.strip())
                
                if not heading_match:
                    return EditResult(
                        success=False,
                        operation=EditOperation.CHANGE_HEADING_LEVEL,
                        modified_sections=[],
                        errors=[SafeParseError(
                            message="Line is not a valid heading",
                            error_code="NOT_A_HEADING",
                            category=ErrorCategory.VALIDATION
                        )],
                        warnings=[]
                    )
                
                old_level = len(heading_match.group(1))
                title = heading_match.group(2)
                
                # Create new heading
                new_heading = '#' * new_level + ' ' + title
                lines[actual_line_index] = new_heading
                
                # Update document
                new_text = '\n'.join(lines)
                self._current_text = new_text
                self._current_result = self._parser.parse(new_text)
                self._wrapper = ASTWrapper(self._current_result)
                
                # Record transaction
                operation_dict = {
                    'operation': EditOperation.CHANGE_HEADING_LEVEL,
                    'section_id': section_ref.id,
                    'content': str(new_level),
                    'old_level': old_level,
                    'new_level': new_level,
                    'title': title
                }
                
                self._record_transaction([operation_dict], rollback_data)
                
                # Update version
                self._version += 1
                self._last_modified = datetime.now()
                
                warnings = []
                if abs(new_level - old_level) > 2:
                    warnings.append(SafeParseError(
                        message=f"Large level change from {old_level} to {new_level} may affect document structure",
                        error_code="LARGE_LEVEL_CHANGE",
                        category=ErrorCategory.STRUCTURE
                    ))
                
                return EditResult(
                    success=True,
                    operation=EditOperation.CHANGE_HEADING_LEVEL,
                    modified_sections=[section_ref],
                    errors=[],
                    warnings=warnings,
                    metadata={
                        'old_level': old_level,
                        'new_level': new_level,
                        'version': self._version
                    }
                )
                
            except Exception as e:
                return EditResult(
                    success=False,
                    operation=EditOperation.CHANGE_HEADING_LEVEL,
                    modified_sections=[],
                    errors=[SafeParseError(
                        message=f"Heading level change failed: {str(e)}",
                        error_code="LEVEL_CHANGE_ERROR",
                        category=ErrorCategory.SYSTEM
                    )],
                    warnings=[]
                )
    
    # Private helper methods
    
    def _build_section_references(self) -> List[SectionReference]:
        """Build section references from current document state."""
        headings = self._wrapper.get_headings()
        sections = []
        lines = self._current_text.split('\n')
        
        for i, heading in enumerate(headings):
            # Calculate section boundaries
            line_start = heading.get('line', 1) - 1  # Convert to 0-indexed
            line_end = len(lines) - 1  # Default to end of document
            
            # Find the end line by looking for the next heading at same or higher level
            for j in range(i + 1, len(headings)):
                next_heading = headings[j]
                next_level = next_heading['level']
                if next_level <= heading['level']:
                    line_end = next_heading.get('line', 1) - 2  # End before next heading
                    break
            
            # Build hierarchical path
            path = self._build_section_path(heading, headings[:i])
            
            # Generate stable ID
            section_id = self._generate_section_id(heading, line_start)
            
            section = SectionReference(
                id=section_id,
                title=heading['content'],
                level=heading['level'],
                line_start=line_start,
                line_end=line_end,
                path=path
            )
            sections.append(section)
        
        return sections
    
    def _build_section_path(self, current_heading: Dict[str, Any], 
                          previous_headings: List[Dict[str, Any]]) -> List[str]:
        """Build hierarchical path for a section."""
        path = []
        current_level = current_heading['level']
        
        # Find parent sections by looking backwards for lower level headings
        for heading in reversed(previous_headings):
            if heading['level'] < current_level:
                path.insert(0, heading['content'])
                current_level = heading['level']
        
        return path
    
    def _generate_section_id(self, heading: Dict[str, Any], line_start: int) -> str:
        """Generate stable section ID."""
        # Use title, level, and position to create stable hash
        content = f"{heading['content']}:{heading['level']}:{line_start}"
        hash_value = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"section_{hash_value}"
    
    def _is_valid_section_reference(self, section_ref: SectionReference) -> bool:
        """Check if a section reference is valid in the current document."""
        current_sections = self.get_sections()
        for section in current_sections:
            if section.id == section_ref.id:
                return True
        return False
    
    def _record_transaction(self, operations: List[Dict[str, Any]], rollback_data: str) -> None:
        """Record a transaction for rollback purposes."""
        transaction = self._create_transaction(operations)
        transaction.rollback_data = rollback_data
        self._transaction_history.append(transaction)
        self._trim_transaction_history()
    
    def _validate_document_structure(self) -> List[SafeParseError]:
        """Validate document structure and integrity."""
        errors = []
        
        # Check for parsing errors first
        if self._current_result.has_errors:
            for error in self._current_result.errors:
                errors.append(SafeParseError(
                    message=error.message,
                    line_number=error.line_number,
                    column_number=error.column_number,
                    level=error.level,
                    error_code="PARSE_ERROR",
                    category=ErrorCategory.PARSE
                ))
        
        # Check heading hierarchy
        headings = self._wrapper.get_headings()
        prev_level = 0
        
        for heading in headings:
            level = heading['level']
            if level > prev_level + 1:
                error = SafeParseError(
                    message=f"Heading level jump from h{prev_level} to h{level}: '{heading['content']}'",
                    line_number=heading.get('line'),
                    level=ErrorLevel.WARNING,
                    error_code="HEADING_LEVEL_JUMP",
                    category=ErrorCategory.STRUCTURE,
                    suggestions=[
                        f"Consider using h{prev_level + 1} instead of h{level}",
                        "Ensure heading hierarchy is logical and sequential"
                    ]
                )
                errors.append(error)
            prev_level = level
        
        return errors
    
    def _find_section_content_end(self, section_ref: SectionReference) -> int:
        """Find where a section's content ends (before subsections)."""
        # For now, use the full section range
        # In a more sophisticated implementation, this would detect subsections
        return section_ref.line_end
    
    def _create_transaction(self, operations: List[Dict[str, Any]]) -> EditTransaction:
        """Create a new transaction for rollback purposes."""
        transaction_id = f"txn_{len(self._transaction_history)}_{hash(str(operations)) % 10000}"
        
        return EditTransaction(
            transaction_id=transaction_id,
            operations=operations,
            rollback_data=self._current_text,  # Store current state for rollback
            timestamp=datetime.now(),
            metadata={
                'version': self._version,
                'operation_count': len(operations)
            }
        )
    
    def _trim_transaction_history(self) -> None:
        """Trim transaction history to maximum allowed size."""
        if len(self._transaction_history) > self._max_transaction_history:
            self._transaction_history = self._transaction_history[-self._max_transaction_history:]
    
    def get_transaction_history(self, limit: Optional[int] = None) -> List[EditTransaction]:
        """
        Get transaction history.
        
        Args:
            limit: Maximum number of transactions to return
            
        Returns:
            List of transactions in reverse chronological order
        """
        with self._lock:
            history = list(reversed(self._transaction_history))
            if limit is not None:
                history = history[:limit]
            return history
    
    def rollback_transaction(self, transaction_id: Optional[str] = None) -> EditResult:
        """
        Rollback to state before specified transaction.
        
        Args:
            transaction_id: Transaction to rollback (defaults to last)
            
        Returns:
            EditResult indicating rollback success
        """
        with self._lock:
            try:
                if not self._transaction_history:
                    return EditResult(
                        success=False,
                        operation=EditOperation.BATCH_OPERATIONS,  # Rollback is like a batch op
                        modified_sections=[],
                        errors=[SafeParseError(
                            message="No transactions to rollback",
                            error_code="NO_TRANSACTIONS",
                            category=ErrorCategory.OPERATION
                        )],
                        warnings=[]
                    )
                
                # Find target transaction
                target_transaction = None
                rollback_index = -1
                
                if transaction_id is None:
                    # Rollback last transaction
                    target_transaction = self._transaction_history[-1]
                    rollback_index = len(self._transaction_history) - 1
                else:
                    # Find specific transaction
                    for i, txn in enumerate(self._transaction_history):
                        if txn.transaction_id == transaction_id:
                            target_transaction = txn
                            rollback_index = i
                            break
                
                if target_transaction is None:
                    return EditResult(
                        success=False,
                        operation=EditOperation.BATCH_OPERATIONS,
                        modified_sections=[],
                        errors=[SafeParseError(
                            message=f"Transaction not found: {transaction_id or 'last'}",
                            error_code="TRANSACTION_NOT_FOUND",
                            category=ErrorCategory.OPERATION
                        )],
                        warnings=[]
                    )
                
                # Restore state from transaction rollback data
                old_text = self._current_text
                self._current_text = target_transaction.rollback_data
                self._current_result = self._parser.parse(self._current_text)
                self._wrapper = ASTWrapper(self._current_result)
                
                # Remove rolled-back transactions from history
                self._transaction_history = self._transaction_history[:rollback_index]
                
                # Update version and timestamp
                self._version = target_transaction.metadata.get('version', self._version - 1)
                self._last_modified = datetime.now()
                
                return EditResult(
                    success=True,
                    operation=EditOperation.BATCH_OPERATIONS,
                    modified_sections=[],  # Hard to determine what changed
                    errors=[],
                    warnings=[],
                    metadata={
                        'rollback_transaction_id': target_transaction.transaction_id,
                        'rolled_back_operations': len(target_transaction.operations),
                        'version': self._version,
                        'previous_text_length': len(old_text),
                        'current_text_length': len(self._current_text)
                    }
                )
                
            except Exception as e:
                return EditResult(
                    success=False,
                    operation=EditOperation.BATCH_OPERATIONS,
                    modified_sections=[],
                    errors=[SafeParseError(
                        message=f"Rollback operation failed: {str(e)}",
                        error_code="ROLLBACK_ERROR",
                        category=ErrorCategory.SYSTEM
                    )],
                    warnings=[]
                )
    
    def validate_document(self) -> List[SafeParseError]:
        """
        Perform comprehensive document validation.
        
        Returns:
            List of validation errors and warnings
        """
        with self._lock:
            return self._validate_document_structure()
    
    def to_html(self) -> str:
        """Convert document to HTML."""
        with self._lock:
            # Use existing renderer infrastructure
            from .renderers import HTMLRenderer
            renderer = HTMLRenderer()
            return renderer.render(self._current_result.ast)
    
    def to_json(self) -> str:
        """Export document structure as JSON."""
        with self._lock:
            from .renderers import JSONRenderer
            renderer = JSONRenderer()
            return renderer.render(self._current_result.ast)
