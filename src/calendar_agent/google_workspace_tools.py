"""
Google Workspace Tools - Convert GoogleWorkspaceExecutor methods into LangChain Tools
Provides READ-ONLY tools for calendar_agent node (no interrupts needed).

These tools maintain the same naming convention as Rube MCP tools:
- google_calendar-list-events
- google_calendar-get-event
- google_calendar-list-calendars

This allows the calendar agent to work seamlessly with either:
- Google Workspace API (direct, fast, cheap)
- Rube MCP (fallback, universal access)
"""

from typing import List, Optional
from langchain_core.tools import BaseTool, StructuredTool
from pydantic import BaseModel, Field


def create_google_workspace_read_tools(executor) -> List[BaseTool]:
    """
    Convert GoogleWorkspaceExecutor READ methods into LangChain Tools.

    These tools are used by the calendar_agent node (create_react_agent)
    for READ-ONLY operations like checking availability and listing events.

    Args:
        executor: GoogleWorkspaceExecutor instance with READ methods

    Returns:
        List of LangChain Tools matching MCP tool naming convention
    """

    # Tool 1: List Events (most important for availability checking)
    class ListEventsInput(BaseModel):
        time_min: Optional[str] = Field(
            None,
            description="RFC3339 timestamp for start of time range (e.g., '2025-01-15T00:00:00-05:00')"
        )
        time_max: Optional[str] = Field(
            None,
            description="RFC3339 timestamp for end of time range (e.g., '2025-01-16T23:59:59-05:00')"
        )
        max_results: int = Field(
            250,
            description="Maximum number of events to return (default 250, max 2500)"
        )

    list_events_tool = StructuredTool.from_function(
        coroutine=executor.list_events,
        name="google_calendar-list-events",
        description=(
            "List calendar events within a time range. Use this to check availability, "
            "find upcoming events, or see what's scheduled. Returns formatted list of events "
            "with start/end times, titles, and attendees."
        ),
        args_schema=ListEventsInput,
    )

    # Tool 2: Get Event (retrieve specific event details)
    class GetEventInput(BaseModel):
        event_id: str = Field(
            ...,
            description="Google Calendar event ID to retrieve"
        )

    get_event_tool = StructuredTool.from_function(
        coroutine=executor.get_event,
        name="google_calendar-get-event",
        description=(
            "Get detailed information about a specific calendar event by its ID. "
            "Returns event title, start/end times, location, description, attendees, and link."
        ),
        args_schema=GetEventInput,
    )

    # Tool 3: List Calendars (show available calendars)
    list_calendars_tool = StructuredTool.from_function(
        coroutine=executor.list_calendars,
        name="google_calendar-list-calendars",
        description=(
            "List all calendars available to the authenticated user. "
            "Shows calendar names, IDs, and access permissions. "
            "Useful for multi-calendar management."
        ),
    )

    return [list_events_tool, get_event_tool, list_calendars_tool]
