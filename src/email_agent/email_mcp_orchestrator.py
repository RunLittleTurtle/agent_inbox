"""
Email Agent using official langchain-mcp-adapters patterns.
Implementation following the exact same pattern as calendar_agent.
Reference: Calendar agent working implementation
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
from langgraph.types import Command
from dotenv import load_dotenv


load_dotenv()

# Add library path for langchain-mcp-adapters
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../library/langchain-mcp-adapters'))

# Local langchain-mcp-adapters imports
from langchain_mcp_adapters.client import MultiServerMCPClient
from .prompt import REACT_AGENT_SYSTEM_PROMPT
from .compose_tool import compose_email, revise_email
from .human_in_the_loop import add_human_in_the_loop


class EmailAgentWithMCP:
    """
    Email agent using official langchain-mcp-adapters patterns.
    Follows the exact same pattern as calendar agent.
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

        # MCP server configuration - connect to Pipedream Gmail MCP server
        pipedream_gmail_url = os.getenv("PIPEDREAM_MCP_SERVER_google_gmail")
        if pipedream_gmail_url:
            self.mcp_servers = mcp_servers or {
                "pipedream_gmail": {
                    "url": pipedream_gmail_url,
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
        self.checkpointer = InMemorySaver()  # Store checkpointer as instance variable

        # Setup logging
        self.logger = logging.getLogger(__name__)

    async def _get_mcp_tools(self):
        """Get Gmail MCP tools using the same pattern as calendar agent"""

        # Use cached tools if available and fresh (same as calendar agent)
        if (self._mcp_tools and self._tools_cache_time and
            (datetime.now() - self._tools_cache_time).seconds < 300):  # 5 min cache
            return self._mcp_tools

        # Get Gmail MCP URL
        mcp_url = self.mcp_servers.get("pipedream_gmail", {}).get("url")
        if not mcp_url:
            raise ValueError("Pipedream Gmail MCP server URL not configured")

        self.logger.info(f"Connecting to Pipedream Gmail MCP server: {mcp_url}")

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
            self.logger.info(f"Loaded {len(tools)} Gmail MCP tools: {[t.name for t in tools]}")
        except asyncio.TimeoutError:
            self.logger.error("Gmail MCP tools loading timed out")
            raise Exception("Gmail MCP server connection timed out")

        # Cache results
        self._mcp_tools = tools
        self._tools_cache_time = datetime.now()
        return tools

    async def initialize(self):
        """Initialize MCP client and load Gmail tools using official patterns"""
        try:
            # Use improved MCP connection with caching and timeout
            mcp_tools = await self._get_mcp_tools()

            # Add compose tools to the tool set
            local_tools = [compose_email, revise_email]

            # Combine MCP and local tools
            all_tools = mcp_tools + local_tools

            # Apply human-in-the-loop wrapper ONLY to destructive email sending actions
            # NOT to draft creation - we want draft creation to happen automatically
            approval_required_tools = {
                'gmail-send-email',      # Only require approval for actual sending
                'gmail-reply-to-email',  # Sending a reply
                'gmail-forward-email',   # Forwarding
                'gmail-delete-email'     # Deleting
                # NOTE: 'gmail-create-draft' removed - drafts should be created without interruption
            }

            wrapped_tools = []
            for tool in all_tools:
                if tool.name in approval_required_tools:
                    # Wrap with human approval
                    wrapped_tool = add_human_in_the_loop(
                        tool,
                        interrupt_config={
                            "allow_accept": True,
                            "allow_edit": True,
                            "allow_respond": True,
                            "continue_after_approval": True  # Custom flag to indicate continuation
                        }
                    )
                    wrapped_tools.append(wrapped_tool)
                    self.logger.info(f"Added human-in-the-loop to {tool.name}")
                else:
                    # No approval needed for draft creation and read-only tools
                    wrapped_tools.append(tool)

            # Store wrapped tools
            self.tools = wrapped_tools

            self.logger.info(f"Loaded {len(mcp_tools)} Gmail MCP tools")
            self.logger.info(f"Added {len(local_tools)} local composition tools")
            self.logger.info(f"Applied human-in-the-loop to email sending tools only")

        except Exception as e:
            self.logger.error(f"Failed to initialize Gmail MCP client: {e}")
            # Fallback to local tools only if MCP fails
            local_tools = [compose_email, revise_email]
            self.tools = local_tools
            self.logger.warning(f"Using local tools only: {len(self.tools)} tools available")

    async def get_agent(self):
        """Create React agent with Gmail MCP tools and human-in-the-loop support"""
        if self.graph is None:
            # Use all wrapped tools (includes human-in-the-loop)
            self.logger.info(f"Creating email agent with {len(self.tools)} tools (with human approval for sending)")

            # Create tool descriptions for LLM guidance
            tool_descriptions = []
            for tool in self.tools:
                tool_descriptions.append(f"- {tool.name}: {tool.description}")

            tools_list = "\n".join(tool_descriptions)

            # Enhanced prompt with complete tool information and clear workflow
            enhanced_prompt = f"""{REACT_AGENT_SYSTEM_PROMPT}

**AVAILABLE EMAIL TOOLS IN THIS SESSION:**
{tools_list}

**IMPORTANT WORKFLOW FOR SENDING EMAILS:**
When a user asks you to send an email, you MUST follow this exact sequence:
1. Use `compose_email` to create the email content
2. Use `gmail-create-draft` to save it as a draft (this happens automatically, no approval needed)
3. Use `gmail-send-email` to send the draft (this will pause for human approval)
4. After approval, the email will be sent automatically

CRITICAL: When the user approves the email send action, the tool will complete the sending automatically.
Do NOT ask the user if they want to send after they've already approved - the approval IS the confirmation to send.

The workflow is: compose → create draft → request approval to send → send (upon approval)
"""

            # Create React agent with wrapped tools and checkpointer for interrupts
            self.graph = create_react_agent(
                model=self.model,
                tools=self.tools,
                prompt=enhanced_prompt,
                checkpointer=self.checkpointer,  # Required for human-in-the-loop
                name="email_agent_mcp"
            )

            self.logger.info("Email agent created with human-in-the-loop support and checkpointer")
        return self.graph

    async def stream(self, messages: Dict[str, Any], config: Dict[str, Any]):
        """
        Stream agent responses with interrupt support.

        Args:
            messages: Input messages for the agent
            config: Configuration including thread_id

        Returns:
            Generator of agent response chunks
        """
        if self.graph is None:
            await self.get_agent()

        # Use the stream method for async streaming
        async for chunk in self.graph.astream(messages, config):
            yield chunk

    async def resume(self, command: Command, config: Dict[str, Any]):
        """
        Resume agent execution after interrupt with human input.

        Args:
            command: Command object with resume value
            config: Configuration including thread_id

        Returns:
            Generator of agent response chunks
        """
        if self.graph is None:
            await self.get_agent()

        # Resume with the provided command
        async for chunk in self.graph.astream(command, config):
            yield chunk

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


async def create_email_agent_with_mcp(
    model: Optional[ChatAnthropic] = None,
    mcp_servers: Optional[Dict[str, Dict[str, Any]]] = None
) -> EmailAgentWithMCP:
    """
    Factory function to create and initialize email agent with MCP.

    Args:
        model: ChatAnthropic model instance
        mcp_servers: MCP server configurations

    Returns:
        Initialized EmailAgentWithMCP instance
    """
    agent = EmailAgentWithMCP(model=model, mcp_servers=mcp_servers)
    await agent.initialize()
    return agent


if __name__ == "__main__":
    async def test_email_agent():
        """Test the email agent with proper MCP integration and interrupt handling"""
        print("Testing Email Agent with human-in-the-loop...")

        agent = await create_email_agent_with_mcp()

        print(f"Agent created with {len(agent.tools)} tools")

        # Test message with proper config for checkpointer
        config = {"configurable": {"thread_id": "test_thread_1"}}

        # Stream the initial request
        print("\n--- Initial Request ---")
        async for chunk in agent.stream(
            {"messages": [{"role": "user", "content": "Send an email to test@example.com saying hello"}]},
            config
        ):
            print(chunk)
            # Check if we hit an interrupt
            if "interrupt" in str(chunk):
                print("\n--- Agent paused for approval ---")
                break

        # Simulate human approval
        print("\n--- Resuming with approval ---")
        async for chunk in agent.resume(
            Command(resume=[{"type": "accept"}]),
            config
        ):
            print(chunk)

        await agent.cleanup()

    asyncio.run(test_email_agent())
