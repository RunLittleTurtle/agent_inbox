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

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
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
from uuid import uuid4


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
1) IMPORTANT: First, CHECK AVAILABILITY with read-only tools using the context above and the AVAILABILITY SEARCH STRATEGY below with list-event.
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

        # Add nodes - SIMPLIFIED: Only 2 nodes needed for 3-button UI
        workflow.add_node("calendar_agent", calendar_agent)
        workflow.add_node("booking_approval", booking_node.booking_approval_node)

        # Smart LLM-based routing with conversation context analysis
        def route_intent(state: MessagesState):
            """Route all calendar requests to calendar_agent first"""
            return "calendar_agent"

        def route_after_calendar(state: MessagesState):
            """Smart LLM-based routing after calendar agent completes"""
            from langchain_core.prompts import ChatPromptTemplate
            from pydantic import BaseModel, Field
            from typing import Literal

            # Use RoutingDecision from state module

            # Get conversation context
            messages = state.get("messages", [])
            if not messages:
                return END

            # Use state messages directly - no manual extraction needed
            # thread_id + MemorySaver already manages conversation history
            context_str = "\n".join([f"{getattr(msg, 'type', 'message')}: {msg.content}" for msg in messages[-6:] if hasattr(msg, 'content')])

            # Get available tools for dynamic prompt generation
            available_tools_list = [f"- {tool.name}: {tool.description}" for tool in self.booking_tools] if self.booking_tools else ["- No MCP tools available"]
            available_tools_text = "\n".join(available_tools_list)

            # Enhanced routing prompt with context extraction
            routing_prompt = ChatPromptTemplate.from_messages([
                            ("system", """You are a smart calendar workflow router. Analyze the conversation to determine the next actions and tools needed.

                        ANALYZE TWO TYPES OF SITUATIONS:

                        1. CALENDAR AGENT EXPLICITLY INDICATES BOOKING APPROVAL NEEDED:
                           - Look for phrases like "requires booking approval", "transfer you to booking approval", "booking approval workflow"
                           - If the calendar agent explicitly mentions booking approval is needed, route to booking_approval
                           - This takes priority over user intent analysis

                        2. USER INTENT ANALYSIS (if no explicit booking approval mentioned):
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

                        ROUTING DECISION PRIORITY:
                        1. First check if calendar agent explicitly mentioned "booking approval" or "approval workflow"
                        2. If yes, return next_action: "booking_approval"
                        3. If no explicit mention, analyze user intent
                        4. If user intent requires booking, return next_action: "booking_approval"
                        5. Otherwise return next_action: "end"

                        AVAILABLE MCP TOOLS (dynamically detected):
                        {available_tools}

                        TOOLS SELECTION RULES - Based on actual available tools:
                        Analyze the user's request and select the appropriate tool(s) from the available tools above:

                        OPERATION ANALYSIS:
                        - NEW event creation → use 'google_calendar-create-event' if available
                        - DELETE entire event → use 'google_calendar-delete-event' if available
                        - QUICK text-based event → use 'google_calendar-quick-add-event' if available
                        - UPDATE existing event (time/date/duration/title/description) → use 'google_calendar-update-event'
                        - ADD attendees to existing event → use 'google_calendar-add-attendees-to-event' if available AND no other changes needed
                        - It is not possible to REMOVE attendees. it is a restriction of the Google Calendar API. please inform the user, BUT YOU MUST continue with other operations.

                        CRITICAL ANALYSIS FOR COMPLEX REQUESTS EXAMPLES:
                        - If user wants ONLY to add attendees (no other changes) → ['google_calendar-add-attendees-to-event']
                        - If user wants to ADD attendees and make other changes → ['google_calendar-add-attendees-to-event', 'google_calendar-update-event']
                        - Multiple separate events → list multiple appropriate tools

                        EXAMPLE ANALYSIS:
                        "move time to 10am + ADD attendee + change duration + change description" →
                        This needs TWO operations: ADD attendee + UPDATE other fields → ['google_calendar-add-attendees-to-event', 'google_calendar-update-event']

                        IMPORTANT: Base your tool selection on the actual available tools listed above, not assumptions.


                        CRITICAL: Pay special attention to the calendar agent's responses that mention "booking approval workflow" or "requires booking approval"."""),
                            ("user", "Conversation context:\n{context}\n\nAnalyze this conversation. Does the calendar agent explicitly mention booking approval is needed? Or does the user intent require booking operations? Return the appropriate next_action.")
                        ])


            try:
                # Use the existing model from calendar agent
                llm = self.model.with_structured_output(RoutingDecision)

                decision = llm.invoke(routing_prompt.format_messages(
                    context=context_str,
                    available_tools=available_tools_text
                ))

                # Log routing decision for debugging
                print(f"🤖 Smart Router Decision: {decision.next_action}")
                print(f"📝 Reasoning: {decision.reasoning}")
                print(f"🎯 User Intent: {decision.user_intent}")
                print(f"🎯 MCP tools to use: {decision.mcp_tools_to_use}")

                # **CRITICAL**: Preserve routing decision in state
                if decision.needs_booking_approval:
                    # Create enriched booking context
                    booking_context = BookingContext(
                        original_intent=decision.user_intent,
                        routing_analysis=decision,
                        conversation_context=context_str,
                        previous_attempts=[],
                        calendar_constraints=[],
                        extracted_details=None,
                        mcp_tools_to_use=decision.mcp_tools_to_use
                    )

                    # Add routing decision and booking context to messages
                    from langchain_core.messages import AIMessage
                    context_message = AIMessage(
                        content=f"🔄 ROUTING CONTEXT: {decision.reasoning}",
                        additional_kwargs={
                            "routing_decision": decision.dict(),
                            "booking_context": booking_context.dict(),
                            "user_intent": decision.user_intent,
                            "conversation_context": context_str,
                            "mcp_tools_to_use": decision.mcp_tools_to_use
                        }
                    )

                    # Add routing decision to messages with additional_kwargs for context preservation
                    from langchain_core.messages import AIMessage
                    context_message = AIMessage(
                        content=f"🔄 ROUTING CONTEXT: {decision.reasoning}",
                        additional_kwargs={
                            "routing_decision": decision.dict(),
                            "booking_context": booking_context.dict(),
                            "user_intent": decision.user_intent,
                            "conversation_context": context_str,
                            "mcp_tools_to_use": decision.mcp_tools_to_use
                        }
                    )

                    # Update state with preserved context
                    state["messages"] = state.get("messages", []) + [context_message]

                    # **FIXED**: Return the specific next action, not just a boolean check
                    print(f"📍 Routing to: {decision.next_action}")
                    return decision.next_action
                else:
                    print("📍 Routing to: END (no booking approval needed)")
                    return END

            except Exception as e:
                print(f"⚠️ Smart routing failed, using fallback: {e}")
                # Fallback to keyword detection if LLM fails
                last_msg = messages[-1] if messages else None
                if last_msg and hasattr(last_msg, 'content'):
                    content = str(last_msg.content).lower()
                    # Look for explicit booking approval mentions
                    if ("booking approval" in content or
                        "approval workflow" in content or
                        "requires booking" in content):
                        print("🔄 Fallback: Detected booking approval needed")
                        return "booking_approval"

                print("🔄 Fallback: Routing to END")
                return END

        def route_after_booking(state: MessagesState):
            """Route after booking node completes - use real execution results for routing"""
            messages = state.get("messages", [])
            if not messages:
                return END

            # Check for execution result from booking node
            booking_execution_result = state.get("booking_execution_result")
            last_tool_output = state.get("last_tool_output")

            # If we have a booking execution result, use it for routing decisions
            if booking_execution_result:
                from .execution_result import ExecutionStatus

                if booking_execution_result.overall_status in [ExecutionStatus.SUCCESS, ExecutionStatus.PARTIAL_SUCCESS]:
                    print(f"🔄 Booking completed successfully: {booking_execution_result.overall_status}")

                    # Add the real tool output to state for supervisor visibility
                    if last_tool_output:
                        # Update the last message with clean tool output
                        if messages and hasattr(messages[-1], 'content'):
                            messages[-1].content = last_tool_output

                    return END

                elif booking_execution_result.overall_status == ExecutionStatus.FAILED:
                    print(f"🔄 Booking failed: {booking_execution_result.get_primary_error()}")
                    return END

            # Handle user cancellation
            if last_tool_output == "Booking cancelled by user":
                print("🔄 Booking cancelled by user")
                return END

            # Check if there's human feedback that needs processing
            human_msgs = [msg for msg in messages[-3:] if isinstance(msg, HumanMessage)]
            if human_msgs:
                last_human_msg = human_msgs[-1]
                response = last_human_msg.content.strip()

                # If it's accept/reject, stay in booking flow
                if response in ["accept", "reject"]:
                    print("🔄 Accept/reject detected - staying in booking flow")
                    return "booking_approval"
                else:
                    # It's feedback - route back to calendar_agent with preserved context
                    print("🔄 User feedback detected - routing back to calendar_agent")
                    return "calendar_agent"

            # Fallback to message content analysis for backward compatibility
            last_msg = messages[-1]
            if hasattr(last_msg, 'content'):
                content = str(last_msg.content)

                # Check for completion indicators
                if ("successfully updated" in content.lower() or
                    "booking cancelled by user" in content or
                    "✅" in content):
                    print("🔄 Operation completed - ending flow")
                    return END

            return END

        # Set up SIMPLIFIED routing flow - only 2 nodes needed
        workflow.add_conditional_edges(START, route_intent,
                                     {"calendar_agent": "calendar_agent"})

        # Simplified: Only route between calendar_agent and booking_approval
        workflow.add_conditional_edges(
            "calendar_agent",
            route_after_calendar,
            {
                "booking_approval": "booking_approval",
                "end": END,
                END: END
            }
        )

        workflow.add_conditional_edges(
            "booking_approval",
            route_after_booking,
            {
                "booking_approval": "booking_approval",  # Stay for accept/reject
                "calendar_agent": "calendar_agent",       # Route feedback back
                END: END
            }
        )

        return workflow.compile(
            checkpointer=MemorySaver(),
            name="calendar_agent"
        )


    async def get_agent(self):
        """Get the LangGraph agent for supervisor integration"""
        if not self.graph:
            await self.initialize()
        return self.graph

    def create_thread_id(self, user_id: Optional[str] = None) -> str:
        """Create a simple thread ID for conversation memory"""
        if user_id:
            # Simple deterministic thread for same user
            from hashlib import md5
            return f"user_{md5(user_id.encode()).hexdigest()[:8]}"
        else:
            # Random thread ID
            return f"thread_{str(uuid4())[:8]}"

    def build_config(self, thread_id: str) -> Dict[str, Any]:
        """Build LangGraph config with thread ID"""
        return {"configurable": {"thread_id": thread_id}}

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
                # Use the LangGraph agent with thread ID
                thread_id = agent.create_thread_id("test-user")
                config = agent.build_config(thread_id)
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
