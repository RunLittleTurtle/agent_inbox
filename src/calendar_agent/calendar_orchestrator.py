"""
Calendar Agent using official langchain-mcp-adapters patterns
Implementation following the latest langchain-mcp-adapters from GitHub.
Reference: https://github.com/langchain-ai/langchain-mcp-adapters
"""
import os
import asyncio
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

# Add local libraries to path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../library/langgraph'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../library/langchain-mcp-adapters'))


# Local LangGraph imports
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition, create_react_agent
from langgraph.checkpoint.memory import MemorySaver

# Local langchain-mcp-adapters imports
from langchain_mcp_adapters.client import MultiServerMCPClient

from .state import CalendarAgentState, RoutingDecision, BookingContext


class CalendarAgentWithMCP:
    """
    Calendar agent using official langchain-mcp-adapters patterns.
    Updated to follow latest GitHub implementation patterns with caching and timeout protection.
    """

    def __init__(
        self,
        model: Optional[ChatAnthropic] = None,
        mcp_servers: Optional[Dict[str, Dict[str, Any]]] = None
    ):
        self.model = model or ChatAnthropic(
            model="claude-sonnet-4-20250514",
            temperature=0,
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
        )

        # MCP server configuration - connect to configured Pipedream Google Calendar MCP server
        pipedream_url = os.getenv("PIPEDREAM_MCP_SERVER")
        if pipedream_url:
            self.mcp_servers = mcp_servers or {
                "pipedream_calendar": {
                    "url": pipedream_url,
                    "transport": "streamable_http"
                }
            }
        else:
            # Fallback to no MCP servers if not configured
            self.mcp_servers = mcp_servers or {}

        # MCP client and tools (initialized async) with caching
        self._mcp_client: Optional[MultiServerMCPClient] = None
        self._mcp_tools: List[BaseTool] = []
        self._tools_cache_time: Optional[datetime] = None
        self.tools: List[BaseTool] = []
        self.graph = None

        # Setup logging
        self.logger = logging.getLogger(__name__)

    async def _get_mcp_tools(self):
        """Get MCP tools with aggressive connection reuse and caching to prevent memory leaks"""

        # Cache tools for 5 minutes to prevent excessive MCP server connections
        # This reduces load on the external MCP server and improves performance
        if (self._mcp_tools and self._tools_cache_time and
            datetime.now() - self._tools_cache_time < timedelta(minutes=5)):
            return self._mcp_tools

        # Use the configured MCP server URL
        mcp_url = self.mcp_servers.get("pipedream_calendar", {}).get("url")
        if not mcp_url:
            raise ValueError("Pipedream MCP server URL not configured")

        self.logger.info(f"Connecting to Pipedream MCP server: {mcp_url}")

        # Reuse MCP client instance to prevent memory leaks
        # Creating new clients for each request can cause resource exhaustion
        if self._mcp_client is None:
            self._mcp_client = MultiServerMCPClient(self.mcp_servers)

        # Add timeout to prevent hanging connections
        try:
            tools = await asyncio.wait_for(
                self._mcp_client.get_tools(),
                timeout=30.0  # 30 second timeout
            )
            self.logger.info(f"Loaded {len(tools)} MCP tools: {[t.name for t in tools]}")
        except asyncio.TimeoutError:
            self.logger.error("MCP tools loading timed out")
            raise Exception("MCP server connection timed out")

        # Cache results
        self._mcp_tools = tools
        self._tools_cache_time = datetime.now()
        return tools

    async def initialize(self):
        """Initialize MCP client and load tools using official patterns"""
        try:
            # Use improved MCP connection with caching and timeout
            all_tools = await self._get_mcp_tools()

            # Filter tools: separate booking tools from read-only tools
            self.booking_tools = []
            self.tools = []

            booking_tool_names = {
                'google_calendar-quick-add-event',
                'google_calendar-create-event',
                'google_calendar-delete-event',
                'google_calendar-add-attendees-to-event',
                'google_calendar-update-event'
            }

            # Tools that don't work properly and should be excluded
            excluded_tool_names = {
                'google_calendar-query-free-busy-calendars'  # This tool doesn't work, use list-events instead
            }

            for tool in all_tools:
                if tool.name in excluded_tool_names:
                    print(f"   EXCLUDED: {tool.name} (doesn't work properly)")
                    continue
                elif tool.name in booking_tool_names:
                    self.booking_tools.append(tool)
                else:
                    self.tools.append(tool)

            print(f"Loaded {len(self.tools)} read-only calendar tools")
            for tool in self.tools:
                print(f"   {tool.name}: {tool.description}")

            print(f"Separated {len(self.booking_tools)} booking tools for approval workflow")
            for tool in self.booking_tools:
                print(f"   {tool.name}: [REQUIRES APPROVAL]")

            # Create the graph
            self.graph = await self._create_calendar_graph()

        except Exception as e:
            print(f"Failed to initialize MCP client: {e}")
            # Fallback to no tools if MCP connection fails
            self.tools = []
            self.booking_tools = []
            self.graph = await self._create_calendar_graph()

    async def _create_calendar_graph(self):
        """Create calendar agent using pure LangGraph create_react_agent pattern"""

        # Create enhanced prompt for calendar operations
        if not self.tools:
            prompt = """You are a calendar agent in a multi-agent supervisor system.


When users request calendar operations:
1. Acknowledge their specific request with details
2. Clearly explain that you cannot access calendar tools currently
3. Provide helpful information about what would normally happen
4. Be completely honest about limitations

NEVER claim to have successfully completed calendar operations when you have no tools."""
        else:
            # Get timezone context from .env USER_TIMEZONE
            import os
            from zoneinfo import ZoneInfo
            from datetime import timedelta
            timezone_name = os.getenv("USER_TIMEZONE", "America/Toronto")
            current_time = datetime.now(ZoneInfo(timezone_name))

            prompt = f"""You are a helpful Calendar Agent with READ-ONLY access to Google Calendar via MCP tools.

CONTEXT (use for all relative references):
- Now: {current_time.isoformat()}
- Timezone: {timezone_name}
- Today: {current_time.strftime('%Y-%m-%d')} ({current_time.strftime('%A')})
- Tomorrow: {(current_time + timedelta(days=1)).strftime('%Y-%m-%d')} ({(current_time + timedelta(days=1)).strftime('%A')})

PRINCIPLES
- Assume ALL user times are in the user’s LOCAL timezone.
- Never ask for timezone; never convert to UTC in tool calls.
- Operate only on the MAIN calendar.
- Always include timezone context in your replies.
- IMPORTANT: You have READ-ONLY access to calendar tools. For any booking, creating, updating, or deleting operations, you must inform the user that this requires booking approval and will transfer them to the booking approval workflow.
- CRITICAL: Never call transfer_back_to_multi_agent_supervisor - the supervisor handles returns automatically.
- When the request and tasks are completed, _end_, this will automatically transfer_back_to_multi_agent_supervisor, do not attempt to call tool to transfer back to supervisor.

CAPABILITIES (read-only)
- Check availability and free/busy by listing events in a time window.
- Read existing events and basic calendar details/settings.

TOOL USAGE
- Prefer `google_calendar-list-events` to inspect availability.
- Use ISO-8601 with explicit offset (e.g., 2025-01-15T09:00:00-05:00).
- For availability checks: list events covering the requested window; analyze overlaps and free gaps.

BOOKING REQUESTS (requires approval workflow)
1) First, check availability with read-only tools using the context above and the AVAILABILITY SEARCH STRATEGY below with list-event.
2) If the requested slot is free, respond exactly with:
   "Time slot is available. This requires booking approval — I'll transfer you to the booking approval workflow."
3) If there is a conflict:
    - Automatically search alternatives (do not ask the user to propose times without options).
    - Follow the AVAILABILITY SEARCH STRATEGY to find free slots.
4) After the user chooses a specific slot, respond exactly with:
   "Perfect! I'll transfer you to the booking approval workflow for [chosen time]."
5) CRITICAL: Never claim that a meeting is booked/scheduled until it has completed the booking_node approval workflow. The booking_node approval workflow performs actual modifications and provides the event link.

MODIFICATION REQUESTS (change/move existing events):
- For ANY modification request (change time, move event, reschedule), respond exactly with:
  "I understand you want to modify the event. This requires booking approval — proceeding to modification workflow."
- NEVER transfer back to supervisor for modification requests
- Let the internal routing handle booking modifications

AVAILABILITY SEARCH STRATEGY
- When conflicts are found, automatically expand your search
- To check if time slots are free: Use list-events for the date/time range
- Derive free gaps by comparing the requested slot against returned events.
- Persist until you can present AT LEAST 2 viable alternatives or until the day's search space is exhausted.
- Try same day: 1-2 hours earlier, 1-2 hours later
- Try next day: same time, 1 hour earlier, 1 hour later
- NEVER give up on availability searches after the first attempt
- Continue searching until you find AT LEAST 2 available options
- Present findings compactly and concretely in LOCAL time.

COMMUNICATION
- Be precise, proactive, and honest about read-only constraints.
- Summarize assumptions in bullet points (date, time, duration, timezone) before proposing or confirming next steps.
- IMPORTANT: Do NOT call transfer tools unless explicitly handling a completed booking workflow
- Let the internal routing system handle workflow transitions to booking_node

USER FEEDBACK AND INPUT
- When user feedback or future input from the user is received, clearly analyse the feedback.
- Once analysed, provide the necessary routing.
- Always follow your instruction, even if you did it in prior workflow.
- The goal is to always help the user with the latest request.

"""

        # Create the main calendar agent (read-only operations)
        calendar_agent = create_react_agent(
            model=self.model,
            tools=self.tools,
            name="calendar_agent",
            prompt=prompt
        )

        # If no booking tools, just return the simple agent
        if not self.booking_tools:
            return calendar_agent

        # Create StateGraph wrapper for routing to booking node
        from langgraph.graph import StateGraph, START, END
        from .booking_node import BookingNode

        workflow = StateGraph(MessagesState)

        # Initialize booking node
        booking_node = BookingNode(self.booking_tools, self.model)

        # Add nodes
        workflow.add_node("calendar_agent", calendar_agent)
        workflow.add_node("booking_approval", booking_node.booking_approval_node)
        workflow.add_node("booking_execute", booking_node.booking_execute_node)
        workflow.add_node("booking_cancel", booking_node.booking_cancel_node)
        workflow.add_node("booking_modify", booking_node.booking_modify_node)

        # Smart LLM-based routing with conversation context analysis
        def route_intent(state: MessagesState):
            """Route all calendar requests to calendar_agent first"""
            return "calendar_agent"

        def route_after_calendar(state: MessagesState):
            """Smart LLM-based routing after calendar agent completes"""
            from langchain_core.prompts import ChatPromptTemplate
            from pydantic import BaseModel, Field
            from typing import Literal

            # Define structured output for routing decisions
            class RoutingDecision(BaseModel):
                """Routing decision based on conversation analysis"""
                needs_booking_approval: bool = Field(
                    description="True if the conversation indicates a booking, scheduling, creating, updating, or deleting calendar events"
                )
                reasoning: str = Field(
                    description="Brief explanation of the routing decision"
                )
                next_action: Literal["booking_approval", "booking_execute", "booking_cancel", "booking_modify", "end"] = Field(
                    description="Next node to route to"
                )
                user_intent: str = Field(
                    description="Extracted user intent from conversation"
                )
                booking_context: Optional[str] = Field(
                    default=None, description="Full booking context from conversation"
                )

            # Get conversation context
            messages = state.get("messages", [])
            if not messages:
                return END

            # Prepare conversation history for LLM analysis
            conversation_context = []
            for msg in messages[-6:]:  # Last 6 messages for context
                if hasattr(msg, 'content'):
                    content = msg.content
                    if isinstance(content, list):
                        content = " ".join(str(item) for item in content if item)
                    elif not isinstance(content, str):
                        content = str(content)

                    role = getattr(msg, 'type', 'unknown')
                    conversation_context.append(f"{role}: {content}")

            context_str = "\n".join(conversation_context)

            # Enhanced routing prompt with context extraction
            routing_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a smart calendar workflow router. Analyze the conversation to determine if the user's request requires booking approval workflow.

