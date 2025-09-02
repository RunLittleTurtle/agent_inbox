"""
Modern LangGraph Email Agent with Supervisor Architecture
Using latest LangGraph 0.6+ patterns with State, reducers, tools, agents, and memory.
Connected to LangSmith for observability and tracing.
"""

import os
import sys
from dotenv import load_dotenv
from typing import Dict, Any, Optional, List, Annotated
from pydantic import BaseModel, Field
from datetime import datetime, timezone

# Load environment variables for LangSmith integration
load_dotenv()

# Add local libraries to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../library/langgraph'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../library/langgraph_supervisor-py'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../library/langchain-mcp-adapters'))

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

# Local LangGraph imports
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

# Local supervisor imports
from langgraph_supervisor import create_supervisor

# Calendar agent imports
try:
    from src.calendar_agent import create_calendar_agent_with_mcp
except ImportError:
    from calendar_agent import create_calendar_agent_with_mcp


class EmailMessage(BaseModel):
    """Email message structure"""
    id: str
    subject: str
    body: str
    sender: str
    recipients: List[str]
    timestamp: str
    attachments: List[str] = Field(default_factory=list)
    thread_id: Optional[str] = None
    message_id: Optional[str] = None


class AgentOutput(BaseModel):
    """Structured output from agents"""
    agent_name: str
    confidence: float
    execution_time: float
    tools_used: List[str]
    structured_data: Dict[str, Any]
    reasoning: str
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class AgentState(BaseModel):
    """Modern LangGraph state with reducers and structured data using Pydantic"""
    # Core email data
    email: Optional[EmailMessage] = None

    # Message history with proper reducer
    messages: Annotated[List[BaseMessage], add_messages] = Field(default_factory=list)

    # Structured agent outputs
    output: List[AgentOutput] = Field(default_factory=list)

    # Current date context - CRITICAL for all LLM operations (Pydantic v2)
    current_date: str = Field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    current_datetime: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    current_timezone: str = Field(default="UTC")

    # Dynamic context and memory
    dynamic_context: Dict[str, Any] = Field(default_factory=lambda: {
        "insights": [],
        "execution_metadata": {},
        "context_updates": {}
    })

    # Long-term memory integration
    long_term_memory: Optional[Dict[str, Any]] = None

    # Processing status
    status: str = "processing"
    intent: Optional[str] = None
    extracted_context: Optional[Dict[str, Any]] = None
    draft_response: Optional[str] = None
    response_metadata: Dict[str, Any] = Field(default_factory=dict)
    error_messages: List[str] = Field(default_factory=list)

    # Service-specific data
    calendar_data: Optional[Dict[str, Any]] = None
    document_data: Optional[Dict[str, Any]] = None
    contact_data: Optional[Dict[str, Any]] = None

    # Timestamps
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


# Reducer functions for state updates
def add_agent_output(state: AgentState, update: AgentOutput) -> AgentState:
    """Add agent output to state"""
    new_output = state.output + [update]
    return state.model_copy(update={"output": new_output})


def update_dynamic_context(state: AgentState, context_updates: Dict[str, Any]) -> AgentState:
    """Update dynamic context with new information"""
    current_context = state.dynamic_context.copy()
    current_context.update(context_updates)
    return state.model_copy(update={"dynamic_context": current_context})






