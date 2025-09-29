"""
Multi-Tool Rube Agent with dual integration approaches:
1. Rube MCP server (meta-tools for workflow orchestration)
2. Direct Composio SDK (specific app tools)

Both approaches provide access to 500+ applications through Composio's platform.
"""

import os
import sys
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from langchain_core.tools import tool, BaseTool
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

# Composio LangChain integration
try:
    from composio_langchain import ComposioToolSet, App
    COMPOSIO_AVAILABLE = True
except ImportError:
    COMPOSIO_AVAILABLE = False
    print("⚠️ composio-langchain not available - using MCP only")

# Import centralized config - handle both module import and direct execution
try:
    from .config import AGENT_NAME, MCP_ENV_VAR, MCP_SERVER_URL, RUBE_AUTH_TOKEN
except ImportError:
    # Direct execution fallback
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from config import AGENT_NAME, MCP_ENV_VAR, MCP_SERVER_URL, RUBE_AUTH_TOKEN

# Load environment variables
load_dotenv()

# Add library path for langchain-mcp-adapters
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../library/langchain-mcp-adapters'))

from langchain_mcp_adapters.client import MultiServerMCPClient

# =============================================================================
# CONFIGURATION - USES CENTRALIZED CONFIG
# =============================================================================

# Environment variable for Rube MCP server
# Rube provides unified access to 500+ applications through a single MCP server
# No need for service-specific URLs - Rube handles all apps through OAuth 2.1
# MCP_ENV_VAR is imported from config.py

# Rube MCP server provides high-level orchestration tools for 500+ applications
# These meta-tools allow dynamic discovery and execution of app-specific tools
USEFUL_TOOL_NAMES = {
    'RUBE_SEARCH_TOOLS',        # Discover tools from 500+ apps (Gmail, Slack, GitHub, etc.)
    'RUBE_MULTI_EXECUTE_TOOL',  # Execute multiple tools in parallel across apps
    'RUBE_CREATE_PLAN',         # Create step-by-step workflow plans
    'RUBE_MANAGE_CONNECTIONS',  # Manage app connections and authentication
    'RUBE_REMOTE_WORKBENCH',    # Process files and bulk operations remotely
    'RUBE_REMOTE_BASH_TOOL',    # Execute bash commands in remote sandbox
}

# =============================================================================
# MCP CONNECTION CLASS
# =============================================================================

