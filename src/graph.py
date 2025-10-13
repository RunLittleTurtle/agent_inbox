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
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        else:
            # Fallback for older Python versions
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
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
logger.info(
    f"[ENCODING-FIX] PYTHONIOENCODING: {os.getenv('PYTHONIOENCODING', 'NOT_SET')}"
)
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
            "timezone_name": user_timezone,
        }
    except Exception as e:
        logger.error(f"Error getting timezone context: {e}")
        # Fallback to UTC
        current_time = datetime.now(ZoneInfo("UTC"))
        return {
            "current_time": current_time.isoformat(),
            "timezone": "UTC",
            "timezone_name": "UTC",
        }


# ============================================================================
# Runtime Wrapper Nodes (Phase 2.1) - 2025 Pattern
# ============================================================================


async def calendar_agent_node(
    state: WorkflowState, config: Optional[RunnableConfig] = None
) -> Dict[str, Any]:
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

    # Load full agent config from Supabase at runtime
    from utils.config_utils import get_agent_config_from_supabase
    from utils.llm_utils import get_llm

    agent_config = get_agent_config_from_supabase(user_id, "calendar_agent")

    # Extract LLM configuration from user's saved settings
    llm_config = agent_config.get("llm", {})
    model_name = llm_config.get("model", DEFAULT_LLM_MODEL)

    # Ensure temperature is a float (Supabase may return as string)
    temp_value = llm_config.get("temperature", 0.0)
    try:
        temperature = float(temp_value) if temp_value is not None else 0.0
    except (ValueError, TypeError):
        temperature = 0.0
        logger.warning(f"[CONFIG] Invalid temperature value '{temp_value}', using default 0.0")

    # Log configuration details
    logger.info(f"[CONFIG] Calendar agent config for user {user_id}:")
    logger.info(f"[CONFIG]   Raw agent_config keys: {list(agent_config.keys())}")
    logger.info(f"[CONFIG]   llm_config contents: {llm_config}")
    logger.info(f"[CONFIG]   Model: {model_name} (from Supabase: {bool(llm_config.get('model'))})")
    logger.info(f"[CONFIG]   Temperature: {temperature}")

    # Delegate to new simplified calendar agent implementation
    # Uses create_react_agent with Google Workspace tools
    from calendar_agent.calendar_orchestrator import create_calendar_agent

    # Determine correct API key based on model provider
    # CRITICAL: Only pass the API key that matches the model provider
    # ChatOpenAI doesn't accept anthropic_api_key, ChatAnthropic doesn't accept api_key
    if model_name.startswith('claude') or model_name.startswith('opus'):
        model_kwargs = {"anthropic_api_key": api_keys.get("anthropic_api_key")}
        logger.info(f"[CONFIG] Using Anthropic model: {model_name}")
    else:
        model_kwargs = {"api_key": api_keys.get("openai_api_key")}
        logger.info(f"[CONFIG] Using OpenAI model: {model_name}")

    # Create calendar model with user-specific settings using cross-provider utility
    logger.info(f"[CONFIG] Creating calendar model with: model={model_name}, temp={temperature}, streaming=False")
    calendar_model = get_llm(
        model_name,
        temperature=temperature,
        **model_kwargs,
        streaming=False,
    )
    logger.info(f"[CONFIG] Successfully created calendar model: {type(calendar_model).__name__}")

    # Create calendar agent using simplified factory function
    # This handles Google Workspace executor initialization and tool loading
    agent = await create_calendar_agent(
        model=calendar_model,
        user_id=user_id,
        agent_config=agent_config
    )

    # Invoke agent with current state
    result = await agent.ainvoke(state)

    logger.info(f"[calendar_agent_node] Completed for user: {user_id}")
    return result


