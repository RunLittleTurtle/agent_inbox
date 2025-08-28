"""
Calendar Agent Subgraph Implementation
Modern LangGraph subgraph with MCP integration for calendar operations.
Reference: https://langchain-ai.github.io/langgraph/concepts/subgraphs/
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from langgraph.pregel import Pregel
from langgraph.types import Command

from .state import (
    CalendarAgentState,
    CalendarEvent,
    CalendarQuery,
    CalendarAnalysis,
    AgentOutput
)
from .mcp_client import CalendarMCPClient, CalendarToolManager

logger = logging.getLogger(__name__)


class CalendarAgentSubgraph:
    """
    Calendar Agent Subgraph for handling calendar operations.
    Integrates with supervisor system via handoff patterns.
    """

    def __init__(
        self,
        model: Optional[ChatOpenAI] = None,
        name: str = "calendar_agent",
        checkpointer: Optional[MemorySaver] = None
    ):
        self.name = name
        self.model = model or ChatOpenAI(
            model="gpt-4o",
            temperature=0.1
        )
        self.checkpointer = checkpointer or MemorySaver()
        self.mcp_client: Optional[CalendarMCPClient] = None
        self.tool_manager: Optional[CalendarToolManager] = None
        self.graph: Optional[Pregel] = None

    async def build(self) -> Pregel:
        """Build and compile the calendar agent subgraph."""
        # Initialize MCP client
        self.mcp_client = CalendarMCPClient()
        self.tool_manager = CalendarToolManager(self.mcp_client)

        # Create state graph
        builder = StateGraph(CalendarAgentState)

        # Add nodes
        builder.add_node("initialize", self._initialize_node)
        builder.add_node("analyze_request", self._analyze_request_node)
        builder.add_node("execute_calendar_action", self._execute_calendar_action_node)
        builder.add_node("synthesize_response", self._synthesize_response_node)
        builder.add_node("handle_error", self._handle_error_node)

        # Define edges
        builder.add_edge(START, "initialize")
        builder.add_conditional_edges(
            "initialize",
            self._should_continue_after_init,
            {
                "analyze": "analyze_request",
                "error": "handle_error"
            }
        )
        builder.add_conditional_edges(
            "analyze_request",
            self._route_after_analysis,
            {
                "execute": "execute_calendar_action",
                "synthesize": "synthesize_response",
                "error": "handle_error"
            }
        )
        builder.add_conditional_edges(
            "execute_calendar_action",
            self._should_synthesize,
            {
                "synthesize": "synthesize_response",
                "error": "handle_error"
            }
        )
        builder.add_edge("synthesize_response", END)
        builder.add_edge("handle_error", END)

        # Compile graph
        self.graph = builder.compile(
            checkpointer=self.checkpointer,
            name=self.name
        )

        return self.graph

    async def _initialize_node(
        self,
        state: CalendarAgentState,
        config: RunnableConfig
    ) -> Dict[str, Any]:
        """Initialize MCP connections and load calendar tools."""
        logger.info("Initializing calendar agent...")

        try:
            # Initialize MCP client and tools
            if not self.tool_manager:
                self.tool_manager = CalendarToolManager(self.mcp_client)

            success = await self.tool_manager.initialize()

            # Create agent output for tracking
            agent_output = AgentOutput(
                status="running" if success else "failed",
                summary="MCP initialization",
                detailed_result=f"MCP connection {'successful' if success else 'failed'}",
                data={"mcp_tools_count": len(self.tool_manager.tools)}
            )

            return {
                "mcp_tools_loaded": success,
                "mcp_session_active": success,
                "output": [agent_output]
            }

        except Exception as e:
            logger.error(f"Initialization error: {e}")
            error_output = AgentOutput(
                status="failed",
                summary="MCP initialization failed",
                detailed_result=f"Error: {str(e)}",
                confidence=0.0
            )

            return {
                "mcp_tools_loaded": False,
                "mcp_session_active": False,
                "output": [error_output]
            }

    async def _analyze_request_node(
        self,
        state: CalendarAgentState,
        config: RunnableConfig
    ) -> Dict[str, Any]:
        """Analyze the user request and determine calendar actions needed."""
        logger.info("Analyzing calendar request...")

        # Get last message
        if not state["messages"]:
            return {"calendar_analysis": CalendarAnalysis(
                action_taken="no_request",
                success=False,
                error_message="No user message found"
            )}

        last_message = state["messages"][-1]
        user_request = last_message.content if hasattr(last_message, 'content') else str(last_message)

        # Use LLM to analyze the request
        system_prompt = """You are a calendar assistant analyzer. Analyze the user's request and determine:
1. What calendar action they want (list, create, update, delete, check_availability)
2. Extract relevant details (dates, times, titles, attendees, etc.)
3. Identify any conflicts or issues

