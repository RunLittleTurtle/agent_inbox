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
    tools_used: List[str] = Field(default_factory=list, description="Google Calendar tools used")


class RoutingDecision(BaseModel):
    """Routing decision context from LLM router analysis."""
    model_config = ConfigDict(str_strip_whitespace=True)

    needs_booking_approval: bool = Field(..., description="Whether booking approval is needed")
    reasoning: str = Field(..., description="LLM reasoning for routing decision")
    next_action: str = Field(..., description="Next node to route to")
    user_intent: str = Field(..., description="Extracted user intent from conversation")
    booking_context: Optional[str] = Field(default=None, description="Full booking context from conversation")
    original_request: str = Field(..., description="Original user request that triggered routing")
    timestamp: datetime = Field(default_factory=datetime.now, description="When routing decision was made")


class BookingContext(BaseModel):
    """Enriched booking context with conversation history."""
    model_config = ConfigDict(str_strip_whitespace=True)

    original_intent: str = Field(..., description="Original booking intent")
    routing_analysis: Optional[RoutingDecision] = Field(default=None, description="Router analysis")
    conversation_context: str = Field(..., description="Relevant conversation context extracted from MessagesState")
    previous_attempts: List[str] = Field(default_factory=list, description="Previous booking attempts")
    calendar_constraints: List[str] = Field(default_factory=list, description="Calendar availability constraints")
    extracted_details: Optional[Dict[str, Any]] = Field(default=None, description="Extracted booking details")


class BookingRequest(BaseModel):
    """Structured booking request for Google Calendar tool execution."""
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(default="Untitled Event", description="Event title/summary")
    start_time: str = Field(default="", description="Start time in ISO format with timezone")
    end_time: str = Field(default="", description="End time in ISO format with timezone")
    description: Optional[str] = Field(default=None, description="Event description")
    location: Optional[str] = Field(default=None, description="Event location")
    attendees: List[str] = Field(default_factory=list, description="List of attendee emails")
    tool_name: str = Field(..., description="Google Calendar tool to execute")
    requires_event_id: bool = Field(default=False, description="Whether operation requires existing event ID")
    color_id: Optional[str] = Field(default=None, description="Calendar color ID (1-11)")
    transparency: str = Field(default="opaque", description="Event transparency for availability")
    visibility: str = Field(default="default", description="Event visibility setting")
    guests_can_invite_others: bool = Field(default=True, description="Allow guests to invite others")
    guests_can_modify: bool = Field(default=False, description="Allow guests to modify event")
    reminders: Dict[str, Any] = Field(default_factory=lambda: {"useDefault": True}, description="Event reminders")
    recurrence: Optional[List[str]] = Field(default=None, description="Recurrence rules")
    conference_data: Optional[Dict[str, Any]] = Field(default=None, description="Video conference data")
    tools_to_use: Optional[List[str]] = Field(default=None, description="List of Google Calendar tools needed for complete operation")
    original_args: Dict[str, Any] = Field(default_factory=dict, description="Original tool arguments")


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


def add_routing_decisions(existing: List[RoutingDecision], new: List[RoutingDecision]) -> List[RoutingDecision]:
    """Reducer for routing decisions - keep chronological order."""
    return list(existing) + list(new)


def update_booking_context(existing: Optional[BookingContext], new: Optional[BookingContext]) -> Optional[BookingContext]:
    """Reducer for booking context - update with latest context."""
    return new if new is not None else existing


class CalendarAgentState(BaseModel):
    """
    Calendar Agent State Schema following LangGraph modern patterns with Pydantic v2.
    Uses message reducers and proper state management.
    Reference: https://langchain-ai.github.io/langgraph/concepts/state/
    """
    # Core message history with reducer
    messages: Annotated[Sequence[BaseMessage], add_messages] = Field(
        default_factory=list,
        description="Message history with automatic reducer"
    )

    # Calendar-specific data with custom reducers
    calendar_events: Annotated[List[CalendarEvent], add_calendar_events] = Field(
        default_factory=list,
        description="Current calendar events with reducer"
    )
    calendar_query: Optional[CalendarQuery] = Field(
        default=None,
        description="Active calendar query"
    )
    calendar_analysis: Optional[CalendarAnalysis] = Field(
        default=None,
        description="Calendar analysis results"
    )

    # Agent execution tracking
    output: Annotated[List[AgentOutput], add_agent_outputs] = Field(
        default_factory=list,
        description="Agent outputs with reducer"
    )

    # Runtime context
    user_email: Optional[str] = Field(
        default=None,
        description="User's email for calendar access"
    )
    calendar_ids: List[str] = Field(
        default_factory=list,
        description="Available calendar IDs"
    )
    timezone: str = Field(
        default="America/Toronto",
        description="User's timezone"
    )

    # Human-in-the-loop support
    requires_human_approval: bool = Field(
        default=False,
        description="Whether human approval is required"
    )
    human_feedback: Optional[str] = Field(
        default=None,
        description="Human feedback if provided"
    )

    # Routing context preservation
    routing_decisions: Annotated[List[RoutingDecision], add_routing_decisions] = Field(
        default_factory=list,
        description="Routing decisions with reducer"
    )
    booking_context: Annotated[Optional[BookingContext], update_booking_context] = Field(
        default=None,
        description="Current booking context with reducer"
    )

    model_config = ConfigDict(
        arbitrary_types_allowed=True,  # Required for BaseMessage types
        extra="forbid"  # Prevent extra fields for better validation
    )
