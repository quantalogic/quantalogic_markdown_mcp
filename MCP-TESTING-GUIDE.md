# MCP Testing Guide for VSCode

This guide will help you test the SafeMarkdownEditor MCP server in VSCode.

## 🚀 Quick Start

1. **Ensure Prerequisites:**
   - VSCode 1.102 or later ✅
   - GitHub Copilot extension installed ✅
   - MCP configuration added (`.vscode/mcp.json`) ✅

2. **Verify MCP Server:**
   - Open Command Palette (`Cmd+Shift+P` / `Ctrl+Shift+P`)
   - Run: `MCP: List Servers`
   - You should see "markdown-editor" in the list

## 📋 Testing Steps

### Step 1: Check Server Status
1. Go to Extensions view (`Cmd+Shift+X` / `Ctrl+Shift+X`)
2. Look for "MCP SERVERS - INSTALLED" section
3. Find "markdown-editor" server
4. Status should be green (running)

### Step 2: Enable Agent Mode
1. Open Chat view (`Cmd+Ctrl+I` / `Ctrl+Alt+I`)
2. Select **Agent mode** from the dropdown
3. Click the **Tools** button
4. Enable markdown-editor tools

### Step 3: Test Basic Operations

**Load the test document:**
```
Load the test-document.md file and show me all sections
```

**List sections:**
```
Show me all the sections in the current document
```

**Get document info:**
```
Get information about the currently loaded file
```

### Step 4: Test Advanced Operations

**Insert a new section:**
```
Create a new section called "Testing Results" after the "Features to Test" section
```

**Update section content:**
```
Update the "Introduction" section to mention that this is for MCP testing in VSCode
```

**Move a section:**
```
Move the "Conclusion" section to be the second section in the document
```

**Delete a section:**
```
Delete the "Appendix" section
```

### Step 5: Test File Operations

**Save document:**
```
Save the modified document to ./test-results.md with backup enabled
```

**Test path resolution:**
```
Test if the path ~/Desktop/test.md would resolve correctly
```

## 🔧 Troubleshooting

### Server Not Appearing
1. Check `.vscode/mcp.json` exists and is valid
2. Restart VSCode
3. Use `MCP: List Servers` to check status

### Tools Not Available
1. Confirm Agent mode is selected
2. Click Tools button to enable markdown-editor tools
3. Check Extensions view for server status

### Server Not Starting
1. Right-click server → Show Output
2. Check terminal output for errors
3. Run test: `uv run python -c "from quantalogic_markdown_mcp.mcp_server import mcp"`

### Debug Mode
1. Server is configured with file watching enabled
2. Changes to `src/**/*.py` will restart the server
3. Check server logs in Extensions view

## 📁 Files Created for Testing

- `.vscode/mcp.json` - MCP server configuration
- `.vscode/settings.json` - Workspace settings
- `.vscode/tasks.json` - Build and test tasks
- `test-document.md` - Sample document for testing
- `MCP-TESTING-GUIDE.md` - This guide

## ⚡ Quick Commands

**VSCode Commands:**
- `MCP: List Servers` - View configured servers
- `MCP: Browse Resources` - View available resources
- Terminal → `Run Task` → "Start MCP Server"

**Chat Examples:**
- "Load README.md and summarize its sections"
- "Add a new section about testing to the document"
- "Show me the document structure"
- "Save the current document with a backup"

## 📝 Notes

- The server runs in development mode with file watching
- Changes to Python files will automatically restart the server
- All operations are atomic and support undo
- The server maintains transaction history for rollbacks

Happy testing! 🎉
