# Agent Setup Guide

Complete technical guide for duplicating and customizing the React Agent MCP template to create new agents.

## Quick Start (5-Minute Setup)

### Step 1: Copy Template

```bash
# Navigate to the project root
cd /path/to/agent_inbox_1.18

# Copy template to your new agent
cp -r src/_react_agent_mcp_template src/{your_agent_name}_agent

# Navigate to your new agent
cd src/{your_agent_name}_agent
```

### Step 2: Configure Agent Identity

Edit `config.py` - Replace ALL placeholder values:

```python
# TODO: Configure for your agent
AGENT_NAME = "gmail"  # e.g., "gmail", "sheets", "drive"
AGENT_DISPLAY_NAME = "Gmail Agent"  # e.g., "Gmail Agent", "Google Sheets"
AGENT_DESCRIPTION = "email management and organization"  # What your agent does
AGENT_STATUS = "active"  # "active" or "disabled"

# MCP Configuration - specify the exact environment variable name
# This is flexible - works with any MCP provider:
#   - Rube: "RUBE_MCP_SERVER" (universal provider)
#   - Composio: "COMPOSIO_MCP_SERVER_slack"
#   - Pipedream: "PIPEDREAM_MCP_SERVER_google_gmail"
#   - Custom: "MY_CUSTOM_MCP_SERVER"
MCP_ENV_VAR = "RUBE_MCP_SERVER"  # Your MCP server env var
```

### Step 3: Discover Available Tools

Use the built-in tool discovery system:

```bash
# Discover all available MCP tools
python discover_tools.py --format copy-paste

# Or save to file for reference
python discover_tools.py --save discovered_tools.txt
```

Copy the discovered tool names to `tools.py`:

```python
USEFUL_TOOL_NAMES = {
    # Use discovery script to find exact tool names
    # Example tools (replace with actual discovered tools):
    'example-tool-1',
    'example-tool-2',
    'example-tool-3',
    # ... other tools from discovery
}
```

### Step 4: Update Function Names

Edit `x_agent_orchestrator.py`:

```python
# Replace {agent} with your agent name
def create_gmail_agent():  # ⬅️ Update this function name
    """
    REQUIRED function for supervisor integration
    MUST match pattern: create_{agent}_agent()
    """
    return create_default_orchestrator()
```

### Step 5: Configure UI Integration (Optional)

To make your agent configurable through the web UI at `http://localhost:3004`:

1. Ensure `ui_config.py` has proper `CONFIG_INFO` and `CONFIG_SECTIONS`
2. Add your agent path to `config-app/src/app/api/config/agents/route.ts`
3. See the **Config App Structure** section below for complete UI integration details
4. See [Config Setup Guide](01_CONFIG_SETUP_GUIDE.md) for additional configuration options

### Step 6: Test Your Agent

```bash
# Test the agent creation
python x_agent_orchestrator.py

# Test MCP tool loading
python tools.py

# Test config UI integration (optional)
cd config-app && npm run dev:config
# Open http://localhost:3004 - your agent should appear in sidebar
```

## Detailed Configuration

### Core Files Structure

```
src/your_agent/
├── config.py              # Main configuration (reads from .env)
├── prompt.py              # System prompts (editable via config UI)
├── tools.py               # MCP tools and tool discovery
├── ui_config.py           # Configuration UI schema definition
├── x_agent_orchestrator.py # React agent creation
├── discover_tools.py      # Tool discovery script
├── schemas.py             # Data structures (optional)
├── human_inbox.py         # Human-in-the-loop integration
└── supervisor_snippet_connection.md # Integration guide
```

**Note**: The template now includes `ui_config.py` for integration with the configuration UI at `http://localhost:3004`. See the [Config Setup Guide](01_CONFIG_SETUP_GUIDE.md) for detailed UI configuration instructions.

### Configuration Details (`config.py`)

