"""
Google Workspace Calendar Executor - Direct Google API Integration
Direct Google Calendar API access for calendar operations.

This executor provides Google Calendar API integration through OAuth credentials
stored in Supabase. Handles READ and WRITE operations for calendar events.
"""
import time
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .execution_result import GoogleCalendarToolResult, ExecutionStatus, BookingExecutionResult
from .state import BookingRequest


class GoogleWorkspaceExecutor:
    """Execute calendar operations using Google Workspace API directly"""

    def __init__(self, google_credentials: Dict[str, str]):
        """
        Initialize with Google OAuth credentials from Supabase.

        Args:
            google_credentials: Dict containing:
                - google_access_token
                - google_refresh_token
                - google_client_id
                - google_client_secret
        """
        self.credentials = Credentials(
            token=google_credentials.get('google_access_token'),
            refresh_token=google_credentials.get('google_refresh_token'),
            client_id=google_credentials.get('google_client_id'),
            client_secret=google_credentials.get('google_client_secret'),
            token_uri='https://oauth2.googleapis.com/token'
        )

        # Build Google Calendar service
        self.service = build('calendar', 'v3', credentials=self.credentials)
        self.calendar_id = 'primary'  # Use primary calendar

    async def execute_booking_request(
        self,
        booking_request: BookingRequest,
        modifications: Dict[str, Any] = None
    ) -> BookingExecutionResult:
        """
        Execute a complete booking request with proper error handling.
        Handles Google Calendar API operations with comprehensive error reporting.

        Args:
            booking_request: BookingRequest with event details
            modifications: Optional modifications to apply

        Returns:
            BookingExecutionResult with execution status and details
        """
        # Create execution result tracker
        execution_result = BookingExecutionResult(
            booking_title=booking_request.title,
            user_request=f"{booking_request.tool_name} - {booking_request.title}",
            overall_status=ExecutionStatus.IN_PROGRESS
        )

        # Prepare event data
        event_data = self._prepare_event_data(booking_request, modifications)

        # Validate event_id requirement for update operations
        if booking_request.requires_event_id:
            event_id = event_data.get('event_id') or booking_request.original_args.get('event_id')
            if not event_id:
                error_result = GoogleCalendarToolResult(
                    tool_name=booking_request.tool_name,
                    status=ExecutionStatus.FAILED,
                    raw_result="Missing required event_id",
                    success=False,
                    error_message="Update operation requires event_id but none was provided"
                )
                execution_result.add_tool_result(error_result)
                execution_result.complete_execution()
                return execution_result
            event_data['event_id'] = event_id

        # Get tools to execute
        tools_to_execute = booking_request.tools_to_use or [booking_request.tool_name]

        # Execute each tool
        for tool_name in tools_to_execute:
            if not tool_name:
                continue

            tool_result = await self._execute_single_tool(tool_name, event_data)
            execution_result.add_tool_result(tool_result)

        execution_result.complete_execution()
        return execution_result

    async def _execute_single_tool(
        self,
        tool_name: str,
        event_data: Dict[str, Any]
    ) -> GoogleCalendarToolResult:
        """
        Execute a single Google Calendar API operation.
        Maps Google Calendar tool names to Google API methods.

        Args:
            tool_name: Google Calendar tool name (e.g., 'google_calendar-create-event')
            event_data: Event data prepared for Google API

        Returns:
            GoogleCalendarToolResult with execution status
        """
        start_time = time.time()

        try:
            # Map tool name to Google API method
            if tool_name == 'google_calendar-create-event':
                result = await self._create_event(event_data)
            elif tool_name == 'google_calendar-update-event':
                result = await self._update_event(event_data)
            elif tool_name == 'google_calendar-add-attendees-to-event':
                result = await self._add_attendees(event_data)
            elif tool_name == 'google_calendar-delete-event':
                result = await self._delete_event(event_data)
            elif tool_name == 'google_calendar-quick-add-event':
                result = await self._quick_add_event(event_data)
            else:
                return GoogleCalendarToolResult(
                    tool_name=tool_name,
                    status=ExecutionStatus.FAILED,
                    raw_result=f"Unknown tool: {tool_name}",
                    success=False,
                    error_message=f"Tool '{tool_name}' not supported by Google Workspace executor",
                    execution_time=time.time() - start_time
                )

            execution_time = time.time() - start_time

            # Parse result into GoogleCalendarToolResult
            return GoogleCalendarToolResult(
                tool_name=tool_name,
                status=ExecutionStatus.SUCCESS,
                raw_result=result,
                success=True,
                execution_time=execution_time
            )

        except HttpError as e:
            return GoogleCalendarToolResult(
                tool_name=tool_name,
                status=ExecutionStatus.FAILED,
                raw_result=str(e),
                success=False,
                error_message=f"Google API error: {e.reason}",
                execution_time=time.time() - start_time
            )
        except Exception as e:
            return GoogleCalendarToolResult(
                tool_name=tool_name,
                status=ExecutionStatus.FAILED,
                raw_result=str(e),
                success=False,
                error_message=f"Exception during {tool_name} execution: {str(e)}",
                execution_time=time.time() - start_time
            )

    async def _create_event(self, event_data: Dict[str, Any]) -> str:
        """Create a new calendar event using Google Calendar API"""
        # Build event body
        event_body = {
            'summary': event_data['summary'],
            'start': {
                'dateTime': event_data['start'],
                'timeZone': self._extract_timezone(event_data['start'])
            },
            'end': {
                'dateTime': event_data['end'],
                'timeZone': self._extract_timezone(event_data['end'])
            }
        }

        # Add optional fields
        if event_data.get('description'):
            event_body['description'] = event_data['description']
        if event_data.get('location'):
            event_body['location'] = event_data['location']
        if event_data.get('attendees'):
            event_body['attendees'] = [{'email': email} for email in event_data['attendees']]
        if event_data.get('colorId'):
            event_body['colorId'] = str(event_data['colorId'])
        if event_data.get('transparency'):
            event_body['transparency'] = event_data['transparency']
        if event_data.get('visibility'):
            event_body['visibility'] = event_data['visibility']
        if event_data.get('recurrence'):
            event_body['recurrence'] = event_data['recurrence']
        if event_data.get('reminders'):
            event_body['reminders'] = event_data['reminders']
        if event_data.get('guestsCanInviteOthers') is not None:
            event_body['guestsCanInviteOthers'] = event_data['guestsCanInviteOthers']
        if event_data.get('guestsCanModify') is not None:
            event_body['guestsCanModify'] = event_data['guestsCanModify']

        # Execute API call in thread pool to avoid blocking
        def _sync_create():
            return self.service.events().insert(
                calendarId=self.calendar_id,
                body=event_body
            ).execute()

        event = await asyncio.to_thread(_sync_create)

        # Return user-friendly message
        event_link = event.get('htmlLink', '')
        return f"Successfully created event '{event_body['summary']}' with ID: {event['id']}. View event: {event_link}"

    async def _update_event(self, event_data: Dict[str, Any]) -> str:
        """Update an existing calendar event using Google Calendar API"""
        event_id = event_data.get('event_id')
        if not event_id:
            raise ValueError("event_id required for update operation")

        # Get existing event first
        def _sync_get():
            return self.service.events().get(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()

        existing_event = await asyncio.to_thread(_sync_get)

        # Update fields
        if event_data.get('summary'):
            existing_event['summary'] = event_data['summary']
        if event_data.get('start'):
            existing_event['start'] = {
                'dateTime': event_data['start'],
                'timeZone': self._extract_timezone(event_data['start'])
            }
        if event_data.get('end'):
            existing_event['end'] = {
                'dateTime': event_data['end'],
                'timeZone': self._extract_timezone(event_data['end'])
            }
        if event_data.get('description') is not None:
            existing_event['description'] = event_data['description']
        if event_data.get('location') is not None:
            existing_event['location'] = event_data['location']
        if event_data.get('colorId'):
            existing_event['colorId'] = str(event_data['colorId'])
        if event_data.get('transparency'):
            existing_event['transparency'] = event_data['transparency']
        if event_data.get('visibility'):
            existing_event['visibility'] = event_data['visibility']

        # Execute update
        def _sync_update():
            return self.service.events().update(
                calendarId=self.calendar_id,
                eventId=event_id,
                body=existing_event
            ).execute()

        updated_event = await asyncio.to_thread(_sync_update)

        event_link = updated_event.get('htmlLink', '')
        return f"Successfully updated event with ID: {event_id}. The calendar event '{updated_event['summary']}' has been successfully updated. View event: {event_link}"

    async def _add_attendees(self, event_data: Dict[str, Any]) -> str:
        """Add attendees to an existing calendar event"""
        event_id = event_data.get('event_id')
        if not event_id:
            raise ValueError("event_id required for add attendees operation")

        attendees_to_add = event_data.get('attendees', [])
        if not attendees_to_add:
            return "No attendees provided to add"

        # Get existing event
        def _sync_get():
            return self.service.events().get(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()

        existing_event = await asyncio.to_thread(_sync_get)

        # Get existing attendees
        existing_attendees = existing_event.get('attendees', [])
        existing_emails = {att['email'].lower() for att in existing_attendees}

        # Add new attendees (avoid duplicates)
        new_attendees = []
        for email in attendees_to_add:
            if email.lower() not in existing_emails:
                new_attendees.append({'email': email})

        if not new_attendees:
            return f"All attendees already invited to event {event_id}"

        # Update attendee list
        existing_event['attendees'] = existing_attendees + new_attendees

        # Execute update
        def _sync_update():
            return self.service.events().patch(
                calendarId=self.calendar_id,
                eventId=event_id,
                body={'attendees': existing_event['attendees']},
                sendUpdates='all'  # Send email notifications
            ).execute()

        updated_event = await asyncio.to_thread(_sync_update)

        event_link = updated_event.get('htmlLink', '')
        added_emails = [att['email'] for att in new_attendees]
        return f"Successfully added attendees {', '.join(added_emails)} to event {event_id}. View event: {event_link}"

    async def _delete_event(self, event_data: Dict[str, Any]) -> str:
        """Delete a calendar event using Google Calendar API"""
        event_id = event_data.get('event_id')
        if not event_id:
            raise ValueError("event_id required for delete operation")

        # Execute delete
        def _sync_delete():
            return self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()

        await asyncio.to_thread(_sync_delete)

        return f"Successfully deleted event with ID: {event_id}"

    async def _quick_add_event(self, event_data: Dict[str, Any]) -> str:
        """Quick add event using natural language text"""
        text = event_data.get('instruction') or event_data.get('summary')
        if not text:
            raise ValueError("text or summary required for quick add")

        # Execute quick add
        def _sync_quick_add():
            return self.service.events().quickAdd(
                calendarId=self.calendar_id,
                text=text
            ).execute()

        event = await asyncio.to_thread(_sync_quick_add)

        event_link = event.get('htmlLink', '')
        return f"Successfully created event via quick add: '{event['summary']}' with ID: {event['id']}. View event: {event_link}"

    def _prepare_event_data(
        self,
        booking_request: BookingRequest,
        modifications: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Prepare event data for Google Calendar API.
        Converts BookingRequest to Google API format.
        """
        # Start with original args
        event_data = booking_request.original_args.copy() if booking_request.original_args else {}

        # Apply modifications
        if modifications:
            event_data.update(modifications)

        # Ensure required fields from BookingRequest
        event_data['summary'] = booking_request.title
        event_data['start'] = booking_request.start_time
        event_data['end'] = booking_request.end_time

        # Add optional fields
        if booking_request.description:
            event_data['description'] = booking_request.description
        if booking_request.location:
            event_data['location'] = booking_request.location
        if booking_request.attendees:
            event_data['attendees'] = booking_request.attendees
        if booking_request.color_id:
            event_data['colorId'] = booking_request.color_id
        if booking_request.transparency:
            event_data['transparency'] = booking_request.transparency
        if booking_request.visibility:
            event_data['visibility'] = booking_request.visibility
        if booking_request.recurrence:
            event_data['recurrence'] = booking_request.recurrence
        if booking_request.reminders:
            event_data['reminders'] = booking_request.reminders
        if booking_request.conference_data:
            event_data['conferenceData'] = booking_request.conference_data

        # Set Google API defaults
        event_data.setdefault('guestsCanInviteOthers', booking_request.guests_can_invite_others)
        event_data.setdefault('guestsCanModify', booking_request.guests_can_modify)

        return event_data

    def _extract_timezone(self, iso_datetime: str) -> str:
        """Extract timezone from ISO datetime string"""
        try:
            # Parse timezone from ISO string
            if '+' in iso_datetime:
                # Has explicit offset like "2025-01-15T09:00:00-05:00"
                return iso_datetime.split('+')[0].split('-')[-1]
            elif 'Z' in iso_datetime:
                return 'UTC'
            else:
                # Try to parse with datetime
                dt = datetime.fromisoformat(iso_datetime.replace('Z', '+00:00'))
                if dt.tzinfo:
                    return str(dt.tzinfo)
                return 'UTC'
        except Exception:
            # Fallback to UTC
            return 'UTC'

    # =============================================================================
    # READ OPERATIONS - For calendar_agent node (no interrupts needed)
    # =============================================================================

    async def list_events(
        self,
        time_min: Optional[str] = None,
        time_max: Optional[str] = None,
        max_results: int = 250,
        order_by: str = "startTime",
        single_events: bool = True
    ) -> str:
        """
        List calendar events within time range using Google Calendar API.

        This is a READ-ONLY operation used by the calendar_agent node
        to check availability and list upcoming events.

        Args:
            time_min: RFC3339 timestamp (lower bound for event end time)
            time_max: RFC3339 timestamp (upper bound for event start time)
            max_results: Maximum number of events to return (default 250, max 2500)
            order_by: Sort by "startTime" or "updated"
            single_events: Whether to expand recurring events

        Returns:
            Formatted string with event list for LLM consumption
        """
        try:
            # Build query parameters
            params = {
                'calendarId': self.calendar_id,
                'maxResults': max_results,
                'singleEvents': single_events,
                'orderBy': order_by if order_by == "startTime" else None
            }

            if time_min:
                params['timeMin'] = time_min
            if time_max:
                params['timeMax'] = time_max

            # Execute API call in thread pool
            def _sync_list():
                return self.service.events().list(**params).execute()

            events_result = await asyncio.to_thread(_sync_list)
            events = events_result.get('items', [])

            if not events:
                return "No events found in the specified time range."

            # Format events for LLM
            formatted_events = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                summary = event.get('summary', 'No title')
                event_id = event.get('id', '')

                # Get attendees if present
                attendees = event.get('attendees', [])
                attendee_str = ""
                if attendees:
                    attendee_emails = [att.get('email', '') for att in attendees]
                    attendee_str = f" | Attendees: {', '.join(attendee_emails)}"

                formatted_events.append(
                    f"• {start} to {end} - {summary} (ID: {event_id}){attendee_str}"
                )

            return f"Found {len(events)} events:\n" + "\n".join(formatted_events)

        except HttpError as e:
            return f"Error listing events: {e.reason}"
        except Exception as e:
            return f"Unexpected error listing events: {str(e)}"

    async def get_event(self, event_id: str) -> str:
        """
        Get single event details by ID using Google Calendar API.

        This is a READ-ONLY operation used by the calendar_agent node
        to view specific event details.

        Args:
            event_id: Google Calendar event ID

        Returns:
            Formatted string with event details for LLM consumption
        """
        try:
            # Execute API call in thread pool
            def _sync_get():
                return self.service.events().get(
                    calendarId=self.calendar_id,
                    eventId=event_id
                ).execute()

            event = await asyncio.to_thread(_sync_get)

            # Format event details
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            summary = event.get('summary', 'No title')
            description = event.get('description', 'No description')
            location = event.get('location', 'No location')
            html_link = event.get('htmlLink', '')

            # Get attendees
            attendees = event.get('attendees', [])
            attendee_list = []
            for att in attendees:
                email = att.get('email', '')
                status = att.get('responseStatus', 'needsAction')
                attendee_list.append(f"{email} ({status})")

            result = f"""Event Details:
Title: {summary}
Start: {start}
End: {end}
Location: {location}
Description: {description}
Event ID: {event_id}
Link: {html_link}"""

            if attendee_list:
                result += "\nAttendees:\n  " + "\n  ".join(attendee_list)

            return result

        except HttpError as e:
            return f"Error retrieving event: {e.reason}"
        except Exception as e:
            return f"Unexpected error retrieving event: {str(e)}"

    async def list_calendars(self) -> str:
        """
        List all calendars for the authenticated user using Google Calendar API.

        This is a READ-ONLY operation used by the calendar_agent node
        to show available calendars.

        Returns:
            Formatted string with calendar list for LLM consumption
        """
        try:
            # Execute API call in thread pool
            def _sync_list_calendars():
                return self.service.calendarList().list().execute()

            calendar_list = await asyncio.to_thread(_sync_list_calendars)
            calendars = calendar_list.get('items', [])

            if not calendars:
                return "No calendars found."

            # Format calendars for LLM
            formatted_calendars = []
            for calendar in calendars:
                summary = calendar.get('summary', 'No name')
                calendar_id = calendar.get('id', '')
                access_role = calendar.get('accessRole', 'unknown')
                primary = " (PRIMARY)" if calendar.get('primary', False) else ""

                formatted_calendars.append(
                    f"• {summary}{primary} - ID: {calendar_id} | Access: {access_role}"
                )

            return f"Found {len(calendars)} calendars:\n" + "\n".join(formatted_calendars)

        except HttpError as e:
            return f"Error listing calendars: {e.reason}"
        except Exception as e:
            return f"Unexpected error listing calendars: {str(e)}"
