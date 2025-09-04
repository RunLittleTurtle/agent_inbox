"""Multi-agent supervisor system using langgraph-supervisor framework.

This module implements a clean multi-agent architecture with:
- Calendar agent for Google Calendar operations via MCP
- Email agent for email management tasks
- Supervisor using official langgraph_supervisor patterns
- Automatic agent handoff and state management
- LangSmith tracing for observability

All agents follow pure LangGraph create_react_agent patterns for consistency.
"""

import os
import sys
from dotenv import load_dotenv
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import List
from langchain_core.messages import BaseMessage
from pydantic import BaseModel

# Load environment variables for LangSmith integration
load_dotenv()

class WorkflowState(BaseModel):
    """Enhanced state with timezone and temporal context for all agents"""
    messages: List[BaseMessage]
    current_time: str
    timezone: str
    timezone_name: str

# Add local libraries to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../library/langgraph'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../library/langgraph_supervisor-py'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../library/langchain-mcp-adapters'))

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

# LangGraph imports
from langgraph.prebuilt import create_react_agent

# Local supervisor imports
from langgraph_supervisor import create_supervisor

# Calendar agent import with graceful fallback if MCP integration unavailable
# This allows the system to work even if calendar tools aren't configured
calendar_tools = []
try:
    from src.calendar_agent.calendar_orchestrator import get_calendar_tools_for_supervisor
    print("Calendar agent import successful")
except ImportError as e:
    print(f"Calendar agent not available: {e}")


async def create_calendar_agent():
    """Create calendar agent using pure LangGraph create_react_agent pattern"""
    from src.calendar_agent.calendar_orchestrator import CalendarAgentWithMCP

    # Use Anthropic Claude for calendar operations
    # Claude handles longer tool names better than OpenAI models
    calendar_model = ChatAnthropic(
        model="claude-sonnet-4-20250514",
        temperature=0,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        streaming=False
    )

    # Create calendar agent instance with MCP integration
    calendar_agent_instance = CalendarAgentWithMCP(model=calendar_model)
    await calendar_agent_instance.initialize()

    # Return the LangGraph agent (create_react_agent) for supervisor integration
    return await calendar_agent_instance.get_agent()


def get_current_context():
    """Get current time and timezone context using USER_TIMEZONE from .env"""
    user_timezone = os.getenv("USER_TIMEZONE", "America/Toronto")
    timezone_zone = ZoneInfo(user_timezone)
    current_time = datetime.now(timezone_zone)

    return {
        "current_time": current_time.isoformat(),
        "timezone": str(timezone_zone),
        "timezone_name": user_timezone
    }

def create_email_agent():
    """Create email agent for email operations using LangGraph create_react_agent"""
    # Use OpenAI GPT-4o-mini for email operations (cost-effective for text tasks)
    email_model = ChatOpenAI(model="gpt-4o", temperature=0)

    email_prompt = """You are an email management expert.
    Help users with email composition, sending, reading, and organization."""

    # Create pure LangGraph react agent (no tools configured yet)
    return create_react_agent(
        model=email_model,
        tools=[],  # No email tools configured yet
        name="email_agent",
        prompt=email_prompt
    )


async def create_supervisor_graph():
    """Create multi-agent supervisor using official langgraph_supervisor patterns"""

    # Create agents using pure LangGraph create_react_agent patterns
    # Both agents follow the same architectural pattern for consistency
    calendar_agent = await create_calendar_agent()
    email_agent = create_email_agent()

    # Use OpenAI GPT-4o for supervisor routing decisions
    # GPT-4o performs well at understanding user intent and routing requests
    supervisor_model = ChatOpenAI(
        model="gpt-4o",
        temperature=0,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    # Add dynamic context to supervisor prompt for better decision making
    user_timezone = os.getenv("USER_TIMEZONE", "America/Toronto")
    current_time = datetime.now(ZoneInfo(user_timezone))

    # Create supervisor prompt following langgraph_supervisor best practices
    supervisor_prompt = f"""You are a team supervisor managing specialized agents.

CURRENT CONTEXT:
- Today: {current_time.strftime("%Y-%m-%d")} at {current_time.strftime("%I:%M %p")}
- Timezone: {user_timezone}

AGENT CAPABILITIES:
- calendar_agent: Handles all calendar operations (scheduling, viewing events, availability)
- email_agent: Handles email composition, sending, reading, and organization

ROUTING RULES:
- ALWAYS look if the request is related to an agent first, onlyif not, handle it yourself
- For calendar/scheduling requests → Use calendar_agent
- For email requests → Use email_agent
- For general questions → Handle directly or route to most appropriate agent

BEHAVIOR:
- When feedback comes back from an agent, analyze the feedback and adjust the routing rules accordingly
- If more actions needs to be taken by an agent, route to the appropriate agent, DO NOT answer yourself
- Your main job is to route to an agent
- CRITICAL : You have no tools, you must route to the appropriate agent.

Be decisive in your routing. Call the appropriate agent transfer tool immediately."""

    # Create supervisor using official langgraph_supervisor framework
    # This handles all agent handoffs and message flow automatically
    workflow = create_supervisor(
        agents=[calendar_agent, email_agent],
        model=supervisor_model,
        prompt=supervisor_prompt,
        supervisor_name="multi_agent_supervisor",
        output_mode="last_message",
        add_handoff_back_messages=True  # Automatic agent return handling
    )

    # Compile the workflow into an executable graph
    compiled_graph = workflow.compile(name="multi_agent_system")
    print("Clean multi-agent supervisor created following official patterns")
    return compiled_graph


# Export the main graph using supervisor pattern
async def make_graph():
    """Factory function for LangGraph server integration"""
    # Create the multi-agent supervisor that handles routing between agents
    graph_instance = await create_supervisor_graph()
    print("Using dynamic supervisor with langgraph-supervisor library")
    return graph_instance

# Synchronous wrapper for LangGraph server compatibility
def create_graph():
    """Synchronous graph factory required by LangGraph server"""
    import asyncio
    return asyncio.run(make_graph())

# Main graph instance exported for LangGraph server
graph = create_graph()
