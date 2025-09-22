"""
Email Agent Orchestrator - React Agent Pattern
Clean implementation following same pattern as calendar_agent and job_search_agent
Uses create_react_agent with MCP tools from Pipedream Gmail
"""

import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv

from .tools import get_email_simple_tools
from .prompt import ROUTER_AGENT_SYSTEM_PROMPT
from .create_draft_workflow.config import LLM_CONFIG

# Load environment variables
load_dotenv()


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
    Email agent orchestrator following React Agent pattern
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
        """Build React agent following same pattern as other agents"""

        # Get current context for time-aware prompts
        context = get_current_context()

        # Enhanced prompt with context and tool information
        enhanced_prompt = f"""{ROUTER_AGENT_SYSTEM_PROMPT}

**CURRENT CONTEXT (use for all time references):**
- Now: {context['current_time']}
- Timezone: {context['timezone_name']}
- Today: {context['today']}
- Tomorrow: {context['tomorrow']}
- Current Time: {context['time_str']}

**AVAILABLE TOOLS IN THIS SESSION:**
The tools available to you include:
- create_draft_workflow_tool: Complex email drafting and workflow (uses sub-agent)
- Gmail MCP tools (if configured): gmail-list-messages, gmail-create-draft, etc.

**EMAIL WORKFLOW STRATEGY:**
1. For simple email queries: Use direct MCP tools if available
2. For complex email processing: Use create_draft_workflow_tool (sub-agent)
3. For email composition/drafting: Prefer create_draft_workflow_tool for human-in-the-loop

**IMPORTANT GUIDELINES:**
- Always use current time context from above for email timestamps
- Be precise about email operations (list, draft, send, reply)
- Route complex workflows to create_draft_workflow_tool
- Keep responses concise and actionable

When an operation completes successfully, you can end the conversation.
"""

        # Create React agent with tools and enhanced prompt
        react_agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=enhanced_prompt,
            name="email_agent"
        )

        return react_agent


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
    Main entry point for graph.py
    Returns React agent ready for LangGraph Studio and supervisor
    """
    return create_default_orchestrator()


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