Respond with a structured analysis."""

        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_request}
            ]

            response = await self.model.ainvoke(messages)
            analysis_text = response.content

            # Parse the response to determine action type
            action_type = self._extract_action_type(analysis_text, user_request)

            analysis = CalendarAnalysis(
                action_taken=f"analyzed_request_for_{action_type}",
                success=True,
                tools_used=["llm_analysis"]
            )

            # Create calendar query based on analysis
            query = self._create_calendar_query(action_type, user_request, analysis_text)

            agent_output = AgentOutput(
                status="completed",
                summary=f"Request analyzed: {action_type}",
                detailed_result=analysis_text,
                confidence=0.8,
                data={"action_type": action_type, "user_request": user_request}
            )

            return {
                "calendar_analysis": analysis,
                "calendar_query": query,
                "output": [agent_output]
            }

        except Exception as e:
            logger.error(f"Analysis error: {e}")
            error_analysis = CalendarAnalysis(
                action_taken="analysis_failed",
                success=False,
                error_message=str(e)
            )

            return {"calendar_analysis": error_analysis}

    async def _execute_calendar_action_node(
        self,
        state: CalendarAgentState,
        config: RunnableConfig
    ) -> Dict[str, Any]:
        """Execute the calendar action using MCP tools."""
        logger.info("Executing calendar action...")

        if not state.get("calendar_query"):
            return {"calendar_analysis": CalendarAnalysis(
                action_taken="no_query",
                success=False,
                error_message="No calendar query found"
            )}

        query = state["calendar_query"]
        action_type = query.query_type

        try:
            start_time = datetime.now()

            if action_type == "list":
                events = await self._execute_list_events(query)
                result_data = {"events_found": len(events)}

            elif action_type == "create":
                event = await self._execute_create_event(query, state)
                events = [event] if event else []
                result_data = {"event_created": bool(event)}

            elif action_type == "check_availability":
                availability = await self._execute_check_availability(query)
                events = []
                result_data = {"availability_checked": True, "slots": availability}

            else:
                events = []
                result_data = {"action": "not_implemented"}

            execution_time = (datetime.now() - start_time).total_seconds()

            analysis = CalendarAnalysis(
                action_taken=f"executed_{action_type}",
                events_found=events,
                success=True,
                execution_time=execution_time,
                tools_used=list(self.tool_manager.tools.keys()) if self.tool_manager else []
            )

            agent_output = AgentOutput(
                status="completed",
                summary=f"Calendar {action_type} executed successfully",
                detailed_result=f"Processed {len(events)} events in {execution_time:.2f}s",
                confidence=0.9,
                data=result_data
            )

            return {
                "calendar_events": events,
                "calendar_analysis": analysis,
                "output": [agent_output]
            }

        except Exception as e:
            logger.error(f"Execution error: {e}")
            error_analysis = CalendarAnalysis(
                action_taken=f"failed_{action_type}",
                success=False,
                error_message=str(e)
            )

            return {"calendar_analysis": error_analysis}

    async def _synthesize_response_node(
        self,
        state: CalendarAgentState,
        config: RunnableConfig
    ) -> Dict[str, Any]:
        """Synthesize final response based on calendar operations."""
        logger.info("Synthesizing calendar response...")

        analysis = state.get("calendar_analysis")
        events = state.get("calendar_events", [])

        # Build comprehensive response
        if analysis and analysis.success:
            if analysis.action_taken.startswith("executed_list"):
                response_content = self._format_events_list(events)
            elif analysis.action_taken.startswith("executed_create"):
                response_content = self._format_creation_response(events)
            elif analysis.action_taken.startswith("executed_check"):
                response_content = self._format_availability_response(analysis)
            else:
                response_content = f"Calendar operation completed: {analysis.action_taken}"
        else:
            error_msg = analysis.error_message if analysis else "Unknown error"
            response_content = f"Calendar operation failed: {error_msg}"

        # Create final AI message
        ai_message = AIMessage(
            content=response_content,
            name=self.name
        )

        # Final agent output
        final_output = AgentOutput(
            status="completed",
            summary="Calendar response synthesized",
            detailed_result=response_content,
            confidence=0.95 if analysis and analysis.success else 0.3,
            data={"events_count": len(events), "success": analysis.success if analysis else False}
        )

        return {
            "messages": [ai_message],
            "output": [final_output]
        }

    async def _handle_error_node(
        self,
        state: CalendarAgentState,
        config: RunnableConfig
    ) -> Dict[str, Any]:
        """Handle errors and provide helpful error messages."""
        logger.info("Handling calendar error...")

        analysis = state.get("calendar_analysis")
        error_msg = analysis.error_message if analysis else "Unknown calendar error occurred"

        error_response = f"I encountered an issue with the calendar operation: {error_msg}. Please try again or contact support if the problem persists."

        ai_message = AIMessage(
            content=error_response,
            name=self.name
        )

        error_output = AgentOutput(
            status="failed",
            summary="Error handled",
            detailed_result=error_response,
            confidence=0.1,
            data={"error": error_msg}
        )

        return {
            "messages": [ai_message],
            "output": [error_output]
        }

    # Conditional edge functions
    def _should_continue_after_init(self, state: CalendarAgentState) -> str:
        """Determine next step after initialization."""
        return "analyze" if state.get("mcp_tools_loaded", False) else "error"

    def _route_after_analysis(self, state: CalendarAgentState) -> str:
        """Route after request analysis."""
        analysis = state.get("calendar_analysis")
        if not analysis or not analysis.success:
            return "error"

        query = state.get("calendar_query")
        if query and query.query_type in ["list", "create", "check_availability"]:
            return "execute"

        return "synthesize"

    def _should_synthesize(self, state: CalendarAgentState) -> str:
        """Determine if we should synthesize or handle error."""
        analysis = state.get("calendar_analysis")
        return "synthesize" if analysis and analysis.success else "error"

    # Helper methods
    def _extract_action_type(self, analysis_text: str, user_request: str) -> str:
        """Extract action type from analysis or user request."""
        text_lower = (analysis_text + " " + user_request).lower()

        if any(word in text_lower for word in ["list", "show", "get", "see", "find"]):
            return "list"
        elif any(word in text_lower for word in ["create", "add", "schedule", "book", "new"]):
            return "create"
        elif any(word in text_lower for word in ["available", "free", "busy", "check"]):
            return "check_availability"
        elif any(word in text_lower for word in ["update", "modify", "change", "edit"]):
            return "update"
        elif any(word in text_lower for word in ["delete", "remove", "cancel"]):
            return "delete"

        return "list"  # Default

    def _create_calendar_query(self, action_type: str, user_request: str, analysis: str) -> CalendarQuery:
        """Create calendar query from analysis."""
        from datetime import date, timedelta

        return CalendarQuery(
            query_type=action_type,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
            max_results=10
        )

    async def _execute_list_events(self, query: CalendarQuery) -> List[CalendarEvent]:
        """Execute list events operation."""
        if not self.tool_manager:
            return []

        return await self.tool_manager.list_events(
            time_min=query.time_min.isoformat() if query.time_min else None,
            time_max=query.time_max.isoformat() if query.time_max else None,
            max_results=query.max_results
        )

    async def _execute_create_event(self, query: CalendarQuery, state: CalendarAgentState) -> Optional[CalendarEvent]:
        """Execute create event operation."""
        # This would need more sophisticated parsing of the user request
        # For now, return None as placeholder
        return None

    async def _execute_check_availability(self, query: CalendarQuery) -> List[Dict[str, Any]]:
        """Execute availability check."""
        if not self.tool_manager:
            return []

        return await self.tool_manager.check_availability(
            time_min=query.time_min.isoformat() if query.time_min else None,
            time_max=query.time_max.isoformat() if query.time_max else None
        )

    def _format_events_list(self, events: List[CalendarEvent]) -> str:
        """Format events list for response."""
        if not events:
            return "No calendar events found for the specified period."

        formatted = "Here are your calendar events:\n\n"
        for i, event in enumerate(events, 1):
            formatted += f"{i}. **{event.title}**\n"
            formatted += f"   📅 {event.start_datetime.strftime('%Y-%m-%d %H:%M')} - {event.end_datetime.strftime('%H:%M')}\n"
            if event.location:
                formatted += f"   📍 {event.location}\n"
            if event.description:
                formatted += f"   📝 {event.description}\n"
            formatted += "\n"

        return formatted

    def _format_creation_response(self, events: List[CalendarEvent]) -> str:
        """Format event creation response."""
        if events and events[0]:
            event = events[0]
            return f"✅ Calendar event created successfully!\n\n**{event.title}**\n📅 {event.start_datetime.strftime('%Y-%m-%d %H:%M')} - {event.end_datetime.strftime('%H:%M')}"

        return "❌ Failed to create calendar event. Please try again."

    def _format_availability_response(self, analysis: CalendarAnalysis) -> str:
        """Format availability check response."""
        if analysis.success:
            return "✅ Availability check completed. Based on your calendar, I can help you find suitable meeting times."

        return "❌ Unable to check calendar availability at this time."


# Factory function
async def create_calendar_agent_subgraph(
    model: Optional[ChatOpenAI] = None,
    name: str = "calendar_agent",
    checkpointer: Optional[MemorySaver] = None
) -> Pregel:
    """Create and build calendar agent subgraph."""
    agent = CalendarAgentSubgraph(model, name, checkpointer)
    return await agent.build()
