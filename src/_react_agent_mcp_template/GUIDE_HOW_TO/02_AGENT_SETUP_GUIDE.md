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
MCP_SERVICE = "google_gmail"  # e.g., "google_gmail", "google_sheets"
AGENT_STATUS = "active"  # "active" or "disabled"
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
    'gmail-send-email',
    'gmail-find-email',
    'gmail-list-labels',
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

### Step 5: Test Your Agent

```bash
# Test the agent creation
python x_agent_orchestrator.py

# Test MCP tool loading
python tools.py
```

## Detailed Configuration

### Core Files Structure

```
src/your_agent/
├── config.py              # Main configuration
├── prompt.py               # System prompts
├── tools.py                # MCP tools and tool discovery
├── ui_config.py           # Configuration UI schema
├── x_agent_orchestrator.py # React agent creation
├── discover_tools.py       # Tool discovery script
├── schemas.py             # Data structures (optional)
├── human_inbox.py         # Human-in-the-loop integration
└── supervisor_snippet_connection.md # Integration guide
```

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
MCP_SERVICE = "google_gmail"  # MCP service identifier
AGENT_STATUS = "active"  # "active" or "disabled"

# Import prompts following LangGraph best practices
from .prompt import AGENT_SYSTEM_PROMPT

# MCP Configuration
MCP_ENV_VAR = f"PIPEDREAM_MCP_SERVER_{MCP_SERVICE}"
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

# MCP Server for your specific agent
PIPEDREAM_MCP_SERVER_{MCP_SERVICE}=https://mcp.pipedream.net/your-id/service

# Examples for different services:
PIPEDREAM_MCP_SERVER_google_gmail=https://mcp.pipedream.net/xxx/google_gmail
PIPEDREAM_MCP_SERVER_google_sheets=https://mcp.pipedream.net/xxx/google_sheets
PIPEDREAM_MCP_SERVER_google_drive=https://mcp.pipedream.net/xxx/google_drive
```

### Service-Specific Examples

**Gmail Agent:**
```bash
PIPEDREAM_MCP_SERVER_google_gmail=https://mcp.pipedream.net/your-id/google_gmail
```

**Google Sheets Agent:**
```bash
PIPEDREAM_MCP_SERVER_google_sheets=https://mcp.pipedream.net/your-id/google_sheets
```

**Google Drive Agent:**
```bash
PIPEDREAM_MCP_SERVER_google_drive=https://mcp.pipedream.net/your-id/google_drive
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

**Gmail/Email Services:**
```python
AGENT_NAME = "gmail"
AGENT_DISPLAY_NAME = "Gmail Agent"
AGENT_DESCRIPTION = "email management and organization"
MCP_SERVICE = "google_gmail"
```

**Google Sheets:**
```python
AGENT_NAME = "sheets"
AGENT_DISPLAY_NAME = "Google Sheets"
AGENT_DESCRIPTION = "spreadsheet operations and data management"
MCP_SERVICE = "google_sheets"
```

**Google Drive:**
```python
AGENT_NAME = "drive"
AGENT_DISPLAY_NAME = "Google Drive"
AGENT_DESCRIPTION = "file storage and document management"
MCP_SERVICE = "google_drive"
```

### Tool Categories

Organize discovered tools by categories:

```python
USEFUL_TOOL_NAMES = {
    # Email Management
    'gmail-send-email',
    'gmail-find-email',

    # Label Operations
    'gmail-list-labels',
    'gmail-create-label',

    # Archive & Delete
    'gmail-archive-email',
    'gmail-delete-email',
}
```

This setup provides a solid foundation for creating production-ready agents that integrate seamlessly with the Agent Inbox ecosystem.