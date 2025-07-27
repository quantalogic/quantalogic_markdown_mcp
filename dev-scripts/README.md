# Development Scripts

This directory contains development and testing scripts used during the development of the Quantalogic Markdown MCP project. These are separate from the formal test suite in the `../tests/` directory.

## Purpose

These scripts serve different purposes:

- **Integration Testing**: Scripts that test the full system integration
- **Manual Validation**: Scripts for manual testing and validation during development
- **MCP Server Testing**: Scripts specifically for testing Model Context Protocol functionality
- **Deployment Testing**: Scripts for validating deployment readiness
- **Debugging**: Utilities for debugging specific functionality

## Categories

### Test Scripts (`test_*.py`)
- `test_api_compliance.py` - API compliance validation
- `test_mcp_comprehensive.py` - Comprehensive MCP functionality testing
- `test_mcp_direct.py` - Direct MCP server testing
- `test_mcp_functionality.py` - MCP functionality validation
- `test_mcp_server.py` - Basic MCP server testing
- `test_mcp_validation.py` - MCP validation testing
- `test_safe_editor.py` - Manual SafeMarkdownEditor testing
- `test_section_operations.py` - Section operations testing
- `test_section_ops.py` - Additional section operations testing
- `test_transactions.py` - Transaction handling testing

### MCP Server Scripts
- `mcp_server_main.py` - Main MCP server entry point
- `run_mcp_server.py` - Script to run the MCP server

### Development Utilities
- `debug_heading.py` - Debug utility for heading operations
- `deployment_test.py` - Final deployment validation script

## Running Scripts

All scripts can be run directly from this directory:

```bash
cd dev-scripts
python test_mcp_server.py
python deployment_test.py
# etc.
```

The scripts automatically handle import paths to access the main codebase in `../src/`.

## Difference from `../tests/`

- **`../tests/`**: Formal test suite using pytest framework, run by CI/CD
- **`dev-scripts/`**: Development and integration testing scripts, manual execution

## Note

These scripts were moved from the project root directory to improve project organization and reduce clutter. They maintain the same functionality but now have proper relative import paths.
