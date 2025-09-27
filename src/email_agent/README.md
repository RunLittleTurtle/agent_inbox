# Email Agent - Gmail MCP Integration

Professional email management agent with Gmail MCP tools for comprehensive email operations.

## Quick Start

### 1. Copy Template
```bash
cp -r src/_react_agent_mcp_template src/{your_agent}_agent
cd src/{your_agent}_agent
```

### 2. Configure Environment
```bash
# Add to .env
PIPEDREAM_MCP_SERVER_{SERVICE_NAME}=https://mcp.pipedream.net/{your-id}/{service}
ANTHROPIC_API_KEY=your_key
USER_TIMEZONE=America/Toronto  # Centralized timezone for all agents
```

### 3. Customize Files

#### `config.py` (centralized configuration):
```python
AGENT_NAME = "gmail"  # Your agent name
AGENT_DISPLAY_NAME = "Gmail"  # Display name
AGENT_DESCRIPTION = "email management"  # What your agent does
MCP_SERVICE = "google_gmail"  # MCP service name
```

#### `tools.py`:
```python
USEFUL_TOOL_NAMES = {
    'gmail-send-email',
    'gmail-find-email',
    # Add tools from https://mcp.pipedream.com/app/{service}
    # OR use the tool discovery script to get exact names (see below)
}
```

#### `x_agent_orchestrator.py`:
```python
def create_gmail_agent():  # Replace {agent} with your agent name
    return create_default_orchestrator()
```

### 4. Add Configuration UI Support

**IMPORTANT**: For the configuration UI to work, you must:

1. **Update API endpoints** in `agent-inbox/src/pages/api/config/`:
   - Add your agent path to `AGENT_CONFIG_PATHS` in `agents.ts`
   - Add reading logic to `values.ts`
   - Add writing logic to `update.ts`

2. **Replace ALL placeholder values** in `config.py`:
   - `{AGENT_NAME}` → actual agent name
   - `{AGENT_DISPLAY_NAME}` → display name
   - `{AGENT_DESCRIPTION}` → description
   - `{MCP_SERVICE}` → MCP service name

3. **Only include implemented fields** in `ui_config.py`

See `../../MCP_AGENT_CONFIGURATION_GUIDE.md` for complete instructions.

### 5. Add to Supervisor

Copy the code from `supervisor_snippet_connection.md` and add it to `src/graph.py`.

The snippet includes:
- Agent creation function with MCP integration
- Fallback handling for errors
- Instructions for adding to supervisor agents list
- Supervisor prompt updates

## Tool Discovery - NEW FEATURE ✨

### Automatic Tool Discovery

The template now includes automatic MCP tool discovery following langchain-mcp-adapters best practices. No more guessing tool names!

#### Method 1: Discovery Script (Recommended)
```bash
# Discover all available tools with formatted output
python discover_tools.py --format copy-paste

# Save results to file
python discover_tools.py --save discovered_tools.txt

# Get JSON output for programmatic use
python discover_tools.py --format json

# Quick validation of environment
python discover_tools.py --validate-env
```

#### Method 2: Direct Script Execution
```bash
# Run tools.py directly to see all available tools
python tools.py
```

#### Method 3: Programmatic Discovery
```python
from tools import discover_mcp_tools_sync, print_discovered_tools

# Get tool info as list of dicts
tools_info = discover_mcp_tools_sync()

# Print formatted output
print_discovered_tools()

# Async version
tools_info = await discover_mcp_tools()
```

### Best Practice Workflow

1. **Configure your agent** in `config.py`
2. **Run tool discovery**: `python discover_tools.py --format copy-paste`
3. **Copy tool names** to `USEFUL_TOOL_NAMES` in `tools.py`
4. **Test your agent** to ensure tools work
5. **Deploy** with confidence

### Tool Discovery Output Example

```bash
🔍 Discovering GMAIL MCP Tools...
============================================================
✅ Discovered 15 tools:

📋 Copy these lines to your USEFUL_TOOL_NAMES:
USEFUL_TOOL_NAMES = {
    # Email Management
    'gmail-send-email',  # Send an email via Gmail
    'gmail-find-email',  # Search for emails in Gmail
    
    # Label Operations  
    'gmail-list-labels',  # List all Gmail labels
    'gmail-create-label',  # Create a new Gmail label
}
```

## File Structure

