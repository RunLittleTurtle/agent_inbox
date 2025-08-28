"""
Calendar Agent State Schema with Pydantic v2
Following LangGraph modern patterns and user rules.
Reference: https://langchain-ai.github.io/langgraph/concepts/state/
"""
from datetime import datetime, date, time
from typing import Any, Dict, List, Optional, Sequence, Union
from uuid import uuid4

from pydantic import BaseModel, Field, ConfigDict
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages
from typing_extensions import Annotated, TypedDict


class CalendarEvent(BaseModel):
    """Structured calendar event data with proper validation."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    id: Optional[str] = Field(default=None, description="Event ID from calendar provider")
    title: str = Field(..., description="Event title/summary")
    description: Optional[str] = Field(default=None, description="Event description/details")
    start_datetime: datetime = Field(..., description="Event start datetime")
    end_datetime: datetime = Field(..., description="Event end datetime") 
    location: Optional[str] = Field(default=None, description="Event location")
    attendees: List[str] = Field(default_factory=list, description="List of attendee emails")
    calendar_id: Optional[str] = Field(default=None, description="Calendar ID")
    status: str = Field(default="confirmed", description="Event status")
    visibility: str = Field(default="default", description="Event visibility")
    
    def __str__(self) -> str:
        return f"{self.title} ({self.start_datetime} - {self.end_datetime})"


class CalendarQuery(BaseModel):
    """Structured calendar query parameters."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    query_type: str = Field(..., description="Type of query: list, create, update, delete, check_availability")
    start_date: Optional[date] = Field(default=None, description="Query start date")
    end_date: Optional[date] = Field(default=None, description="Query end date")
    time_min: Optional[datetime] = Field(default=None, description="Minimum time for query")
    time_max: Optional[datetime] = Field(default=None, description="Maximum time for query")
    calendar_ids: List[str] = Field(default_factory=list, description="Calendar IDs to query")
    max_results: int = Field(default=10, description="Maximum number of results")


class CalendarAnalysis(BaseModel):
    """Analysis results from calendar operations."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    action_taken: str = Field(..., description="Action performed")
    events_found: List[CalendarEvent] = Field(default_factory=list, description="Events found/processed")
    conflicts_detected: List[CalendarEvent] = Field(default_factory=list, description="Conflicting events")
    suggestions: List[str] = Field(default_factory=list, description="Scheduling suggestions")
    success: bool = Field(default=True, description="Whether operation succeeded")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    execution_time: Optional[float] = Field(default=None, description="Execution time in seconds")
    tools_used: List[str] = Field(default_factory=list, description="MCP tools used")


class AgentOutput(BaseModel):
    """Structured agent output for supervisor visibility."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    agent_name: str = Field(default="calendar_agent", description="Name of agent")
    task_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique task ID")
    status: str = Field(..., description="Task status: pending, running, completed, failed")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence in result")
    summary: str = Field(..., description="Brief summary of what was done")
    detailed_result: str = Field(..., description="Detailed result description")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Structured data payload")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")


def add_calendar_events(existing: List[CalendarEvent], new: List[CalendarEvent]) -> List[CalendarEvent]:
    """Reducer for calendar events - merge without duplicates."""
    existing_ids = {event.id for event in existing if event.id}
    result = list(existing)
    
    for event in new:
        if event.id is None or event.id not in existing_ids:
            result.append(event)
    
    return result


def add_agent_outputs(existing: List[AgentOutput], new: List[AgentOutput]) -> List[AgentOutput]:
    """Reducer for agent outputs - keep chronological order."""
    return list(existing) + list(new)


class CalendarAgentState(TypedDict):
    """
    Calendar Agent State Schema following LangGraph modern patterns.
    Uses message reducers and proper state management.
    Reference: https://langchain-ai.github.io/langgraph/concepts/state/
    """
    # Core message history with reducer
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # Calendar-specific data with custom reducers
    calendar_events: Annotated[List[CalendarEvent], add_calendar_events]
    calendar_query: Optional[CalendarQuery]
    calendar_analysis: Optional[CalendarAnalysis]
    
    # Agent execution tracking
    output: Annotated[List[AgentOutput], add_agent_outputs]
    
    # Runtime context
    user_email: Optional[str]
    calendar_ids: List[str]
    timezone: str
    
    # MCP connection state
    mcp_tools_loaded: bool
    mcp_session_active: bool
    
    # Human-in-the-loop support
    requires_human_approval: bool
    human_feedback: Optional[str]