```python
"""
Agent configuration - centralized settings
"""

import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Dict
from dotenv import load_dotenv

load_dotenv()

# Agent Identity (REQUIRED - Replace placeholders)
AGENT_NAME = "gmail"  # Internal identifier
AGENT_DISPLAY_NAME = "Gmail Agent"  # UI display name
AGENT_DESCRIPTION = "email management and organization"  # Brief description
AGENT_STATUS = "active"  # "active" or "disabled"

# Import prompts following LangGraph best practices
from .prompt import AGENT_SYSTEM_PROMPT

# MCP Configuration - flexible for any provider
# Specify the exact environment variable name from your .env file
MCP_ENV_VAR = "RUBE_MCP_SERVER"  # e.g., "RUBE_MCP_SERVER", "COMPOSIO_MCP_SERVER_slack"
MCP_SERVER_URL = os.getenv(MCP_ENV_VAR, '')

# Timezone Configuration
TEMPLATE_TIMEZONE = 'global'  # Use global timezone by default
USER_TIMEZONE = os.getenv('USER_TIMEZONE', 'America/Toronto')

# LLM Configuration
LLM_CONFIG = {
    "model": "claude-sonnet-4-20250514",
    "temperature": 0.3,
    "streaming": False,  # Required for LangGraph compatibility
    "api_key": os.getenv("ANTHROPIC_API_KEY")
}

def get_current_context() -> Dict[str, str]:
    """Get current time and timezone context"""
    # Implementation provided in template...

def is_agent_enabled():
    """Check if the agent is enabled"""
    return AGENT_STATUS == "active"
```

### Tool Configuration (`tools.py`)

The template includes a powerful tool discovery system:

```python
# Configure which tools to use from MCP server
USEFUL_TOOL_NAMES = {
    # TODO: Use discovery script to find exact names
    'gmail-send-email',
    'gmail-find-email',
    'gmail-list-labels',
    'gmail-archive-email',
}

# Tool discovery functions (provided by template)
async def discover_mcp_tools() -> List[Dict[str, str]]:
    """Discover all available tools from MCP server"""

def discover_mcp_tools_sync() -> List[Dict[str, str]]:
    """Synchronous wrapper for tool discovery"""

def print_discovered_tools():
    """Print tools in copy-paste format for USEFUL_TOOL_NAMES"""
```

### Agent Orchestrator (`x_agent_orchestrator.py`)

```python
"""
React Agent Orchestrator with MCP Integration
"""

from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent

from .tools import get_agent_simple_tools
from .prompt import AGENT_SYSTEM_PROMPT
from .config import LLM_CONFIG, AGENT_NAME, get_current_context

def create_gmail_agent():  # ⬅️ Update function name
    """
    REQUIRED function for supervisor integration
    MUST match pattern: create_{agent}_agent()
    """
    return create_default_orchestrator()
```

## Environment Setup

### Required Environment Variables

Add to your main `.env` file:

```bash
# API Key
ANTHROPIC_API_KEY=your_api_key_here

# Global timezone (used by all agents)
USER_TIMEZONE=America/Toronto

# MCP Server URLs - flexible naming based on your provider
# Examples for different providers:

# Rube (Universal Provider):
RUBE_MCP_SERVER=https://rube.app/mcp
RUBE_BEARER_TOKEN=your_bearer_token_here

# Composio:
COMPOSIO_MCP_SERVER_slack=https://mcp.composio.dev/xxx/slack
COMPOSIO_MCP_SERVER_github=https://mcp.composio.dev/xxx/github

# Pipedream:
PIPEDREAM_MCP_SERVER_google_gmail=https://mcp.pipedream.net/xxx/google_gmail
PIPEDREAM_MCP_SERVER_google_sheets=https://mcp.pipedream.net/xxx/google_sheets

# Custom:
MY_CUSTOM_MCP_SERVER=https://your-server.com/mcp
COMPANY_MCP_API_ENDPOINT=https://api.company.com/mcp
```

### Service-Specific Examples