async def multi_tool_rube_agent_node(
    state: WorkflowState, config: Optional[RunnableConfig] = None
) -> Dict[str, Any]:
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

    logger.info(f"[multi_tool_rube_agent_node] Starting execution for user: {user_id}")
    logger.info(f"[multi_tool_rube_agent_node] Input state keys: {list(state.keys())}")

    # Load full agent config from Supabase at runtime
    from utils.config_utils import get_agent_config_from_supabase
    from utils.llm_utils import get_llm

    agent_config = get_agent_config_from_supabase(user_id, "multi_tool_rube_agent")

    # Extract LLM configuration from user's saved settings
    llm_config = agent_config.get("llm", {})
    model_name = llm_config.get("model", DEFAULT_LLM_MODEL)

    # Ensure temperature is a float (Supabase may return as string)
    temp_value = llm_config.get("temperature", 0.0)
    try:
        temperature = float(temp_value) if temp_value is not None else 0.0
    except (ValueError, TypeError):
        temperature = 0.0
        logger.warning(f"[CONFIG] Invalid temperature value '{temp_value}', using default 0.0")

    # Log configuration details
    logger.info(f"[CONFIG] Multi-tool Rube agent config for user {user_id}:")
    logger.info(f"[CONFIG]   Raw agent_config keys: {list(agent_config.keys())}")
    logger.info(f"[CONFIG]   llm_config contents: {llm_config}")
    logger.info(f"[CONFIG]   Model: {model_name} (from Supabase: {bool(llm_config.get('model'))})")
    logger.info(f"[CONFIG]   Temperature: {temperature}")

    # Determine correct API key based on model provider
    # CRITICAL: Only pass the API key that matches the model provider
    # ChatOpenAI doesn't accept anthropic_api_key, ChatAnthropic doesn't accept api_key
    if model_name.startswith('claude') or model_name.startswith('opus'):
        model_kwargs = {"anthropic_api_key": api_keys.get("anthropic_api_key")}
        logger.info(f"[CONFIG] Using Anthropic model: {model_name}")
    else:
        model_kwargs = {"api_key": api_keys.get("openai_api_key")}
        logger.info(f"[CONFIG] Using OpenAI model: {model_name}")

    # Create Rube model with user-specific settings using cross-provider utility
    logger.info(f"[CONFIG] Creating Rube model with: model={model_name}, temp={temperature}, streaming=False")
    rube_model = get_llm(
        model_name,
        temperature=temperature,
        **model_kwargs,
        streaming=False,
    )
    logger.info(f"[CONFIG] Successfully created Rube model: {type(rube_model).__name__}")

    # Load tools using OAuth-aware function (supports per-user tokens from Supabase)
    try:
        logger.info(f"[multi_tool_rube_agent_node] Loading OAuth-enabled tools for user: {user_id}")

        from multi_tool_rube_agent.tools import get_agent_simple_tools

        useful_tools = get_agent_simple_tools(user_id=user_id)

        logger.info(f"[multi_tool_rube_agent_node] Successfully loaded {len(useful_tools)} tools")
        if useful_tools:
            logger.info(f"[multi_tool_rube_agent_node] Tool names: {[t.name for t in useful_tools]}")
        else:
            logger.error(f"[multi_tool_rube_agent_node] WARNING: No tools loaded! Agent will have no capabilities.")
    except Exception as e:
        logger.error(f"[multi_tool_rube_agent_node] CRITICAL: Failed to load tools: {type(e).__name__}: {e}")
        import traceback
        logger.error(f"[multi_tool_rube_agent_node] Traceback:\n{traceback.format_exc()}")
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
    logger.info(f"[multi_tool_rube_agent_node] Creating react agent with {len(useful_tools)} tools")
    rube_agent = create_react_agent(
        model=rube_model,
        tools=useful_tools,
        name="multi_tool_rube_agent",
        prompt=rube_prompt,
    )
    logger.info(f"[multi_tool_rube_agent_node] Agent created successfully")

    # Invoke agent with current state
    try:
        logger.info(f"[multi_tool_rube_agent_node] Invoking agent with state")
        result = await rube_agent.ainvoke(state)
        logger.info(f"[multi_tool_rube_agent_node] Agent invocation completed successfully")
        logger.info(f"[multi_tool_rube_agent_node] Result keys: {list(result.keys()) if isinstance(result, dict) else 'not a dict'}")
        return result
    except Exception as e:
        logger.error(f"[multi_tool_rube_agent_node] Agent invocation failed: {type(e).__name__}: {e}")
        import traceback
        logger.error(f"[multi_tool_rube_agent_node] Traceback:\n{traceback.format_exc()}")
        raise


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
            error_msg = (
                f"Production mode: No API keys provided in config for user {user_id}"
            )
            logger.error(error_msg)
            raise EnvironmentError(error_msg)

        logger.info(
            f"Multi-tenant mode: Using API keys from config for user: {user_id}"
        )

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
        streaming=False,
    )

    # Create calendar agent instance with MCP integration
    # Pass user_id so agent can load user-specific MCP config from Supabase
    calendar_agent_instance = CalendarAgentWithMCP(
        model=calendar_model,
        user_id=api_keys["user_id"],  #  NEW: Load user-specific MCP URL from Supabase
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
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "multi_tool_rube_agent"))
    from tools import _agent_mcp

    logger.info(f"Creating Multi-Tool Rube Agent for user: {api_keys['user_id']}...")

    # Create model with user's API key
    rube_model = ChatAnthropic(
        model=DEFAULT_LLM_MODEL,
        temperature=0,
        anthropic_api_key=api_keys["anthropic_api_key"],
        streaming=False,
    )

    # Get Rube MCP tools
    mcp_tools = await _agent_mcp.get_mcp_tools()

    # Filter to useful Rube tools
    useful_tools = [
        tool
        for tool in mcp_tools
        if hasattr(tool, "name")
        and tool.name
        in {
            "RUBE_SEARCH_TOOLS",
            "RUBE_MULTI_EXECUTE_TOOL",
            "RUBE_CREATE_PLAN",
            "RUBE_MANAGE_CONNECTIONS",
            "RUBE_REMOTE_WORKBENCH",
            "RUBE_REMOTE_BASH_TOOL",
        }
    ]

    logger.info(
        f"Found {len(useful_tools)} Rube tools for user {api_keys['user_id']}: {[t.name for t in useful_tools]}"
    )

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
        prompt=rube_prompt,
    )

    logger.info(
        f"Multi-Tool Rube Agent created successfully for user: {api_keys['user_id']}"
    )
    return rube_agent


