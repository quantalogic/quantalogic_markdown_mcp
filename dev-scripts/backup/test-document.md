# Test Document for MCP

This is a sample document for testing the SafeMarkdownEditor MCP server.

## Introduction

This document serves as a hands-on playground for exploring the SafeMarkdownEditor MCP server. Here, you can try out all the core and advanced features in a safe environment.

**How to use this document:**

- Follow the examples and checklists to test each feature
- Add, edit, or remove sections to see live updates
- Use the code and table samples to verify formatting and content handling
- Refer to the troubleshooting tips if you encounter issues

Feel free to experiment and make changes—this document is designed for learning and validation. Each section highlights a different capability of the MCP server, making it easy to test and understand the available tools.

## Features to Test

### Basic Operations

- Document loading
- Section listing
- Content retrieval

### Advanced Operations

- Section insertion
- Section deletion
- Section moving
- Content updating

## Sample Content

### Code Examples

Here's a simple Python function:

```python
def hello_world():
    print("Hello from MCP!")
    return "success"
```

## Deep Nesting Test

#### Level 4 Heading

Content at level 4 with indentation: - Indented content under level 4 - More indented content

##### Level 5 Heading

Even deeper content: - Deeply indented - Content here

###### Level 6 Heading (Maximum)

Maximum depth content: - Very deep indentation - Testing extreme nesting

### Lists and Tables

**Task List:**

- [x] Set up MCP server
- [x] Test basic operations
- [x] Test advanced operations
- [x] Test edge cases
- [x] Fix all identified issues
- [x] Document findings

**Feature Comparison - Final Results:**

| Feature          | Status | Notes                          |
| ---------------- | ------ | ------------------------------ |
| Load Document    | ✅     | Working perfectly              |
| Save Document    | ✅     | Working perfectly              |
| List Sections    | ✅     | Working perfectly              |
| Insert Section   | ✅     | Working perfectly              |
| Update Section   | ✅     | Working perfectly              |
| Delete Section   | ✅     | **FIXED** - Now working        |
| Move Section     | ✅     | **FIXED** - Now working        |
| Get Section      | ✅     | Working perfectly              |
| Analyze Document | ✅     | Working perfectly              |
| Error Handling   | ✅     | **IMPROVED** - Proper messages |

**Edge Cases Tested:**

- ✅ Empty content insertion
- ✅ Special characters in headings
- ✅ Very long content blocks
- ✅ Nested heading levels (up to level 6)
- ✅ Invalid position handling
- ✅ Non-existent section operations
- ✅ Section movement functionality

3.  **Indented horizontal rules:**
    Normal rule:

    ***

        Indented rule (4 spaces):
        ---

            Deeply indented rule (8 spaces):
            ---

4.  **Indented links and images:**

    - [Normal link](http://example.com)
      - [Indented link](http://example.com)
        - [Deeply indented link](http://example.com)
          - [Very deep link](http://example.com)

5.  **Indented emphasis:**

    - **Bold text**
      - **Indented bold**
        - **_Indented bold italic_**
          - ~~Indented strikethrough~~

6.  **Footnote-style with indentation:**
    Main text[1]

        [1]: This footnote is indented
             with multiple lines
             all properly aligned

## Conclusion

This document provides a good foundation for testing MCP functionality. Feel free to modify, add, or remove sections to test the various tools available.

---

## Appendix

### Troubleshooting

If you encounter issues, check the MCP server logs in VSCode.

### Additional Resources

- MCP Documentation
- VSCode Extension Documentation