class AgentMCPConnection:
    """MCP connection for Rube universal MCP server with caching"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._mcp_client: Optional[MultiServerMCPClient] = None
        self._mcp_tools: List[BaseTool] = []
        self._tools_cache_time: Optional[datetime] = None

        # Get Rube MCP server URL and auth token from config
        self.mcp_url = MCP_SERVER_URL
        self.auth_token = RUBE_AUTH_TOKEN

        if self.mcp_url:
            # Configure MCP server with Bearer token authentication
            server_config = {
                "url": self.mcp_url,
                "transport": "streamable_http"
            }

            # Add auth headers if token is available
            if self.auth_token:
                server_config["headers"] = {
                    "Authorization": f"Bearer {self.auth_token}"
                }
                self.logger.info(f"Configured Rube MCP with Bearer token authentication")
            else:
                self.logger.warning(f"No Rube auth token found - MCP connection may fail")

            self.mcp_servers = {
                f"rube_{AGENT_NAME}": server_config
            }
        else:
            self.mcp_servers = {}

    async def get_mcp_tools(self) -> List[BaseTool]:
        """Get MCP tools with 5-minute cache"""

        # Use cached tools if fresh
        if (self._mcp_tools and self._tools_cache_time and
            (datetime.now() - self._tools_cache_time).seconds < 300):
            return self._mcp_tools

        # No MCP server configured
        if not self.mcp_url:
            self.logger.warning(f"No Rube {AGENT_NAME} MCP server configured")
            return []

        self.logger.info(f"Connecting to Rube {AGENT_NAME} MCP: {self.mcp_url}")

        # Reuse MCP client to prevent memory leaks
        if self._mcp_client is None:
            self._mcp_client = MultiServerMCPClient(self.mcp_servers)

        try:
            # 30-second timeout
            tools = await asyncio.wait_for(
                self._mcp_client.get_tools(),
                timeout=30.0
            )

            # DEBUG: Log all available tools for discovery
            all_tool_names = [t.name for t in tools]
            self.logger.info(f"ALL available Rube {AGENT_NAME} MCP tools: {all_tool_names}")

            # Filter to configured tools only
            useful_tools = []
            for tool in tools:
                if tool.name in USEFUL_TOOL_NAMES:
                    useful_tools.append(tool)
                else:
                    self.logger.debug(f"Skipping {AGENT_NAME} tool: {tool.name}")

            self.logger.info(f"Loaded {len(useful_tools)} Rube {AGENT_NAME} MCP tools: {[t.name for t in useful_tools]}")

            # If no tools matched, show available tools for debugging
            if not useful_tools and tools:
                self.logger.warning(f"No tools matched USEFUL_TOOL_NAMES. Available tools:")
                for tool in tools[:10]:  # Show first 10 tools
                    self.logger.warning(f"  - {tool.name}: {tool.description[:80]}...")

            # Cache results
            self._mcp_tools = useful_tools
            self._tools_cache_time = datetime.now()
            return useful_tools

        except asyncio.TimeoutError:
            self.logger.error(f"Rube {AGENT_NAME} MCP tools loading timed out")
            return []
        except Exception as e:
            self.logger.error(f"Failed to load Rube {AGENT_NAME} MCP tools: {e}")
            return []

    async def discover_all_tools(self) -> List[Dict[str, str]]:
        """
        Discover ALL available tools from MCP server for development/debugging
        Returns list of tool info dicts with name, description, and input_schema info

        This is a best practice function for template users to discover tool names
        before adding them to USEFUL_TOOL_NAMES
        """
        if not self.mcp_url:
            self.logger.warning(f"No Rube MCP server configured for {AGENT_NAME}")
            return []

        if self._mcp_client is None:
            self._mcp_client = MultiServerMCPClient(self.mcp_servers)

        try:
            # Use the direct MCP client session for tool discovery
            server_name = f"rube_{AGENT_NAME}"
            tools_info = []

            async with self._mcp_client.session(server_name) as session:
                # List all tools using MCP protocol (inspired by langchain-mcp-adapters)
                current_cursor = None
                max_iterations = 100
                iterations = 0

                while True:
                    iterations += 1
                    if iterations > max_iterations:
                        self.logger.warning("Reached max iterations while discovering tools")
                        break

                    list_tools_result = await session.list_tools(cursor=current_cursor)

                    if list_tools_result.tools:
                        for tool in list_tools_result.tools:
                            # Extract useful info about each tool
                            tool_info = {
                                'name': tool.name,
                                'description': tool.description[:150] + '...' if len(tool.description) > 150 else tool.description,
                                'inputs': str(tool.inputSchema.get('properties', {}).keys()) if tool.inputSchema else 'None'
                            }
                            tools_info.append(tool_info)

                    # Check pagination
                    if not list_tools_result.nextCursor:
                        break
                    current_cursor = list_tools_result.nextCursor

            self.logger.info(f"Discovered {len(tools_info)} tools from Rube {AGENT_NAME} MCP server")
            return tools_info

        except Exception as e:
            self.logger.error(f"Tool discovery failed for Rube {AGENT_NAME}: {e}")
            return []


# Global MCP connection instance
_agent_mcp = AgentMCPConnection()

# =============================================================================
# SUB-AGENT WRAPPER EXAMPLE
# =============================================================================

# TODO: Add sub-agent tools if you have complex StateGraph workflows
# Example: Wrap a complex StateGraph as a tool for React Agent

@tool
def complex_workflow_tool(request: str, data: str = None) -> str:
    """
    Example: Wrap a complex StateGraph workflow as a tool
    Use this pattern if you have existing StateGraph workflows to integrate
    """
    try:
        # TODO: Import your complex workflow graph
        # from .complex_workflow.graph import graph

        # Prepare initial state
        initial_state = {
            "messages": [HumanMessage(content=request)],
        }

        # Add additional data if provided
        if data:
            try:
                import json
                data_dict = json.loads(data) if isinstance(data, str) else data
                initial_state["data"] = data_dict
            except (json.JSONDecodeError, TypeError):
                return f"Error: Invalid data format. Expected JSON string."

        # Execute the sub-graph
        # config = {"configurable": {"key": "value"}}
        # result = graph.invoke(initial_state, config=config)

        # For now, return example response
        return f"Complex workflow completed for: {request}"

        # Extract the result message
        # if result.get("messages"):
        #     final_message = result["messages"][-1]
        #     if hasattr(final_message, 'content'):
        #         return f"Workflow completed: {final_message.content}"
        #     else:
        #         return f"Workflow completed: {str(final_message)}"
        # else:
        #     return "Workflow completed successfully"

    except Exception as e:
        error_msg = f"Error in complex workflow: {str(e)}"
        print(f"DEBUG: {error_msg}")
        return error_msg

# =============================================================================
# TOOL AGGREGATION
# =============================================================================

def get_composio_tools() -> List[BaseTool]:
    """Get tools using direct Composio SDK integration"""
    if not COMPOSIO_AVAILABLE:
        return []

    try:
        # Initialize Composio toolset
        composio_toolset = ComposioToolSet()

        # Get tools for popular apps - start with essentials
        essential_apps = [
            App.GMAIL,      # Email management
            App.SLACK,      # Team communication
            App.GITHUB,     # Development tools
            App.NOTION,     # Note-taking and databases
            App.CALENDAR,   # Google Calendar
        ]

        composio_tools = []
        for app in essential_apps:
            try:
                app_tools = composio_toolset.get_tools(apps=[app])
                composio_tools.extend(app_tools)
                print(f"✅ Loaded {len(app_tools)} tools from {app.value}")
            except Exception as e:
                print(f"⚠️ Could not load tools from {app.value}: {e}")

        print(f"✅ Total Composio tools loaded: {len(composio_tools)}")
        return composio_tools

    except Exception as e:
        print(f"⚠️ Failed to initialize Composio tools: {e}")
        return []

async def get_agent_tools_with_mcp() -> List[BaseTool]:
    """Get all agent tools: Rube MCP meta-tools + Composio direct tools + local tools"""
    tools = []

    # Add sub-agent tools if needed
    # TODO: Uncomment if you have complex workflows to wrap
    # tools.append(complex_workflow_tool)

    # Add MCP tools from Rube
    try:
        mcp_tools = await _agent_mcp.get_mcp_tools()
        tools.extend(mcp_tools)

        if mcp_tools:
            print(f"✅ Loaded {len(mcp_tools)} Rube {AGENT_NAME} MCP tools: {[t.name for t in mcp_tools]}")
        else:
            print(f"⚠️ No Rube {AGENT_NAME} MCP tools available")

    except Exception as e:
        print(f"⚠️ Failed to load {AGENT_NAME} MCP tools: {e}")

    return tools


def get_agent_simple_tools() -> List[BaseTool]:
    """Synchronous wrapper for getting agent tools"""
    try:
        # Handle asyncio event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, get_agent_tools_with_mcp())
                return future.result(timeout=10)
        else:
            return asyncio.run(get_agent_tools_with_mcp())

    except Exception as e:
        print(f"⚠️ Rube {AGENT_NAME} MCP connection failed: {e}")

        # Fallback to sub-agent tools only
        # TODO: Return your local/sub-agent tools as fallback
        # return [complex_workflow_tool]
        return []


# =============================================================================
# TOOL DISCOVERY - Best Practice for Template Users
# =============================================================================

async def discover_mcp_tools() -> List[Dict[str, str]]:
    """
    TEMPLATE BEST PRACTICE: Discover all available tools from MCP server

    Use this function to discover tool names before adding them to USEFUL_TOOL_NAMES.
    Perfect for development, debugging, and template configuration.

    Returns:
        List of tool info dicts with 'name', 'description', and 'inputs' keys

    Example usage:
        tools_info = await discover_mcp_tools()
        for tool in tools_info:
            print(f"'{tool['name']}',  # {tool['description']}")
    """
    return await _agent_mcp.discover_all_tools()


def discover_mcp_tools_sync() -> List[Dict[str, str]]:
    """
    Synchronous wrapper for discover_mcp_tools()
    Use this in scripts or when you can't use async/await
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, discover_mcp_tools())
                return future.result(timeout=30)
        else:
            return asyncio.run(discover_mcp_tools())
    except Exception as e:
        print(f"⚠️ Tool discovery failed: {e}")
        return []


