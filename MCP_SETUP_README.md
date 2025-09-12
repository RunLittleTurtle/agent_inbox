# MCP Server Setup for LangGraph Documentation Access

This guide explains how to set up the MCP (Model Context Protocol) server to provide Claude Code with access to LangGraph and LangChain documentation.

## Prerequisites

Make sure you have `uvx` installed (part of uv):
```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with pip
pip install uv
```

## Setup Instructions

### 1. MCP Configuration File

The `mcp.json` file is already created in the root directory with the following configuration:

```json
{
  "langgraph-docs-mcp": {
    "command": "uvx",
    "args": [
      "--from",
      "mcpdoc",
      "mcpdoc",
      "--urls",
      "LangGraph Python:https://langchain-ai.github.io/langgraph/llms.txt LangGraph JS:https://langchain-ai.github.io/langgraphjs/llms.txt LangChain Python:https://python.langchain.com/llms.txt LangChain JS:https://js.langchain.com/llms.txt",
      "--transport",
      "stdio"
    ]
  }
}
```

### 2. Integration with Claude Code

To use this MCP server with Claude Code:

1. **Copy the MCP configuration to Claude Code's config directory:**
   ```bash
   # Find Claude Code's config directory
   # Usually ~/.claude/ or similar

   # Copy or merge the mcp.json content into Claude Code's MCP servers configuration
   ```

2. **Alternative: Use environment variable:**
   ```bash
   # Set the MCP_SERVERS_FILE environment variable
   export MCP_SERVERS_FILE="$(pwd)/mcp.json"

   # Start Claude Code
   claude
   ```

### 3. Available Documentation Sources

The MCP server provides access to:

- **LangGraph Python**: Core graph functionality, state management, routing
- **LangGraph JS**: JavaScript implementation (for reference)
- **LangChain Python**: Tool integration, model management, chains
- **LangChain JS**: JavaScript implementation (for reference)

### 4. Testing the MCP Connection

You can test if the MCP server is working by:

1. **Manual testing:**
   ```bash
   # Test the mcpdoc tool directly
   uvx --from mcpdoc mcpdoc --urls "LangGraph Python:https://langchain-ai.github.io/langgraph/llms.txt" --transport stdio
   ```

2. **Within Claude Code:**
   - Ask Claude Code to search for LangGraph documentation
   - Request specific implementation examples
   - Ask about best practices for state management

### 5. Usage Examples

Once configured, you can ask Claude Code:

```
"Show me examples of LangGraph StateGraph implementation"
"What are the best practices for LangGraph state management?"
"How do I implement human-in-the-loop with LangGraph?"
"Find documentation about LangGraph create_react_agent"
```

## Troubleshooting

### Common Issues

1. **uvx not found:**
   ```bash
   # Install uv and uvx
   pip install uv
   ```

2. **MCP server connection timeout:**
   - Check internet connectivity
   - Verify the documentation URLs are accessible
   - Try with a single URL first for testing

3. **Claude Code not finding MCP config:**
   - Verify the path to mcp.json
   - Check Claude Code's documentation for MCP server configuration
   - Ensure proper JSON formatting

### Debug Commands

```bash
# Test individual documentation access
curl -s https://langchain-ai.github.io/langgraph/llms.txt | head -20

# Test mcpdoc installation
uvx --from mcpdoc mcpdoc --help

# Validate JSON configuration
python -m json.tool mcp.json
```

## Benefits

With this setup, Claude Code will have:

1. **Contextual documentation access**: Real-time access to the latest LangGraph patterns
2. **Smart documentation retrieval**: Fetch only relevant sections based on context
3. **Multi-source knowledge**: Access to both LangGraph and LangChain documentation
4. **Reduced context window usage**: Fetch specific information instead of loading entire docs

This complements the comprehensive guidance in `CLAUDE.md` by providing access to detailed documentation when needed.
