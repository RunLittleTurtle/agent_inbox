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
from langchain_core.messages import BaseMessage
from pydantic import BaseModel

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
    """Create email agent for email operations"""
    try:
        email_model = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )

        email_prompt = """You are an email management expert.
        Help users with email composition, sending, reading, and organization.

        Current capabilities:
        - Email composition assistance
        - Email etiquette and formatting guidance
        - Email organization strategies

        Note: Direct email sending is not yet configured."""

        return create_react_agent(
            model=email_model,
            tools=[],
            name="email_agent",
            prompt=email_prompt
        )
    except Exception as e:
        logger.error(f"Failed to create email agent: {e}")
        raise

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

async def create_supervisor_graph():
    """Create multi-agent supervisor with improved error handling"""
    try:
        # Validate environment first
        validate_environment()

        # Create agents with individual error handling
        logger.info("Creating agents...")
        calendar_agent = await create_calendar_agent()
        email_agent = await create_email_agent()
        job_search_agent = await create_job_search_agent()

        logger.info("All agents created successfully")

        # Create supervisor model
        supervisor_model = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            openai_api_key=os.getenv("OPENAI_API_KEY")
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
- email_agent: **PRIMARY EMAIL AGENT** - Complete email management, Gmail integration, triage, drafting, sending,
- job_search_agent: CV upload, Job Offer, Job search, resume/cover letter advice, interview prep

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
            agents=[calendar_agent, email_agent, job_search_agent],
            model=supervisor_model,
            prompt=supervisor_prompt,
            supervisor_name="multi_agent_supervisor",
            output_mode="last_message",
            add_handoff_back_messages=True
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
