"""
Email Agent Orchestrator - Hybrid StateGraph Architecture
Clean implementation with:
- Router node for intelligent decision making
- ToolNode for MCP tools (gmail operations)
- Draft workflow subgraph node for complex workflows with interrupt propagation
Compatible with supervisor multi-agent system
"""

import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langgraph.prebuilt import create_react_agent, ToolNode
from langgraph.graph import StateGraph, MessagesState, START, END
from typing import TypedDict, Literal, Annotated
from dotenv import load_dotenv
import uuid

from .tools import get_email_simple_tools, create_synthetic_email_context
from .prompt import ROUTER_AGENT_SYSTEM_PROMPT
from .create_draft_workflow.config import LLM_CONFIG
from .create_draft_workflow.graph import graph as draft_workflow_graph

# Load environment variables
load_dotenv()


# State schema for hybrid StateGraph architecture
class EmailAgentState(MessagesState):
    """State for the hybrid email agent StateGraph"""
    next_action: Optional[Literal["tools", "draft_workflow", "end"]]
    tool_result: Optional[str]


def get_current_context():
    """Get current time and timezone context from environment"""
    user_timezone = os.getenv("USER_TIMEZONE", "America/Toronto")
    try:
        timezone_zone = ZoneInfo(user_timezone)
        current_time = datetime.now(timezone_zone)
        tomorrow = current_time + timedelta(days=1)

        return {
            "current_time": current_time.isoformat(),
            "timezone": str(timezone_zone),
            "timezone_name": user_timezone,
            "today": f"{current_time.strftime('%Y-%m-%d')} ({current_time.strftime('%A')})",
            "tomorrow": f"{tomorrow.strftime('%Y-%m-%d')} ({tomorrow.strftime('%A')})",
            "time_str": current_time.strftime('%I:%M %p %Z')
        }
    except Exception as e:
        # Fallback to UTC
        current_time = datetime.now(ZoneInfo("UTC"))
        return {
            "current_time": current_time.isoformat(),
            "timezone": "UTC",
            "timezone_name": "UTC",
            "today": f"{current_time.strftime('%Y-%m-%d')} ({current_time.strftime('%A')})",
            "tomorrow": f"{current_time.strftime('%Y-%m-%d')} ({current_time.strftime('%A')})",
            "time_str": current_time.strftime('%I:%M %p UTC')
        }


