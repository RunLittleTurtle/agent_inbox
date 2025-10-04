"""Multi-agent supervisor system using langgraph-supervisor framework.

This module implements a clean multi-agent architecture with:
- Calendar agent for Google Calendar operations via MCP
- Multi-Tool Rube agent for multi-application integration
- Supervisor using official langgraph_supervisor patterns
- Automatic agent handoff and state management
- LangSmith tracing for observability

All agents follow pure LangGraph create_react_agent patterns for consistency.
"""

import os
import sys
import io

# ============================================================================
# CRITICAL: Fix Unicode Encoding BEFORE Any Other Imports
# ============================================================================
# This MUST be the first code that runs to prevent UnicodeEncodeError
# in Docker containers where Python defaults to ASCII encoding.
#
# Issue: LangGraph Cloud deployment was failing with:
# "UnicodeEncodeError: 'ascii' codec can't encode characters"
#
# Root cause: Docker containers don't have locale set, so Python's
# sys.stdout defaults to ASCII. Environment variables in .env are loaded
# TOO LATE (after stdout encoding is already set).
#
# Solution: Reconfigure stdout/stderr to UTF-8 IMMEDIATELY at module load.
# ============================================================================

def _fix_encoding():
    """Force UTF-8 encoding for stdout/stderr to prevent UnicodeEncodeError.

    This function MUST run before any logging or print statements that might
    contain Unicode characters (e.g., MCP URLs from Supabase).
    """
    try:
        # Python 3.7+ has reconfigure() method
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        else:
            # Fallback for older Python versions
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except Exception:
        # If reconfiguration fails, we're in an environment that doesn't support it
        # (e.g., some IDEs). Ignore silently - encoding is likely already UTF-8.
        pass

# Apply encoding fix IMMEDIATELY
_fix_encoding()

# Now safe to import and use logging/printing
import asyncio
import logging
from dotenv import load_dotenv
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from langchain_core.messages import BaseMessage, AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

# LangGraph Runtime API (v0.6.0+) for multi-tenant context
from langgraph.runtime import Runtime, get_runtime


# Import the global state from state.py
from state import WorkflowState

# Import centralized configuration constants
from shared_utils import DEFAULT_LLM_MODEL

# Load environment variables for LangSmith integration
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# DIAGNOSTIC: Verify encoding configuration after fix
logger.info(f"[ENCODING-FIX] Python default encoding: {sys.getdefaultencoding()}")
logger.info(f"[ENCODING-FIX] stdout encoding: {sys.stdout.encoding}")
logger.info(f"[ENCODING-FIX] stderr encoding: {sys.stderr.encoding}")
logger.info(f"[ENCODING-FIX] PYTHONIOENCODING: {os.getenv('PYTHONIOENCODING', 'NOT_SET')}")
logger.info(f"[ENCODING-FIX] PYTHONUTF8: {os.getenv('PYTHONUTF8', 'NOT_SET')}")

# ============================================================================
# 2025 Runtime Context Schema (Phase 2.1)
# ============================================================================

@dataclass
class UserContext:
    """User-specific runtime context for multi-tenant MCP tool loading.

    This context is passed at request time via the Runtime API (LangGraph v0.6.0+).
    Each request can have different MCP URLs based on the user's configuration.

    Attributes:
        user_id: Clerk user ID for multi-tenant isolation
        mcp_calendar_url: Optional user-specific MCP server URL for calendar tools
        mcp_rube_url: Optional user-specific MCP server URL for Rube multi-tool
        rube_auth_token: Optional auth token for Rube MCP server
    """
    user_id: str
    mcp_calendar_url: str | None = None
    mcp_rube_url: str | None = None
    rube_auth_token: str | None = None

# Local dev only - uses git submodules from library/
# In deployment, these packages come from requirements.txt (pip-installed from PyPI)
# sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../library/langgraph'))
# sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../library/langgraph_supervisor-py'))
# sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../library/langchain-mcp-adapters'))

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor

