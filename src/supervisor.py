"""
Production Email Agent with Supervisor Architecture
Modern LangGraph implementation using langgraph-supervisor library.
Integrates email processing with calendar agent via supervisor routing.
Reference: https://langchain-ai.github.io/langgraph/reference/supervisor/
"""
import os
from dotenv import load_dotenv
load_dotenv()

from typing import Annotated, List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor


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


class EmailAgentState(BaseModel):
    """Modern LangGraph state for email processing with supervisor integration"""
    # Core email data
    email: Optional[EmailMessage] = None
    
    # Message history with proper reducer
    messages: Annotated[List[BaseMessage], add_messages] = Field(default_factory=list)
    
    # Agent outputs for supervisor coordination
    output: List[AgentOutput] = Field(default_factory=list)
    
    # Processing status and routing
    status: str = "processing"
    intent: Optional[str] = None
    agent_route: Optional[str] = None
    
    # Response data
    draft_response: Optional[str] = None
    final_response: Optional[str] = None
    
    # Service-specific data
    calendar_data: Optional[Dict[str, Any]] = None
    
    # Error handling
    error_messages: List[str] = Field(default_factory=list)
    
    # Timestamps
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


def email_processor_node(state: EmailAgentState) -> EmailAgentState:
    """Process incoming email and determine routing intent"""
    
    if not state.email:
        return state.model_copy(update={
            "status": "error",
            "error_messages": ["No email provided"]
        })
    
    # Analyze email content for intent
    email_content = f"{state.email.subject} {state.email.body}".lower()
    
    # Determine intent and routing
    intent = "general"
    agent_route = None
    
    if any(word in email_content for word in ["meeting", "schedule", "calendar", "appointment", "availability", "book", "reschedule"]):
        intent = "calendar"
        agent_route = "calendar_agent"
    elif any(word in email_content for word in ["email", "send", "reply", "forward", "message"]):
        intent = "email"
        agent_route = "email_agent"
    
    # Create processing message for supervisor
    processing_msg = HumanMessage(
        content=f"Process this email request: {state.email.subject}\n\nContent: {state.email.body}"
    )
    
    # Create agent output
    output = AgentOutput(
        agent_name="email_processor",
        confidence=0.9 if agent_route else 0.6,
        execution_time=0.1,
        tools_used=["text_analysis"],
        structured_data={"intent": intent, "route": agent_route},
        reasoning=f"Analyzed email and determined intent: {intent}, suggested route: {agent_route}"
    )
    
    return state.model_copy(update={
        "messages": state.messages + [processing_msg],
        "output": state.output + [output],
        "intent": intent,
        "agent_route": agent_route,
        "status": "analyzed"
    })


def supervisor_routing_node(state: EmailAgentState) -> EmailAgentState:
    """Route through supervisor for specialized agent handling"""
    
    # This is where the supervisor takes over and routes to appropriate agents
    # The supervisor will analyze the messages and route accordingly
    
    routing_msg = AIMessage(
        content="Routing request through supervisor to appropriate specialized agent",
        name="supervisor_router"
    )
    
    output = AgentOutput(
        agent_name="supervisor_router",
        confidence=1.0,
        execution_time=0.05,
        tools_used=["supervisor_routing"],
        structured_data={"routed": True, "intent": state.intent},
        reasoning=f"Routed {state.intent} request to supervisor for agent coordination"
    )
    
    return state.model_copy(update={
        "messages": state.messages + [routing_msg],
        "output": state.output + [output],
        "status": "routed_to_supervisor"
    })