def print_discovered_tools():
    """
    TEMPLATE HELPER: Print all discovered tools in copy-paste format for USEFUL_TOOL_NAMES

    Run this function to get the exact tool names to add to your USEFUL_TOOL_NAMES set.
    Perfect for template configuration and debugging.
    """
    print(f"\n🔍 Discovering Rube {AGENT_NAME.upper()} MCP Tools...")
    print("=" * 60)

    tools_info = discover_mcp_tools_sync()

    if not tools_info:
        print(f"❌ No tools discovered. Check your Rube MCP server configuration.")
        print(f"Environment variable: {MCP_ENV_VAR}")
        print(f"Current value: {os.getenv(MCP_ENV_VAR, 'NOT SET')}")
        return

    print(f"✅ Discovered {len(tools_info)} tools:")
    print("\n📋 Copy these lines to your USEFUL_TOOL_NAMES:")
    print("USEFUL_TOOL_NAMES = {")

    for tool in tools_info:
        # Truncate description for clean output
        desc = tool['description'][:80] + '...' if len(tool['description']) > 80 else tool['description']
        print(f"    '{tool['name']}',  # {desc}")

    print("}")

    print(f"\n📊 Tool Details:")
    for i, tool in enumerate(tools_info, 1):
        print(f"{i:2d}. {tool['name']}")
        print(f"    Description: {tool['description']}")
        print(f"    Inputs: {tool['inputs']}")
        print()


if __name__ == "__main__":
    """Run tool discovery when script is executed directly"""
    print_discovered_tools()
