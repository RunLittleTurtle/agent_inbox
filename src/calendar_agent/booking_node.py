"""
Booking Node for Calendar Agent - Human-in-the-Loop Approval
Handles booking operations that require human approval before execution.
"""
import os
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

# Add local libraries to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../library/langgraph'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../library/langchain-mcp-adapters'))

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_anthropic import ChatAnthropic
from langgraph.graph import MessagesState
from langgraph.types import interrupt, Command
from pydantic import BaseModel, Field


class BookingRequest(BaseModel):
    """Pydantic v2 model for calendar booking validation"""
    tool_name: str = Field(..., description="MCP tool being called")
    title: str = Field(..., description="Event title")
    start_time: str = Field(..., description="Event start time")
    end_time: str = Field(..., description="Event end time") 
    description: Optional[str] = Field(None, description="Event description")
    attendees: Optional[List[str]] = Field(default_factory=list, description="Event attendees")
    location: Optional[str] = Field(None, description="Event location")
    original_args: Dict[str, Any] = Field(..., description="Original MCP tool arguments")


class ApprovalResponse(BaseModel):
    """Human approval response model"""
    approved: bool = Field(..., description="Whether booking is approved")
    modifications: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Human modifications to booking")
    feedback: Optional[str] = Field(None, description="Human feedback or rejection reason")