def response_synthesizer_node(state: EmailAgentState) -> EmailAgentState:
    """Synthesize final response from supervisor output"""
    
    # Extract the supervisor's response
    final_response = "Request processed successfully"
    
    if state.messages:
        # Get the last AI message as the response
        ai_messages = [msg for msg in state.messages if isinstance(msg, AIMessage)]
        if ai_messages:
            final_response = ai_messages[-1].content
    
    synthesis_msg = AIMessage(
        content=f"Final response synthesized: {final_response}",
        name="response_synthesizer"
    )
    
    output = AgentOutput(
        agent_name="response_synthesizer",
        confidence=0.95,
        execution_time=0.1,
        tools_used=["response_synthesis"],
        structured_data={"response_ready": True},
        reasoning="Synthesized final response from supervisor coordination"
    )
    
    return state.model_copy(update={
        "messages": state.messages + [synthesis_msg],
        "output": state.output + [output],
        "final_response": final_response,
        "status": "completed"
    })


def human_review_node(state: EmailAgentState) -> EmailAgentState:
    """Human-in-the-loop review point for Agent Inbox"""
    
    review_msg = AIMessage(
        content="Email processed and ready for human review in Agent Inbox",
        name="human_reviewer"
    )
    
    output = AgentOutput(
        agent_name="human_reviewer",
        confidence=1.0,
        execution_time=0.05,
        tools_used=["agent_inbox"],
        structured_data={"requires_review": True, "final_response": state.final_response},
        reasoning="Reached human review checkpoint for Agent Inbox"
    )
    
    return state.model_copy(update={
        "messages": state.messages + [review_msg],
        "output": state.output + [output],
        "status": "awaiting_review"
    })