**Examples for Different Providers:**

**Rube (Universal Provider):**
```bash
RUBE_MCP_SERVER=https://rube.app/mcp
RUBE_BEARER_TOKEN=your_bearer_token_here
```

**Composio Services:**
```bash
COMPOSIO_MCP_SERVER_slack=https://mcp.composio.dev/your-id/slack
COMPOSIO_MCP_SERVER_github=https://mcp.composio.dev/your-id/github
```

**Pipedream Services:**
```bash
PIPEDREAM_MCP_SERVER_google_gmail=https://mcp.pipedream.net/your-id/google_gmail
PIPEDREAM_MCP_SERVER_google_sheets=https://mcp.pipedream.net/your-id/google_sheets
PIPEDREAM_MCP_SERVER_google_drive=https://mcp.pipedream.net/your-id/google_drive
```

**Custom MCP Servers:**
```bash
MY_CUSTOM_MCP_SERVER=https://your-server.com/mcp
COMPANY_INTERNAL_MCP=https://internal.company.com/mcp
```

## Tool Discovery Workflow

### Method 1: Discovery Script (Recommended)

```bash
# Basic discovery with formatted output
python discover_tools.py --format copy-paste

# Save results for future reference
python discover_tools.py --save tools_list.txt

# JSON format for programmatic use
python discover_tools.py --format json

# Validate environment setup
python discover_tools.py --validate-env
```

### Method 2: Direct Execution

```bash
# Run tools.py directly to see available tools
python tools.py
```

### Method 3: Programmatic Discovery

```python
from tools import discover_mcp_tools_sync, print_discovered_tools

# Get tool information as list of dictionaries
tools_info = discover_mcp_tools_sync()

# Print formatted output
print_discovered_tools()
```

### Example Discovery Output

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

## Supervisor Integration

### Add to Main Graph

Copy the code from `supervisor_snippet_connection.md` to `src/graph.py`:

```python
# Add to src/graph.py
from src.gmail_agent.x_agent_orchestrator import create_gmail_agent

async def create_supervisor_graph():
    # Existing supervisor code...

    # Add your agent
    agents = [
        # Existing agents...
        ("gmail_agent", create_gmail_agent),  # ⬅️ Add your agent
    ]

    # Update supervisor prompt
    supervisor_prompt = f"""You are a supervisor managing these agents:

    Previous agents...
    - gmail_agent: {get_agent_description("gmail_agent")}  # ⬅️ Add description
    """
```

### Agent Integration Pattern

```python
def agent_fallback(agent_name: str, error: Exception) -> str:
    """Fallback handler for agent failures"""
    return f"{agent_name} agent is unavailable: {str(error)}"

# Agent creation with error handling
try:
    gmail_agent = create_gmail_agent()
    print("✅ Gmail agent loaded successfully")
except Exception as e:
    print(f"⚠️ Gmail agent failed to load: {e}")
    gmail_agent = lambda state: agent_fallback("Gmail", e)
```

## Testing and Validation

### Test Agent Creation

```bash
# Test the agent orchestrator
cd src/your_agent
python x_agent_orchestrator.py
```

Expected output:
```
✅ your_agent Agent Created Successfully
```

### Test MCP Connection

```bash
# Test tool loading
python tools.py
```

Expected output:
```
✅ Loaded 5 gmail MCP tools: ['gmail-send-email', 'gmail-find-email', ...]
```

### Test Full Integration

```bash
# Test complete system
cd /path/to/agent_inbox_1.18
python cli.py start

# Optionally test config UI
cd config-app && npm run dev:config
# Navigate to http://localhost:3004
```

### Troubleshooting

**No tools loading:**
- Check `MCP_SERVER_URL` in config
- Verify environment variable name matches pattern
- Use tool discovery to find available tools

**Agent creation fails:**
- Check API key configuration
- Verify import statements
- Check function naming conventions

