"""
MCP Tool Executor with proper result validation and error handling
Handles the actual execution of MCP tools with robust parsing.
"""
import time
import re
from typing import List, Dict, Any, Optional
from langchain_core.tools import BaseTool

from .execution_result import MCPToolResult, ExecutionStatus, BookingExecutionResult
from .state import BookingRequest


class MCPToolExecutor:
    """Executes MCP tools with proper result validation and parsing"""

    def __init__(self, booking_tools: List[BaseTool]):
        self.booking_tools = booking_tools

    async def execute_booking_request(self, booking_request: BookingRequest, modifications: Dict[str, Any] = None) -> BookingExecutionResult:
        """Execute a complete booking request with proper error handling"""

        # Create execution result tracker
        execution_result = BookingExecutionResult(
            booking_title=booking_request.title,
            user_request=f"{booking_request.tool_name} - {booking_request.title}",
            overall_status=ExecutionStatus.IN_PROGRESS
        )

        # Prepare arguments
        args = self._prepare_mcp_args(booking_request, modifications)

        # Validate event_id requirement
        if booking_request.requires_event_id and "event_id" not in args:
            error_result = MCPToolResult(
                tool_name=booking_request.tool_name,
                status=ExecutionStatus.FAILED,
                raw_result="Missing required event_id",
                success=False,
                error_message="Update operation requires event_id but none was provided"
            )
            execution_result.add_tool_result(error_result)
            execution_result.complete_execution()
            return execution_result

        # Get tools to execute
        tools_to_execute = booking_request.mcp_tools_to_use or [booking_request.tool_name]

        # Execute each tool
        for tool_name in tools_to_execute:
            if not tool_name:
                continue

            tool_result = await self._execute_single_tool(tool_name, args, booking_request)
            execution_result.add_tool_result(tool_result)

        execution_result.complete_execution()
        return execution_result

    async def _execute_single_tool(self, tool_name: str, args: Dict[str, Any], booking_request: BookingRequest) -> MCPToolResult:
        """Execute a single MCP tool with proper result validation"""

        start_time = time.time()

        # Find the tool
        tool_to_use = None
        for tool in self.booking_tools:
            if tool.name == tool_name:
                tool_to_use = tool
                break

        if not tool_to_use:
            return MCPToolResult(
                tool_name=tool_name,
                status=ExecutionStatus.FAILED,
                raw_result=f"Tool {tool_name} not available",
                success=False,
                error_message=f"MCP tool '{tool_name}' not found in available tools",
                execution_time=time.time() - start_time
            )

        try:
            print(f"Executing {tool_name} with args: {args}")
            raw_result = await tool_to_use.ainvoke(args)
            execution_time = time.time() - start_time

            print(f"Raw result from {tool_name}: {raw_result}")

            # CRITICAL: Parse the result properly
            parsed_result = self._parse_mcp_result(tool_name, raw_result)
            parsed_result.execution_time = execution_time

            return parsed_result

        except Exception as e:
            return MCPToolResult(
                tool_name=tool_name,
                status=ExecutionStatus.FAILED,
                raw_result=str(e),
                success=False,
                error_message=f"Exception during {tool_name} execution: {str(e)}",
                execution_time=time.time() - start_time
            )

    def _parse_mcp_result(self, tool_name: str, raw_result: Any) -> MCPToolResult:
        """Parse MCP tool result with proper error detection"""

        result_str = str(raw_result).lower()

        # Check for explicit error indicators
        error_indicators = [
            "failed",
            "error",
            "invalid",
            "could not",
            "unable to",
            "not found",
            "permission denied",
            "unauthorized"
        ]

        success_indicators = [
            "success",
            "successful",
            "created",
            "updated",
            "completed",
            "confirmed"
        ]

        # Detect API restrictions
        api_restrictions = []
        restriction_patterns = [
            r"restriction.*api",
            r"api.*not support",
            r"cannot.*removed.*manually",
            r"need.*removed.*manually",
            r"manually.*through.*interface"
        ]

        for pattern in restriction_patterns:
            if re.search(pattern, result_str):
                api_restrictions.append(str(raw_result))
                break

        # Determine success/failure
        has_error = any(indicator in result_str for indicator in error_indicators)
        has_success = any(indicator in result_str for indicator in success_indicators)

        if has_error and not has_success:
            return MCPToolResult(
                tool_name=tool_name,
                status=ExecutionStatus.FAILED,
                raw_result=raw_result,
                success=False,
                error_message=str(raw_result),
                api_restrictions=api_restrictions
            )
        elif has_success and not has_error:
            return MCPToolResult(
                tool_name=tool_name,
                status=ExecutionStatus.SUCCESS,
                raw_result=raw_result,
                success=True,
                api_restrictions=api_restrictions
            )
        elif api_restrictions:
            # Success but with restrictions
            return MCPToolResult(
                tool_name=tool_name,
                status=ExecutionStatus.PARTIAL_SUCCESS,
                raw_result=raw_result,
                success=True,
                api_restrictions=api_restrictions,
                error_message="Operation completed with API restrictions"
            )
        else:
            # Ambiguous result - be conservative
            return MCPToolResult(
                tool_name=tool_name,
                status=ExecutionStatus.FAILED,
                raw_result=raw_result,
                success=False,
                error_message=f"Ambiguous result from {tool_name}: {raw_result}",
                api_restrictions=api_restrictions
            )

    def _prepare_mcp_args(self, booking_request: BookingRequest, modifications: Dict[str, Any] = None) -> Dict[str, Any]:
        """Prepare MCP tool arguments with proper validation"""

        # Start with original args
        args = booking_request.original_args.copy()

        # Apply modifications
        if modifications:
            args.update(modifications)

        # Ensure required fields are always updated with current values
        args["summary"] = booking_request.title  # Always use the current title, even for updates
        args["start"] = booking_request.start_time  # Always use the current start time
        args["end"] = booking_request.end_time  # Always use the current end time

        # Handle attendees properly
        if "attendees" in args and args["attendees"]:
            if isinstance(args["attendees"], list):
                # Ensure all attendees are strings
                formatted_attendees = []
                for attendee in args["attendees"]:
                    if isinstance(attendee, dict) and "email" in attendee:
                        formatted_attendees.append(attendee["email"])
                    elif isinstance(attendee, str):
                        formatted_attendees.append(attendee)
                args["attendees"] = formatted_attendees
            elif isinstance(args["attendees"], str):
                args["attendees"] = [args["attendees"]]

        # Set defaults for Google Calendar fields
        defaults = {
            "colorId": None,
            "transparency": "opaque",
            "visibility": "default",
            "guestsCanInviteOthers": True,
            "guestsCanModify": False,
            "guestsCanSeeOtherGuests": True,
            "anyoneCanAddSelf": False,
            "reminders": {"useDefault": True}
        }

        for key, value in defaults.items():
            if key not in args:
                args[key] = value

        # Build instruction for Pipedream MCP tools
        if "instruction" not in args:
            instruction_parts = []

            if "update" in booking_request.tool_name:
                instruction_parts.append(f"Update calendar event: {booking_request.title}")
            elif "add-attendees" in booking_request.tool_name:
                instruction_parts.append(f"Add attendees to calendar event: {booking_request.title}")
            else:
                instruction_parts.append(f"Create calendar event: {booking_request.title}")

            instruction_parts.append(f"Time: {booking_request.start_time} to {booking_request.end_time}")

            # Add optional fields to instruction
            optional_fields = ["description", "location", "attendees"]
            for field in optional_fields:
                if args.get(field):
                    if field == "attendees" and isinstance(args[field], list):
                        instruction_parts.append(f"Attendees: {', '.join(args[field])}")
                    else:
                        instruction_parts.append(f"{field.title()}: {args[field]}")

            args["instruction"] = "; ".join(instruction_parts)

        return args