async def create_calendar_agent():
    """Create calendar agent for supervisor"""
    model = ChatOpenAI(
        model="gpt-4o-mini", 
        temperature=0,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    agent = create_react_agent(
        model=model,
        tools=[],  # Add calendar MCP tools here
    )
    agent.name = "calendar_agent"
    return agent


async def create_email_agent():
    """Create email agent for supervisor"""
    model = ChatOpenAI(
        model="gpt-4o-mini", 
        temperature=0,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    agent = create_react_agent(
        model=model,
        tools=[],  # Add email tools here
    )
    agent.name = "email_agent"
    return agent


async def create_production_supervisor():
    """Create production supervisor with specialized agents"""
    
    # Create specialized agents
    calendar_agent = await create_calendar_agent()
    email_agent = await create_email_agent()
    
    # Create supervisor model
    supervisor_model = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.1,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Create supervisor with agents
    supervisor_graph = create_supervisor(
        agents=[calendar_agent, email_agent],
        model=supervisor_model,
        prompt="""You are a supervisor managing email processing agents.

Available agents:
- calendar_agent: Handles calendar, scheduling, meetings, availability checks
- email_agent: Handles email composition, replies, and general communication

For calendar/scheduling requests, route to calendar_agent.
For email composition requests, route to email_agent.
For general questions, respond directly with helpful information.""",
        supervisor_name="email_supervisor",
        output_mode="last_message"
    )
    
    # Compile with memory
    checkpointer = MemorySaver()
    return supervisor_graph.compile(
        checkpointer=checkpointer,
        name="production_email_supervisor"
    )


def create_email_workflow_with_supervisor():
    """Create email workflow that integrates with supervisor"""
    
    # Initialize the state graph
    workflow = StateGraph(EmailAgentState)
    
    # Add processing nodes
    workflow.add_node("email_processor", email_processor_node)
    workflow.add_node("supervisor_routing", supervisor_routing_node)
    workflow.add_node("response_synthesizer", response_synthesizer_node)
    workflow.add_node("human_review", human_review_node)
    
    # Define the flow
    workflow.add_edge(START, "email_processor")
    workflow.add_edge("email_processor", "supervisor_routing")
    workflow.add_edge("supervisor_routing", "response_synthesizer")
    workflow.add_edge("response_synthesizer", "human_review")
    workflow.add_edge("human_review", END)
    
    # Compile with memory for Agent Inbox integration
    checkpointer = MemorySaver()
    return workflow.compile(checkpointer=checkpointer)


def create_integrated_supervisor_workflow():
    """Create fully integrated workflow with embedded supervisor"""
    
    # Create supervisor once at module level (synchronous)
    def create_sync_supervisor():
        """Create supervisor synchronously"""
        model = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Create simple agents without async
        calendar_model = ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=os.getenv("OPENAI_API_KEY"))
        email_model = ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=os.getenv("OPENAI_API_KEY"))
        
        calendar_agent = create_react_agent(calendar_model, tools=[])
        calendar_agent.name = "calendar_agent"
        
        email_agent = create_react_agent(email_model, tools=[])
        email_agent.name = "email_agent"
        
        # Create supervisor
        supervisor_graph = create_supervisor(
            agents=[calendar_agent, email_agent],
            model=model,
            prompt="""You are a supervisor managing email processing agents.

Available agents:
- calendar_agent: Handles calendar, scheduling, meetings, availability checks
- email_agent: Handles email composition, replies, and general communication

For calendar/scheduling requests, route to calendar_agent.
For email composition requests, route to email_agent.
For general questions, respond directly with helpful information.""",
            supervisor_name="email_supervisor",
            output_mode="last_message"
        )
        
        checkpointer = MemorySaver()
        return supervisor_graph.compile(checkpointer=checkpointer, name="production_email_supervisor")
    
    # Create supervisor once
    try:
        supervisor = create_sync_supervisor()
    except Exception as e:
        print(f"⚠️ Supervisor creation failed: {e}")
        supervisor = None
    
    def supervisor_node(state: EmailAgentState) -> EmailAgentState:
        """Node that runs the supervisor internally (synchronous for LangGraph compatibility)"""
        
        if not supervisor:
            error_msg = AIMessage(
                content="Supervisor not available",
                name="supervisor_error"
            )
            return state.model_copy(update={
                "messages": state.messages + [error_msg],
                "error_messages": state.error_messages + ["Supervisor not initialized"],
                "status": "supervisor_error"
            })
        
        # Extract the user request from messages
        if state.messages:
            user_message = state.messages[-1]
            
            # Run through supervisor (synchronous call)
            try:
                result = supervisor.invoke(
                    {"messages": [user_message]},
                    config={"thread_id": f"email_{state.email.id if state.email else 'default'}"}
                )
                
                # Extract response
                if result.get("messages"):
                    supervisor_response = result["messages"][-1]
                    
                    # Add supervisor response to state
                    output = AgentOutput(
                        agent_name="supervisor_coordinator",
                        confidence=0.9,
                        execution_time=1.0,
                        tools_used=["supervisor", "agent_routing"],
                        structured_data=result,
                        reasoning="Coordinated request through multi-agent supervisor"
                    )
                    
                    return state.model_copy(update={
                        "messages": state.messages + [supervisor_response],
                        "output": state.output + [output],
                        "status": "supervisor_processed"
                    })
                    
            except Exception as e:
                error_msg = AIMessage(
                    content=f"Supervisor processing error: {str(e)}",
                    name="supervisor_error"
                )
                return state.model_copy(update={
                    "messages": state.messages + [error_msg],
                    "error_messages": state.error_messages + [str(e)],
                    "status": "supervisor_error"
                })
        
        return state
    
    # Create workflow with embedded supervisor
    workflow = StateGraph(EmailAgentState)
    
    # Add nodes
    workflow.add_node("email_processor", email_processor_node)
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("response_synthesizer", response_synthesizer_node)
    workflow.add_node("human_review", human_review_node)
    
    # Define flow
    workflow.add_edge(START, "email_processor")
    workflow.add_edge("email_processor", "supervisor")
    workflow.add_edge("supervisor", "response_synthesizer")
    workflow.add_edge("response_synthesizer", "human_review")
    workflow.add_edge("human_review", END)
    
    # Compile with checkpointer
    checkpointer = MemorySaver()
    return workflow.compile(checkpointer=checkpointer)


# Export the production graph
try:
    graph = create_integrated_supervisor_workflow()
    graph.name = "email_agent_with_supervisor"
    print("✅ Production email agent with supervisor created successfully")
except Exception as e:
    print(f"⚠️  Falling back to simple workflow: {e}")
    graph = create_email_workflow_with_supervisor()
    graph.name = "email_agent"