def get_current_context():
    """Get current time and timezone context using USER_TIMEZONE from .env"""
    user_timezone = os.getenv("USER_TIMEZONE", "America/Toronto")
    try:
        timezone_zone = ZoneInfo(user_timezone)
        current_time = datetime.now(timezone_zone)
        return {
            "current_time": current_time.isoformat(),
            "timezone": str(timezone_zone),
            "timezone_name": user_timezone
        }
    except Exception as e:
        logger.error(f"Error getting timezone context: {e}")
        # Fallback to UTC
        current_time = datetime.now(ZoneInfo("UTC"))
        return {
            "current_time": current_time.isoformat(),
            "timezone": "UTC",
            "timezone_name": "UTC"
        }

# ============================================================================
# Runtime Wrapper Nodes (Phase 2.1) - 2025 Pattern
# ============================================================================

async def calendar_agent_node(state: WorkflowState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    """Runtime wrapper for calendar agent with dynamic MCP tool loading.

    This node loads calendar MCP tools at REQUEST TIME based on user-specific
    configuration from Supabase, following LangGraph 2025 best practices.

    Args:
        state: Current workflow state with messages
        config: RunnableConfig with user API keys

    Returns:
        Dict with updated messages from calendar agent
    """
    # Get user_id from config
    api_keys = get_api_keys_from_config(config)
    user_id = api_keys["user_id"]

    logger.info(f"[calendar_agent_node] Loading for user: {user_id}")

    # Load MCP URL from Supabase at runtime
    from utils.config_utils import get_agent_config_from_supabase

    agent_config = get_agent_config_from_supabase(user_id, "calendar_agent")
    mcp_integration = agent_config.get("mcp_integration", {})
    mcp_url = mcp_integration.get("mcp_server_url")

    logger.info(f"[calendar_agent_node] MCP URL from Supabase: {mcp_url or 'Not configured'}")

    # Delegate to existing CalendarAgentWithMCP implementation
    # CalendarAgentWithMCP will load MCP tools using the user_id
    from calendar_agent.calendar_orchestrator import CalendarAgentWithMCP

    # Create calendar model
    calendar_model = ChatAnthropic(
        model=DEFAULT_LLM_MODEL,
        temperature=0,
        anthropic_api_key=api_keys["anthropic_api_key"],
        streaming=False
    )

    # Create calendar agent instance with runtime user_id
    #  KEY CHANGE: Pass user_id from request config, not fallback "local_dev_user"
    calendar_agent_instance = CalendarAgentWithMCP(
        model=calendar_model,
        user_id=user_id
    )
    await calendar_agent_instance.initialize()

    agent = await calendar_agent_instance.get_agent()

    # Invoke agent with current state
    result = await agent.ainvoke(state)

    logger.info(f"[calendar_agent_node] Completed for user: {user_id}")
    return result


async def multi_tool_rube_agent_node(state: WorkflowState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    """Runtime wrapper for multi-tool Rube agent with dynamic MCP tool loading.

    This node loads Rube MCP tools at REQUEST TIME based on user-specific
    configuration from Supabase, following LangGraph 2025 best practices.

    Args:
        state: Current workflow state with messages
        config: RunnableConfig with user API keys

    Returns:
        Dict with updated messages from Rube agent
    """
    # Get user_id from config
    api_keys = get_api_keys_from_config(config)
    user_id = api_keys["user_id"]

    logger.info(f"[multi_tool_rube_agent_node] Loading for user: {user_id}")

    # Load MCP URL from Supabase at runtime
    from utils.config_utils import get_agent_config_from_supabase

    agent_config = get_agent_config_from_supabase(user_id, "multi_tool_rube_agent")
    mcp_integration = agent_config.get("mcp_integration", {})
    mcp_url = mcp_integration.get("mcp_server_url")
    auth_token = mcp_integration.get("auth_token")  # Optional auth token

    logger.info(f"[multi_tool_rube_agent_node] MCP URL from Supabase: {mcp_url or 'Not configured'}")

    # Create Rube model
    rube_model = ChatAnthropic(
        model=DEFAULT_LLM_MODEL,
        temperature=0,
        anthropic_api_key=api_keys["anthropic_api_key"],
        streaming=False
    )

    # Load MCP tools dynamically
    tools = []
    if mcp_url:
        try:
            logger.info(f"[multi_tool_rube_agent_node] Loading MCP tools from: {mcp_url}")

            # Import MCP client
            from langchain_mcp_adapters.client import MultiServerMCPClient

            # Create MCP client with user-specific URL
            mcp_config = {
                "rube": {
                    "url": mcp_url,
                    "transport": "streamable_http"
                }
            }

            # Add auth token if provided
            if auth_token:
                mcp_config["rube"]["headers"] = {
                    "Authorization": f"Bearer {auth_token}"
                }

            client = MultiServerMCPClient(mcp_config)
            tools = await client.get_tools()

            logger.info(f"[multi_tool_rube_agent_node] Loaded {len(tools)} tools: {[t.name for t in tools]}")
        except Exception as e:
            logger.error(f"[multi_tool_rube_agent_node] Failed to load MCP tools: {e}")
            import traceback
            traceback.print_exc()
            tools = []
    else:
        logger.warning(f"[multi_tool_rube_agent_node] No MCP URL configured for user {user_id}")

    # Filter to useful Rube tools (if we loaded any)
    if tools:
        useful_tools = [tool for tool in tools if hasattr(tool, 'name') and tool.name in {
            'RUBE_SEARCH_TOOLS',
            'RUBE_MULTI_EXECUTE_TOOL',
            'RUBE_CREATE_PLAN',
            'RUBE_MANAGE_CONNECTIONS',
            'RUBE_REMOTE_WORKBENCH',
            'RUBE_REMOTE_BASH_TOOL'
        }]
        logger.info(f"[multi_tool_rube_agent_node] Filtered to {len(useful_tools)} useful tools")
    else:
        useful_tools = []

    # Create agent prompt
    rube_prompt = """You are the Multi-Tool Rube Agent with access to tools across connected applications through Rube MCP server.

**WORKFLOW PATTERN:**
1. Understand the user's specific request
2. Use RUBE_SEARCH_TOOLS to find the right tools for the task
3. Show the user what tools were discovered
4. Execute using RUBE_MULTI_EXECUTE_TOOL with proper parameters
5. Present clear results and suggest next steps

**IMPORTANT GUIDELINES:**
- Always explain what you're doing and why
- Show discovered tools before executing them
- Handle errors gracefully and provide alternatives
- Ask for confirmation before destructive operations
- Respect user privacy and data security"""

    # Create the agent with runtime-loaded tools
    rube_agent = create_react_agent(
        model=rube_model,
        tools=useful_tools,
        name="multi_tool_rube_agent",
        prompt=rube_prompt
    )

    # Invoke agent with current state
    result = await rube_agent.ainvoke(state)

    logger.info(f"[multi_tool_rube_agent_node] Completed for user: {user_id}")
    return result


# ============================================================================
# Runtime-Aware Agent Graph Builders (Phase 3)
# ============================================================================

def create_runtime_calendar_agent() -> Any:
    """Create compiled calendar agent graph with Runtime API support.

    This creates a simple StateGraph containing the runtime wrapper node.
    The supervisor can route to this graph, and Runtime context will be available.

    Returns:
        Compiled graph that invokes calendar_agent_node with Runtime context
    """
    from langgraph.graph import StateGraph, START, END

    # Create simple graph with single node
    workflow = StateGraph(WorkflowState)
    workflow.add_node("calendar_agent", calendar_agent_node)
    workflow.add_edge(START, "calendar_agent")
    workflow.add_edge("calendar_agent", END)

    compiled_graph = workflow.compile(name="calendar_agent")
    logger.info("Runtime-aware calendar agent graph created")
    return compiled_graph


def create_runtime_multi_tool_agent() -> Any:
    """Create compiled multi-tool Rube agent graph with Runtime API support.

    This creates a simple StateGraph containing the runtime wrapper node.
    The supervisor can route to this graph, and Runtime context will be available.

    Returns:
        Compiled graph that invokes multi_tool_rube_agent_node with Runtime context
    """
    from langgraph.graph import StateGraph, START, END

    # Create simple graph with single node
    workflow = StateGraph(WorkflowState)
    workflow.add_node("multi_tool_rube_agent", multi_tool_rube_agent_node)
    workflow.add_edge(START, "multi_tool_rube_agent")
    workflow.add_edge("multi_tool_rube_agent", END)

    compiled_graph = workflow.compile(name="multi_tool_rube_agent")
    logger.info("Runtime-aware multi-tool Rube agent graph created")
    return compiled_graph


def get_api_keys_from_config(config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    """Extract API keys from config.configurable or fallback to environment variables.

    Multi-Tenant Production Pattern (LangGraph Platform 2025):
    - API keys are passed via config.configurable on every request
    - Each user's keys are injected by the frontend API route
    - LangGraph Platform automatically propagates config through the graph

    Local Development Fallback:
    - Falls back to .env variables when config is None
    - Allows local testing without mocking config

    Args:
        config: RunnableConfig with configurable dict containing user-specific keys

    Returns:
        Dict with openai_api_key, anthropic_api_key, and user_id

    Raises:
        EnvironmentError: If in production and keys are missing from config
    """
    # Check if we have config with configurable keys (production multi-tenant mode)
    if config and "configurable" in config:
        configurable = config["configurable"]

        # Extract keys from config (user-specific)
        openai_key = configurable.get("openai_api_key")
        anthropic_key = configurable.get("anthropic_api_key")
        user_id = configurable.get("user_id", "unknown_user")

        # In production, require at least one API key
        if not openai_key and not anthropic_key:
            error_msg = f"Production mode: No API keys provided in config for user {user_id}"
            logger.error(error_msg)
            raise EnvironmentError(error_msg)

        logger.info(f"Multi-tenant mode: Using API keys from config for user: {user_id}")

        return {
            "openai_api_key": openai_key,
            "anthropic_api_key": anthropic_key,
            "user_id": user_id,
        }

    # Fallback to environment variables (local development)
    logger.info("Local development mode: Using API keys from .env")

    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    if not openai_key and not anthropic_key:
        error_msg = "Local development: No API keys found in environment variables"
        logger.error(error_msg)
        raise EnvironmentError(error_msg)

    return {
        "openai_api_key": openai_key,
        "anthropic_api_key": anthropic_key,
        "user_id": "local_dev_user",
    }

async def create_calendar_agent(config: Optional[RunnableConfig] = None):
    """Create calendar agent with MCP integration (multi-tenant).

    Args:
        config: RunnableConfig with user-specific API keys in configurable dict

    Returns:
        Calendar agent graph with MCP tools

    Raises:
        Exception: Clear error if MCP connection or initialization fails
    """
    # Get user-specific API keys (or fallback to .env for local dev)
    api_keys = get_api_keys_from_config(config)

    from calendar_agent.calendar_orchestrator import CalendarAgentWithMCP

    # Create model with user's API key
    calendar_model = ChatAnthropic(
        model=DEFAULT_LLM_MODEL,
        temperature=0,
        anthropic_api_key=api_keys["anthropic_api_key"],
        streaming=False
    )

    # Create calendar agent instance with MCP integration
    # Pass user_id so agent can load user-specific MCP config from Supabase
    calendar_agent_instance = CalendarAgentWithMCP(
        model=calendar_model,
        user_id=api_keys["user_id"]  #  NEW: Load user-specific MCP URL from Supabase
    )
    await calendar_agent_instance.initialize()

    logger.info(f"Calendar agent initialized for user: {api_keys['user_id']}")
    return await calendar_agent_instance.get_agent()






async def create_multi_tool_rube_agent(config: Optional[RunnableConfig] = None):
    """Create Multi-Tool Rube Agent with access to 500+ applications (multi-tenant).

    Args:
        config: RunnableConfig with user-specific API keys in configurable dict

    Returns:
        Multi-Tool Rube agent with MCP tools

    Raises:
        Exception: Clear error if Rube MCP connection fails
    """
    # Get user-specific API keys (or fallback to .env for local dev)
    api_keys = get_api_keys_from_config(config)

    # Import the Multi-Tool Rube Agent configuration
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'multi_tool_rube_agent'))
    from tools import _agent_mcp

    logger.info(f"Creating Multi-Tool Rube Agent for user: {api_keys['user_id']}...")

    # Create model with user's API key
    rube_model = ChatAnthropic(
        model=DEFAULT_LLM_MODEL,
        temperature=0,
        anthropic_api_key=api_keys["anthropic_api_key"],
        streaming=False
    )

    # Get Rube MCP tools
    mcp_tools = await _agent_mcp.get_mcp_tools()

    # Filter to useful Rube tools
    useful_tools = [tool for tool in mcp_tools if hasattr(tool, 'name') and tool.name in {
        'RUBE_SEARCH_TOOLS',
        'RUBE_MULTI_EXECUTE_TOOL',
        'RUBE_CREATE_PLAN',
        'RUBE_MANAGE_CONNECTIONS',
        'RUBE_REMOTE_WORKBENCH',
        'RUBE_REMOTE_BASH_TOOL'
    }]

    logger.info(f"Found {len(useful_tools)} Rube tools for user {api_keys['user_id']}: {[t.name for t in useful_tools]}")

    # Create agent prompt with confirmed capabilities
    rube_prompt = """You are the Multi-Tool Rube Agent with access to 89 tools across 10 connected applications through Rube MCP server.

**CONFIRMED CAPABILITIES (89 tools available):**

**GMAIL** (11 tools) - Email Operations:
- Send emails, create drafts, fetch emails, list drafts
- Move emails to trash, search people, get attachments
- Access user profile and email management

**CODA** (10 tools) - Document & Database Management:
- List and create documents, manage tables and rows
- Search documents, create pages, database operations
- Collaborative document editing and data management

**SLACK** (8 tools) - Team Communication:
- Find channels, send messages, fetch conversation history
- Search messages, list channels and users
- Workspace communication management

**GITHUB** (10 tools) - Development & Collaboration:
- Find repositories, manage branches, create pull requests
- Merge branches, create issues, search issues/PRs
- Code review and repository management

**GOOGLE SHEETS** (10 tools) - Spreadsheet Operations:
- Search spreadsheets, manage sheets, batch updates
- Add/delete sheets, clear values, update properties
- Data analysis and spreadsheet automation

**GOOGLE DOCS** (7 tools) - Document Management:
- Search documents, update existing documents
- Get documents by ID, create from markdown
- Insert text and document formatting

**GOOGLE DRIVE** (7 tools) - File Management:
- Upload files, manage sharing preferences
- Find and list files, create folders
- File organization and collaboration

**GOOGLE CALENDAR** (8 tools) - Calendar Management:
- List calendars, find free slots, create events
- Get specific calendars, free/busy queries
- Event scheduling and availability management

**NOTION** (8 tools) - Productivity & Notes:
- Search pages, create pages, add content blocks
- Fetch block contents, update pages, query databases
- Knowledge management and collaboration

**LINEAR** (10 tools) - Project Management:
- Manage user profile, list projects and issues
- Create and update issues, add comments
- Attach files and track project progress

**HOW TO USE YOUR TOOLS:**

1. **RUBE_SEARCH_TOOLS** - Discover tools by use case or platform
   - Example: Search for "gmail send email" or "coda create document"

2. **RUBE_MULTI_EXECUTE_TOOL** - Execute discovered tools with parameters
   - Always show discovered tools before executing
   - Handle parameters based on tool requirements

3. **RUBE_CREATE_PLAN** - Create multi-step workflow plans
4. **RUBE_MANAGE_CONNECTIONS** - Check app connection status
5. **RUBE_REMOTE_WORKBENCH** - Handle file operations
6. **RUBE_REMOTE_BASH_TOOL** - Execute system commands if needed

**WORKFLOW PATTERN:**
1. Understand the user's specific request
2. Use RUBE_SEARCH_TOOLS to find the right tools for the task
3. Show the user what tools were discovered
4. Execute using RUBE_MULTI_EXECUTE_TOOL with proper parameters
5. Present clear results and suggest next steps

**IMPORTANT GUIDELINES:**
- Always explain what you're doing and why
- Show discovered tools before executing them
- Handle errors gracefully and provide alternatives
- Ask for confirmation before destructive operations
- Respect user privacy and data security
- Only claim capabilities for the 10 confirmed applications above

You have verified access to these 89 tools and can perform real operations across all connected applications."""

    # Create the agent
    rube_agent = create_react_agent(
        model=rube_model,
        tools=useful_tools,
        name="multi_tool_rube_agent",
        prompt=rube_prompt
    )

    logger.info(f"Multi-Tool Rube Agent created successfully for user: {api_keys['user_id']}")
    return rube_agent

async def post_model_hook(messages, model_output=None):
    """
    post_model_hook that ensures the supervisor ends with a recap message.
    """
    try:
        if not messages:
            return messages

        last_msg = messages[-1]
        if isinstance(last_msg, AIMessage) and ("recap" in last_msg.content.lower() or "summary" in last_msg.content.lower()):
            return messages

        source_text = ""
        for m in reversed(messages):
            if isinstance(m, AIMessage) or isinstance(m, ToolMessage):
                source_text = (m.content or "").strip()
                if source_text:
                    break

        if not source_text:
            recap_content = "Recap: The supervisor completed routing and agent handoff as required."
        else:
            short_snippet = " ".join(source_text.splitlines())[:480].strip()
            recap_content = f"Recap: {short_snippet}"

        messages.append(AIMessage(content=recap_content))
        return messages

    except Exception as e:
        logger.exception("post_model_hook failed -- returning original messages.")
        return messages

def validate_environment():
    """Validate required environment variables"""
    required_vars = ["ANTHROPIC_API_KEY", "OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        raise EnvironmentError(f"Missing required environment variables: {missing_vars}")

    logger.info("Environment validation passed")

async def create_supervisor_graph(config: Optional[RunnableConfig] = None):
    """Create multi-agent supervisor with Runtime API support (Phase 3).

    This supervisor uses runtime-aware agent graphs that load MCP tools dynamically
    at request time based on user-specific context.

    Args:
        config: RunnableConfig with user-specific API keys in configurable dict

    Returns:
        Compiled supervisor graph

    Raises:
        Exception: Clear error if agent creation or graph compilation fails
    """
    # Get user-specific API keys (or fallback to .env for local dev)
    api_keys = get_api_keys_from_config(config)

    # Skip environment validation in production (multi-tenant mode)
    # API keys are provided per-request via config.configurable
    # Only validate in local dev when explicitly requested
    if not config or not config.get("configurable"):
        logger.info("Local development mode: Using API keys from .env")
        # validate_environment()  # Disabled for multi-tenant deployment

    # PHASE 3: Create runtime-aware agent graphs
    # These graphs contain wrapper nodes that load MCP tools at REQUEST TIME
    logger.info(f"Creating runtime-aware agents for user: {api_keys['user_id']}...")
    calendar_agent = create_runtime_calendar_agent()
    multi_tool_rube_agent = create_runtime_multi_tool_agent()

    logger.info(f"Runtime-aware agents created for user: {api_keys['user_id']}")

    # Create supervisor model with user's API key
    supervisor_model = ChatAnthropic(
        model=DEFAULT_LLM_MODEL,
        temperature=0,
        anthropic_api_key=api_keys["anthropic_api_key"],
        streaming=False
    )

    # Get dynamic context
    context = get_current_context()

    # Improved supervisor prompt with clearer instructions
    supervisor_prompt = f"""You are a team supervisor dispatching requests and managing specialized agents.

CURRENT CONTEXT:
- Today: {datetime.fromisoformat(context['current_time']).strftime("%Y-%m-%d")} at {datetime.fromisoformat(context['current_time']).strftime("%I:%M %p")}
- Timezone: {context['timezone_name']}

IMPORTANT --> Always look at agent list before trying to answer!!

AGENT CAPABILITIES:
- calendar_agent: All calendar operations (create/view/modify events, check availability, scheduling)
- email_agent: **PRIMARY EMAIL AGENT** - Email composition/drafting/writing -> email_agent / Email management (list, send drafts, search) -> email_agent / Email reading/organization/ -> email_agent IMPORTANT : If the agent writes a DRAFTor a NEW email you MUST show it to the user
- ALL EMAIL TASKS -> email_agent (autonomous subgraph)
- drive_agent: File management, Google Drive integration, file sharing, document collaboration
- multi_tool_rube_agent: Multi-application tasks across Gmail, Slack, GitHub, Google Workspace, Coda, Linear, Notion, and other connected platforms

ROUTING STRATEGY:
1. ANALYZE the user's request carefully
2. IDENTIFY which agent is most appropriate
3. ROUTE immediately to that agent
4. Let the agent handle the task completely

ROUTING RULES:
- Calendar/scheduling/appointments/meetings -> calendar_agent
- ALL EMAIL TASKS (composition, sending, management, organization, triage) -> email_agent
- Multi-app tasks involving Slack, GitHub, Coda, Linear, Notion, Google Workspace -> multi_tool_rube_agent
- Cross-platform workflows and automation -> multi_tool_rube_agent
- General questions of the world -> Only if there is no agent related, you can answer

EMAIL ROUTING - IMPORTANT:
- Any mention of email, Gmail, inbox, sending, drafting, replying -> email_agent
- Email management -> email_agent


CRITICAL GUIDELINES:
- You are a ROUTER, not a problem solver
- NEVER answer a question that is not within your domain
- Route quickly and decisively
- Trust your agents to handle their domains
- Only provide direct answers for simple greetings or clarifications

When an agent completes their task, analyze if additional routing is needed."""

    # Create supervisor workflow
    workflow = create_supervisor(
        agents=[calendar_agent, multi_tool_rube_agent],
        model=supervisor_model,
        prompt=supervisor_prompt,
        supervisor_name="multi_agent_supervisor",
        output_mode="last_message",
        add_handoff_back_messages=True,
        post_model_hook=post_model_hook,
    )

    # Compile the workflow
    compiled_graph = workflow.compile(name="multi_agent_system")
    logger.info(f"Multi-agent supervisor created successfully for user: {api_keys['user_id']}")
    return compiled_graph

async def make_graph_async(config: Optional[RunnableConfig] = None):
    """Async factory for creating supervisor graph with multi-tenant support.

    Args:
        config: RunnableConfig with user API keys (injected by LangGraph Platform)

    Returns:
        Compiled graph instance

    Raises:
        Exception: Clear error if graph creation fails
    """
    graph_instance = await create_supervisor_graph(config)
    logger.info("Graph creation completed successfully")
    return graph_instance

def make_graph(config: Optional[RunnableConfig] = None):
    """Sync factory function for LangGraph Platform with multi-tenant support.

    This function is called by LangGraph Platform on every request.
    The config parameter is automatically injected with user-specific data.

    NOTE: This wraps the async graph creation in asyncio.run() for Platform compatibility.
    LangGraph Platform requires sync factory functions, not async.

    Args:
        config: RunnableConfig with user API keys (injected by LangGraph Platform)

    Returns:
        Compiled graph instance

    Raises:
        Exception: Clear error if graph creation fails
    """
    logger.info("Creating supervisor graph via sync factory function")
    return asyncio.run(make_graph_async(config))

# Export a static graph instance for LangGraph Platform registration
# Platform uses this instance and injects config on each request via RunnableConfig
# This pattern matches the working executive graphs (static compilation)
graph = make_graph(None)  # Create with None config - will use env vars for registration
logger.info("Static supervisor graph instance created for LangGraph Platform")