class EmailAgentOrchestrator:
    """
    Email agent orchestrator using hybrid StateGraph architecture
    - Router node for intelligent decision making
    - MCP tools for direct email operations
    - Draft workflow node (subgraph) for complex workflows with human-in-the-loop
    Compatible with supervisor multi-agent system
    """

    def __init__(self, llm_config: Dict[str, Any] = None):
        """Initialize orchestrator with proper API key handling"""
        self.llm_config = llm_config or LLM_CONFIG

        # Ensure API key is available
        api_key = self.llm_config.get("api_key") or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

        # Update config with confirmed API key
        self.llm_config = {**self.llm_config, "api_key": api_key}

        # Initialize model
        self.llm = ChatAnthropic(**self.llm_config)

        # Get tools (includes MCP tools if available)
        self.tools = get_email_simple_tools()

        # Build React agent workflow
        self.workflow = self._build_workflow()

    def _build_workflow(self):
        """Build hybrid StateGraph with React agent for MCP tools and draft workflow node"""

        # Get current context for time-aware prompts
        context = get_current_context()

        # Filter out create_draft_workflow_tool - it's now a node, not a tool
        mcp_tools_only = [tool for tool in self.tools if tool.name != "create_draft_workflow_tool"]

        # Create React agent for MCP tools (following calendar agent pattern)
        from langgraph.prebuilt import create_react_agent

        mcp_react_agent = create_react_agent(
            model=self.llm,
            tools=mcp_tools_only,
            name="email_mcp_agent",
            prompt=f"""{ROUTER_AGENT_SYSTEM_PROMPT}

**CURRENT CONTEXT:**
- Now: {context['current_time']}
- Timezone: {context['timezone_name']}

You are the MCP tools executor for email operations. Use the available Gmail tools to:
- List, search, and read emails
- Send emails and manage drafts
- Manage labels and attachments
- Handle email aliases and signatures

Be concise and efficient in your responses."""
        )

        # Create StateGraph
        graph_builder = StateGraph(EmailAgentState)

        # Add nodes
        graph_builder.add_node("router", self._router_node)
        graph_builder.add_node("mcp_tools", mcp_react_agent)  # React agent as a node
        graph_builder.add_node("draft_workflow", self._draft_workflow_node)

        # Set entry point
        graph_builder.set_entry_point("router")

        # Add conditional edges
        graph_builder.add_conditional_edges("router", self._route_after_router)

        # Add edges from action nodes back to END
        graph_builder.add_edge("mcp_tools", END)
        graph_builder.add_edge("draft_workflow", END)

        # Compile graph with name (following calendar agent pattern)
        return graph_builder.compile(name="email_agent")

    def _router_node(self, state: EmailAgentState, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Router node that decides between tools, draft workflow, or direct response"""

        context = get_current_context()

        # Enhanced router prompt for decision making
        router_prompt = f"""{ROUTER_AGENT_SYSTEM_PROMPT}

**CURRENT CONTEXT (use for all time references):**
- Now: {context['current_time']}
- Timezone: {context['timezone_name']}
- Today: {context['today']}
- Tomorrow: {context['tomorrow']}
- Current Time: {context['time_str']}

**ROUTING DECISION REQUIRED:**
Based on the user request, you must choose the appropriate approach:

1. **MCP Tools** - For simple operations like:
   - List emails (gmail-list-messages)
   - Create drafts (gmail-create-draft)
   - Send emails (gmail-send-email)

2. **Draft Workflow** - For complex operations like:
   - Email analysis and response drafting
   - Meeting scheduling assistance
   - Multi-step workflows requiring human approval
   - Any request to "draft" or "create" email responses

3. **Direct Response** - For simple informational requests

**IMPORTANT:**
- For "draft email" requests → Use draft workflow
- For "list emails" requests → Use MCP tools
- For general questions → Respond directly

Analyze the user's request and respond with your reasoning and chosen approach.
If choosing tools or draft workflow, indicate clearly which approach you're taking.
"""

        # Get the last user message
        user_message = state["messages"][-1].content if state["messages"] else ""

        # Create messages for LLM
        llm_messages = [
            HumanMessage(content=f"{router_prompt}\n\nUser Request: {user_message}")
        ]

        # Get LLM decision
        llm_response = self.llm.invoke(llm_messages)

        # Determine next action based on LLM response
        response_content = llm_response.content.lower()

        if any(keyword in response_content for keyword in ["draft workflow", "draft email", "create email", "human approval", "complex", "meeting"]):
            next_action = "draft_workflow"
        elif any(keyword in response_content for keyword in ["mcp tools", "list emails", "gmail-", "simple operation"]):
            next_action = "mcp_tools"  # Updated to match node name
        else:
            # Direct response - no further action needed
            next_action = "end"

        print(f"🧭 Router decision: {next_action} based on: {response_content[:100]}...")

        return {
            "messages": [llm_response],
            "next_action": next_action
        }

    async def _draft_workflow_node(self, state: EmailAgentState, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Draft workflow node - invokes subgraph with interrupt propagation (ASYNC)"""

        print("📧 Executing draft workflow node")

        # Get the original user request
        user_request = state["messages"][-2].content if len(state["messages"]) >= 2 else state["messages"][-1].content

        # Create synthetic email context
        synthetic_email = create_synthetic_email_context(user_request)

        # Prepare state for draft workflow
        draft_state = {
            "messages": [HumanMessage(content=user_request)],
            "email": synthetic_email
        }

        # CRITICAL: Pass config to maintain thread context for interrupts
        # The config will be passed automatically by StateGraph
        print(f"🔗 Invoking draft workflow subgraph with thread context")

        try:
            # FIXED: Use async invocation for subgraph with async nodes (draft_response)
            result = await draft_workflow_graph.ainvoke(draft_state, config=config)
            print("✅ Draft workflow completed successfully")

            return {
                "messages": result.get("messages", [AIMessage(content="Draft workflow completed")]),
                "next_action": "end"
            }

        except Exception as e:
            print(f"❌ Draft workflow error: {e}")
            return {
                "messages": [AIMessage(content=f"Error in draft workflow: {str(e)}")],
                "next_action": "end"
            }

    def _route_after_router(self, state: EmailAgentState) -> str:
        """Routing function after router node"""
        action = state.get("next_action", "end")
        print(f"🔀 Routing to: {action}")

        # If mcp_tools requested but no MCP tools available, go to end
        if action == "mcp_tools" and not any(tool.name != "create_draft_workflow_tool" for tool in self.tools):
            return "end"

        return action


# =============================================================================
# FACTORY FUNCTIONS - Same pattern as other agents
# =============================================================================

def create_email_agent_orchestrator(llm_config: Dict[str, Any] = None):
    """
    Factory function to create email agent orchestrator

    Args:
        llm_config: Optional LLM configuration

    Returns:
        React agent workflow ready for execution
    """
    orchestrator = EmailAgentOrchestrator(llm_config)
    return orchestrator.workflow


def create_default_orchestrator():
    """
    Create orchestrator with default configuration

    Returns:
        React agent workflow ready for execution
    """
    orchestrator = EmailAgentOrchestrator(LLM_CONFIG)
    return orchestrator.workflow


# =============================================================================
# MAIN INTERFACE FOR GRAPH.PY - Same pattern as other agents
# =============================================================================

def create_email_agent():
    """
    Main entry point for graph.py - returns compiled StateGraph
    Following calendar agent pattern for supervisor compatibility
    """
    orchestrator = EmailAgentOrchestrator(LLM_CONFIG)
    return orchestrator.workflow


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    """Example usage of the orchestrator"""

    try:
        # Create orchestrator
        workflow = create_default_orchestrator()

        print("🚀 Email Agent Orchestrator Created Successfully")
        print("✅ Ready for LangGraph Studio")
        print("✅ Uses React Agent pattern")
        print("✅ Compatible with supervisor system")
        print("✅ Includes MCP tools for Gmail")

        # Test basic functionality
        from langchain_core.messages import HumanMessage

        test_input = {"messages": [HumanMessage(content="What emails do I have?")]}
        result = workflow.invoke(test_input)

        if result and result.get("messages"):
            print("✅ Basic test successful")
        else:
            print("⚠️ Test completed but no messages returned")

    except Exception as e:
        print(f"❌ Error creating orchestrator: {e}")
        print("Check ANTHROPIC_API_KEY environment variable")
