"""
MCP Client Integration for Calendar Agent
Integrates with Pipedream MCP server for Google Calendar operations.
Reference: https://langchain-ai.github.io/langgraph/reference/mcp/
"""
import asyncio
import os
from typing import List, Optional, Dict, Any
import logging

from langchain_core.tools import BaseTool
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from .state import CalendarEvent, CalendarQuery, CalendarAnalysis

logger = logging.getLogger(__name__)


class CalendarMCPClient:
    """
    MCP Client for Google Calendar operations via Pipedream.
    Handles connection management and tool loading.
    """
    
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.tools: List[BaseTool] = []
        self.server_url = os.getenv("PIPEDREAM_MCP_SERVER")
        self.is_connected = False
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
        
    async def connect(self) -> bool:
        """
        Connect to MCP server and load calendar tools.
        Returns True if successful, False otherwise.
        """
        try:
            if not self.server_url:
                logger.error("PIPEDREAM_MCP_SERVER environment variable not set")
                return False
                
            # For Pipedream MCP server, we use the supergateway connection
            server_params = StdioServerParameters(
                command="npx",
                args=[
                    "-y",
                    "supergateway", 
                    "--sse",
                    self.server_url
                ]
            )
            
            # Create session
            async with stdio_client(server_params) as (read, write):
                self.session = ClientSession(read, write)
                
                # Load tools using LangGraph MCP adapter
                self.tools = await load_mcp_tools(
                    session=self.session,
                    connection=None
                )
                
                self.is_connected = True
                logger.info(f"Connected to MCP server, loaded {len(self.tools)} tools")
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            self.is_connected = False
            return False
            
    async def disconnect(self):
        """Disconnect from MCP server."""
        if self.session:
            # Close session if needed
            self.session = None
        self.is_connected = False
        self.tools = []
        logger.info("Disconnected from MCP server")
        
    def get_tools(self) -> List[BaseTool]:
        """Get loaded MCP tools."""
        return self.tools
        
    def get_calendar_tools(self) -> Dict[str, BaseTool]:
        """Get calendar-specific tools organized by function."""
        calendar_tools = {}
        
        for tool in self.tools:
            tool_name = tool.name.lower()
            
            # Map tool names to calendar functions
            if "list" in tool_name or "get" in tool_name:
                calendar_tools["list_events"] = tool
            elif "create" in tool_name or "add" in tool_name:
                calendar_tools["create_event"] = tool  
            elif "update" in tool_name or "modify" in tool_name:
                calendar_tools["update_event"] = tool
            elif "delete" in tool_name or "remove" in tool_name:
                calendar_tools["delete_event"] = tool
            elif "availability" in tool_name or "busy" in tool_name:
                calendar_tools["check_availability"] = tool
                
        return calendar_tools


