"""Multi-agent supervisor system using langgraph-supervisor framework.

This module implements a clean multi-agent architecture with:
- Calendar agent for Google Calendar operations via MCP
- Email agent for email management tasks
- Job search agent for job search tasks
- Supervisor using official langgraph_supervisor patterns
- Automatic agent handoff and state management
- LangSmith tracing for observability

All agents follow pure LangGraph create_react_agent patterns for consistency.
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import List, Optional
from langchain_core.messages import BaseMessage, AIMessage, ToolMessage
from pydantic import BaseModel
from langchain_core.messages import HumanMessage


# Import the global state from state.py
from src.state import WorkflowState

# Load environment variables for LangSmith integration
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add local libraries to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../library/langgraph'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../library/langgraph_supervisor-py'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../library/langchain-mcp-adapters'))

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

async def create_calendar_agent():
    """Create calendar agent with graceful fallback handling"""
    try:
        from src.calendar_agent.calendar_orchestrator import CalendarAgentWithMCP

        # Use Anthropic Claude for calendar operations
        calendar_model = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            temperature=0,
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            streaming=False
        )

        # Create calendar agent instance with MCP integration
        calendar_agent_instance = CalendarAgentWithMCP(model=calendar_model)
        await calendar_agent_instance.initialize()

        logger.info("Calendar agent with MCP integration initialized successfully")
        return await calendar_agent_instance.get_agent()

    except Exception as e:
        logger.error(f"Failed to create calendar agent with MCP: {e}")
        logger.info("Creating fallback calendar agent without MCP tools")

        # Fallback: basic calendar agent without MCP tools
        calendar_model = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            temperature=0,
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            streaming=False
        )

        fallback_prompt = """You are a calendar assistant.
        I apologize, but I cannot directly access your calendar at the moment due to a technical issue.
        I can provide general scheduling advice and help you plan your time, but cannot create, modify, or view actual calendar events.
        Please let me know how I can assist you with scheduling planning."""

        return create_react_agent(
            model=calendar_model,
            tools=[],
            name="calendar_agent_fallback",
            prompt=fallback_prompt
        )

async def create_email_agent():
    """Create email agent with MCP integration for email operations"""
    try:
        from src.email_agent.eaia.email_agent_orchestrator import create_email_agent as create_email_orchestrator

        # Use proper email agent orchestrator (returns compiled workflow)
        email_agent_workflow = create_email_orchestrator()

        logger.info("Email agent with MCP integration initialized successfully")
        return email_agent_workflow

    except Exception as e:
        logger.error(f"Failed to create email agent with MCP: {e}")
        logger.info("Creating fallback email agent without MCP tools")

        # Fallback: basic email agent without MCP tools
        email_model = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            temperature=0,
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            streaming=False
        )

        fallback_prompt = """You are Samuel's email assistant.
        I apologize, but I cannot directly access your Gmail at the moment due to a technical issue.
        I can provide email composition assistance and help you plan your communications, but cannot send, read, or manage actual emails.
        Please let me know how I can assist you with email planning and composition."""

        return create_react_agent(
            model=email_model,
            tools=[],
            name="email_agent_fallback",
            prompt=fallback_prompt
        )


async def create_drive_agent():
    """Create Google Drive agent with MCP integration for file management and Google Drive operations"""
    try:
        from src.drive_react_agent.x_agent_orchestrator import create_drive_agent as create_drive_orchestrator

        # Use proper drive agent orchestrator (returns compiled workflow)
        drive_agent_workflow = create_drive_orchestrator()

        logger.info("Google Drive agent with MCP integration initialized successfully")
        return drive_agent_workflow

    except Exception as e:
        logger.error(f"Failed to create drive agent with MCP: {e}")
        logger.info("Creating fallback drive agent without MCP tools")

        # Fallback: basic drive agent without MCP tools
        drive_model = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            temperature=0,
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            streaming=False
        )

        fallback_prompt = """You are a Google Drive assistant.
        I apologize, but I cannot directly access Google Drive at the moment due to a technical issue.
        I can provide general file management assistance and planning, but cannot perform actual operations.
        Please let me know how I can assist you with file management planning."""

        return create_react_agent(
            model=drive_model,
            tools=[],
            name="drive_agent_fallback",
            prompt=fallback_prompt
        )


async def create_job_search_agent():
    """Create job search agent using the orchestrator"""
    try:
        from src.job_search_agent.job_search_orchestrator import create_default_orchestrator

        logger.info("Creating job search agent with clean orchestrator...")

        # Create the compiled workflow directly
        workflow = create_default_orchestrator()

        logger.info("Job search agent created successfully with fixed orchestrator")
        return workflow

    except Exception as e:
        logger.error(f"Failed to create job search agent: {e}")
        # Fallback to simple react agent
        logger.info("Creating fallback job search agent...")

        job_model = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )

        job_prompt = """You are a job search specialist.
        Help users with job search strategies, application preparation, and career guidance.

        Current capabilities:
        - Resume and cover letter advice
        - Interview preparation
        - Job search strategies
        - Career planning guidance

        Note: Full job search workflow not available due to technical issues."""

        return create_react_agent(
            model=job_model,
            tools=[],
            name="job_search_agent_fallback",
            prompt=job_prompt
        )

def validate_environment():
    """Validate required environment variables"""
    required_vars = ["ANTHROPIC_API_KEY", "OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        raise EnvironmentError(f"Missing required environment variables: {missing_vars}")

    logger.info("Environment validation passed")

# -----------------------------
# Ensure supervisor always ends with a recap
# -----------------------------
async def post_model_hook(messages, model_output=None):
    """
    post_model_hook that ensures the supervisor ends with a recap message.

    Notes:
    - Many langgraph supervisor hooks receive the conversation messages and optionally
      the model output. If the real signature differs in your version of
      langgraph_supervisor, adapt the parameters accordingly (e.g., remove model_output
      or accept a kwargs).
    - We use langchain_core.messages.AIMessage which is already imported above.
    """
    try:
        # Defensive: handle sync or async usage
        # messages is expected to be a list-like of BaseMessage objects
        if not messages:
            return messages

        last_msg = messages[-1]
        # If last message is an AIMessage and already looks like a recap, do nothing.
        if isinstance(last_msg, AIMessage) and ("recap" in last_msg.content.lower() or "summary" in last_msg.content.lower()):
            return messages

        # Create a short recap from the last AI or Tool message content available.
        # We'll try to extract a short snippet because models may produce long content.
        source_text = ""
        # prefer last AIMessage, else fallback to last message content
        for m in reversed(messages):
            if isinstance(m, AIMessage) or isinstance(m, ToolMessage):
                source_text = (m.content or "").strip()
                if source_text:
                    break

        # fallback safe default
        if not source_text:
            recap_content = "Recap: The supervisor completed routing and agent handoff as required."
        else:
            # Keep recap short — first 480 chars, and remove newlines for compactness
            short_snippet = " ".join(source_text.splitlines())[:480].strip()
            recap_content = f"Recap: {short_snippet}"

        # Append the recap as an AIMessage
        messages.append(AIMessage(content=recap_content))
        return messages

    except Exception as e:
        logger.exception("post_model_hook failed — returning original messages.")
        return messages

async def create_supervisor_graph():
    """Create multi-agent supervisor with improved error handling"""
    try:
        # Validate environment first
        validate_environment()

        # Create agents with individual error handling
        logger.info("Creating agents...")
        calendar_agent = await create_calendar_agent()
        email_agent = await create_email_agent()
        drive_agent = await create_drive_agent()
        job_search_agent = await create_job_search_agent()


        logger.info("All agents created successfully")

        # Create supervisor model
        supervisor_model = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            temperature=0,
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
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
- email_agent: **PRIMARY EMAIL AGENT** - Email composition/drafting/writing → email_agent / Email management (list, send drafts, search) → email_agent / Email reading/organization/ → email_agent
- ALL EMAIL TASKS → email_agent (autonomous subgraph)
- job_search_agent: CV upload, Job Offer, Job search, resume/cover letter advice, interview prep
- drive_agent: File management, Google Drive integration, file sharing, document collaboration

ROUTING STRATEGY:
1. ANALYZE the user's request carefully
2. IDENTIFY which agent is most appropriate
3. ROUTE immediately to that agent
4. Let the agent handle the task completely

ROUTING RULES:
- Calendar/scheduling/appointments/meetings → calendar_agent
- ALL EMAIL TASKS (composition, sending, management, organization, triage) → email_agent
- Job search/career/resume/interviews/CV → job_search_agent
- General questions of the world → Only if there is no agent related, you can answer

EMAIL ROUTING - IMPORTANT:
- Any mention of email, Gmail, inbox, sending, drafting, replying → email_agent
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
            agents=[calendar_agent, email_agent, drive_agent, job_search_agent],
            model=supervisor_model,
            prompt=supervisor_prompt,
            supervisor_name="multi_agent_supervisor",
            output_mode="last_message",
            add_handoff_back_messages=True,
            post_model_hook=post_model_hook,
        )

        # Compile the workflow
        compiled_graph = workflow.compile(name="multi_agent_system")
        logger.info("Multi-agent supervisor created successfully")
        return compiled_graph

    except Exception as e:
        logger.error(f"Failed to create supervisor graph: {e}")
        raise

async def make_graph():
    """Factory function for LangGraph server integration with error handling"""
    try:
        graph_instance = await create_supervisor_graph()
        logger.info("Graph creation completed successfully")
        return graph_instance
    except Exception as e:
        logger.error(f"Graph creation failed: {e}")
        raise

def create_graph():
    """Synchronous graph factory with proper error handling"""
    try:
        return asyncio.run(make_graph())
    except Exception as e:
        logger.error(f"Synchronous graph creation failed: {e}")
        raise

# Create graph instance with error handling
try:
    graph = create_graph()
    logger.info("Graph initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize graph: {e}")
    graph = None
