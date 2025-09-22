import os
import sys
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from langchain_core.tools import tool, BaseTool
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add library path for langchain-mcp-adapters
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../library/langchain-mcp-adapters'))

from langchain_mcp_adapters.client import MultiServerMCPClient


class EmailMCPConnection:
    """
    Simplified MCP connection for Gmail tools using Pipedream
    Based on calendar_agent pattern but simplified for email use case
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._mcp_client: Optional[MultiServerMCPClient] = None
        self._mcp_tools: List[BaseTool] = []
        self._tools_cache_time: Optional[datetime] = None

        # Get Pipedream Gmail URL from environment
        self.pipedream_gmail_url = os.getenv("PIPEDREAM_MCP_SERVER_google_gmail")

        if self.pipedream_gmail_url:
            self.mcp_servers = {
                "pipedream_gmail": {
                    "url": self.pipedream_gmail_url,
                    "transport": "streamable_http"
                }
            }
        else:
            self.mcp_servers = {}

    async def get_mcp_tools(self) -> List[BaseTool]:
        """Get Gmail MCP tools with caching (simplified from calendar pattern)"""

        # Use cached tools if available and fresh (5 min cache)
        if (self._mcp_tools and self._tools_cache_time and
            (datetime.now() - self._tools_cache_time).seconds < 300):
            return self._mcp_tools

        # No MCP server configured
        if not self.pipedream_gmail_url:
            self.logger.warning("No Pipedream Gmail MCP server configured")
            return []

        self.logger.info(f"Connecting to Pipedream Gmail MCP: {self.pipedream_gmail_url}")

        # Reuse MCP client to prevent memory leaks
        if self._mcp_client is None:
            self._mcp_client = MultiServerMCPClient(self.mcp_servers)

        try:
            # Add timeout to prevent hanging
            tools = await asyncio.wait_for(
                self._mcp_client.get_tools(),
                timeout=30.0
            )

            # Use ALL available Gmail MCP tools from Pipedream
            # Based on https://mcp.pipedream.com/app/gmail
            useful_tools = []
            useful_tool_names = {
                # Email Management
                'gmail-send-email',                    # Send Email
                'gmail-find-email',                    # Find Email
                'gmail-delete-email',                  # Delete Email
                'gmail-archive-email',                 # Archive Email

                # Draft Management (excluded - use sub-agent instead)
                # 'gmail-create-draft',               # Excluded: use create_draft_workflow sub-agent

                # Labels
                'gmail-list-labels',                   # List Labels
                'gmail-add-label-to-email',           # Add Label to Email
                'gmail-remove-label-from-email',      # Remove Label from Email
                'gmail-create-label',                  # Create Label

                # Attachments
                'gmail-download-attachment',           # Download Attachment

                # Send As / Aliases
                'gmail-list-send-as-aliases',         # List Send As Aliases
                'gmail-get-send-as-alias',            # Get Send As Alias

                # Signatures
                'gmail-update-signature-for-primary-email-address',  # Update Signature for Primary Email Address
                'gmail-update-signature-for-email-in-organization',  # Update Signature for Email in Organization

                # Workflow
                'gmail-approve-workflow',              # Approve Workflow

                # Additional common tools that might be available
                'gmail-list-messages',                 # List messages (common)
                'gmail-get-message',                   # Get message (common)
                'gmail-list-drafts',                   # List drafts (common)
                'gmail-reply-to-email',                # Reply to email (common)
                'gmail-forward-email',                 # Forward email (common)
            }

            for tool in tools:
                if tool.name in useful_tool_names:
                    useful_tools.append(tool)
                else:
                    # Log unknown tools for debugging
                    self.logger.debug(f"Unknown Gmail tool: {tool.name}")

            self.logger.info(f"Loaded {len(useful_tools)} useful Gmail MCP tools: {[t.name for t in useful_tools]}")

            # Cache results
            self._mcp_tools = useful_tools
            self._tools_cache_time = datetime.now()
            return useful_tools

        except asyncio.TimeoutError:
            self.logger.error("Gmail MCP tools loading timed out")
            return []
        except Exception as e:
            self.logger.error(f"Failed to load Gmail MCP tools: {e}")
            return []


# Global MCP connection instance
_email_mcp = EmailMCPConnection()


@tool
def create_draft_workflow_tool(request: str, email_data: str = None) -> str:
    """
    Tool that encapsulates the create_draft_workflow as a sub-agent.

    Args:
        request: The user's request or email content to process
        email_data: Optional email data (JSON string format)

    Returns:
        Result from the draft workflow execution
    """
    try:
        from .create_draft_workflow.graph import graph

        # Prepare initial state for the create_draft_workflow
        initial_state = {
            "messages": [HumanMessage(content=request)],
        }

        # Add email data if provided
        if email_data:
            try:
                import json
                email_dict = json.loads(email_data) if isinstance(email_data, str) else email_data
                initial_state["email"] = email_dict
            except (json.JSONDecodeError, TypeError):
                return f"Error: Invalid email_data format. Expected JSON string."

        # Execute the create_draft_workflow sub-graph
        config = {"configurable": {"db_id": 1, "model": "claude-3-5-sonnet-20241022"}}
        result = graph.invoke(initial_state, config=config)

        # Extract the result message
        if result.get("messages"):
            final_message = result["messages"][-1]
            if hasattr(final_message, 'content'):
                return f"Draft workflow completed: {final_message.content}"
            else:
                return f"Draft workflow completed: {str(final_message)}"
        else:
            return "Draft workflow completed successfully (no message content)"

    except Exception as e:
        error_msg = f"Error in create_draft_workflow: {str(e)}"
        print(f"DEBUG: {error_msg}")
        return error_msg


async def get_email_tools_with_mcp() -> List[BaseTool]:
    """
    Get all Gmail MCP tools from Pipedream
    Note: create_draft_workflow is handled as sub-agent, not exposed as direct tool
    """
    tools = []

    # Add create_draft_workflow_tool as sub-agent (for complex drafting workflows)
    tools.append(create_draft_workflow_tool)

    # Try to get MCP tools from Pipedream
    try:
        mcp_tools = await _email_mcp.get_mcp_tools()
        tools.extend(mcp_tools)

        if mcp_tools:
            print(f"✅ Loaded {len(mcp_tools)} Gmail MCP tools: {[t.name for t in mcp_tools]}")
        else:
            print("⚠️ No Gmail MCP tools available (fallback to local tools)")

    except Exception as e:
        print(f"⚠️ Failed to load MCP tools: {e}")
        print("📧 Using local tools only")

    return tools


def get_email_simple_tools() -> List[BaseTool]:
    """
    Synchronous wrapper for getting email tools
    For compatibility with existing orchestrator
    """
    try:
        # Try to get tools with MCP
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If event loop is running, use asyncio.create_task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, get_email_tools_with_mcp())
                return future.result(timeout=10)
        else:
            # No event loop running, use asyncio.run
            return asyncio.run(get_email_tools_with_mcp())

    except Exception as e:
        print(f"⚠️ MCP connection failed: {e}")
        print("📧 Falling back to local tool only")

        # Fallback to just the local tool
        return [create_draft_workflow_tool]
