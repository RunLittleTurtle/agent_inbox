"""
Calendar Agent Supervisor Integration
Provides handoff tools and integration with the supervisor system.
Reference: https://langchain-ai.github.io/langgraph/how-tos/multi_agent/
"""
import os
from typing import Dict, Any, Optional
import logging

from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph_supervisor import create_supervisor
from langgraph.pregel import Pregel

from .subgraph import create_calendar_agent_subgraph
from .state import CalendarAgentState

logger = logging.getLogger(__name__)


async def create_calendar_supervisor_system(
    model: Optional[ChatOpenAI] = None,
    checkpointer: Optional[MemorySaver] = None
) -> Pregel:
    """
    Create a supervisor system that includes the calendar agent.
    This demonstrates how to integrate the calendar agent with a supervisor.
    """
    if not model:
        model = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
    
    if not checkpointer:
        checkpointer = MemorySaver()
    
    # Create calendar agent subgraph
    calendar_agent = await create_calendar_agent_subgraph(
        model=model,
        name="calendar_agent", 
        checkpointer=checkpointer
    )
    
    # Create supervisor with calendar agent
    supervisor_prompt = """You are a calendar supervisor managing specialized calendar operations.

Your role is to:
1. Route calendar-related requests to the calendar_agent
2. Handle general inquiries about calendar functionality
3. Coordinate between multiple calendar operations if needed

Available agents:
- calendar_agent: Handles all calendar operations including listing events, creating events, checking availability, updating events, and deleting events

When a user asks about calendar operations, delegate to the calendar_agent.
For general questions, respond directly.
"""
    
    supervisor_workflow = create_supervisor(
        agents=[calendar_agent],
        model=model,
        prompt=supervisor_prompt,
        output_mode="last_message",
        supervisor_name="calendar_supervisor"
    )
    
    return supervisor_workflow.compile(
        checkpointer=checkpointer,
        name="calendar_supervisor_system"
    )


class CalendarAgentIntegration:
    """
    Helper class for integrating calendar agent into existing supervisor systems.
    Provides utilities for adding calendar capabilities to supervisor workflows.
    """
    
    def __init__(self):
        self.calendar_agent: Optional[Pregel] = None
        self.model: Optional[ChatOpenAI] = None
        
    async def initialize(
        self, 
        model: Optional[ChatOpenAI] = None,
        checkpointer: Optional[MemorySaver] = None
    ) -> bool:
        """Initialize the calendar agent integration."""
        try:
            self.model = model or ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.1,
                openai_api_key=os.getenv("OPENAI_API_KEY")
            )
            
            # Create calendar agent
            self.calendar_agent = await create_calendar_agent_subgraph(
                model=self.model,
                name="calendar_agent",
                checkpointer=checkpointer or MemorySaver()
            )
            
            logger.info("Calendar agent integration initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize calendar agent integration: {e}")
            return False
            
    def get_agent(self) -> Optional[Pregel]:
        """Get the calendar agent for supervisor integration."""
        return self.calendar_agent
        
    def get_calendar_handoff_prompt(self) -> str:
        """Get prompt text for calendar agent handoffs."""
        return """calendar_agent: A specialized agent for Google Calendar operations. Use this agent for:
- Listing calendar events
- Creating new calendar events and meetings
- Checking calendar availability and scheduling conflicts
- Updating existing calendar events
- Deleting calendar events
- Managing calendar attendees and invitations

The calendar agent integrates with Google Calendar via MCP (Model Context Protocol) and can perform real calendar operations."""

    def is_calendar_request(self, message: str) -> bool:
        """Detect if a message requires calendar operations."""
        calendar_keywords = [
            "calendar", "schedule", "meeting", "appointment", "event",
            "book", "available", "availability", "busy", "free",
            "create event", "list events", "check calendar", "time",
            "today", "tomorrow", "next week", "this week", "agenda"
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in calendar_keywords)
        
    async def process_calendar_request(
        self,
        message: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Process a calendar request directly using the calendar agent."""
        if not self.calendar_agent:
            return {
                "error": "Calendar agent not initialized",
                "success": False
            }
            
        try:
            # Prepare state for calendar agent
            initial_state: CalendarAgentState = {
                "messages": [AIMessage(content=message)],
                "calendar_events": [],
                "calendar_query": None,
                "calendar_analysis": None,
                "output": [],
                "user_email": context.get("user_email") if context else None,
                "calendar_ids": context.get("calendar_ids", ["primary"]) if context else ["primary"],
                "timezone": context.get("timezone", "UTC") if context else "UTC",
                "mcp_tools_loaded": False,
                "mcp_session_active": False,
                "requires_human_approval": False,
                "human_feedback": None
            }
            
            # Run calendar agent
            result = await self.calendar_agent.ainvoke(
                initial_state,
                config={"thread_id": "calendar_request"}
            )
            
            return {
                "result": result,
                "success": True,
                "messages": result.get("messages", []),
                "events": result.get("calendar_events", []),
                "analysis": result.get("calendar_analysis")
            }
            
        except Exception as e:
            logger.error(f"Error processing calendar request: {e}")
            return {
                "error": str(e),
                "success": False
            }


# Factory functions for easy integration
async def add_calendar_agent_to_supervisor(
    existing_agents: list,
    model: Optional[ChatOpenAI] = None,
    checkpointer: Optional[MemorySaver] = None
) -> list:
    """
    Add calendar agent to an existing list of agents for supervisor creation.
    
    Usage:
        agents = [research_agent, math_agent]
        agents_with_calendar = await add_calendar_agent_to_supervisor(agents)
        supervisor = create_supervisor(agents_with_calendar, model=model)
    """
    calendar_agent = await create_calendar_agent_subgraph(
        model=model,
        name="calendar_agent",
        checkpointer=checkpointer
    )
    
    return existing_agents + [calendar_agent]


def get_calendar_supervisor_prompt() -> str:
    """Get enhanced supervisor prompt that includes calendar agent instructions."""
    return """You are a multi-agent supervisor coordinating specialized agents.

Available agents:
- calendar_agent: Handles Google Calendar operations (list, create, update, delete events, check availability)

For calendar and scheduling requests, always delegate to calendar_agent.
The calendar agent can:
- List upcoming events and meetings
- Create new calendar events with proper scheduling
- Check availability and detect conflicts
- Update existing events (time, attendees, details)
- Delete or cancel events
- Manage meeting invitations and attendees

Route requests appropriately based on the user's needs."""


# Configuration helper
class CalendarAgentConfig:
    """Configuration helper for calendar agent deployment."""
    
    @staticmethod
    def get_required_env_vars() -> list:
        """Get list of required environment variables."""
        return [
            "OPENAI_API_KEY",
            "PIPEDREAM_MCP_SERVER",
            "USER_GOOGLE_EMAIL"
        ]
        
    @staticmethod
    def validate_config() -> Dict[str, bool]:
        """Validate calendar agent configuration."""
        required_vars = CalendarAgentConfig.get_required_env_vars()
        validation = {}
        
        for var in required_vars:
            validation[var] = bool(os.getenv(var))
            
        return validation
        
    @staticmethod
    def get_config_status() -> Dict[str, Any]:
        """Get comprehensive configuration status."""
        validation = CalendarAgentConfig.validate_config()
        
        return {
            "all_configured": all(validation.values()),
            "missing_vars": [var for var, configured in validation.items() if not configured],
            "validation_details": validation,
            "pipedream_server": os.getenv("PIPEDREAM_MCP_SERVER"),
            "user_email": os.getenv("USER_GOOGLE_EMAIL")
        }