async def post_model_hook(state, model_output=None):
    """
    post_model_hook that ensures the supervisor ends with a recap message.

    Per LangGraph 2025 best practices, this receives the full state dict.
    """
    try:
        # Extract messages from state dictionary
        messages = state.get("messages", [])
        if not messages or not isinstance(messages, list):
            return state  # Return full state if no valid messages

        last_msg = messages[-1]
        # Handle both string and list content (multimodal messages with tool calls)
        if isinstance(last_msg, AIMessage):
            content = last_msg.content
            if isinstance(content, str) and (
                "recap" in content.lower() or "summary" in content.lower()
            ):
                return {"messages": messages}

        source_text = ""
        for m in reversed(messages):
            if isinstance(m, AIMessage) or isinstance(m, ToolMessage):
                # Type-safe content extraction for multimodal messages
                content = m.content or ""
                if isinstance(content, str):
                    source_text = content
                elif isinstance(content, list):
                    # Multimodal content: [{"type": "text", "text": "..."}, {"type": "image", ...}]
                    text_parts = [
                        block.get("text", "")
                        for block in content
                        if isinstance(block, dict) and block.get("type") == "text"
                    ]
                    source_text = " ".join(text_parts)
                else:
                    # Fallback for unknown content types
                    source_text = str(content)

                source_text = source_text.strip()
                if source_text:
                    break

        if not source_text:
            recap_content = (
                "Recap: The supervisor completed routing and agent handoff as required."
            )
        else:
            short_snippet = " ".join(source_text.splitlines())[:480].strip()
            recap_content = f"Recap: {short_snippet}"

        messages.append(AIMessage(content=recap_content))
        return {"messages": messages}  # Return state update dict

    except Exception as e:
        logger.exception("post_model_hook failed -- returning original state.")
        return state  # Return original state on error