**Supervisor integration fails:**
- Verify function name matches `create_{agent}_agent()` pattern
- Check import paths in `graph.py`
- Ensure MessagesState compatibility

**Config UI issues:**
- Verify `ui_config.py` exists and has valid Python syntax
- Check agent path is added to `AGENT_CONFIG_PATHS` in routes
- See [Config Setup Guide](01_CONFIG_SETUP_GUIDE.md) for troubleshooting

## Advanced Features

### Custom Schemas (Optional)

Add domain-specific data structures in `schemas.py`:

```python
from pydantic import BaseModel

class EmailData(BaseModel):
    id: str
    subject: str
    sender: str
    content: str
```

### Human-in-the-Loop Integration

Use `human_inbox.py` for operations requiring approval:

```python
from human_inbox import create_human_interrupt

# Request human approval for sensitive operations
create_human_interrupt(
    action="send_email",
    args={"to": "user@example.com", "subject": "Important Email"},
    description="Send important email to user"
)
```

### Local Tools (Optional)

Add custom tools in `tools.py`:

```python
from langchain_core.tools import tool

@tool
def custom_email_parser(email_content: str) -> str:
    """Parse email content for specific information"""
    # Custom parsing logic
    return f"Parsed: {email_content}"

# Add to tool list
async def get_agent_tools_with_mcp() -> List[BaseTool]:
    tools = [custom_email_parser]  # ⬅️ Add custom tools

    # Add MCP tools
    mcp_tools = await _agent_mcp.get_mcp_tools()
    tools.extend(mcp_tools)

    return tools
```

## Best Practices

1. **Start Simple**: Begin with core MCP tools, add complexity gradually
2. **Use Discovery**: Always use tool discovery instead of guessing tool names
3. **Test Early**: Test each component before integration
4. **Follow Naming**: Use consistent naming conventions throughout
5. **Clear Errors**: Prefer clear error messages over graceful fallbacks
6. **MessagesState**: Use standard state, avoid custom state classes
7. **Documentation**: Update documentation as you add features

## Common Patterns

### Service-Specific Configurations

**Email Services:**
```python
AGENT_NAME = "gmail"
AGENT_DISPLAY_NAME = "Gmail Agent"
AGENT_DESCRIPTION = "email management and organization"
MCP_ENV_VAR = "RUBE_MCP_SERVER"  # For universal Rube provider
# or MCP_ENV_VAR = "PIPEDREAM_MCP_SERVER_google_gmail"  # For Pipedream
```

**Spreadsheet Services:**
```python
AGENT_NAME = "sheets"
AGENT_DISPLAY_NAME = "Google Sheets"
AGENT_DESCRIPTION = "spreadsheet operations and data management"
MCP_ENV_VAR = "RUBE_MCP_SERVER"  # For universal Rube provider
# or MCP_ENV_VAR = "PIPEDREAM_MCP_SERVER_google_sheets"  # For Pipedream
```

**File Storage Services:**
```python
AGENT_NAME = "drive"
AGENT_DISPLAY_NAME = "Google Drive"
AGENT_DESCRIPTION = "file storage and document management"
MCP_ENV_VAR = "RUBE_MCP_SERVER"  # For universal Rube provider
# or MCP_ENV_VAR = "PIPEDREAM_MCP_SERVER_google_drive"  # For Pipedream
```

### Tool Categories

Organize discovered tools by categories:

```python
USEFUL_TOOL_NAMES = {
    # Example tool categories - replace with your discovered tools
    # Email Management
    'example-email-tool-1',
    'example-email-tool-2',

    # File Operations
    'example-file-tool-1',
    'example-file-tool-2',

    # Data Operations
    'example-data-tool-1',
    'example-data-tool-2',
}
```

## Config App Structure & Integration

The Agent Inbox includes a comprehensive configuration UI at `http://localhost:3004` that allows real-time agent configuration through a web interface. Here's how to integrate your agent with this system:

### Config App Architecture

