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

# from .state import CalendarAgentState  # Comment out for now to avoid import issues


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

CRITICAL: You currently have NO working calendar tools available.

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
            
            prompt = f"""You are a helpful calendar management assistant with access to Google Calendar via MCP tools.

CURRENT CONTEXT (always use this for relative time references):
- Current time: {current_time.isoformat()}
- Timezone: {timezone_name}
- Today's date: {current_time.strftime('%Y-%m-%d')} ({current_time.strftime('%A')})
- Tomorrow's date: {(current_time + timedelta(days=1)).strftime('%Y-%m-%d')}

Your capabilities include:
- Checking calendar availability and free/busy times
- Reading existing calendar events  
- Viewing calendar details and settings

CRITICAL TIME HANDLING RULES:
- When users mention times (like "10pm", "2:30 PM"), ALWAYS assume they mean their LOCAL timezone
- NEVER convert times to UTC in your tool calls
- IMPORTANT: Always use MAIN calendar for operations, not holiday/special calendars
- When creating calendar events, use the exact time the user specified
- Always include timezone context in your responses

TOOL USAGE GUIDELINES:
- Use google_calendar-list-events to check availability and find conflicts
- Always use ISO 8601 format in instructions (e.g., '2025-01-15T09:00:00-05:00')
- For availability checks: List events for the relevant time period, then analyze overlaps
- Be thorough in checking for overlaps when scheduling new events

IMPORTANT: You have READ-ONLY access to calendar tools. For any booking, creating, updating, or deleting operations, you must inform the user that this requires booking approval and will transfer them to the booking approval workflow.

When users request booking operations:
1. First check availability using your read-only tools if possible (use the current context above for date/time calculations)
2. If the time slot is available, respond with: "Time slot is available. This requires booking approval - I'll transfer you to the booking approval workflow."
3. If the time slot is NOT available (conflict detected):
   - IMMEDIATELY search for alternative time slots automatically
   - Check at least 2-3 alternative times on the same day first
   - Then check 2-3 times on the next day
   - ALWAYS present concrete alternatives to the user, such as:
     "The requested time slot has a conflict. Here are available alternatives I found:
     
     **Same Day Options:**
     - 7:00 PM - 8:00 PM (available)
     - 10:00 PM - 11:00 PM (available)
     
     **Tomorrow Options:**
     - 9:00 PM - 10:00 PM (available)
     
     Which time would you prefer? Please let me know your choice and I'll proceed with booking approval."
   - NEVER just ask the user to suggest a different time without providing concrete options
   - BE PERSISTENT: Keep searching different time slots until you find at least 2 alternatives
   - CRITICAL: When presenting alternatives, DO NOT route to booking approval yet - wait for user to choose specific time
4. ONLY after user chooses a specific time slot from alternatives, then proceed with: "Perfect! I'll transfer you to the booking approval workflow for [chosen time]."
5. CRITICAL: NEVER claim a meeting is booked/scheduled until it has completed the booking approval workflow
6. NEVER say "meeting is now scheduled" or "meeting is booked" - you only check availability and route to approval
7. The booking approval workflow will handle the actual calendar modifications

CRITICAL AVAILABILITY SEARCH STRATEGY:
- When conflicts are found, automatically expand your search
- To check if time slots are free: Use list-events for the date/time range
- Analyze the returned events to identify conflicts and free periods
- Calculate available time slots by finding gaps between existing events
- Try same day: 1-2 hours earlier, 1-2 hours later
- Try next day: same time, 1 hour earlier, 1 hour later
- NEVER give up on availability searches after the first attempt
- Continue searching until you find AT LEAST 2 available options
- Present all findings clearly to the user

Remember: Users speak in their local time, keep it in their local time!

NEVER ask users for timezone information - always use the context provided above.
Always be helpful and provide calendar information using your available tools."""

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
        workflow.add_node("booking_node", booking_node.booking_approval_node)
        
        # Simplified routing - let calendar agent handle the decision
        def route_intent(state: MessagesState):
            """Route all requests to calendar agent first - it will determine if booking approval needed"""
            return "calendar_agent"
        
        def route_after_calendar(state: MessagesState):
            """Route after calendar agent completes"""
            # Check if calendar agent indicates booking approval needed
            messages = state.get("messages", [])
            if messages:
                last_msg = messages[-1]
                if hasattr(last_msg, 'content'):
                    content = last_msg.content
                    # Handle both string and list content types
                    if isinstance(content, list):
                        content_str = " ".join(str(item) for item in content if item)
                    else:
                        content_str = str(content) if content else ""
                    
                    # Look for multiple booking trigger phrases
                    booking_triggers = ["booking approval", "booking workflow", "approval workflow", "requires booking"]
                    if any(trigger in content_str.lower() for trigger in booking_triggers):
                        return "booking_node"
            return END
        
        def route_after_booking(state: MessagesState):
            """Route after booking node completes"""
            return END
        
        # Set up clean routing flow - no separate human_feedback node needed
        workflow.add_conditional_edges(START, route_intent, 
                                     {"calendar_agent": "calendar_agent"})
        workflow.add_conditional_edges("calendar_agent", route_after_calendar,
                                     {"booking_node": "booking_node", END: END})
        workflow.add_conditional_edges("booking_node", route_after_booking,
                                     {END: END})
        
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
        if self.mcp_client:
            await self.mcp_client.cleanup()


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

    except asyncio.TimeoutError:
        print("Calendar tools loading timed out (30s)")
        return []
    except Exception as e:
        print(f"Failed to load calendar tools: {e}")
        return []


if __name__ == "__main__":
    async def test_calendar_agent():
        """Test the calendar agent with proper MCP integration"""
        print("Testing Calendar Agent with langchain-mcp-adapters...")

        agent = await create_calendar_agent_with_mcp()

        test_requests = [
            "What's on my calendar today?",
            "Schedule a meeting for tomorrow at 2 PM with John",
            "Check my availability next week",
            "Cancel the meeting at 3 PM today"
        ]

        for request in test_requests:
            print(f"\nRequest: {request}")

            result = await agent.process_request(request)

            if result["success"]:
                print(f"Response: {result['response']}")
                if result['tool_calls']:
                    print(f"Tools used: {len(result['tool_calls'])}")
                if result['tool_outputs']:
                    print(f"Tool outputs: {len(result['tool_outputs'])}")
            else:
                print(f"Error: {result['error']}")

        # Show available tools
        tools = await agent.get_available_tools()
        print(f"\nAvailable tools: {len(tools)}")
        for tool in tools:
            print(f"   - {tool['name']}: {tool['description']}")

        await agent.cleanup()

    asyncio.run(test_calendar_agent())