class BookingNode:
    """Dedicated node for booking operations with human approval"""
    
    def __init__(self, booking_tools: List, model: Optional[ChatAnthropic] = None):
        self.booking_tools = booking_tools
        self.model = model or ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            temperature=0,
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        
    async def booking_approval_node(self, state: MessagesState) -> Dict[str, Any]:
        """
        Handle booking approval with human-in-the-loop
        Uses LangGraph interrupts to pause for human approval
        Follows LangGraph best practices for Command(resume=...) pattern
        """
        messages = state.get("messages", [])
        if not messages:
            return {"messages": [AIMessage(content="No messages found.")]}
        
        # Get the last human message that contains booking intent
        last_message = None
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                last_message = msg
                break
        
        if not last_message:
            return {"messages": [AIMessage(content="No booking request found.")]}
        
        # Extract booking intent from the last message
        booking_intent = last_message.content
        
        # Parse booking details using LLM
        booking_details = await self._extract_booking_details(booking_intent, messages)
        
        if not booking_details:
            return {"messages": [AIMessage(content="Could not understand booking request. Please provide more details.")]}
        
        # Create booking request for human approval
        booking_request = BookingRequest(**booking_details)
        
        # Handle human approval with proper LangGraph interrupt pattern
        prompt = f"📅 Booking approval required: {booking_request.title}\n\nStart: {booking_request.start_time}\nEnd: {booking_request.end_time}\nLocation: {booking_request.location or 'None'}\nDescription: {booking_request.description or 'None'}\n\nApprove (yes), modify, or reject?"
        
        while True:
            approval_response = interrupt(prompt)
            
            # Handle different response types
            if isinstance(approval_response, str):
                response_lower = approval_response.lower().strip()
                
                # Check for approval
                if response_lower in ['yes', 'approve', 'approved', 'confirm', 'ok']:
                    # Execute the original booking
                    result = await self._execute_booking(booking_request, {})
                    return {"messages": messages + [AIMessage(content=result)]}
                
                # Check for rejection
                elif response_lower in ['no', 'reject', 'rejected', 'cancel', 'deny']:
                    return {"messages": messages + [AIMessage(content="Booking cancelled by user.")]}
                
                # Handle modification requests (feedback)
                else:
                    # Process the feedback to extract modifications
                    try:
                        # Use LLM to extract modifications from feedback
                        from .booking_modification import process_booking_modification
                        modified_details = await process_booking_modification(
                            approval_response, booking_request, messages
                        )
                        
                        if modified_details:
                            # Update booking request with modifications
                            booking_request = BookingRequest(**modified_details)
                            prompt = f"📅 Updated booking: {booking_request.title}\n\nStart: {booking_request.start_time}\nEnd: {booking_request.end_time}\nLocation: {booking_request.location or 'None'}\nDescription: {booking_request.description or 'None'}\n\nApprove this updated version?"
                        else:
                            prompt = f"Could not understand modification: '{approval_response}'. Please try again or approve/reject the original booking."
                        
                    except Exception as e:
                        prompt = f"Error processing modification: {e}. Please approve (yes) or reject (no) the original booking."
            
            elif isinstance(approval_response, dict):
                # Handle structured responses
                response_type = approval_response.get('type', '').lower()
                
                if response_type == 'accept':
                    result = await self._execute_booking(booking_request, {})
                    return {"messages": messages + [AIMessage(content=result)]}
                
                elif response_type == 'reject':
                    return {"messages": messages + [AIMessage(content="Booking rejected by user.")]}
                
                else:
                    prompt = "Please respond with 'yes' to approve, 'no' to reject, or provide modification details."
            
            else:
                prompt = "Please respond with 'yes' to approve, 'no' to reject, or provide modification details."
    
    async def _extract_booking_details(self, booking_intent: str, context_messages: List[BaseMessage]) -> Optional[Dict[str, Any]]:
        """Extract structured booking details from natural language intent with conversation context"""
        
        # Get timezone context from .env using async pattern
        import os
        import asyncio
        from zoneinfo import ZoneInfo
        
        timezone_name = os.getenv("USER_TIMEZONE", "America/Toronto")
        # Use asyncio.to_thread to avoid blocking I/O in async context
        current_time = await asyncio.to_thread(lambda: datetime.now(ZoneInfo(timezone_name)))
        
        extraction_prompt = f"""Extract booking details from this request: "{booking_intent}"

IMPORTANT CONTEXT:
- Current time: {current_time.isoformat()}
- Timezone: {timezone_name}
- Today's date: {current_time.strftime('%Y-%m-%d')}
- Current day: {current_time.strftime('%A')}

Based on the request, extract:
1. Event title/summary
2. Start date/time (convert relative terms using the current context above)
   - "tomorrow" = {(current_time + timedelta(days=1)).strftime('%Y-%m-%d')}
   - "tonight" = today ({current_time.strftime('%Y-%m-%d')}) evening
   - "next week" = week starting {(current_time + timedelta(days=7)).strftime('%Y-%m-%d')}
3. End date/time (if not specified, assume 1 hour duration)
4. Description (if any)
5. Location (if any)
6. Attendees (if any)

Return a JSON object with these fields:
- tool_name: "google_calendar-create-event"
- title: string
- start_time: ISO format with timezone (e.g., "2025-09-03T15:00:00-04:00")
- end_time: ISO format with timezone  
- description: string or null
- location: string or null
- attendees: array of strings
- original_args: object with Google Calendar API format

ALWAYS include timezone offset in ISO format. Use {timezone_name} timezone.
"""
        
        try:
            response = await self.model.ainvoke([HumanMessage(content=extraction_prompt)])
            # Parse JSON from response (simplified - in production, use proper JSON parsing)
            import json
            content = response.content
            
            # Extract JSON from response
            if '{' in content and '}' in content:
                start = content.find('{')
                end = content.rfind('}') + 1
                json_str = content[start:end]
                return json.loads(json_str)
        except Exception as e:
            print(f"Error extracting booking details: {e}")
        
        return None
    
    async def _execute_booking(self, booking_request: BookingRequest, modifications: Dict[str, Any]) -> str:
        """Execute the approved booking using MCP tools"""
        
        # Apply any human modifications
        args = booking_request.original_args.copy()
        if modifications:
            args.update(modifications)
        
        # Find the appropriate tool
        tool_to_use = None
        for tool in self.booking_tools:
            if tool.name == booking_request.tool_name:
                tool_to_use = tool
                break
        
        if not tool_to_use:
            return f"❌ Booking tool {booking_request.tool_name} not available"
        
        try:
            # Execute the MCP tool
            result = tool_to_use.run(args)
            return f"✅ Booking confirmed: {booking_request.title}\n{result}"
        except Exception as e:
            return f"❌ Booking failed: {str(e)}"