# Create supervisor with specialized agents (when they exist)
async def create_supervisor_graph():
    """Create supervisor architecture with specialized agents for any type of request"""

    # Initialize model with LangSmith tracing
    model = ChatOpenAI(
        model="gpt-4o",
        temperature=0.1,
        api_key=os.getenv("OPENAI_API_KEY")
    )

    # Verify LangSmith connection
    langsmith_key = os.getenv("LANGSMITH_API_KEY")
    langchain_tracing = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    langchain_project = os.getenv("LANGCHAIN_PROJECT", "ambient-email-agent")

    if langsmith_key and langchain_tracing:
        print(f"✅ LangSmith tracing enabled for project: {langchain_project}")
    else:
        print("⚠️  LangSmith tracing not configured")

    # Create calendar agent with MCP tools
    calendar_tools = []

    # DEBUG: Check environment variables
    pipedream_url = os.getenv("PIPEDREAM_MCP_SERVER")
    print(f"🔍 DEBUG: PIPEDREAM_MCP_SERVER = {pipedream_url}")
    print(f"🔍 DEBUG: create_calendar_agent_with_mcp = {create_calendar_agent_with_mcp}")

    if create_calendar_agent_with_mcp:
        try:
            # Import the function to get calendar tools
            try:
                from src.calendar_agent.langchain_mcp_integration import get_calendar_tools_for_supervisor
            except ImportError:
                from calendar_agent.langchain_mcp_integration import get_calendar_tools_for_supervisor
            calendar_tools = await get_calendar_tools_for_supervisor()
            print(f"✅ Loaded {len(calendar_tools)} calendar MCP tools")
        except Exception as e:
            print(f"❌ Calendar MCP tools ERROR: {e}")
            import traceback
            print(f"❌ Full traceback: {traceback.format_exc()}")
            calendar_tools = []

    # Create calendar agent with tools (either MCP tools or empty)
    calendar_agent = create_react_agent(
        model=model,
        tools=calendar_tools,
        name="calendar_agent"
    )

    # Debug: Print calendar agent tools
    print(f"🔧 Calendar agent created with {len(calendar_tools)} tools:")
    for tool in calendar_tools:
        print(f"   📋 {tool.name}")

    # Verify the agent has tools by checking its graph
    if hasattr(calendar_agent, 'get_graph') and hasattr(calendar_agent, 'nodes'):
        nodes = list(calendar_agent.get_graph().nodes.keys())
        print(f"🏗️  Calendar agent graph nodes: {nodes}")
        has_tools_node = 'tools' in nodes
        print(f"🔍 Calendar agent has tools node: {has_tools_node}")

    # Create email agent for communication and email processing tasks
    email_agent = create_react_agent(
        model=model,
        tools=[],  # Email tools can be added here when available
        name="email_agent"
    )

    # Get current date for dynamic prompt context with user's timezone (simplified)
    from zoneinfo import ZoneInfo
    
    # Get user timezone from .env with Montreal fallback
    user_timezone_str = os.getenv("USER_TIMEZONE", "America/Montreal")
    try:
        user_timezone = ZoneInfo(user_timezone_str)
        current_timezone_name = user_timezone_str.replace("America/", "").replace("_", " ") + " Time"
    except Exception:
        user_timezone = ZoneInfo("America/Montreal")
        current_timezone_name = "Montreal Time"
    
    current_date = datetime.now(user_timezone).strftime("%Y-%m-%d")
    current_datetime = datetime.now(user_timezone).isoformat()
    current_day_name = datetime.now(user_timezone).strftime("%A")
    current_formatted_date = datetime.now(user_timezone).strftime("%A, %B %d, %Y")
    current_time_12h = datetime.now(user_timezone).strftime("%I:%M %p")
    
    print(f"🌍 Using timezone: {user_timezone_str} ({current_timezone_name})")
    print(f"📅 Current time: {current_time_12h} on {current_formatted_date}")

    # Create supervisor with multiple agents for ANY type of request
    supervisor = create_supervisor(
        agents=[calendar_agent, email_agent],
        model=model,
        tools=calendar_tools,  # Pass MCP tools to supervisor directly
        prompt=f"""You are a multi-agent supervisor handling requests from various sources: chatbot users, email processing, and API calls.

CRITICAL DATE & TIME CONTEXT:
- Today's date: {current_date}
- Current datetime: {current_datetime}
- Current time: {current_time_12h}
- Day of week: {current_day_name}
- Formatted date: {current_formatted_date}
- User's timezone: {current_timezone_name}

IMPORTANT TIME & DATE RULES:
- When users say "today", they mean {current_date}
- When users say "tomorrow", they mean the day after {current_date}
- When users say "tonight", they mean {current_date} evening
- When users say "this week", use {current_date} as the reference point
- ALL TIMES mentioned by users are in {current_timezone_name} unless explicitly stated otherwise
- When creating calendar events, ALWAYS specify times in {current_timezone_name}
- NEVER convert user times to UTC in calendar requests - keep them in user's timezone
- Always use {current_date} as the basis for any relative date calculations
- Never assume dates from previous conversations - always use the current date above

CRITICAL CALENDAR TIME FORMATTING:
- User says "10pm" → Create event at 10:00 PM {current_timezone_name}
- User says "2:30 PM" → Create event at 2:30 PM {current_timezone_name}  
- User says "tonight at 8" → Create event at 8:00 PM {current_timezone_name} on {current_date}
- ALWAYS include timezone context when creating calendar events

Available tools:
- Google Calendar MCP tools: Use these for direct calendar operations (create events, list events, check availability)

Available agents:
- calendar_agent: Handles calendar operations, scheduling, and time management
- email_agent: Handles email processing, communication tasks, message drafting, and email analysis

Routing guidelines:
- Calendar/scheduling requests → calendar_agent
- Email processing, communication, drafting → email_agent
- Mixed requests: delegate to appropriate agent or handle with tools
- General questions: respond directly with helpful information

DYNAMIC DECISION MAKING:
- Analyze each request to determine the best agent or approach
- Consider request complexity and available tools
- Route to specialized agents when their expertise is needed
- Handle simple requests directly when appropriate

IMPORTANT:
1. Accept requests in any format - treat all inputs as natural language requests regardless of source
2. Always reference the current date ({current_date}) when handling date-related queries
3. Be explicit about dates in your responses to avoid confusion""",
        supervisor_name="supervisor",
        output_mode="last_message",
        add_handoff_messages=True
    )

    # Compile without custom checkpointer (use LangGraph's built-in persistence)
    return supervisor.compile(name="supervisor")


# Export the main graph using supervisor
async def make_graph():
    """Factory function for LangGraph server"""
    # Use supervisor that handles any type of request dynamically
    graph_instance = await create_supervisor_graph()
    print("✅ Using dynamic supervisor with langgraph-supervisor library")
    return graph_instance

# Create graph factory function for LangGraph server
def create_graph():
    """Synchronous graph factory for LangGraph server"""
    import asyncio
    return asyncio.run(make_graph())

# Export for LangGraph server
graph = create_graph()
