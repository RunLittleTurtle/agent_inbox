"""
Booking Node for Calendar Agent - Human-in-the-Loop Approval
Handles booking operations that require human approval before execution.
"""
import os
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add local libraries to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../library/langgraph'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../library/langchain-mcp-adapters'))

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_anthropic import ChatAnthropic
from langgraph.graph import MessagesState
from langgraph.types import interrupt, Command
from pydantic import BaseModel, Field
from langgraph.prebuilt.interrupt import HumanInterruptConfig, HumanInterrupt


class BookingRequest(BaseModel):
    """Pydantic v2 model for calendar booking validation"""
    tool_name: str = Field(..., description="MCP tool being called")
    title: str = Field(..., description="Event title")
    start_time: str = Field(..., description="Event start time")
    end_time: str = Field(..., description="Event end time")
    description: Optional[str] = Field(None, description="Event description")
    attendees: Optional[List[str]] = Field(default_factory=list, description="Event attendees")
    location: Optional[str] = Field(None, description="Event location")
    requires_event_id: bool = Field(default=False, description="Whether event ID is required for updates")
    color_id: Optional[str] = Field(None, description="Event color ID (1-11)")
    transparency: str = Field(default="opaque", description="Event transparency (opaque/transparent)")
    visibility: str = Field(default="default", description="Event visibility (default/public/private)")
    recurrence: Optional[List[str]] = Field(None, description="Recurrence rules (RRULE)")
    reminders: Dict[str, Any] = Field(default_factory=lambda: {"useDefault": True}, description="Reminder settings")
    guests_can_invite_others: bool = Field(default=True, description="Whether guests can invite others")
    guests_can_modify: bool = Field(default=False, description="Whether guests can modify event")
    guests_can_see_other_guests: bool = Field(default=True, description="Whether guests can see other guests")
    anyone_can_add_self: bool = Field(default=False, description="Whether anyone can add themselves")
    conference_data: Optional[Dict[str, Any]] = Field(None, description="Conference/video meeting data")
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
        Handle booking approval with human-in-the-loop using proper LangGraph patterns.
        Uses interrupt() and Command(resume=...) following official LangGraph best practices.
        Reference: https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/add-human-in-the-loop/
        """
        messages = state.get("messages", [])
        if not messages:
            return {"messages": [AIMessage(content="No messages found.")]}

        # Extract booking intent from routing context or conversation
        booking_intent, routing_context, conversation_summary = self._extract_routing_context(messages)

        if not booking_intent:
            return {"messages": [AIMessage(content="No booking request found.")]}

        # Parse booking details using enhanced context
        booking_details = await self._extract_booking_details_enhanced(
            booking_intent, messages, conversation_summary, routing_context
        )

        if not booking_details:
            error_msg = f"Could not understand booking request: '{booking_intent}'"
            if routing_context:
                error_msg += f"\nRouter analysis: {routing_context.get('reasoning', 'N/A')}"
            return {"messages": [AIMessage(content=error_msg)]}

        # Create booking request for human approval
        booking_request = BookingRequest(**booking_details)

        # **PROPER LANGGRAPH PATTERN**: Use interrupt() with structured payload
        approval_prompt = {
            "type": "booking_approval",
            "message": "📅 Booking Approval Required",
            "booking_details": {
                "title": booking_request.title,
                "start_time": booking_request.start_time,
                "end_time": booking_request.end_time,
                "location": booking_request.location or "None",
                "description": booking_request.description or "None",
                "tool_name": booking_request.tool_name,
                "attendees": booking_request.attendees,
                "requires_event_id": booking_request.requires_event_id,
                "transparency": booking_request.transparency,
                "visibility": booking_request.visibility,
                "color_id": booking_request.color_id,
                "guests_can_invite_others": booking_request.guests_can_invite_others,
                "guests_can_modify": booking_request.guests_can_modify,
                "reminders": booking_request.reminders,
                "recurrence": booking_request.recurrence,
                "conference_data": booking_request.conference_data
            },
            "instructions": "Please respond with 'approve', 'reject', or provide modification feedback"
        }

        # Use validation loop with multiple interrupt() calls for proper validation
        while True:
            # **CORE LANGGRAPH PATTERN**: interrupt() pauses and waits for human input
            human_response = interrupt(approval_prompt)

            # Validate and process the human response
            validation_result = self._validate_human_response(human_response, booking_request)

            if validation_result["valid"]:
                action = validation_result["action"]

                if action == "approve":
                    # Execute the booking
                    result = await self._execute_booking(booking_request, validation_result.get("modifications", {}))
                    return {"messages": messages + [AIMessage(content=result)]}

                elif action == "reject":
                    return {"messages": messages + [AIMessage(content="❌ Booking cancelled by user.")]}

                elif action == "modify":
                    # Update booking request with modifications
                    try:
                        modified_details = await self._process_modifications(
                            human_response, booking_request, messages
                        )
                        if modified_details:
                            booking_request = BookingRequest(**modified_details)
                            # Update prompt with new details for next iteration
                            approval_prompt["booking_details"] = {
                                "title": booking_request.title,
                                "start_time": booking_request.start_time,
                                "end_time": booking_request.end_time,
                                "location": booking_request.location or "None",
                                "description": booking_request.description or "None"
                            }
                            approval_prompt["message"] = "📅 Updated Booking - Please Review"
                        else:
                            approval_prompt["message"] = "❌ Could not process modifications. Please try again."
                    except Exception as e:
                        approval_prompt["message"] = f"❌ Error processing modifications: {e}"

            else:
                # Invalid response - update prompt with validation message
                approval_prompt["message"] = f"❌ {validation_result['error']}. Please try again."
                approval_prompt["instructions"] = "Valid responses: 'approve', 'reject', or modification details"

    async def _extract_booking_details_enhanced(
        self,
        booking_intent: str,
        context_messages: List[BaseMessage],
        conversation_summary: str,
        routing_context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Enhanced booking detail extraction with full conversation context"""

        # Get timezone context from .env using async pattern
        import os
        import asyncio
        from zoneinfo import ZoneInfo

        timezone_name = os.getenv("USER_TIMEZONE", "America/Toronto")
        # Use asyncio.to_thread to avoid blocking I/O in async context
        current_time = await asyncio.to_thread(lambda: datetime.now(ZoneInfo(timezone_name)))

        # Enhanced extraction prompt with MCP tool schema requirements
        extraction_prompt = f"""Extract booking details from this request: "{booking_intent}"

CONVERSATION CONTEXT:
{conversation_summary}

ROUTING ANALYSIS:
{routing_context.get('reasoning', 'None') if routing_context else 'None'}

CURRENT TIME CONTEXT:
- Current time: {current_time.isoformat()}
- Timezone: {timezone_name}
- Today's date: {current_time.strftime('%Y-%m-%d')}
- Current day: {current_time.strftime('%A')}

EXTRACTION RULES:
1. Use the FULL conversation context to understand the booking intent
2. If the request mentions "instead" or "change to", look for previous booking attempts
3. Extract relative time references (tonight, tomorrow, next week)
4. Infer missing details from conversation context

Based on the request and context, extract:
1. Event title/summary (infer from conversation if not explicit)
2. Start date/time (convert relative terms using the current context above)
   - "tomorrow" = {(current_time + timedelta(days=1)).strftime('%Y-%m-%d')}
   - "tonight" = today ({current_time.strftime('%Y-%m-%d')}) evening
   - "next week" = week starting {(current_time + timedelta(days=7)).strftime('%Y-%m-%d')}
3. End date/time (if not specified, assume 1 hour duration)
4. Description (if any, or infer from conversation)
5. Location (if any)
6. Attendees (if any)
TOOL SELECTION RULES:
Analyze the conversation context and choose the appropriate tool:
- Use "google_calendar-create-event" for NEW bookings (first time booking)
- Use "google_calendar-add-attendees-to-event" for ADDING attendees (prioritize this when attendees are mentioned, even with other changes)
- Use "google_calendar-update-event" for OTHER changes to existing bookings (time, title, location changes WITHOUT attendees)
- Look for keywords like "change", "modify", "update", "instead", "move to", "reschedule", "made a mistake"
- If conversation shows a previous booking was successful and user wants changes, use UPDATE
- CRITICAL: If attendees are being added/mentioned, always use "google_calendar-add-attendees-to-event" even if other fields are changing
- When both time AND attendees are changing, prioritize attendee addition as the primary operation

Return a JSON object with these fields matching the Pipedream MCP tool format:
- tool_name: Choose appropriate tool based on conversation analysis above
- title: string (descriptive title based on context)
- start_time: ISO format with timezone (e.g., "2025-09-03T15:00:00-04:00")
- end_time: ISO format with timezone
- description: string or null
- location: string or null
- attendees: array of email strings (CRITICAL: always include attendee emails when mentioned)
- requires_event_id: boolean (true if updating/modifying existing event)
- color_id: string or null (1-11 for different colors)
- transparency: "transparent" or "opaque" (for availability)
- visibility: "default", "public", or "private"
- recurrence: array of RRULE strings or null (for recurring events)
- reminders: object with useDefault boolean or overrides array
- guests_can_invite_others: boolean (default true)
- guests_can_modify: boolean (default false)
- guests_can_see_other_guests: boolean (default true)
- anyone_can_add_self: boolean (default false)
- conference_data: object or null (for video meetings)
- original_args: object with complete MCP tool format:
  {{
    "summary": "Event title",
    "start": "2025-09-03T15:00:00-04:00",
    "end": "2025-09-03T16:00:00-04:00",
    "description": "Event description",
    "location": "Location if any",
    "attendees": ["email1@domain.com", "email2@domain.com"],
    "colorId": "2",
    "transparency": "opaque",
    "visibility": "default",
    "recurrence": null,
    "reminders": {{"useDefault": true}},
    "guestsCanInviteOthers": true,
    "guestsCanModify": false,
    "guestsCanSeeOtherGuests": true,
    "anyoneCanAddSelf": false,
    "conferenceData": null
  }}

CRITICAL: Use SIMPLE format - no nested objects, just direct field values.
ALWAYS include timezone offset in ISO format. Use {timezone_name} timezone.
If context suggests this is modifying a previous booking, incorporate that into the title.
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
                result = json.loads(json_str)

                # Add context metadata
                result['_context'] = {
                    'routing_analysis': routing_context,
                    'conversation_summary': conversation_summary,
                    'extraction_source': 'enhanced_context'
                }

                return result
        except Exception as e:
            print(f"Error extracting booking details: {e}")

        return None

    def _extract_routing_context(self, messages: List[BaseMessage]) -> tuple[str, Optional[Dict], str]:
        """Extract routing context from messages using LangGraph patterns"""
        routing_context = None
        booking_context = None
        conversation_summary = ""
        booking_intent = ""

        # Look for routing context in recent messages
        for msg in reversed(messages[-10:]):
            if hasattr(msg, 'additional_kwargs') and msg.additional_kwargs:
                kwargs = msg.additional_kwargs
                if 'routing_decision' in kwargs:
                    routing_context = kwargs['routing_decision']
                if 'booking_context' in kwargs:
                    booking_context = kwargs['booking_context']
                if 'conversation_summary' in kwargs:
                    conversation_summary = kwargs['conversation_summary']
                if 'user_intent' in kwargs:
                    booking_intent = kwargs['user_intent']
                    break

        # Fallback: Extract from conversation if no routing context found
        if not routing_context:
            user_messages = []
            for msg in messages:
                if isinstance(msg, HumanMessage):
                    content = msg.content
                    if isinstance(content, list):
                        content_str = " ".join(str(item) for item in content if item)
                    else:
                        content_str = str(content) if content else ""
                    user_messages.append(content_str)

            if user_messages:
                booking_intent = " ".join(user_messages[-3:])
                conversation_summary = "\n".join([f"User: {msg}" for msg in user_messages[-5:]])
        else:
            # Use preserved routing context
            if not booking_intent:
                booking_intent = routing_context.get('user_intent', '')
                if not booking_intent and booking_context:
                    booking_intent = booking_context.get('original_intent', '')

        return booking_intent, routing_context, conversation_summary

    def _validate_human_response(self, response: Any, booking_request: BookingRequest) -> Dict[str, Any]:
        """Validate human response following LangGraph validation patterns"""
        # **FIX**: Handle list responses from Agent Inbox UI
        if isinstance(response, list):
            if len(response) == 0:
                return {"valid": False, "error": "Empty list response received"}
            # Take the first item from the list
            response = response[0]

        if isinstance(response, str):
            response_lower = response.lower().strip()

            # Check for approval keywords
            if response_lower in ['approve', 'approved', 'yes', 'confirm', 'ok', 'accept']:
                return {"valid": True, "action": "approve"}

            # Check for rejection keywords
            elif response_lower in ['reject', 'rejected', 'no', 'cancel', 'deny']:
                return {"valid": True, "action": "reject"}

            # Any other text is treated as modification request
            elif len(response.strip()) > 0:
                return {"valid": True, "action": "modify", "modifications": response}
            else:
                return {"valid": False, "error": "Empty response received"}

        elif isinstance(response, dict):
            # Handle structured responses (from UI)
            response_type = response.get('type', '').lower()
            if response_type in ['accept', 'approve']:
                return {"valid": True, "action": "approve"}
            elif response_type in ['reject', 'deny']:
                return {"valid": True, "action": "reject"}
            elif response_type == 'edit':
                return {"valid": True, "action": "modify", "modifications": response.get('modifications', {})}
            else:
                return {"valid": False, "error": f"Unknown response type: {response_type}"}
        else:
            return {"valid": False, "error": f"Invalid response format: {type(response)}"}

    async def _process_modifications(self, response: Any, booking_request: BookingRequest, messages: List[BaseMessage]) -> Optional[Dict[str, Any]]:
        """Process modification requests using LLM analysis"""
        try:
            # For now, return the original booking details
            # TODO: Implement LLM-based modification processing
            modification_text = response if isinstance(response, str) else str(response)

            # Simple keyword-based modifications (can be enhanced with LLM)
            original_details = booking_request.dict()

            # Basic time modification detection
            if "time" in modification_text.lower():
                # Could use LLM here to extract new time
                pass

            return original_details

        except Exception as e:
            print(f"Error processing modifications: {e}")
            return None

    async def _execute_booking(self, booking_request: BookingRequest, modifications: Dict[str, Any]) -> str:
        """Execute the approved booking using MCP tools following LangGraph best practices"""

        # Apply any human modifications
        args = booking_request.original_args.copy()
        args.update(modifications)

        # Ensure all required fields are present for Pipedream MCP tool
        if "summary" not in args:
            args["summary"] = booking_request.title
        if "start" not in args:
            args["start"] = booking_request.start_time
        if "end" not in args:
            args["end"] = booking_request.end_time

        # Ensure attendees are properly formatted as array of email strings
        if "attendees" in args and args["attendees"]:
            if isinstance(args["attendees"], list):
                # Convert attendee objects to email strings if needed
                formatted_attendees = []
                for attendee in args["attendees"]:
                    if isinstance(attendee, dict) and "email" in attendee:
                        formatted_attendees.append(attendee["email"])
                    elif isinstance(attendee, str):
                        formatted_attendees.append(attendee)
                args["attendees"] = formatted_attendees
            elif isinstance(args["attendees"], str):
                args["attendees"] = [args["attendees"]]

        # Set default values for optional Google Calendar fields
        if "colorId" not in args:
            args["colorId"] = None
        if "transparency" not in args:
            args["transparency"] = "opaque"  # User is busy by default
        if "visibility" not in args:
            args["visibility"] = "default"
        if "guestsCanInviteOthers" not in args:
            args["guestsCanInviteOthers"] = True
        if "guestsCanModify" not in args:
            args["guestsCanModify"] = False
        if "guestsCanSeeOtherGuests" not in args:
            args["guestsCanSeeOtherGuests"] = True
        if "anyoneCanAddSelf" not in args:
            args["anyoneCanAddSelf"] = False
        if "reminders" not in args:
            args["reminders"] = {"useDefault": True}

        # Add the missing instruction parameter that Pipedream MCP tools require
        # Include ALL available fields in the instruction for proper MCP tool data passing
        if "instruction" not in args:
            # Build comprehensive instruction with all available fields
            instruction_parts = []

            if "update" in booking_request.tool_name:
                instruction_parts.append(f"Update calendar event: {booking_request.title}")
                instruction_parts.append(f"Time: {booking_request.start_time} to {booking_request.end_time}")
            elif "add-attendees" in booking_request.tool_name:
                instruction_parts.append(f"Add attendees to calendar event: {booking_request.title}")
                if args.get("attendees"):
                    instruction_parts.append(f"Attendees to add: {', '.join(args['attendees'])}")
            else:
                instruction_parts.append(f"Create calendar event: {booking_request.title}")
                instruction_parts.append(f"Time: {booking_request.start_time} to {booking_request.end_time}")

            # Add all optional fields to instruction if present
            if args.get("description"):
                instruction_parts.append(f"Description: {args['description']}")
            if args.get("location"):
                instruction_parts.append(f"Location: {args['location']}")
            if args.get("attendees") and "add-attendees" not in booking_request.tool_name:
                instruction_parts.append(f"Attendees: {', '.join(args['attendees'])}")
            if args.get("colorId"):
                instruction_parts.append(f"Color: {args['colorId']}")
            if args.get("transparency"):
                instruction_parts.append(f"Transparency: {args['transparency']}")
            if args.get("visibility"):
                instruction_parts.append(f"Visibility: {args['visibility']}")
            if args.get("guestsCanInviteOthers") is not None:
                instruction_parts.append(f"Guests can invite others: {args['guestsCanInviteOthers']}")
            if args.get("guestsCanModify") is not None:
                instruction_parts.append(f"Guests can modify: {args['guestsCanModify']}")
            if args.get("guestsCanSeeOtherGuests") is not None:
                instruction_parts.append(f"Guests can see other guests: {args['guestsCanSeeOtherGuests']}")
            if args.get("anyoneCanAddSelf") is not None:
                instruction_parts.append(f"Anyone can add self: {args['anyoneCanAddSelf']}")
            if args.get("reminders"):
                instruction_parts.append(f"Reminders: {args['reminders']}")

            # Join all instruction parts with semicolons for clarity
            args["instruction"] = "; ".join(instruction_parts)

        # Handle event ID for update/modify operations
        if "update" in booking_request.tool_name or "add-attendees" in booking_request.tool_name:
            # For now, we'll need to search for the most recent event that matches
            # In a real implementation, we'd need to track event IDs from previous bookings
            if "event_id" not in args:
                print("⚠️  Warning: Update operation requires event_id - may need to implement event search")
                # Could add logic here to search for recent events matching the criteria

        # Find the correct MCP tool
        tool_to_use = None
        for tool in self.booking_tools:
            if tool.name == booking_request.tool_name:
                tool_to_use = tool
                break


        if not tool_to_use:
            return f"❌ Booking tool {booking_request.tool_name} not available"

        try:
            # **LANGGRAPH BEST PRACTICE**: Use async ainvoke() for StructuredTool
            print(f"🔧 Executing booking with args: {args}")
            result = await tool_to_use.ainvoke(args)

            # Check if result indicates success
            if "error" in str(result).lower() or "failed" in str(result).lower():
                return f"❌ Booking failed: {result}"

            return f"✅ Booking Confirmed Successfully!\n\n📅 **{booking_request.title}**\n🕒 {booking_request.start_time} - {booking_request.end_time}\n\n📋 Event Details:\n{result}"

        except Exception as e:
            error_msg = str(e)
            print(f"❌ Tool execution error: {error_msg}")

            # Parse common error patterns
            if "invalid_type" in error_msg and "instruction" in error_msg:
                return f"❌ Booking failed: Missing required instruction field for MCP tool\nError: {error_msg}"
            elif "StructuredTool does not support sync invocation" in error_msg:
                return f"❌ Booking failed: Tool invocation error (async/sync mismatch)\nError: {error_msg}"
            else:
                return f"❌ Booking failed: {error_msg}"

    async def booking_execute_node(self, state: MessagesState) -> Dict[str, Any]:
        """Execute approved booking after human approval"""
        # This would be called after approval is given
        return {"messages": [AIMessage(content="Booking execution not implemented yet.")]}

    async def booking_cancel_node(self, state: MessagesState) -> Dict[str, Any]:
        """Handle booking cancellation"""
        return {"messages": [AIMessage(content="Booking cancelled by user.")]}

    async def booking_modify_node(self, state: MessagesState) -> Dict[str, Any]:
        """Handle booking modifications"""
        return {"messages": [AIMessage(content="Booking modification not implemented yet.")]}
