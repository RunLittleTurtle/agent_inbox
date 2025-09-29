"""Multi-agent supervisor system using langgraph-supervisor framework.

This module implements a clean multi-agent architecture with:
- Calendar agent for Google Calendar operations via MCP
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

        fallback_prompt = """❌ CALENDAR AGENT ERROR: The calendar agent failed to initialize properly.

        **TECHNICAL ISSUE DETECTED:**
        - MCP calendar tools could not be loaded
        - This is likely due to configuration, API key, or import errors
        - Check the console logs for specific error details

        **CURRENT LIMITATIONS:**
        - ✅ I can provide general scheduling advice
        - ❌ I CANNOT access your actual Google Calendar
        - ❌ I CANNOT create, modify, or view real calendar events
        - ❌ I CANNOT check availability or book meetings

        **IMMEDIATE ACTION REQUIRED:**
        Please check system logs and fix the calendar agent configuration before using calendar features."""

        return create_react_agent(
            model=calendar_model,
            tools=[],
            name="calendar_agent_fallback",
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

async def create_multi_tool_rube_agent():
    """Create Multi-Tool Rube Agent with access to 500+ applications"""
    try:
        # Import the Multi-Tool Rube Agent configuration
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'multi_tool_rube_agent'))
        from tools import _agent_mcp

        logger.info("Creating Multi-Tool Rube Agent with Rube MCP integration...")

        # Create model for the agent
        rube_model = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            temperature=0,
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            streaming=False
        )

        # Get Rube MCP tools
        mcp_tools = await _agent_mcp.get_mcp_tools()

        # Filter to useful Rube tools
        useful_tools = [tool for tool in mcp_tools if hasattr(tool, 'name') and tool.name in {
            'RUBE_SEARCH_TOOLS',
            'RUBE_MULTI_EXECUTE_TOOL',
            'RUBE_CREATE_PLAN',
            'RUBE_MANAGE_CONNECTIONS',
            'RUBE_REMOTE_WORKBENCH',
            'RUBE_REMOTE_BASH_TOOL'
        }]

        logger.info(f"Found {len(useful_tools)} Rube tools: {[t.name for t in useful_tools]}")

        # Create agent prompt with confirmed capabilities
        rube_prompt = """You are the Multi-Tool Rube Agent with access to 89 tools across 10 connected applications through Rube MCP server.

**CONFIRMED CAPABILITIES (89 tools available):**

📧 **GMAIL** (11 tools) - Email Operations:
- Send emails, create drafts, fetch emails, list drafts
- Move emails to trash, search people, get attachments
- Access user profile and email management

📄 **CODA** (10 tools) - Document & Database Management:
- List and create documents, manage tables and rows
- Search documents, create pages, database operations
- Collaborative document editing and data management

💬 **SLACK** (8 tools) - Team Communication:
- Find channels, send messages, fetch conversation history
- Search messages, list channels and users
- Workspace communication management

🔧 **GITHUB** (10 tools) - Development & Collaboration:
- Find repositories, manage branches, create pull requests
- Merge branches, create issues, search issues/PRs
- Code review and repository management

📊 **GOOGLE SHEETS** (10 tools) - Spreadsheet Operations:
- Search spreadsheets, manage sheets, batch updates
- Add/delete sheets, clear values, update properties
- Data analysis and spreadsheet automation

📝 **GOOGLE DOCS** (7 tools) - Document Management:
- Search documents, update existing documents
- Get documents by ID, create from markdown
- Insert text and document formatting

📁 **GOOGLE DRIVE** (7 tools) - File Management:
- Upload files, manage sharing preferences
- Find and list files, create folders
- File organization and collaboration

📅 **GOOGLE CALENDAR** (8 tools) - Calendar Management:
- List calendars, find free slots, create events
- Get specific calendars, free/busy queries
- Event scheduling and availability management

📋 **NOTION** (8 tools) - Productivity & Notes:
- Search pages, create pages, add content blocks
- Fetch block contents, update pages, query databases
- Knowledge management and collaboration

🎯 **LINEAR** (10 tools) - Project Management:
- Manage user profile, list projects and issues
- Create and update issues, add comments
- Attach files and track project progress

**HOW TO USE YOUR TOOLS:**

1. **RUBE_SEARCH_TOOLS** - Discover tools by use case or platform
   - Example: Search for "gmail send email" or "coda create document"

2. **RUBE_MULTI_EXECUTE_TOOL** - Execute discovered tools with parameters
   - Always show discovered tools before executing
   - Handle parameters based on tool requirements