```
config-app/                           # Next.js configuration application
├── src/
│   ├── app/
│   │   ├── api/
│   │   │   └── config/
│   │   │       ├── agents/
│   │   │       │   └── route.ts      # Agent discovery & configuration API
│   │   │       ├── [agentName]/
│   │   │       │   └── route.ts      # Individual agent config API
│   │   │       └── env/
│   │   │           └── route.ts      # Environment variable management
│   │   ├── components/
│   │   │   ├── ConfigCard.tsx        # Configuration card UI component
│   │   │   ├── ConfigForm.tsx        # Dynamic form generation
│   │   │   └── AgentSidebar.tsx      # Agent navigation sidebar
│   │   └── page.tsx                  # Main configuration dashboard
│   ├── lib/
│   │   ├── config-loader.ts          # Dynamic config loading system
│   │   └── form-utils.ts             # Form validation utilities
│   └── styles/
│       └── globals.css               # Configuration UI styling
├── package.json                      # Next.js dependencies
└── next.config.js                    # Next.js configuration
```

### Agent Configuration Integration

#### 1. Agent Registration (`config-app/src/app/api/config/agents/route.ts`)

Your agent is automatically discovered by the config app through the `AGENT_CONFIG_PATHS` array:

```typescript
// config-app/src/app/api/config/agents/route.ts
const AGENT_CONFIG_PATHS = [
  'src/multi_tool_rube_agent',
  'src/_react_agent_mcp_template',
  'src/your_new_agent',  // ← Add your agent here
  // ... other agents
];
```

**Integration Steps:**
1. Copy template to your agent directory
2. Configure `ui_config.py` with your agent's schema
3. Add your agent path to `AGENT_CONFIG_PATHS`
4. The config app automatically discovers and loads your agent

#### 2. Configuration Schema (`ui_config.py`)

Your agent's configuration interface is defined in `ui_config.py`:

```python
# src/your_agent/ui_config.py
CONFIG_INFO = {
    'name': 'Your Agent Name',
    'description': 'Agent description for the UI',
    'config_type': 'agent_config',  # Used for categorization
    'config_path': 'src/your_agent/ui_config.py'
}

CONFIG_SECTIONS = [
    {
        'key': 'agent_identity',
        'label': 'Agent Identity',
        'description': 'Agent identification and status',
        'card_style': 'blue',  # Optional: blue, green, orange, red
        'fields': [
            {
                'key': 'agent_name',
                'label': 'Agent Name',
                'type': 'text',
                'default': 'your_agent',
                'readonly': True,
                'required': True,
                'description': 'Internal agent identifier'
            },
            # ... more fields
        ]
    },
    # ... more sections
]
```

#### 3. Data Flow Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Config UI     │    │    Config API    │    │   Agent Files   │
│ (localhost:3004)│    │   (Next.js)      │    │   (config.py)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         │ 1. GET /api/config     │                        │
         │    /agents             │                        │
         ├────────────────────────┤                        │
         │                        │ 2. Dynamic import      │
         │                        │    ui_config.py        │
         │                        ├────────────────────────┤
         │                        │                        │
         │ 3. Render form with    │                        │
         │    CONFIG_SECTIONS     │                        │
         ├────────────────────────┤                        │
         │                        │                        │
         │ 4. POST config changes │                        │
         ├────────────────────────┤                        │
         │                        │ 5. Update config.py   │
         │                        │    and/or .env file    │
         │                        ├────────────────────────┤
         │                        │                        │
         │ 6. Success response    │                        │
         ├────────────────────────┤                        │
```

#### 4. Configuration Field Types

The config app supports various field types for building dynamic forms:

```python
# Text input
{
    'key': 'agent_name',
    'label': 'Agent Name',
    'type': 'text',
    'placeholder': 'Enter agent name...',
    'required': True
}

# Dropdown selection
{
    'key': 'model',
    'label': 'AI Model',
    'type': 'select',
    'options': ['claude-sonnet-4', 'gpt-4o', 'gemini-1.5-pro'],
    'default': 'claude-sonnet-4'
}

