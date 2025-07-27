"""
Additional edge case tests for SafeMarkdownEditor to maximize coverage.
"""

import threading
from quantalogic_markdown_mcp import (
    SafeMarkdownEditor,
    ValidationLevel,
    EditOperation
)


class TestSafeMarkdownEditorEdgeCases:
    """Edge case tests for SafeMarkdownEditor."""
    
    def test_empty_document_operations(self):
        """Test operations on empty document."""
        editor = SafeMarkdownEditor("", ValidationLevel.NORMAL)
        
        # Should handle empty document gracefully
        sections = editor.get_sections()
        assert len(sections) == 0
        
        stats = editor.get_statistics()
        assert stats.total_sections == 0
        assert stats.word_count == 0
        
        # Validation should work on empty document
        errors = editor.validate_document()
        assert isinstance(errors, list)
    
    def test_single_heading_document(self):
        """Test document with single heading."""
        editor = SafeMarkdownEditor("# Single Heading", ValidationLevel.NORMAL)
        
        sections = editor.get_sections()
        assert len(sections) == 1
        assert sections[0].title == "Single Heading"
        assert sections[0].level == 1
    
    def test_document_with_only_content_no_headings(self):
        """Test document with content but no headings."""
        editor = SafeMarkdownEditor("Just some content\nwith multiple lines.", ValidationLevel.NORMAL)
        
        sections = editor.get_sections()
        assert len(sections) == 0
        
        stats = editor.get_statistics()
        assert stats.total_sections == 0
        assert stats.word_count > 0  # Should still count words
    
    def test_malformed_headings(self):
        """Test handling of malformed headings."""
        malformed = """# Valid Heading
        
##Invalid - no space
# # Double space
###    Multiple spaces
        
## Valid Heading 2"""
        
        editor = SafeMarkdownEditor(malformed, ValidationLevel.PERMISSIVE)
        sections = editor.get_sections()
        
        # Should still parse valid headings
        valid_titles = [s.title for s in sections if s.title in ["Valid Heading", "Valid Heading 2"]]
        assert len(valid_titles) >= 2
    
    def test_very_deep_heading_hierarchy(self):
        """Test with maximum heading depth."""
        deep_markdown = """# Level 1
## Level 2  
### Level 3
#### Level 4
##### Level 5
###### Level 6"""
        
        editor = SafeMarkdownEditor(deep_markdown, ValidationLevel.NORMAL)
        sections = editor.get_sections()
        
        assert len(sections) == 6
        levels = [s.level for s in sections]
        assert levels == [1, 2, 3, 4, 5, 6]
        
        stats = editor.get_statistics()
        assert stats.max_heading_depth == 6
    
    def test_sections_with_special_characters(self):
        """Test sections with special characters in titles."""
        special_chars = """# Section with "quotes"
## Section with *asterisks*
### Section with [brackets]
#### Section with `code`
##### Section with & ampersand"""
        
        editor = SafeMarkdownEditor(special_chars, ValidationLevel.NORMAL)
        sections = editor.get_sections()
        
        assert len(sections) == 5
        # Should preserve special characters in titles
        titles = [s.title for s in sections]
        assert 'Section with "quotes"' in titles
        assert 'Section with *asterisks*' in titles
    
    def test_update_section_preserve_subsections_false(self):
        """Test update_section_content with preserve_subsections=False."""
        markdown = """# Main
## Section A
Content A
### Subsection A1
Content A1
### Subsection A2  
Content A2
## Section B"""
        
        editor = SafeMarkdownEditor(markdown, ValidationLevel.NORMAL)
        sections = editor.get_sections()
        section_a = None
        
        for section in sections:
            if section.title == "Section A":
                section_a = section
                break
        
        assert section_a is not None
        
        # Update without preserving subsections
        result = editor.update_section_content(
            section_a, 
            "New content for A", 
            preserve_subsections=False
        )
        
        assert result.success is True
        
        # Subsections should be affected
        new_content = editor.to_markdown()
        assert "New content for A" in new_content
    
    def test_insert_section_auto_adjust_level(self):
        """Test insert_section_after with auto level adjustment."""
        markdown = """# Main
## Section A
### Subsection A1"""
        
        editor = SafeMarkdownEditor(markdown, ValidationLevel.NORMAL)
        sections = editor.get_sections()
        main_section = sections[0]
        
        # Try to insert level 1 after main (should auto-adjust to 2)
        result = editor.insert_section_after(
            main_section,
            level=1,  # Will be adjusted to 2
            title="New Section",
            content="New content",
            auto_adjust_level=True
        )
        
        assert result.success is True
        
        # Verify level was adjusted
        new_sections = editor.get_sections()
        new_section = None
        for section in new_sections:
            if section.title == "New Section":
                new_section = section
                break
        
        assert new_section is not None
        assert new_section.level == 2  # Should be adjusted from 1 to 2
    
    def test_change_heading_level_with_warnings(self):
        """Test change_heading_level that triggers warnings."""
        editor = SafeMarkdownEditor("# Main\n## Section A", ValidationLevel.NORMAL)
        sections = editor.get_sections()
        section_a = sections[1]
        
        # Change from level 2 to level 5 (large jump)
        result = editor.change_heading_level(section_a, 5)
        
        assert result.success is True
        assert len(result.warnings) > 0
        
        # Should warn about large level change
        warning_messages = [w.message for w in result.warnings]
        large_change_warning = any("large level change" in msg.lower() for msg in warning_messages)
        assert large_change_warning
    
    def test_transaction_history_trimming(self):
        """Test transaction history trimming."""
        editor = SafeMarkdownEditor("# Test", ValidationLevel.NORMAL)
        
        # Force small transaction history limit for testing
        original_limit = editor._max_transaction_history
        editor._max_transaction_history = 3
        
        try:
            # Perform more operations than the limit
            for i in range(5):
                result = editor.insert_section_after(
                    editor.get_sections()[0],
                    level=2,
                    title=f"Section {i}",
                    content=f"Content {i}"
                )
                assert result.success is True
            
            # History should be trimmed
            history = editor.get_transaction_history()
            assert len(history) <= 3
            
        finally:
            # Restore original limit
            editor._max_transaction_history = original_limit
    
    def test_rollback_with_invalid_transaction_id(self):
        """Test rollback_transaction with invalid transaction ID."""
        editor = SafeMarkdownEditor("# Test", ValidationLevel.NORMAL)
        
        # Perform an operation to create transaction
        sections = editor.get_sections()
        editor.insert_section_after(sections[0], level=2, title="New", content="content")
        
        # Try to rollback non-existent transaction
        result = editor.rollback_transaction("invalid_transaction_id")
        
        assert result.success is False
        assert len(result.errors) > 0
        assert "not found" in result.errors[0].message.lower()
    
    def test_validation_with_parse_errors(self):
        """Test document validation when parse errors exist."""
        # Create editor with content that might have parse issues
        editor = SafeMarkdownEditor("# Test\n\n```\nUnclosed code block", ValidationLevel.STRICT)
        
        errors = editor.validate_document()
        # Should handle any parse errors gracefully
        assert isinstance(errors, list)
    
    def test_statistics_after_modifications(self):
        """Test that statistics update correctly after modifications."""
        editor = SafeMarkdownEditor("# Test\n\nInitial content.", ValidationLevel.NORMAL)
        
        initial_stats = editor.get_statistics()
        assert initial_stats.edit_count == 0
        
        # Make an edit
        sections = editor.get_sections()
        editor.update_section_content(sections[0], "Modified content with more words.")
        
        updated_stats = editor.get_statistics()
        assert updated_stats.edit_count == 1
        assert updated_stats.word_count >= initial_stats.word_count
    
    def test_preview_operation_edge_cases(self):
        """Test preview_operation with edge cases."""
        editor = SafeMarkdownEditor("# Test", ValidationLevel.NORMAL)
        sections = editor.get_sections()
        
        # Test with empty content
        result = editor.preview_operation(
            EditOperation.UPDATE_SECTION,
            section_ref=sections[0],
            content=""
        )
        assert result.success is True
        
        # Test with very long content
        long_content = "Very long content. " * 1000
        result = editor.preview_operation(
            EditOperation.UPDATE_SECTION,
            section_ref=sections[0],
            content=long_content
        )
        assert result.success is True
    
    def test_export_methods_with_modified_content(self):
        """Test export methods after content modifications."""
        editor = SafeMarkdownEditor("# Original\n\nOriginal content.", ValidationLevel.NORMAL)
        
        # Modify content
        sections = editor.get_sections()
        editor.update_section_content(sections[0], "**Modified** content with formatting.")
        
        # Test all export methods
        markdown = editor.to_markdown()
        assert "**Modified**" in markdown
        
        html = editor.to_html()
        assert len(html) > 0
        
        json_str = editor.to_json()
        assert len(json_str) > 0
    
    def test_concurrent_access_with_rollback(self):
        """Test concurrent access during rollback operations."""
        editor = SafeMarkdownEditor("# Test\n\nContent.", ValidationLevel.NORMAL)
        
        # Make initial change
        sections = editor.get_sections()
        editor.update_section_content(sections[0], "Modified content")
        
        results = []
        errors = []
        
        def concurrent_operations(thread_id):
            try:
                if thread_id == 0:
                    # Thread 0 does rollback
                    result = editor.rollback_transaction()
                    results.append(('rollback', result.success))
                else:
                    # Other threads try to read
                    sections = editor.get_sections()
                    results.append(('read', len(sections)))
            except Exception as e:
                errors.append(f"Thread {thread_id}: {e}")
        
        # Run concurrent operations
        threads = []
        for i in range(3):
            thread = threading.Thread(target=concurrent_operations, args=(i,))
            threads.append(thread)
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Should not have any errors
        assert len(errors) == 0
        assert len(results) == 3
    
    def test_helper_method_coverage(self):
        """Test various helper methods indirectly."""
        markdown = """# Main Document

Content here.

## Section A

### Subsection A1

Content for A1.

## Section B"""
        
        editor = SafeMarkdownEditor(markdown, ValidationLevel.NORMAL)
        
        # Test _build_section_references through get_sections
        sections = editor.get_sections()
        assert len(sections) > 0
        
        # All sections should have proper IDs
        for section in sections:
            assert section.id.startswith("section_")
            assert len(section.id) > 8
        
        # Test _generate_section_id consistency
        # Same content should generate same ID
        sections1 = editor.get_sections()
        sections2 = editor.get_sections()
        
        for s1, s2 in zip(sections1, sections2):
            assert s1.id == s2.id
    
    def test_section_boundary_detection(self):
        """Test section boundary detection in complex documents."""
        complex_markdown = """# Main

Content before section A.

## Section A

Content for section A.

Some more content.

### Subsection A1

Content for A1.

### Subsection A2

Content for A2.

## Section B

Content for section B."""
        
        editor = SafeMarkdownEditor(complex_markdown, ValidationLevel.NORMAL)
        sections = editor.get_sections()
        
        # Verify line boundaries make sense
        for i, section in enumerate(sections):
            assert section.line_start >= 0  # 0-based indexing is valid
            assert section.line_end >= section.line_start
            
            # Next section should start after current section
            if i < len(sections) - 1:
                next_section = sections[i + 1]
                assert next_section.line_start > section.line_start
    
    def test_error_recovery(self):
        """Test error recovery in various scenarios."""
        editor = SafeMarkdownEditor("# Test", ValidationLevel.NORMAL)
        
        # Test recovery from failed operations - create an invalid section reference
        from quantalogic_markdown_mcp.safe_editor_types import SectionReference
        fake_section = SectionReference(
            id="invalid_id",
            title="Fake",
            level=1,
            line_start=999,  # Invalid line numbers
            line_end=1000,
            path=[]
        )
        
        # Operation should fail gracefully
        result = editor.update_section_content(fake_section, "test")
        assert result.success is False
        assert len(result.errors) > 0
        
        # Editor should still be in valid state
        sections = editor.get_sections()
        assert len(sections) == 1
        assert sections[0].title == "Test"