3. **RUBE_CREATE_PLAN** - Create multi-step workflow plans
4. **RUBE_MANAGE_CONNECTIONS** - Check app connection status
5. **RUBE_REMOTE_WORKBENCH** - Handle file operations
6. **RUBE_REMOTE_BASH_TOOL** - Execute system commands if needed

**WORKFLOW PATTERN:**
1. Understand the user's specific request
2. Use RUBE_SEARCH_TOOLS to find the right tools for the task
3. Show the user what tools were discovered
4. Execute using RUBE_MULTI_EXECUTE_TOOL with proper parameters
5. Present clear results and suggest next steps

**IMPORTANT GUIDELINES:**
- Always explain what you're doing and why
- Show discovered tools before executing them
- Handle errors gracefully and provide alternatives
- Ask for confirmation before destructive operations
- Respect user privacy and data security
- Only claim capabilities for the 10 confirmed applications above

You have verified access to these 89 tools and can perform real operations across all connected applications."""

        # Create the agent
        rube_agent = create_react_agent(
            model=rube_model,
            tools=useful_tools,
            name="multi_tool_rube_agent",
            prompt=rube_prompt
        )

        logger.info("Multi-Tool Rube Agent created successfully")
        return rube_agent

    except Exception as e:
        logger.error(f"Failed to create Multi-Tool Rube Agent: {e}")
        logger.info("Creating fallback Multi-Tool Rube Agent...")

        # Fallback agent without MCP tools
        fallback_model = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            temperature=0,
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            streaming=False
        )

        fallback_prompt = """❌ MULTI-TOOL RUBE AGENT ERROR: The Rube integration failed to initialize.

**TECHNICAL ISSUE DETECTED:**
- Rube MCP server connection failed
- This is likely due to authentication, network, or configuration errors
- Check the console logs for specific error details

**CURRENT LIMITATIONS:**
- ✅ I can provide general guidance about application integrations
- ❌ I CANNOT access external applications (Gmail, Slack, etc.)
- ❌ I CANNOT execute tools or automation workflows
- ❌ I CANNOT manage files or data across platforms

**IMMEDIATE ACTION REQUIRED:**
Please check system logs and fix the Rube MCP server configuration before using multi-tool features."""

        return create_react_agent(
            model=fallback_model,
            tools=[],
            name="multi_tool_rube_agent_fallback",
            prompt=fallback_prompt
        )

async def post_model_hook(messages, model_output=None):
    """
    post_model_hook that ensures the supervisor ends with a recap message.
    """
    try:
        if not messages:
            return messages

        last_msg = messages[-1]
        if isinstance(last_msg, AIMessage) and ("recap" in last_msg.content.lower() or "summary" in last_msg.content.lower()):
            return messages

        source_text = ""
        for m in reversed(messages):
            if isinstance(m, AIMessage) or isinstance(m, ToolMessage):
                source_text = (m.content or "").strip()
                if source_text:
                    break

        if not source_text:
            recap_content = "Recap: The supervisor completed routing and agent handoff as required."
        else:
            short_snippet = " ".join(source_text.splitlines())[:480].strip()
            recap_content = f"Recap: {short_snippet}"

        messages.append(AIMessage(content=recap_content))
        return messages

    except Exception as e:
        logger.exception("post_model_hook failed — returning original messages.")
        return messages

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
        job_search_agent = await create_job_search_agent()
        multi_tool_rube_agent = await create_multi_tool_rube_agent()

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
- email_agent: **PRIMARY EMAIL AGENT** - Email composition/drafting/writing → email_agent / Email management (list, send drafts, search) → email_agent / Email reading/organization/ → email_agent IMPORTANT : If the agent writes a DRAFTor a NEW email you MUST show it to the user
- ALL EMAIL TASKS → email_agent (autonomous subgraph)
- job_search_agent: CV upload, Job Offer, Job search, resume/cover letter advice, interview prep
- drive_agent: File management, Google Drive integration, file sharing, document collaboration
- multi_tool_rube_agent: Multi-application tasks across Gmail, Slack, GitHub, Google Workspace, Coda, Linear, Notion, and other connected platforms

ROUTING STRATEGY:
1. ANALYZE the user's request carefully
2. IDENTIFY which agent is most appropriate
3. ROUTE immediately to that agent
4. Let the agent handle the task completely

ROUTING RULES:
- Calendar/scheduling/appointments/meetings → calendar_agent
- ALL EMAIL TASKS (composition, sending, management, organization, triage) → email_agent
- Job search/career/resume/interviews/CV → job_search_agent
- Multi-app tasks involving Slack, GitHub, Coda, Linear, Notion, Google Workspace → multi_tool_rube_agent
- Cross-platform workflows and automation → multi_tool_rube_agent
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
            agents=[calendar_agent, job_search_agent, multi_tool_rube_agent],
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
