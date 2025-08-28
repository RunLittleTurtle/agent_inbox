"""
Calendar Agent Module
Modern LangGraph calendar agent with official langchain-mcp-adapters integration.
"""
from .state import CalendarAgentState, CalendarEvent, CalendarQuery, CalendarAnalysis, AgentOutput
from .langchain_mcp_integration import CalendarAgentWithMCP, create_calendar_agent_with_mcp

__all__ = [
    "CalendarAgentState",
    "CalendarEvent", 
    "CalendarQuery",
    "CalendarAnalysis",
    "AgentOutput",
    "CalendarAgentWithMCP",
    "create_calendar_agent_with_mcp"
]
