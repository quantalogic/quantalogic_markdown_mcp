"""Test utilities for stateless operations."""

import tempfile
from pathlib import Path
from typing import Dict, Any


class StatelessTestHelper:
    """Helper class for testing stateless operations."""
    
    @staticmethod
    def create_temp_document(content: str) -> Path:
        """Create a temporary document for testing."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
        temp_file.write(content)
        temp_file.close()
        return Path(temp_file.name)
    
    @staticmethod
    def create_sample_document() -> str:
        """Create sample document content for testing."""
        return """# Test Document

## Introduction
This is a test document.

## Features
- Feature 1
- Feature 2

## Conclusion
End of document.
"""
    
    @staticmethod
    def assert_operation_success(result: Dict[str, Any], expected_message: str = None):
        """Assert that an operation was successful."""
        assert result["success"] is True, f"Operation failed: {result.get('error', 'Unknown error')}"
        if expected_message:
            assert expected_message in result.get("message", ""), f"Expected message not found: {result}"
    
    @staticmethod
    def assert_operation_failure(result: Dict[str, Any], expected_error: str = None):
        """Assert that an operation failed as expected."""
        assert result["success"] is False, f"Operation should have failed but succeeded: {result}"
        if expected_error:
            error_msg = result.get("error", {})
            if isinstance(error_msg, dict):
                error_msg = error_msg.get("message", str(error_msg))
            assert expected_error in str(error_msg), f"Expected error not found: {result}"
