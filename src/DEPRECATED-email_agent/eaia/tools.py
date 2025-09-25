import os
import sys
import asyncio
import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from langchain_core.tools import tool, BaseTool
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
from langsmith import traceable

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


def create_synthetic_email_context(user_request: str) -> dict:
    """Create synthetic email context from live chat request"""
    timestamp = datetime.now()
    return {
        "id": f"chat-{uuid.uuid4().hex[:8]}",
        "thread_id": "live-chat",
        "from_email": "user@chat.local",
        "subject": f"Live Chat Request: {user_request[:50]}{'...' if len(user_request) > 50 else ''}",
        "page_content": user_request,
        "send_time": timestamp.isoformat(),
        "to_email": "assistant@chat.local"
    }


@tool
@traceable(name="create_draft_workflow_subagent", run_type="chain")
async def create_draft_workflow_tool(request: str) -> str:
    """
    Tool for creating email drafts through live interactions with human interrupts.
    Supports draft creation, corrections, calendar invites, and email sending.

    CRITICAL: This tool MUST receive config from parent to maintain thread context.
    Without proper thread_id inheritance, interrupts won't reach agent-inbox UI.

    Args:
        request: The user's request for email draft assistance
        config: Runtime config with thread_id for interrupt propagation

    Returns:
        Clear, structured result from the draft workflow execution
    """
    try:
        print(f"🔧 create_draft_workflow_tool called for live interactions")

        # Set up import paths for both local and LangGraph server contexts
        import sys
        import os

        # Add both project root and email_agent as base paths
        current_dir = os.path.dirname(__file__)
        project_root = os.path.abspath(os.path.join(current_dir, '../../..'))
        email_agent_root = os.path.abspath(os.path.join(current_dir, '..'))

        for path in [project_root, email_agent_root]:
            if path not in sys.path:
                sys.path.insert(0, path)

        # Import the single unified StateGraph
        try:
            # Try absolute import first (LangGraph server)
            from src.email_agent.eaia.create_draft_workflow.graph import graph
            print("✅ Using absolute imports for StateGraph")
        except ImportError as e1:
            print(f"⚠️ Absolute import failed: {e1}")
            try:
                # Fallback to relative import (local development)
                from eaia.create_draft_workflow.graph import graph
                print("✅ Using relative imports for StateGraph")
            except ImportError as e2:
                return f"❌ Error: Could not import StateGraph. Absolute: {e1}, Relative: {e2}"

        # Create synthetic email context for live interactions
        synthetic_email = create_synthetic_email_context(request)
        initial_state = {
            "messages": [HumanMessage(content=request)],
            "email": synthetic_email
        }
        print(f"📧 Created synthetic email context: {synthetic_email['subject']}")

        # Use proper config from config.py/config.yaml - let get_config() load from YAML
        try:
            from src.email_agent.eaia.create_draft_workflow.config import LLM_CONFIG
            print("✅ Using absolute import for LLM_CONFIG")
        except ImportError as e1:
            print(f"⚠️ Absolute config import failed: {e1}")
            try:
                from eaia.create_draft_workflow.config import LLM_CONFIG
                print("✅ Using relative import for LLM_CONFIG")
            except ImportError as e2:
                return f"❌ Error: Could not import LLM_CONFIG. Absolute: {e1}, Relative: {e2}"

        # CRITICAL: Inherit parent thread context for interrupt propagation
        # This ensures interrupts reach the agent-inbox UI monitoring the parent thread
        import uuid
        import contextvars
        from langchain_core.runnables.config import var_child_runnable_config

        # Try to get the runtime config from LangChain's context
        parent_thread_id = None
        parent_config = {}

        try:
            # Access the runtime config from context variables
            runtime_config = var_child_runnable_config.get()
            if runtime_config:
                parent_config = runtime_config
                parent_thread_id = runtime_config.get("configurable", {}).get("thread_id")
                print(f"📍 Found parent thread_id from runtime context: {parent_thread_id}")
        except Exception as e:
            print(f"⚠️ Could not get runtime config: {e}")

        # Use parent thread_id to maintain interrupt context continuity
        config = {
            "configurable": {
                "db_id": parent_config.get("configurable", {}).get("db_id", 1),
                "model": "gpt-4o",  # Compatible with draft_response.py (uses ChatOpenAI)
                # CRITICAL: Use parent thread_id for interrupt visibility
                "thread_id": parent_thread_id or ("draft-" + uuid.uuid4().hex[:8]),
                # Pass through any assistant_id for proper routing
                "assistant_id": parent_config.get("configurable", {}).get("assistant_id", "email_agent"),
                # Preserve any other parent config values
                **{k: v for k, v in parent_config.get("configurable", {}).items()
                   if k not in ["db_id", "model", "thread_id", "assistant_id"]}
            }
        }

        print(f"🔐 Using thread_id for interrupt propagation: {config['configurable']['thread_id']}")
        print(f"🚀 Executing subagent with interrupt propagation enabled")

        # Direct graph execution with proper async context for LangSmith tracing
        try:
            # Use await directly to preserve tracing context
            # This ensures the subagent appears in LangSmith traces
            print(f"📊 Executing subagent with LangSmith tracing enabled")
            result = await graph.ainvoke(initial_state, config=config)
            print(f"✅ Subagent execution completed with tracing")

        except Exception as e:
            print(f"❌ Direct graph execution error: {e}")
            return f"❌ Error in draft workflow execution: {str(e)}"
        print(f"✅ Draft workflow execution completed")

        # Extract clear, structured output
        return extract_clear_workflow_output(result)

    except Exception as e:
        error_msg = f"❌ Error in create_draft_workflow: {str(e)}"
        print(f"DEBUG: {error_msg}")
        return error_msg


