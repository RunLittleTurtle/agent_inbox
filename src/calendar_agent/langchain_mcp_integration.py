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
        model: Optional[ChatOpenAI] = None,
        mcp_servers: Optional[Dict[str, Dict[str, Any]]] = None
    ):
        self.model = model or ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            openai_api_key=os.getenv("OPENAI_API_KEY")
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
        
        # Cache tools for 5 minutes to prevent excessive connections
        if (self._mcp_tools and self._tools_cache_time and
            datetime.now() - self._tools_cache_time < timedelta(minutes=5)):
            return self._mcp_tools

        # Use the configured MCP server URL
        mcp_url = self.mcp_servers.get("pipedream_calendar", {}).get("url")
        if not mcp_url:
            raise ValueError("Pipedream MCP server URL not configured")

        self.logger.info(f"Connecting to Pipedream MCP server: {mcp_url}")

        # MEMORY LEAK FIX: Reuse client instance with timeout protection
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
            self.tools = await self._get_mcp_tools()
            
            print(f"✅ Loaded {len(self.tools)} calendar tools from MCP server")
            for tool in self.tools:
                print(f"   📋 {tool.name}: {tool.description}")
                
            # Create the graph
            self.graph = await self._create_calendar_graph()
            
        except Exception as e:
            print(f"❌ Failed to initialize MCP client: {e}")
            # Fallback to no tools
            self.tools = []
            self.graph = await self._create_calendar_graph()

    async def _create_calendar_graph(self):
        """Create calendar agent graph with proper tool integration"""

        def call_model(state: MessagesState):
            """Call model with tools bound and proper limitations awareness"""
            if not self.tools:
                # No tools available - use model with explicit limitations prompt
                system_message = """You are a calendar agent in a multi-agent supervisor system.

CRITICAL: You currently have NO working calendar tools available.

When users request calendar operations:
1. Acknowledge their specific request with details
2. Clearly explain that you cannot access calendar tools currently
3. Provide helpful information about what would normally happen
4. Be completely honest about limitations

Example: "I understand you want to book a meeting for [specific details]. However, I currently cannot access Google Calendar tools to create this event. The MCP server connection needs to be established first. Once connected, I can help with calendar operations."

NEVER claim to have successfully completed calendar operations when you have no tools."""
                
                messages_with_system = [{"role": "system", "content": system_message}] + state["messages"]
                response = self.model.invoke(messages_with_system)
            else:
                # Tools available - bind tools to model with enhanced temporal and tool usage prompt
                temporal_system_message = """You are a calendar agent with access to Google Calendar tools.

CRITICAL TIME HANDLING RULES:
- When users mention times (like "10pm", "2:30 PM"), ALWAYS assume they mean their LOCAL timezone
- NEVER convert times to UTC in your tool calls
- When creating calendar events, use the exact time the user specified
- Always include timezone context in your responses
- Structure temporal requests clearly before calling tools

TOOL USAGE GUIDELINES:
- Use google_calendar_tool for ALL calendar operations (it's a comprehensive tool)
- For FINDING/SEARCHING events: Use instruction like "List all events containing '[keyword]'" or "Find events with [search_terms]"
- For CHECKING availability: Use instruction like "Check for conflicts on [date/time]"
- For CREATING events: Use appropriate creation instructions with [event_details]
- The tool can handle multiple types of operations - be specific in your instruction parameter

CRITICAL PERSISTENCE RULES:
- NEVER give up on availability searches after the first attempt
- When searching for available time slots, systematically check multiple dates/times
- If the first suggested time is unavailable, immediately check alternative times
- Continue searching until you find AT LEAST one available option that meets the criteria
- Expand search parameters if needed (different days, times, durations)
- Only report "no availability" after exhaustively checking multiple options
- Be proactive in suggesting alternative times when conflicts are found

EXAMPLES:
- User: "find my [EVENT_NAME]" → google_calendar_tool with instruction: "List all events containing '[EVENT_NAME]'"
- User: "what's on my calendar [TIME_PERIOD]" → google_calendar_tool with instruction: "List all events for [TIME_PERIOD]"
- User: "check if I'm free at [TIME]" → google_calendar_tool with instruction: "Check availability for [TIME]"
- User: "book [EVENT_TYPE] at [TIME]" → Create event with appropriate details

Remember: Users speak in their local time, keep it in their local time!"""
                
                messages_with_system = [{"role": "system", "content": temporal_system_message}] + state["messages"]
                model_with_tools = self.model.bind_tools(self.tools)
                response = model_with_tools.invoke(messages_with_system)
            
            return {"messages": [response]}

        # Build StateGraph following langchain-mcp-adapters patterns
        builder = StateGraph(MessagesState)

        # Add model node
        builder.add_node("call_model", call_model)

        # Add tool node if we have tools
        if self.tools:
            builder.add_node("tools", ToolNode(self.tools))

            # Add conditional edges for tool calling
            builder.add_conditional_edges(
                "call_model",
                tools_condition,
                {"tools": "tools", "__end__": "__end__"}
            )

            # Tools route back to model
            builder.add_edge("tools", "call_model")
        else:
            # No tools, just end after model call
            builder.add_edge("call_model", "__end__")

        # Set entry point
        builder.add_edge(START, "call_model")

        # Compile with checkpointer
        checkpointer = MemorySaver()
        return builder.compile(checkpointer=checkpointer)

    async def process_request(
        self,
        message: str,
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process calendar request through MCP tools"""

        if not self.graph:
            await self.initialize()

        if not self.graph:
            return {
                "error": "Calendar agent not initialized",
                "success": False
            }

        try:
            # Create input message
            input_message = HumanMessage(content=message)

            # Run through graph
            result = await self.graph.ainvoke(
                {"messages": [input_message]},
                config={"thread_id": thread_id or f"calendar_{datetime.now().isoformat()}"}
            )

            # Extract response
            messages = result.get("messages", [])
            if messages:
                last_message = messages[-1]
                response_content = last_message.content

                # Check if tools were used
                tool_calls = []
                tool_outputs = []

                for msg in messages:
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        tool_calls.extend(msg.tool_calls)
                    if hasattr(msg, 'name') and hasattr(msg, 'content'):
                        # This is a tool output message
                        tool_outputs.append({
                            "tool": msg.name,
                            "output": msg.content
                        })

                return {
                    "response": response_content,
                    "tool_calls": tool_calls,
                    "tool_outputs": tool_outputs,
                    "messages": messages,
                    "success": True,
                    "tools_available": len(self.tools)
                }
            else:
                return {
                    "error": "No response generated",
                    "success": False
                }

        except Exception as e:
            return {
                "error": f"Processing failed: {str(e)}",
                "success": False
            }

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
    model: Optional[ChatOpenAI] = None,
    mcp_servers: Optional[Dict[str, Dict[str, Any]]] = None
) -> CalendarAgentWithMCP:
    """
    Factory function to create and initialize calendar agent with MCP.

    Args:
        model: ChatOpenAI model instance
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
            print("⚠️ PIPEDREAM_MCP_SERVER environment variable not set")
            return []

        mcp_servers = {
            "pipedream_calendar": {
                "url": pipedream_url,
                "transport": "streamable_http"
            }
        }

        print(f"🔗 Connecting to Pipedream MCP server: {pipedream_url}")
        
        client = MultiServerMCPClient(mcp_servers)
        
        # Add timeout to prevent hanging
        tools = await asyncio.wait_for(
            client.get_tools(),
            timeout=30.0
        )

        print(f"✅ Retrieved {len(tools)} calendar tools for supervisor")
        for tool in tools:
            print(f"   📊 {tool.name}: {tool.description[:100]}...")
        
        # CRITICAL FIX: Create truly synchronous tools from async MCP tools
        from langchain_core.tools import StructuredTool
        import asyncio as async_module
        import concurrent.futures
        
        sync_tools = []
        
        # Create tool name mapping for problematic names
        tool_name_mapping = {
            "google_calendar-query-free-busy-calendars": "calendar_check_availability"
        }
        
        for async_tool in tools:
            # Handle problematic tool names (OpenAI 64-char limit)
            if async_tool.name == "google_calendar-query-free-busy-calendars":
                # Create wrapper with short name but preserve all functionality
                def calendar_tool_sync(**kwargs) -> str:
                    """Google Calendar tool - supports both availability checking and event listing"""
                    try:
                        # Run the original async tool
                        loop = None
                        try:
                            loop = async_module.get_running_loop()
                        except RuntimeError:
                            pass
                        
                        if loop is None:
                            result = async_module.run(async_tool.ainvoke(kwargs))
                        else:
                            with concurrent.futures.ThreadPoolExecutor() as executor:
                                future = executor.submit(async_module.run, async_tool.ainvoke(kwargs))
                                result = future.result(timeout=30)
                        
                        return str(result)
                    except Exception as e:
                        return f"Error executing calendar operation: {str(e)}"
                
                # Create single tool with comprehensive description
                calendar_tool = StructuredTool(
                    name="google_calendar_tool",  # 19 chars - well under limit
                    description="Google Calendar operations: list events, search events by keyword (e.g. 'motocross'), check availability, find conflicts, and query calendar data. Use instruction parameter to specify what you want to do.",
                    args_schema=async_tool.args_schema,
                    func=calendar_tool_sync,
                    return_direct=False
                )
                sync_tools.append(calendar_tool)
                continue
            
            # Create a truly synchronous tool function for other tools
            def make_sync_tool(atool):
                def sync_func(**kwargs) -> str:
                    """Synchronous function that runs async MCP tool"""
                    try:
                        # Run the async tool in a new event loop if needed
                        loop = None
                        try:
                            loop = async_module.get_running_loop()
                        except RuntimeError:
                            pass
                        
                        if loop is None:
                            # No running loop, create new one
                            result = async_module.run(atool.ainvoke(kwargs))
                        else:
                            # Create a new thread to run the async tool
                            with concurrent.futures.ThreadPoolExecutor() as executor:
                                future = executor.submit(async_module.run, atool.ainvoke(kwargs))
                                result = future.result(timeout=30)
                        
                        return str(result)
                    except Exception as e:
                        return f"Error executing {atool.name}: {str(e)}"
                
                # Create StructuredTool with sync func, NOT coroutine
                sync_tool = StructuredTool(
                    name=atool.name,
                    description=atool.description,
                    args_schema=atool.args_schema,
                    func=sync_func,  # Use func, NOT coroutine
                    return_direct=False
                )
                return sync_tool
            
            sync_tools.append(make_sync_tool(async_tool))
        
        print(f"✅ Created {len(sync_tools)} truly sync calendar tools")
        return sync_tools

    except asyncio.TimeoutError:
        print("⚠️ Calendar tools loading timed out (30s)")
        return []
    except Exception as e:
        print(f"⚠️ Failed to load calendar tools: {e}")
        return []


if __name__ == "__main__":
    async def test_calendar_agent():
        """Test the calendar agent with proper MCP integration"""
        print("🧪 Testing Calendar Agent with langchain-mcp-adapters...")

        agent = await create_calendar_agent_with_mcp()

        test_requests = [
            "What's on my calendar today?",
            "Schedule a meeting for tomorrow at 2 PM with John",
            "Check my availability next week",
            "Cancel the meeting at 3 PM today"
        ]

        for request in test_requests:
            print(f"\n📝 Request: {request}")

            result = await agent.process_request(request)

            if result["success"]:
                print(f"✅ Response: {result['response']}")
                if result['tool_calls']:
                    print(f"🔧 Tools used: {len(result['tool_calls'])}")
                if result['tool_outputs']:
                    print(f"📊 Tool outputs: {len(result['tool_outputs'])}")
            else:
                print(f"❌ Error: {result['error']}")

        # Show available tools
        tools = await agent.get_available_tools()
        print(f"\n📋 Available tools: {len(tools)}")
        for tool in tools:
            print(f"   • {tool['name']}: {tool['description']}")

        await agent.cleanup()

    asyncio.run(test_calendar_agent())
