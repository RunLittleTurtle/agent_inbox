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
from datetime import datetime

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
from src.calendar_agent import create_calendar_agent_with_mcp


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


# Simple email processing node
def process_email_node(state: AgentState) -> AgentState:
    """Process incoming email and extract basic information"""

    if not state.email:
        return state.model_copy(update={
            "status": "error",
            "error_messages": ["No email provided"]
        })

    # Extract intent from subject and body
    email_content = f"{state.email.subject} {state.email.body}".lower()

    intent = "general"
    if any(word in email_content for word in ["meeting", "schedule", "calendar", "appointment"]):
        intent = "calendar"
    elif any(word in email_content for word in ["document", "file", "attachment", "share"]):
        intent = "document"
    elif any(word in email_content for word in ["contact", "phone", "address", "info"]):
        intent = "contact"

    # Add processing message
    processing_msg = AIMessage(
        content=f"Processing email from {state.email.sender} about: {state.email.subject}",
        name="email_processor"
    )

    # Create agent output
    output = AgentOutput(
        agent_name="email_processor",
        confidence=0.9,
        execution_time=0.1,
        tools_used=["text_analysis"],
        structured_data={"intent": intent, "processed": True},
        reasoning=f"Analyzed email content and determined intent: {intent}"
    )

    return state.model_copy(update={
        "messages": state.messages + [processing_msg],
        "output": state.output + [output],
        "intent": intent,
        "status": "processed"
    })


# Human review node (Agent Inbox integration)
def human_review_node(state: AgentState) -> AgentState:
    """Human-in-the-loop review point"""

    review_msg = AIMessage(
        content="Email processed and ready for human review in Agent Inbox",
        name="human_reviewer"
    )

    output = AgentOutput(
        agent_name="human_reviewer",
        confidence=1.0,
        execution_time=0.05,
        tools_used=["agent_inbox"],
        structured_data={"requires_review": True},
        reasoning="Reached human review checkpoint for Agent Inbox"
    )

    return state.model_copy(update={
        "messages": state.messages + [review_msg],
        "output": state.output + [output],
        "status": "awaiting_review"
    })


# Create the main graph
def create_email_graph():
    """Create the main email processing graph with modern LangGraph patterns"""

    # Initialize the state graph with proper typing
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("process_email", process_email_node)
    workflow.add_node("human_review", human_review_node)

    # Define the flow
    workflow.add_edge(START, "process_email")
    workflow.add_edge("process_email", "human_review")
    workflow.add_edge("human_review", END)

    # Compile without custom checkpointer (use LangGraph's built-in persistence)
    return workflow.compile()


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
            from src.calendar_agent.langchain_mcp_integration import get_calendar_tools_for_supervisor
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

    # Create email agent for communication tasks
    email_agent = create_react_agent(
        model=model,
        tools=[],  # Add email tools here
        name="email_agent"
    )

    # Create supervisor with multiple agents for ANY type of request
    supervisor = create_supervisor(
        agents=[calendar_agent, email_agent],
        model=model,
        tools=calendar_tools,  # Pass MCP tools to supervisor directly
        prompt="""You are a multi-agent supervisor handling requests from various sources: chatbot users, email processing, and API calls.

Available tools:
- Google Calendar MCP tools: Use these for direct calendar operations (create events, list events, check availability)

Available agents:
- calendar_agent: Handles complex calendar operations and analysis
- email_agent: Handles email processing, communication tasks, and message drafting

Routing guidelines:
- For simple calendar operations: USE CALENDAR TOOLS DIRECTLY
- For complex calendar tasks or analysis → calendar_agent  
- Email/communication requests → email_agent
- Mixed requests: handle directly with tools or delegate as needed
- General questions: respond directly with helpful information

IMPORTANT: Accept requests in any format - treat all inputs as natural language requests regardless of source.""",
        supervisor_name="supervisor",
        output_mode="last_message",
        add_handoff_messages=True
    )

    # Compile without custom checkpointer (use LangGraph's built-in persistence)
    return supervisor.compile(name="supervisor")


# Export the main graph using supervisor
async def make_graph():
    """Factory function for LangGraph server"""
    try:
        # Use supervisor that handles any type of request
        graph_instance = await create_supervisor_graph()
        print("✅ Using supervisor with langgraph-supervisor library")
        return graph_instance
    except Exception as e:
        print(f"⚠️ Supervisor creation failed: {e}")
        # Only fallback if supervisor truly fails
        graph_instance = create_email_graph()
        graph_instance.name = "email_agent"
        return graph_instance

# Create graph factory function for LangGraph server
def create_graph():
    """Synchronous graph factory for LangGraph server"""
    import asyncio
    return asyncio.run(make_graph())

# Export for LangGraph server
graph = create_graph()