def validate_environment():
    """Validate required environment variables"""
    required_vars = ["ANTHROPIC_API_KEY", "OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        raise EnvironmentError(
            f"Missing required environment variables: {missing_vars}"
        )

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
        streaming=False,
    )

    # Get dynamic context
    context = get_current_context()

    # Enhanced supervisor prompt with intelligent intermediary pattern
    supervisor_prompt = f"""You are an intelligent team supervisor acting as an intermediary between users and specialized agents.

CURRENT CONTEXT:
- Today: {datetime.fromisoformat(context["current_time"]).strftime("%Y-%m-%d")} at {datetime.fromisoformat(context["current_time"]).strftime("%I:%M %p")}
- Timezone: {context["timezone_name"]}

AGENT CAPABILITIES:
- calendar_agent: All calendar operations (create/view/modify events, check availability, scheduling)
- multi_tool_rube_agent: Multi-application tasks across Gmail, GitHub, Google Workspace, Coda, Shopify and other platforms

═══════════════════════════════════════════════════════════════════
YOUR ROLE AS INTELLIGENT INTERMEDIARY
═══════════════════════════════════════════════════════════════════

You are NOT just a router. You are the bridge between users and agents:
1. All agent requests pass through you
2. All user responses pass through you
3. You analyze, reformulate, and add context
4. You verify critical outputs before delivery

═══════════════════════════════════════════════════════════════════
HANDLING AGENT REQUESTS TO USER
═══════════════════════════════════════════════════════════════════

When an agent needs information from the user:
1. ANALYZE the agent's request
2. REFORMULATE it clearly for the user
3. ASK the user directly (don't just pass through agent's message)

Example:
❌ BAD: Just forwarding agent's technical question
✅ GOOD: "The calendar agent needs to confirm: Would you like to book 'Team Meeting' on January 15th at 2 PM? Please reply 'yes' to confirm or suggest changes."

═══════════════════════════════════════════════════════════════════
HANDLING USER RESPONSES TO AGENT
═══════════════════════════════════════════════════════════════════

When user responds to an agent's question:
1. ANALYZE the overall conversation state
2. ANALYZE the agent's previous request
3. ANALYZE the user's response
4. PROVIDE FULL CONTEXT back to the agent

Your message to agent should include:
- Summary of what the agent asked
- User's response
- Any relevant context from conversation history
- Clear instruction on what to do next

Example:
❌ BAD: Just routing "yes" back to calendar_agent
✅ GOOD: Route to calendar_agent with message: "User confirmed booking approval. Original request: Book 'Team Meeting' on January 15th at 2 PM. User response: 'yes'. Please proceed with booking and provide confirmation with event link."

═══════════════════════════════════════════════════════════════════
CRITICAL OUTPUT VERIFICATION (LINKS)
═══════════════════════════════════════════════════════════════════

For critical actions (bookings, purchases, file uploads, etc.):
1. CHECK if agent provided a valid link/URL
2. IF NO LINK: Push back to agent requesting the link
3. IF LINK PROVIDED: Verify it appears valid (not placeholder/fake)
4. ONLY deliver to user with verified link

Critical action indicators:
- "booked", "scheduled", "created event"
- "purchased", "ordered", "bought"
- "uploaded", "shared", "sent"
- "submitted", "posted", "published"

Verification rules:
- Real links: https://calendar.google.com/event?eid=..., https://github.com/user/repo/issues/123
- Fake links: "link", "[link]", "event link", "booking URL", placeholders
- If uncertain: Push back to agent for clarification

Example flow:
1. Agent: "Successfully booked meeting"
2. Supervisor: "Please provide the calendar event link"
3. Agent: "Here's the link: [calendar link]"
4. Supervisor (analyzing): This is a placeholder, not real link
5. Supervisor to agent: "The link '[calendar link]' appears to be a placeholder. Please provide the actual Google Calendar event URL (format: https://calendar.google.com/event?eid=...)"

═══════════════════════════════════════════════════════════════════
ROUTING RULES
═══════════════════════════════════════════════════════════════════

NEW USER REQUEST (no ongoing agent conversation):
- Calendar/scheduling/appointments -> calendar_agent
- Multi-app tasks (Gmail, GitHub, Drive, etc.) -> multi_tool_rube_agent
- General questions -> Answer directly only if no agent needed

USER RESPONDING TO AGENT (ongoing conversation):
- Analyze conversation state and user response
- Add full context
- Route back to the SAME agent with enriched message

AGENT NEEDS CLARIFICATION FROM USER:
- Don't route back to user immediately
- Reformulate agent's question clearly
- Present to user for response

═══════════════════════════════════════════════════════════════════
EXAMPLE INTERACTIONS
═══════════════════════════════════════════════════════════════════

Example 1: Agent asks for confirmation
Agent output: "I found a slot at 2 PM. Should I book it?"
Supervisor to user: "The calendar agent found an available time slot at 2 PM for your meeting. Would you like me to book it? Reply 'yes' to confirm."
User: "yes"
Supervisor to calendar_agent: "User confirmed booking for 2 PM slot. Previous context: User requested meeting, agent proposed 2 PM, user approved. Please complete the booking and provide the Google Calendar event link."

Example 2: Agent completes action but no link
Agent: "I successfully booked your meeting for tomorrow at 2 PM"
Supervisor to agent: "Please provide the Google Calendar event link for the booking."
Agent: "https://calendar.google.com/event?eid=abc123xyz"
Supervisor to user: "Meeting booked successfully for tomorrow at 2 PM. View event: https://calendar.google.com/event?eid=abc123xyz"

Example 3: Agent provides fake link
Agent: "Meeting booked! Link: [event link]"
Supervisor to agent: "The link '[event link]' is a placeholder. Please provide the actual Google Calendar event URL."

═══════════════════════════════════════════════════════════════════
CRITICAL PRINCIPLES
═══════════════════════════════════════════════════════════════════

1. Context Awareness: Always analyze the full conversation state
2. Reformulation: Don't just pass messages through - add clarity and context
3. Verification: Always verify critical outputs have real links
4. Trust Building: Never deliver fake links to users
5. Agent Support: Provide agents with full context to continue their work
6. User Clarity: Make agent requests clear and actionable for users

Remember: You are the intelligent bridge that ensures quality, context, and trust in every interaction."""

    # Create supervisor workflow
    workflow = create_supervisor(
        agents=[calendar_agent, multi_tool_rube_agent],
        model=supervisor_model,
        prompt=supervisor_prompt,
        supervisor_name="multi_agent_supervisor",
        output_mode="last_message",
        add_handoff_back_messages=True,
        # DISABLED: post_model_hook breaks Anthropic tool execution
        # Issue: Hook appends recap AIMessage which violates Anthropic's requirement that
        # tool_use blocks must be IMMEDIATELY followed by tool_result in next message.
        # Error: "messages.3: tool_use ids were found without tool_result blocks immediately after"
        # Can re-enable later with proper guards to skip recap when tool calls are pending.
        # post_model_hook=post_model_hook,
    )

    # Compile the workflow
    compiled_graph = workflow.compile(name="multi_agent_system")
    logger.info(
        f"Multi-agent supervisor created successfully for user: {api_keys['user_id']}"
    )
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