- **`config.py`**: Centralized configuration (agent details, LLM config, timezone handling)
- **`tools.py`**: MCP connection + tool configuration + discovery functions
- **`discover_tools.py`**: **NEW** - Standalone tool discovery script
- **`x_agent_orchestrator.py`**: React agent orchestrator
- **`prompt.py`**: System prompt
- **`schemas.py`**: Data structures (optional)
- **`human_inbox.py`**: Human-in-the-loop integration
- **`supervisor_snippet_connection.md`**: Supervisor setup guide

## Available Services

Based on your environment variables:

```bash
# Google Services
PIPEDREAM_MCP_SERVER_google_gmail          # Gmail
PIPEDREAM_MCP_SERVER_google_sheets         # Sheets
PIPEDREAM_MCP_SERVER_google_drive          # Drive
PIPEDREAM_MCP_SERVER_google_docs           # Docs
PIPEDREAM_MCP_SERVER_google_calendar       # Calendar
PIPEDREAM_MCP_SERVER_google_contacts       # Contacts

# Other Services
PIPEDREAM_MCP_SERVER_shopify               # Shopify
PIPEDREAM_MCP_SERVER_linkedin              # LinkedIn
PIPEDREAM_MCP_SERVER_coda                  # Coda
```

## Key Patterns

### MCP Connection Pattern
- Environment variable: `PIPEDREAM_MCP_SERVER_{SERVICE_NAME}`
- 5-minute tool caching for performance
- Clear error messages (no graceful fallbacks)
- 30-second timeout for MCP connections

### Tool Discovery Pattern **NEW**
- Use `discover_tools.py` script for tool name discovery
- Built on langchain-mcp-adapters best practices
- MCP protocol with pagination support
- Multiple output formats (table, JSON, copy-paste)
- Programmatic and command-line interfaces

### React Agent Pattern
- Uses `create_react_agent` for MessagesState compatibility
- Automatic supervisor integration
- Time-aware prompts with timezone context
- Clear tool availability feedback

### Supervisor Integration
- Function name MUST match: `create_{agent}_agent()`
- Returns `CompiledStateGraph` compatible with supervisor
- Clear error handling (agent_fallback pattern for failures)
- No graceful fallbacks - easier debugging

## Testing

### Test MCP Connection
```python
from tools import get_agent_simple_tools
tools = get_agent_simple_tools()
print(f'Loaded {len(tools)} tools: {[t.name for t in tools]}')
```

### Test Agent Creation
```python
from x_agent_orchestrator import create_{agent}_agent
agent = create_{agent}_agent()
print(f'Agent created: {type(agent)}')
```

### Test Supervisor Integration
```python
import asyncio
from src.graph import create_supervisor_graph
supervisor = asyncio.run(create_supervisor_graph())
```

## Design Principles

1. **KISS**: Keep it simple, essentials only
2. **Clear Errors**: No graceful fallbacks, clear error messages
3. **MessagesState**: Use standard state, avoid custom state classes
4. **Supervisor Ready**: Automatic integration with supervisor routing
5. **MCP First**: Leverage Pipedream MCP tools, add local tools sparingly
6. **Tool Discovery**: Use automatic discovery to find exact tool names

## Common Issues

### MCP Connection Fails
- Check environment variable name matches pattern
- Verify Pipedream server URL is correct
- Check network connectivity

### Supervisor Integration Fails
- Verify function name: `create_{agent}_agent()`
- Check MessagesState compatibility
- Ensure proper error handling

### Tool Loading Fails
- Check USEFUL_TOOL_NAMES matches available tools
- Visit https://mcp.pipedream.com/app/{service} for tool list
- Verify timeout settings

## Advanced Features

### Human-in-the-Loop
Use `human_inbox.py` for operations requiring approval:
```python
from human_inbox import create_human_interrupt

create_human_interrupt(
    action="send_email",
    args={"to": "user@example.com", "subject": "Test"},
    description="Send email to user"
)
```

### Custom Schemas
Only add to `schemas.py` if you need domain-specific data structures:
```python
class EmailData(BaseModel):
    id: str
    subject: str
    content: str
```

### Local Tools
Add local tools in `tools.py`:
```python
@tool
def custom_local_tool(query: str) -> str:
    """Custom tool for domain-specific operations"""
    return f"Processed: {query}"
```

## Best Practices

- Start with core MCP tools, add complexity gradually
- Use MessagesState, avoid custom state management
- Keep prompts simple and domain-focused
- Test MCP connection before supervisor integration
- Follow naming conventions consistently
- Clear error messages over graceful fallbacks