class CalendarToolManager:
    """
    High-level interface for calendar operations using MCP tools.
    Provides typed methods for common calendar operations.
    """
    
    def __init__(self, mcp_client: CalendarMCPClient):
        self.mcp_client = mcp_client
        self.tools = {}
        
    async def initialize(self) -> bool:
        """Initialize the tool manager and load tools."""
        if not self.mcp_client.is_connected:
            success = await self.mcp_client.connect()
            if not success:
                return False
                
        self.tools = self.mcp_client.get_calendar_tools()
        return len(self.tools) > 0
        
    async def list_events(
        self,
        calendar_id: str = "primary",
        time_min: Optional[str] = None,
        time_max: Optional[str] = None,
        max_results: int = 10
    ) -> List[CalendarEvent]:
        """List calendar events using MCP tool."""
        if "list_events" not in self.tools:
            raise ValueError("List events tool not available")
            
        tool = self.tools["list_events"]
        
        # Prepare tool arguments
        args = {
            "calendar_id": calendar_id,
            "max_results": max_results
        }
        
        if time_min:
            args["time_min"] = time_min
        if time_max:
            args["time_max"] = time_max
            
        try:
            # Execute MCP tool
            result = await tool.ainvoke(args)
            
            # Parse result into CalendarEvent objects
            events = []
            if isinstance(result, dict) and "events" in result:
                for event_data in result["events"]:
                    events.append(self._parse_event_data(event_data))
            elif isinstance(result, list):
                for event_data in result:
                    events.append(self._parse_event_data(event_data))
                    
            return events
            
        except Exception as e:
            logger.error(f"Error listing events: {e}")
            return []
            
    async def create_event(
        self,
        event: CalendarEvent,
        calendar_id: str = "primary"
    ) -> Optional[CalendarEvent]:
        """Create a calendar event using MCP tool."""
        if "create_event" not in self.tools:
            raise ValueError("Create event tool not available")
            
        tool = self.tools["create_event"]
        
        # Prepare event data
        event_data = {
            "calendar_id": calendar_id,
            "summary": event.title,
            "description": event.description,
            "start": {
                "dateTime": event.start_datetime.isoformat(),
                "timeZone": "UTC"
            },
            "end": {
                "dateTime": event.end_datetime.isoformat(),
                "timeZone": "UTC"
            },
            "location": event.location,
            "attendees": [{"email": email} for email in event.attendees] if event.attendees else []
        }
        
        try:
            result = await tool.ainvoke(event_data)
            
            if isinstance(result, dict):
                return self._parse_event_data(result)
            return None
            
        except Exception as e:
            logger.error(f"Error creating event: {e}")
            return None
            
    async def check_availability(
        self,
        time_min: str,
        time_max: str,
        calendar_ids: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Check calendar availability using MCP tool."""
        if "check_availability" not in self.tools:
            raise ValueError("Check availability tool not available")
            
        tool = self.tools["check_availability"]
        
        args = {
            "time_min": time_min,
            "time_max": time_max,
            "calendar_ids": calendar_ids or ["primary"]
        }
        
        try:
            result = await tool.ainvoke(args)
            return result if isinstance(result, list) else []
            
        except Exception as e:
            logger.error(f"Error checking availability: {e}")
            return []
            
    def _parse_event_data(self, event_data: Dict[str, Any]) -> CalendarEvent:
        """Parse raw event data into CalendarEvent object."""
        from datetime import datetime
        
        # Handle different datetime formats
        start_dt = self._parse_datetime(event_data.get("start", {}))
        end_dt = self._parse_datetime(event_data.get("end", {}))
        
        # Extract attendees
        attendees = []
        if "attendees" in event_data:
            attendees = [attendee.get("email", "") for attendee in event_data["attendees"]]
            
        return CalendarEvent(
            id=event_data.get("id"),
            title=event_data.get("summary", ""),
            description=event_data.get("description"),
            start_datetime=start_dt,
            end_datetime=end_dt,
            location=event_data.get("location"),
            attendees=attendees,
            calendar_id=event_data.get("calendar_id"),
            status=event_data.get("status", "confirmed"),
            visibility=event_data.get("visibility", "default")
        )
        
    def _parse_datetime(self, dt_data: Dict[str, Any]) -> datetime:
        """Parse datetime from various formats."""
        from datetime import datetime
        
        if "dateTime" in dt_data:
            dt_str = dt_data["dateTime"]
            # Handle ISO format with timezone
            if dt_str.endswith("Z"):
                return datetime.fromisoformat(dt_str[:-1])
            elif "+" in dt_str or dt_str.count("-") > 2:
                # Has timezone info
                return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            else:
                return datetime.fromisoformat(dt_str)
        elif "date" in dt_data:
            # All-day event
            date_str = dt_data["date"]
            return datetime.fromisoformat(f"{date_str}T00:00:00")
        else:
            # Fallback to current time
            return datetime.now()


# Factory function for creating MCP client
async def create_calendar_mcp_client() -> CalendarMCPClient:
    """Create and initialize calendar MCP client."""
    client = CalendarMCPClient()
    await client.connect()
    return client
