"""
Google Workspace Tools - Convert GoogleWorkspaceExecutor methods into LangChain Tools
Provides READ-ONLY tools for calendar_agent node (no interrupts needed).

Following LangChain v1 Multi-Agent Pattern:
- Uses CLOSURE FUNCTIONS (not bound methods) for proper serialization
- Standalone async functions that close over the executor instance
- Ensures tools survive serialization through LangGraph node transitions

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


# ============================================================================
# PYDANTIC SCHEMAS - Module level for proper pickle serialization
# ============================================================================
# These must be at module level (not inside functions) so they can be pickled
# by LangGraph when tools pass through node transitions


class ListEventsInput(BaseModel):
    """Input schema for list_events tool"""
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


class GetEventInput(BaseModel):
    """Input schema for get_event tool"""
    event_id: str = Field(
        ...,
        description="Google Calendar event ID to retrieve"
    )


def create_google_workspace_read_tools(executor) -> List[BaseTool]:
    """
    Convert GoogleWorkspaceExecutor READ methods into LangChain Tools.

    Following LangChain v1 multi-agent pattern: Creates standalone wrapper
    functions (closures) instead of passing bound methods directly.

    These tools are used by the calendar_agent node (create_react_agent)
    for READ-ONLY operations like checking availability and listing events.

    Args:
        executor: GoogleWorkspaceExecutor instance with READ methods

    Returns:
        List of LangChain Tools matching MCP tool naming convention

    Design Pattern (LangChain v1):
        Per multi-agent docs, tools should be standalone functions, not bound methods.
        When you need instance state, create wrapper functions that close over the instance.
        This ensures proper serialization when tools pass through LangGraph nodes.
    """

    # ========================================================================
    # CLOSURE FUNCTIONS - Standalone async functions that capture executor
    # ========================================================================
    # These are NOT bound methods - they're standalone functions that happen
    # to reference the executor instance through closure scope.
    # This pattern allows proper serialization through LangGraph nodes.

    async def list_events_wrapper(
        time_min: Optional[str] = None,
        time_max: Optional[str] = None,
        max_results: int = 250
    ) -> str:
        """
        List calendar events within time range.
        Closure over executor instance for proper serialization.
        """
        return await executor.list_events(
            time_min=time_min,
            time_max=time_max,
            max_results=max_results
        )

    async def get_event_wrapper(event_id: str) -> str:
        """
        Get single event details by ID.
        Closure over executor instance for proper serialization.
        """
        return await executor.get_event(event_id=event_id)

    async def list_calendars_wrapper() -> str:
        """
        List all calendars for user.
        Closure over executor instance for proper serialization.
        """
        return await executor.list_calendars()

    # ========================================================================
    # TOOL CREATION - From wrapper functions (not bound methods!)
    # ========================================================================

    # Tool 1: List Events (most important for availability checking)
    list_events_tool = StructuredTool.from_function(
        coroutine=list_events_wrapper,  # ✅ Closure function, not bound method
        name="google_calendar-list-events",
        description=(
            "List calendar events within a time range. Use this to check availability, "
            "find upcoming events, or see what's scheduled. Returns formatted list of events "
            "with start/end times, titles, and attendees."
        ),
        args_schema=ListEventsInput,
    )

    # Tool 2: Get Event (retrieve specific event details)
    get_event_tool = StructuredTool.from_function(
        coroutine=get_event_wrapper,  # ✅ Closure function, not bound method
        name="google_calendar-get-event",
        description=(
            "Get detailed information about a specific calendar event by its ID. "
            "Returns event title, start/end times, location, description, attendees, and link."
        ),
        args_schema=GetEventInput,
    )

    # Tool 3: List Calendars (show available calendars)
    list_calendars_tool = StructuredTool.from_function(
        coroutine=list_calendars_wrapper,  # ✅ Closure function, not bound method
        name="google_calendar-list-calendars",
        description=(
            "List all calendars available to the authenticated user. "
            "Shows calendar names, IDs, and access permissions. "
            "Useful for multi-calendar management."
        ),
    )

    return [list_events_tool, get_event_tool, list_calendars_tool]