BOOKING APPROVAL NEEDED FOR:
- Creating new calendar events/meetings
- Scheduling appointments
- Booking time slots
- Updating existing events (time, date, attendees)
- Moving/rescheduling events
- Deleting events
- Any calendar modifications

READ-ONLY OPERATIONS (no approval needed):
- Checking availability
- Viewing calendar events
- Asking about free time slots
- General calendar inquiries

USER CONTEXT CLUES:
- "book", "schedule", "create", "move", "change", "update", "delete"
- Specific time requests like "move to 11pm", "schedule for tomorrow"
- Confirmation of available time slots
- Meeting setup requests

IMPORTANT: Extract the user's intent and full booking context for downstream processing.

Analyze the FULL conversation context, not just the last message."""),
                ("user", "Conversation context:\n{context}\n\nBased on this conversation, does the user need booking approval workflow? Also extract the user intent and booking context.")
            ])

            try:
                # Use the existing model from calendar agent
                llm = self.model.with_structured_output(RoutingDecision)

                decision = llm.invoke(routing_prompt.format_messages(context=context_str))

                # Log routing decision for debugging
                print(f"🤖 Smart Router Decision: {decision.next_action}")
                print(f"📝 Reasoning: {decision.reasoning}")
                print(f"🎯 User Intent: {decision.user_intent}")

                # **CRITICAL**: Preserve routing decision in state
                if decision.needs_booking_approval:
                    # Create enriched booking context
                    booking_context = BookingContext(
                        original_intent=decision.user_intent,
                        routing_analysis=decision,
                        conversation_summary=context_str,
                        previous_attempts=[],
                        calendar_constraints=[],
                        extracted_details=None
                    )

                    # Add routing decision and booking context to messages
                    from langchain_core.messages import AIMessage
                    context_message = AIMessage(
                        content=f"🔄 ROUTING CONTEXT: {decision.reasoning}",
                        additional_kwargs={
                            "routing_decision": decision.dict(),
                            "booking_context": booking_context.dict(),
                            "user_intent": decision.user_intent,
                            "conversation_summary": context_str
                        }
                    )

                    # Update state with preserved context
                    state["messages"] = state.get("messages", []) + [context_message]

                return decision.next_action if decision.needs_booking_approval else END

            except Exception as e:
                print(f"⚠️ Smart routing failed, using fallback: {e}")
                # Fallback to simple keyword detection
                last_msg = messages[-1] if messages else None
                if last_msg and hasattr(last_msg, 'content'):
                    content = str(last_msg.content).lower()
                    booking_keywords = ["book", "schedule", "create", "move", "change", "update", "delete", "cancel", "set up"]
                    if any(keyword in content for keyword in booking_keywords):
                        return "booking_approval"
                return END

        def route_after_booking(state: MessagesState):
            """Route after booking node completes - allow booking_node to route back to itself"""
            # Check if there's new human feedback that needs booking_node processing
            messages = state.get("messages", [])
            if messages:
                last_msg = messages[-1]
                # If last message is human feedback, route back to booking_node
                if hasattr(last_msg, 'type') and last_msg.type == "human":
                    print("🔄 Human feedback detected - routing back to booking_node")
                    return "booking_approval"
            return END

        # Set up clean routing flow - human feedback loops back through booking_node
        workflow.add_conditional_edges(START, route_intent,
                                     {"calendar_agent": "calendar_agent"})
        workflow.add_conditional_edges("calendar_agent", route_after_calendar,
                                     {"booking_approval": "booking_approval", "booking_execute": "booking_execute", "booking_cancel": "booking_cancel", "booking_modify": "booking_modify", END: END})
        workflow.add_conditional_edges("booking_approval", route_after_booking,
                                     {"booking_approval": "booking_approval", "booking_execute": "booking_execute", "booking_cancel": "booking_cancel", "booking_modify": "booking_modify", END: END})

        return workflow.compile(checkpointer=MemorySaver(), name="calendar_agent")

    async def get_agent(self):
        """Get the LangGraph agent for supervisor integration"""
        if not self.graph:
            await self.initialize()
        return self.graph

    async def get_available_tools(self) -> List[Dict[str, str]]:
        """Get list of available tools"""
        if not self.tools:
            await self.initialize()

        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": str(tool.args) if hasattr(tool, 'args') else "Unknown"
            }
            for tool in self.tools
        ]

    async def cleanup(self):
        """Clean up MCP client resources"""
        if self._mcp_client:
            try:
                await self._mcp_client.cleanup()
            except Exception as e:
                self.logger.warning(f"Error during cleanup: {e}")


async def create_calendar_agent_with_mcp(
    model: Optional[ChatAnthropic] = None,
    mcp_servers: Optional[Dict[str, Dict[str, Any]]] = None
) -> CalendarAgentWithMCP:
    """
    Factory function to create and initialize calendar agent with MCP.

    Args:
        model: ChatAnthropic model instance
        mcp_servers: MCP server configurations

    Returns:
        Initialized CalendarAgentWithMCP instance
    """
    agent = CalendarAgentWithMCP(model=model, mcp_servers=mcp_servers)
    await agent.initialize()
    return agent


# Integration function for supervisor
async def get_calendar_tools_for_supervisor() -> List[BaseTool]:
    """
    Get calendar tools for supervisor integration.
    Returns properly configured LangChain tools from Pipedream MCP server.
    """
    try:
        # Use Pipedream MCP server URL from environment
        pipedream_url = os.getenv("PIPEDREAM_MCP_SERVER")
        if not pipedream_url:
            print("PIPEDREAM_MCP_SERVER environment variable not set")
            return []

        mcp_servers = {
            "pipedream_calendar": {
                "url": pipedream_url,
                "transport": "streamable_http"
            }
        }

        print(f"Connecting to Pipedream MCP server: {pipedream_url}")

        client = MultiServerMCPClient(mcp_servers)

        # Add timeout to prevent hanging
        tools = await asyncio.wait_for(
            client.get_tools(),
            timeout=30.0
        )

        # Filter out problematic tools that cause API errors
        # The google_calendar-query-free-busy-calendars tool has a name length > 64 characters
        # which causes "string too long" errors in the OpenAI API
        filtered_tools = [tool for tool in tools if tool.name != "google_calendar-query-free-busy-calendars"]

        print(f"Retrieved {len(filtered_tools)} working calendar tools for supervisor")
        for tool in filtered_tools:
            print(f"   {tool.name}: {tool.description[:100]}...")

        if len(tools) > len(filtered_tools):
            print(f"Filtered out {len(tools) - len(filtered_tools)} problematic tools")

        # Convert async MCP tools to synchronous tools for LangGraph compatibility
        # LangGraph supervisor requires synchronous tools, but MCP tools are async
        # This wrapper handles the async-to-sync conversion safely
        from langchain_core.tools import StructuredTool
        from pydantic import BaseModel, Field
        import asyncio as async_module
        import concurrent.futures

        sync_tools = []

        for async_tool in filtered_tools:
            # Create a synchronous wrapper for each async MCP tool
            def make_sync_tool(atool):
                def sync_func(**kwargs) -> str:
                    """Synchronous wrapper that executes async MCP tool safely"""
                    try:
                        # Check if we're already in an event loop
                        loop = None
                        try:
                            loop = async_module.get_running_loop()
                        except RuntimeError:
                            pass

                        if loop is None:
                            # No running loop, create new one
                            result = async_module.run(atool.ainvoke(kwargs))
                        else:
                            # Running in existing loop, use thread pool to avoid blocking
                            with concurrent.futures.ThreadPoolExecutor() as executor:
                                future = executor.submit(async_module.run, atool.ainvoke(kwargs))
                                result = future.result(timeout=30)

                        return str(result)
                    except Exception as e:
                        return f"Error executing {atool.name}: {str(e)}"

                # Create LangChain StructuredTool from MCP tool
                sync_tool = StructuredTool(
                    name=atool.name,
                    description=atool.description,
                    args_schema=atool.args_schema,
                    func=sync_func,  # Synchronous function, not coroutine
                    return_direct=False
                )
                return sync_tool

            sync_tools.append(make_sync_tool(async_tool))

        print(f"Created {len(sync_tools)} synchronous calendar tools")
        return sync_tools

    except Exception as e:
        print(f"Error getting calendar tools for supervisor: {e}")
        return []


if __name__ == "__main__":
    async def test_calendar_agent():
        """Test the calendar agent with proper MCP integration"""
        print("Testing Calendar Agent with langchain-mcp-adapters...")

        agent = await create_calendar_agent_with_mcp()
        graph = await agent.get_agent()

        test_requests = [
            "What's on my calendar today?",
            "Schedule a meeting for tomorrow at 2 PM with John",
            "Check my availability next week",
            "Cancel the meeting at 3 PM today"
        ]

        for request in test_requests:
            print(f"\nRequest: {request}")

            try:
                # Use the LangGraph agent properly
                config = {"configurable": {"thread_id": "test-thread"}}
                result = await graph.ainvoke(
                    {"messages": [{"role": "user", "content": request}]},
                    config=config
                )

                if result and "messages" in result:
                    last_message = result["messages"][-1]
                    print(f"Response: {last_message.content}")
                else:
                    print("No response received")

            except Exception as e:
                print(f"Error processing request: {e}")

        # Show available tools
        tools = await agent.get_available_tools()
        print(f"\nAvailable tools: {len(tools)}")
        for tool in tools:
            print(f"   - {tool['name']}: {tool['description']}")

        await agent.cleanup()

    asyncio.run(test_calendar_agent())
