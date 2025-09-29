# React Agent MCP Template

Template for creating MCP-enabled React Agents compatible with supervisor system.

## Quick Start

### 1. Copy Template
```bash
cp -r src/_react_agent_mcp_template src/{your_agent}_agent
cd src/{your_agent}_agent
```

### 2. Configure Environment
```bash
# Add to .env (choose your MCP provider)

# Rube (Universal Provider)
RUBE_MCP_SERVER=https://rube.app/mcp
RUBE_BEARER_TOKEN=your_bearer_token_here

# OR Pipedream
PIPEDREAM_MCP_SERVER_{SERVICE_NAME}=https://mcp.pipedream.net/{your-id}/{service}

# OR Composio
COMPOSIO_MCP_SERVER_{SERVICE}=https://mcp.composio.dev/{your-id}/{service}

# Required
ANTHROPIC_API_KEY=your_key
USER_TIMEZONE=America/Toronto  # Centralized timezone for all agents
```

### 3. Customize Files

#### `config.py` (centralized configuration):
```python
AGENT_NAME = "your_agent"  # Your agent name
AGENT_DISPLAY_NAME = "Your Agent"  # Display name
AGENT_DESCRIPTION = "description of what your agent does"  # What your agent does
MCP_ENV_VAR = "RUBE_MCP_SERVER"  # Environment variable for your MCP provider
```

#### `tools.py`:
```python
USEFUL_TOOL_NAMES = {
    # Use the tool discovery script to get exact names (see below)
    # Example tools (replace with your actual discovered tools):
    'example-tool-1',
    'example-tool-2',
    # OR check your MCP provider's documentation
}
```

#### `x_agent_orchestrator.py`:
```python
def create_your_agent():  # Replace 'your' with your actual agent name
    return create_default_orchestrator()
```

### 4. Add Configuration UI Support

**IMPORTANT**: The template now includes comprehensive configuration UI integration at `http://localhost:3004`:

1. **Update API endpoints** in `config-app/src/app/api/config/`:
   - Add your agent path to `AGENT_CONFIG_PATHS` in `agents/route.ts`
   - Agent configuration is automatically discovered via `ui_config.py`

2. **Replace ALL placeholder values** in `config.py`:
   - `{AGENT_NAME}` → actual agent name
   - `{AGENT_DISPLAY_NAME}` → display name
   - `{AGENT_DESCRIPTION}` → description
   - `{MCP_PROVIDER}` → your MCP provider prefix

3. **Only include implemented fields** in `ui_config.py`

See `GUIDE_HOW_TO/01_CONFIG_SETUP_GUIDE.md` for complete configuration UI instructions.

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
🔍 Discovering MCP Tools...
============================================================
✅ Discovered 15 tools:

📋 Copy these lines to your USEFUL_TOOL_NAMES:
USEFUL_TOOL_NAMES = {
    # Example discovered tools (replace with your actual tools)
    'example-tool-1',  # Description of tool 1
    'example-tool-2',  # Description of tool 2

    # More discovered tools
    'example-tool-3',  # Description of tool 3
    'example-tool-4',  # Description of tool 4
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

## MCP Provider Examples

Based on your chosen MCP provider:

### Rube (Universal Provider)
```bash
RUBE_MCP_SERVER=https://rube.app/mcp
RUBE_BEARER_TOKEN=your_bearer_token_here
```
*Rube provides access to 500+ tools across 100+ applications through a single endpoint.*

### Composio (Service-Specific)
```bash
COMPOSIO_MCP_SERVER_slack=https://mcp.composio.dev/{your-id}/slack
COMPOSIO_MCP_SERVER_github=https://mcp.composio.dev/{your-id}/github
COMPOSIO_MCP_SERVER_google_sheets=https://mcp.composio.dev/{your-id}/google_sheets
```

### Pipedream (Service-Specific)
```bash
PIPEDREAM_MCP_SERVER_google_gmail=https://mcp.pipedream.net/{your-id}/google_gmail
PIPEDREAM_MCP_SERVER_google_sheets=https://mcp.pipedream.net/{your-id}/google_sheets
PIPEDREAM_MCP_SERVER_shopify=https://mcp.pipedream.net/{your-id}/shopify
```

### Custom MCP Servers
```bash
MY_CUSTOM_MCP_SERVER=https://your-server.com/mcp
COMPANY_INTERNAL_MCP=https://internal.company.com/mcp
```

## Key Patterns

### MCP Connection Pattern
- Flexible environment variables: `{PROVIDER}_MCP_SERVER_{SERVICE}` or `{PROVIDER}_MCP_SERVER`
- 5-minute tool caching for performance
- Clear error messages (no graceful fallbacks)
- 30-second timeout for MCP connections
- Universal provider support (Rube, Composio, Pipedream, custom)

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
5. **MCP First**: Leverage MCP provider tools (Rube, Composio, Pipedream, etc.), add local tools sparingly
6. **Tool Discovery**: Use automatic discovery to find exact tool names

## Common Issues

### MCP Connection Fails
- Check environment variable name matches your provider's pattern
- Verify MCP server URL is correct for your provider
- Check network connectivity
- For Rube: Verify bearer token is set

### Supervisor Integration Fails
- Verify function name: `create_{agent}_agent()`
- Check MessagesState compatibility
- Ensure proper error handling

### Tool Loading Fails
- Check USEFUL_TOOL_NAMES matches available tools
- Use tool discovery script: `python discover_tools.py`
- Check your MCP provider's documentation for available tools
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
