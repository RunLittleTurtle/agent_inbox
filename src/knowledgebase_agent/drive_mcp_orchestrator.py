"""
Drive Agent using official langchain-mcp-adapters patterns.
Implementation following the exact same pattern as email_agent.
Reference: Email agent working implementation
"""

import os
import sys
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver
from dotenv import load_dotenv


load_dotenv()

# Add library path for langchain-mcp-adapters
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../library/langchain-mcp-adapters'))

# Local langchain-mcp-adapters imports
from langchain_mcp_adapters.client import MultiServerMCPClient
from .prompt import REACT_AGENT_SYSTEM_PROMPT
from .human_in_the_loop_drive import create_drive_approval_tools


class DriveAgentWithMCP:
    """
    Drive agent using official langchain-mcp-adapters patterns.
    Follows the exact same pattern as email agent.
    """

    def __init__(
        self,
        model: Optional[ChatAnthropic] = None,
        mcp_servers: Optional[Dict[str, Dict[str, Any]]] = None
    ):
        self.model = model or ChatAnthropic(
            model="claude-sonnet-4-20250514",
            temperature=0,
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
        )

        # MCP server configuration - connect to Pipedream Google Drive MCP server
        pipedream_drive_url = os.getenv("PIPEDREAM_MCP_SERVER_google_drive")
        if pipedream_drive_url:
            self.mcp_servers = mcp_servers or {
                "pipedream_google_drive": {
                    "url": pipedream_drive_url,
                    "transport": "streamable_http"
                }
            }
        else:
            # Fallback to no MCP servers if not configured
            self.mcp_servers = mcp_servers or {}

        # MCP client and tools (initialized async) with caching
        self._mcp_client: Optional[MultiServerMCPClient] = None
        self._mcp_tools: List[BaseTool] = []
        self._tools_cache_time: Optional[datetime] = None
        self.tools: List[BaseTool] = []
        self.graph = None

        # Setup logging
        self.logger = logging.getLogger(__name__)

    async def _get_mcp_tools(self):
        """Get Google Drive MCP tools using the same pattern as email agent"""

        # Use cached tools if available and fresh (same as email agent)
        if (self._mcp_tools and self._tools_cache_time and
            (datetime.now() - self._tools_cache_time).seconds < 300):  # 5 min cache
            return self._mcp_tools

        # Get Google Drive MCP URL
        mcp_url = self.mcp_servers.get("pipedream_google_drive", {}).get("url")
        if not mcp_url:
            raise ValueError("Pipedream Google Drive MCP server URL not configured")

        self.logger.info(f"Connecting to Pipedream Google Drive MCP server: {mcp_url}")

        # Reuse MCP client instance to prevent memory leaks
        # Creating new clients for each request can cause resource exhaustion
        if self._mcp_client is None:
            self._mcp_client = MultiServerMCPClient(self.mcp_servers)

        # Add timeout to prevent hanging connections
        try:
            tools = await asyncio.wait_for(
                self._mcp_client.get_tools(),
                timeout=30.0  # 30 second timeout
            )
            self.logger.info(f"Loaded {len(tools)} Google Drive MCP tools: {[t.name for t in tools]}")
        except asyncio.TimeoutError:
            self.logger.error("Google Drive MCP tools loading timed out")
            raise Exception("Google Drive MCP server connection timed out")

        # Cache results
        self._mcp_tools = tools
        self._tools_cache_time = datetime.now()
        return tools

    async def initialize(self):
        """Initialize MCP client and load Google Drive tools using official patterns"""
        try:
            # Use improved MCP connection with caching and timeout
            mcp_tools = await self._get_mcp_tools()

            # For now, using only MCP tools - add local drive tools here if you create them
            # local_tools = []  # Add drive-specific local tools here when available

            # Use only MCP tools for now
            all_tools = mcp_tools

            # Apply human-in-the-loop wrapper to drive tools requiring approval
            wrapped_tools = create_drive_approval_tools(all_tools)

            # Store wrapped tools
            self.tools = wrapped_tools

            self.logger.info(f"Loaded {len(mcp_tools)} Google Drive MCP tools")
            self.logger.info(f"Applied human-in-the-loop to {len(wrapped_tools)} total tools")

        except Exception as e:
            self.logger.error(f"Failed to initialize Google Drive MCP client: {e}")
            # Fallback to empty tools if MCP fails
            self.tools = create_drive_approval_tools([])
            self.logger.warning(f"Using no tools due to MCP failure")

    async def get_agent(self):
        """Create React agent with Google Drive MCP tools and human-in-the-loop support"""
        if self.graph is None:
            # Use all wrapped tools (includes human-in-the-loop)
            self.logger.info(f"Creating drive agent with {len(self.tools)} tools (with human approval)")

            # Create tool descriptions for LLM guidance
            tool_descriptions = []
            for tool in self.tools:
                tool_descriptions.append(f"- {tool.name}: {tool.description}")

            tools_list = "\n".join(tool_descriptions)

            # Enhanced prompt with complete tool information
            enhanced_prompt = f"""{REACT_AGENT_SYSTEM_PROMPT}

**AVAILABLE GOOGLE DRIVE TOOLS IN THIS SESSION:**
{tools_list}

Remember: For critical operations that require approval:
1. Call the tool → it will return "requires_approval" → 2. interrupt() for approval → 3. Tool executes after confirmation
Always be careful with file deletions, permissions changes, and other destructive operations.
"""

            # Create checkpointer for interrupt functionality
            checkpointer = InMemorySaver()

            # Create React agent with wrapped tools and checkpointer for interrupts
            self.graph = create_react_agent(
                model=self.model,
                tools=self.tools,
                prompt=enhanced_prompt,
                checkpointer=checkpointer,  # Required for human-in-the-loop
                name="drive_agent_mcp"
            )

            self.logger.info("Drive agent created with human-in-the-loop support and checkpointer")
        return self.graph

    async def cleanup(self):
        """Clean up MCP client resources"""
        if self._mcp_client:
            try:
                # MultiServerMCPClient doesn't have cleanup method, just close connections
                if hasattr(self._mcp_client, 'close'):
                    await self._mcp_client.close()
                # Clear the client reference
                self._mcp_client = None
                self.logger.info("MCP client cleaned up successfully")
            except Exception as e:
                self.logger.error(f"Error cleaning up MCP client: {e}")


async def create_drive_agent_with_mcp(
    model: Optional[ChatAnthropic] = None,
    mcp_servers: Optional[Dict[str, Dict[str, Any]]] = None
) -> DriveAgentWithMCP:
    """
    Factory function to create and initialize drive agent with MCP.

    Args:
        model: ChatAnthropic model instance
        mcp_servers: MCP server configurations

    Returns:
        Initialized DriveAgentWithMCP instance
    """
    agent = DriveAgentWithMCP(model=model, mcp_servers=mcp_servers)
    await agent.initialize()
    return agent


if __name__ == "__main__":
    async def test_drive_agent():
        """Test the drive agent with proper MCP integration"""
        print("Testing Drive Agent with langchain-mcp-adapters...")

        agent = await create_drive_agent_with_mcp()
        graph = await agent.get_agent()

        print(f"Agent created with {len(agent.tools)} tools")

        # Test message
        result = await graph.ainvoke({
            "messages": [{"role": "user", "content": "List my available Google Drive tools"}]
        })

        print("Agent response:", result["messages"][-1].content)

        await agent.cleanup()

    asyncio.run(test_drive_agent())