def extract_clear_workflow_output(result) -> str:
    """Extract clear, actionable output for React agent with proper formatting"""

    print(f"📤 Extracting output from result type: {type(result)}")

    # Handle server API response format
    if isinstance(result, dict) and "values" in result:
        # Server API returns {values: {...}, next: [...], ...}
        values = result["values"]
        if values and "messages" in values:
            messages = values["messages"]
        else:
            return "✅ Draft workflow completed - no messages in server response"
    elif isinstance(result, dict) and "messages" in result:
        # Direct graph invocation format
        messages = result["messages"]
    else:
        print(f"⚠️ Unexpected result format: {result}")
        return "✅ Draft workflow completed - unexpected result format"

    if not messages:
        return "✅ Draft workflow completed - no content generated"

    final_message = messages[-1]
    print(f"📤 Extracting output from final message: {type(final_message)}")

    # Handle message object vs dict format
    if hasattr(final_message, 'content'):
        content = final_message.content
        tool_calls = getattr(final_message, 'tool_calls', None)
    elif isinstance(final_message, dict):
        content = final_message.get('content', '')
        tool_calls = final_message.get('tool_calls', None)
    else:
        content = str(final_message)
        tool_calls = None

    # Check if it's already a formatted response
    if content and any(emoji in content for emoji in ["✅", "📧", "📅", "💬"]):
        print(f"📋 Returning pre-formatted content")
        return content

    # Handle tool calls
    if tool_calls:
        tool_call = tool_calls[0]
        action_name = tool_call["name"]

        print(f"🔧 Processing tool call: {action_name}")

        if action_name == "ResponseEmailDraft":
            draft_content = tool_call["args"]["content"]
            recipients = tool_call["args"].get("new_recipients", [])

            output = f"✅ **Email Draft Created:**\n\n{draft_content}"
            if recipients:
                output += f"\n\n📧 **Additional Recipients:** {', '.join(recipients)}"
            return output

        elif action_name == "SendCalendarInvite":
            invite_args = tool_call["args"]
            return f"📅 **Calendar Invite Created:**\n\n📍 **Event:** {invite_args['title']}\n🕐 **Time:** {invite_args['start_time']} - {invite_args['end_time']}\n👥 **Attendees:** {', '.join(invite_args['emails'])}"

        elif action_name == "Question":
            question_content = tool_call["args"]["content"]
            return f"❓ **Question for User:**\n\n{question_content}"

    # Handle regular message content
    if content:
        return f"💬 **Draft Workflow Result:**\n\n{content}"

    # Fallback
    return f"✅ Draft workflow completed successfully"


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
    Note: create_draft_workflow_tool is now async for proper tracing
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

        # Fallback to just the local tool (now async)
        return [create_draft_workflow_tool]
