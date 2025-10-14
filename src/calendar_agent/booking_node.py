"""
Booking Node for Calendar Agent - Human-in-the-Loop Approval
Handles booking operations that require human approval before execution.
"""
import os
import sys
import asyncio
import json
import re
from typing import List, Dict, Any, Optional, Sequence
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Local dev only - uses git submodules from library/
# In deployment, these packages come from requirements.txt (pip-installed from PyPI)
# sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../library/langgraph'))
# sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../library/langchain-mcp-adapters'))

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_anthropic import ChatAnthropic
from langgraph.graph import MessagesState
from langgraph.types import interrupt, Command
from pydantic import BaseModel, Field

from shared_utils import DEFAULT_LLM_MODEL

from .config import USER_TIMEZONE, get_current_context
from .state import BookingRequest
from .execution_result import ExecutionStatus
from .google_workspace_executor import GoogleWorkspaceExecutor
from .prompt import get_booking_extraction_prompt





class ApprovalResponse(BaseModel):
    """Human approval response model"""
    approved: bool = Field(..., description="Whether booking is approved")
    modifications: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Human modifications to booking")
    feedback: Optional[str] = Field(None, description="Human feedback or rejection reason")


class BookingNode:
    """Dedicated node for booking operations with human approval"""

    def __init__(
        self,
        executor: Optional[GoogleWorkspaceExecutor],
        model: Optional[ChatAnthropic] = None
    ):
        """
        Initialize BookingNode with Google Workspace executor.

        Args:
            executor: Google Workspace Calendar executor, or None if credentials missing
            model: LLM model for extraction and analysis

        Note:
            When executor is None (missing Google OAuth credentials), the booking node
            will gracefully handle requests and guide users to connect their account.
        """
        from .config import LLM_CONFIG, USER_TIMEZONE, WORK_HOURS_START, WORK_HOURS_END, DEFAULT_MEETING_DURATION
        self.executor = executor  # Use generic executor interface (can be None)
        self.model = model or ChatAnthropic(
            model=LLM_CONFIG.get("model", DEFAULT_LLM_MODEL),
            temperature=LLM_CONFIG.get("temperature", 0.1),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
        )

    async def booking_approval_node(self, state: MessagesState, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle booking approval with human-in-the-loop using proper LangGraph patterns.
        Uses interrupt() and Command(resume=...) following official LangGraph best practices.
        Reference: https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/add-human-in-the-loop/
        """
        messages = state.get("messages", [])
        if not messages:
            return {"messages": [AIMessage(content="No messages found.")]}

        # Handle missing Google OAuth credentials gracefully
        if self.executor is None:
            error_message = (
                "Cannot process booking request: Google Calendar is not connected.\n\n"
                "To enable calendar bookings, please connect your Google Calendar account:\n\n"
                "1. Go to the Configuration App (config app)\n"
                "2. Look for the 'Connect Google Account' or 'Google Calendar' section\n"
                "3. Follow the OAuth flow to authorize calendar access\n"
                "4. Once connected, you'll be able to create and manage calendar events!\n\n"
                "After connecting your account, please try your booking request again."
            )
            return {"messages": messages + [AIMessage(content=error_message)]}

        # NOTE: Task tracking not available with MessagesState
        current_task = None

        # Extract booking intent from routing context or conversation
        booking_intent, routing_context, event_id = self._extract_routing_context(messages)

        if not booking_intent:
            return {"messages": [AIMessage(content="No booking request found.")]}

        # Parse booking details using enhanced context - pass messages directly
        booking_details = await self._extract_booking_details_enhanced(
            booking_intent, messages, routing_context, event_id, config
        )

        if not booking_details:
            error_msg = f"Could not understand booking request: '{booking_intent}'"
            if routing_context:
                error_msg += f"\nRouter analysis: {routing_context.get('reasoning', 'N/A')}"
            return {"messages": [AIMessage(content=error_msg)]}

        # Create booking request for human approval - filter out None values to use defaults
        clean_booking_details = {k: v for k, v in booking_details.items() if v is not None}
        booking_request = BookingRequest(**clean_booking_details)

        # **PROPER LANGGRAPH PATTERN**: Use interrupt() with structured payload
        approval_prompt = {
            "type": "booking_approval",
            "message": "Booking Approval Required",
            "booking_details": {
                "title": booking_request.title,
                "start_time": booking_request.start_time,
                "end_time": booking_request.end_time,
                "location": booking_request.location or "None",
                "description": booking_request.description or "None",
                "tool_name": booking_request.tool_name,
                "attendees": booking_request.attendees,
                "requires_event_id": booking_request.requires_event_id,
                "event_id": event_id if event_id else "None",
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
                    # Execute the booking using the Google Workspace executor
                    execution_result = await self.executor.execute_booking_request(
                        booking_request,
                        validation_result.get("modifications", {})
                    )

                    # COMPLETE TASK TRACKING with accurate status
                    if current_task:
                        if execution_result.overall_status == ExecutionStatus.SUCCESS:
                            current_task.complete(execution_result.get_task_result_summary())
                        elif execution_result.overall_status == ExecutionStatus.PARTIAL_SUCCESS:
                            current_task.complete(f"Partially successful: {execution_result.get_task_result_summary()}")
                        else:
                            current_task.fail(execution_result.get_task_result_summary())

                    # Get the real tool output for user-facing message
                    real_tool_output = self._extract_real_tool_output(execution_result)
                    supervisor_message = real_tool_output if real_tool_output else execution_result.get_supervisor_message()

                    # Pass execution result through state for route_after_booking access
                    return {
                        "messages": messages + [AIMessage(content=supervisor_message)],
                        "booking_execution_result": execution_result,
                        "last_tool_output": real_tool_output
                    }

                elif action == "reject":
                    # COMPLETE TASK TRACKING for rejection
                    if current_task:
                        current_task.complete("Booking rejected by user")

                    return {
                        "messages": messages + [AIMessage(content="Booking cancelled by user.")],
                        "booking_execution_result": None,
                        "last_tool_output": "Booking cancelled by user"
                    }

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
                            approval_prompt["message"] = "Updated Booking - Please Review"
                        else:
                            approval_prompt["message"] = "Could not process modifications. Please try again."
                    except Exception as e:
                        approval_prompt["message"] = f"Error processing modifications: {e}"

            else:
                # Invalid response - update prompt with validation message
                approval_prompt["message"] = f"{validation_result['error']}. Please try again."
                approval_prompt["instructions"] = "Valid responses: 'approve', 'reject', or modification details"

    def _extract_real_tool_output(self, execution_result) -> str:
        """Extract the real tool output for user-facing messages"""
        if not execution_result or not execution_result.tool_results:
            return ""

        # Get the most recent successful tool result
        successful_results = [r for r in execution_result.tool_results if r.is_successful()]

        if successful_results:
            latest_result = successful_results[-1]
            raw_output = str(latest_result.raw_result)

            # Clean up the output to be user-friendly
            if "successfully updated" in raw_output.lower():
                # Extract key information from the output
                if "event with ID" in raw_output and "has been successfully updated" in raw_output:
                    return raw_output
                elif "The calendar event" in raw_output and "updated" in raw_output:
                    return raw_output

            # For other successful operations, return cleaned output
            return raw_output

        # If no successful results, return error information
        failed_results = [r for r in execution_result.tool_results if not r.is_successful()]
        if failed_results:
            return f"Operation failed: {failed_results[0].get_error_details()}"

        return "Operation completed with unknown status"



    async def _extract_booking_details_enhanced(
        self,
        booking_intent: str,
        messages: Sequence[BaseMessage],
        routing_context: Optional[Dict[str, Any]] = None,
        event_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Enhanced booking detail extraction with full conversation context"""

        # Get timezone context using centralized function
        context = get_current_context()
        timezone_name = context['timezone_name']
        # Use asyncio.to_thread to avoid blocking I/O in async context
        current_time = await asyncio.to_thread(lambda: datetime.now(ZoneInfo(timezone_name)))

        # Use booking_intent directly since MessagesState provides clean text
        clean_booking_intent = booking_intent

        # Extract conversation context directly from MessagesState
        recent_messages = messages[-15:] if len(messages) > 15 else messages
        conversation_context = []
        for msg in recent_messages:
            if hasattr(msg, 'content') and msg.content:
                msg_type = getattr(msg, 'type', type(msg).__name__.replace('Message', ''))
                conversation_context.append(f"{msg_type}: {msg.content}")

        conversation_summary = "\n".join(conversation_context)

        # Use centralized extraction prompt from prompt.py with config variables
        extraction_prompt = get_booking_extraction_prompt(
            clean_booking_intent=clean_booking_intent,
            conversation_summary=conversation_summary,
            routing_reasoning=routing_context.get('reasoning', 'None') if routing_context else 'None',
            event_id=event_id if event_id else 'None',
            operation_type='an UPDATE operation' if event_id else 'a NEW event creation',
            current_time_iso=current_time.isoformat(),
            timezone_name=timezone_name,
            today_date=current_time.strftime('%Y-%m-%d'),
            current_day=current_time.strftime('%A'),
            work_hours_start=WORK_HOURS_START,
            work_hours_end=WORK_HOURS_END,
            default_duration=DEFAULT_MEETING_DURATION,
            tomorrow_date=(current_time + timedelta(days=1)).strftime('%Y-%m-%d'),
            next_week_date=(current_time + timedelta(days=7)).strftime('%Y-%m-%d')
        )

        try:
            response = await self.model.ainvoke([HumanMessage(content=extraction_prompt)])
            # Parse JSON from response (simplified - in production, use proper JSON parsing)
            content = response.content

            # Handle content as string for JSON extraction
            content_str = str(content) if not isinstance(content, str) else content

            # Extract JSON from response
            if '{' in content_str and '}' in content_str:
                start = content_str.find('{')
                end = content_str.rfind('}') + 1
                json_str = content_str[start:end]
                result = json.loads(json_str)

                # Handle tool_name as list (convert to tools_to_use)
                if 'tool_name' in result and isinstance(result['tool_name'], list):
                    # Multiple tools needed - move to tools_to_use
                    result['tools_to_use'] = result['tool_name']
                    result['tool_name'] = result['tool_name'][0] if result['tool_name'] else None
                elif 'tool_name' in result and isinstance(result['tool_name'], str):
                    # Single tool - also add to tools_to_use for consistency
                    result['tools_to_use'] = [result['tool_name']]

                # Add event_id to original_args if found
                if event_id and 'original_args' in result:
                    result['original_args']['event_id'] = event_id
                    result['requires_event_id'] = True
                    print(f"Added event_id to booking request: {event_id}")

                # Add context metadata
                result['_context'] = {
                    'routing_analysis': routing_context,
                    'conversation_context': conversation_summary,  # Generated from MessagesState
                    'extraction_source': 'enhanced_context',
                    'found_event_id': event_id
                }

                return result
        except Exception as e:
            print(f"Error extracting booking details: {e}")

        return None

    def _extract_routing_context(self, messages: Sequence[BaseMessage]) -> tuple[str, Optional[Dict], Optional[str]]:
        """Extract routing context from messages using LangGraph patterns"""
        routing_context = None
        booking_context = None
        booking_intent = ""
        event_id = None  # ADD EVENT ID EXTRACTION

        # Look for routing context in recent messages AND event ID
        for msg in reversed(messages[-10:]):
            if hasattr(msg, 'additional_kwargs') and msg.additional_kwargs:
                kwargs = msg.additional_kwargs
                if 'routing_decision' in kwargs:
                    routing_context = kwargs['routing_decision']
                if 'booking_context' in kwargs:
                    booking_context = kwargs['booking_context']

                if 'user_intent' in kwargs:
                    booking_intent = kwargs['user_intent']
                    break

            # EXTRACT EVENT ID from calendar agent messages
            if hasattr(msg, 'content') and isinstance(msg.content, str):
                content = msg.content
                # Look for event ID patterns like "Event ID:** k2a1uubdogqd08k1fetqrm4lhs"
                event_id_match = re.search(r'Event ID[:\*\s]*([a-zA-Z0-9]+)', content)
                if event_id_match:
                    event_id = event_id_match.group(1)
                    print(f"Found event ID in calendar agent message: {event_id}")
                    # Don't break here, continue looking for routing context

        # Fallback: Extract from conversation if no routing context found
        if not routing_context:
            user_messages = []
            for msg in messages:
                if isinstance(msg, HumanMessage):
                    content = msg.content

                    # MessagesState provides clean content directly
                    if isinstance(content, list):
                        content_str = " ".join(str(item) for item in content if item)
                    else:
                        content_str = str(content) if content else ""
                    user_messages.append(content_str)

            if user_messages:
                booking_intent = " ".join(user_messages[-3:])
        else:
            # Use preserved routing context
            if not booking_intent:
                booking_intent = routing_context.get('user_intent', '')
                if not booking_intent and booking_context:
                    booking_intent = booking_context.get('original_intent', '')

        return booking_intent, routing_context, event_id

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

    async def _process_modifications(self, response: Any, booking_request: BookingRequest, messages: Sequence[BaseMessage]) -> Optional[Dict[str, Any]]:
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

    # REMOVED: Old _execute_booking method replaced by GoogleWorkspaceExecutor for better reliability