# Textarea for long text
{
    'key': 'system_prompt',
    'label': 'System Prompt',
    'type': 'textarea',
    'rows': 10,
    'description': 'Define agent behavior'
}

# Number input with validation
{
    'key': 'temperature',
    'label': 'Temperature',
    'type': 'number',
    'validation': {'min': 0.0, 'max': 1.0, 'step': 0.1},
    'default': 0.3
}

# Read-only display
{
    'key': 'mcp_env_var',
    'label': 'MCP Environment Variable',
    'type': 'text',
    'readonly': True,
    'description': 'Environment variable used for MCP server URL'
}
```

#### 5. Environment Variable Management

The config app can manage environment variables through the `/api/config/env` endpoint:

```typescript
// Example: Update MCP server URL
const response = await fetch('/api/config/env', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    key: 'RUBE_MCP_SERVER',
    value: 'https://rube.app/mcp',
    agent: 'your_agent'
  })
});
```

#### 6. Real-time Configuration Updates

Changes made in the config UI are immediately reflected in your agent:

1. **UI Change**: User updates a field in the web interface
2. **API Call**: Config app sends POST request to `/api/config/[agentName]`
3. **File Update**: API updates `config.py` and/or `.env` files
4. **Agent Reload**: Agent automatically picks up new configuration
5. **Feedback**: UI shows success/error status

#### 7. Starting the Config App

```bash
# Development mode (recommended)
cd config-app
npm run dev:config
# Opens at http://localhost:3004

# Alternative: Standard Next.js dev server
npm run dev
# Opens at http://localhost:3000

# Production mode
npm run build
npm run start
```

#### 8. Config App Features

**Agent Discovery**: Automatically finds all agents in your project
**Dynamic Forms**: Generates forms based on `CONFIG_SECTIONS`
**Real-time Updates**: Changes are applied immediately
**Environment Management**: Manages `.env` variables through UI
**Validation**: Client and server-side field validation
**Error Handling**: Clear error messages for configuration issues
**Responsive Design**: Works on desktop and mobile devices

#### 9. Integration with config.py and ui_config.py

The relationship between core configuration files:

```python
# config.py - Core agent configuration (reads from .env)
AGENT_NAME = "your_agent"
MCP_SERVER_URL = os.getenv(MCP_ENV_VAR, '')
LLM_CONFIG = {"model": "claude-sonnet-4", "temperature": 0.3}

# ui_config.py - UI schema definition (defines form structure)
CONFIG_SECTIONS = [...]  # Defines how config.py values are edited

# prompt.py - System prompts (editable via config UI)
AGENT_SYSTEM_PROMPT = "You are a helpful agent..."
```

**Data Flow:**
1. `.env` → `config.py` (environment variables)
2. `config.py` → `ui_config.py` (current values)
3. `ui_config.py` → Config UI (form generation)
4. Config UI → `config.py`/`.env` (updates)

#### 10. Troubleshooting Config Integration

**Agent not appearing in sidebar:**
- Check agent path is added to `AGENT_CONFIG_PATHS`
- Verify `ui_config.py` exists and has valid Python syntax
- Check `CONFIG_INFO` is properly defined

**Form fields not rendering:**
- Validate `CONFIG_SECTIONS` structure
- Check field types are supported
- Verify required fields have `required: true`

**Configuration changes not persisting:**
- Check file permissions for `config.py` and `.env`
- Verify API endpoints are responding correctly
- Check browser console for JavaScript errors

**MCP connection issues:**
- Verify environment variable names match between `config.py` and `.env`
- Check MCP server URL format and accessibility
- Use tool discovery script to validate connection

This comprehensive integration allows you to build agents that are fully configurable through the web interface, providing a professional development and deployment experience.

---

This setup provides a solid foundation for creating production-ready agents that integrate seamlessly with the Agent Inbox ecosystem.