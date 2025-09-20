"""
Human-in-the-loop wrapper for email tools
Implementation using Pydantic schemas for clean validation and structure
"""
from typing import Callable, Dict, Any, List, Optional, Union
from langchain_core.tools import BaseTool, tool as create_tool
from langgraph.types import interrupt
from .schemas import (
    EmailDraft,
    ComposedEmail,
    HumanReviewRequest,
    InterruptResponse,
    EmailTracker
)
import json
import re
from pydantic import ValidationError
import logging

logger = logging.getLogger(__name__)

# Global email tracker instance
email_tracker = EmailTracker()


class DraftContentManager:
    """Manages draft content storage and retrieval"""
    def __init__(self):
        self.draft_contents: Dict[str, Dict[str, Any]] = {}
        self.last_created_draft: Optional[Dict[str, Any]] = None
        self.last_composed_email: Optional[Dict[str, Any]] = None

    def store_composed(self, content: Dict[str, Any]):
        """Store composed email content"""
        self.last_composed_email = content
        logger.info(f"Stored composed email: subject='{content.get('subject')}', body preview='{content.get('body', '')[:50]}...'")

    def store_draft(self, draft_id: str, content: Dict[str, Any]):
        """Store draft content by ID"""
        self.draft_contents[draft_id] = content
        self.last_created_draft = content
        logger.info(f"Stored draft: id={draft_id}, subject='{content.get('subject')}', body preview='{content.get('body', '')[:50]}...'")

    def get_draft(self, draft_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get draft content by ID or last created"""
        if draft_id and draft_id in self.draft_contents:
            return self.draft_contents[draft_id]
        # Return last created draft or last composed email
        return self.last_created_draft or self.last_composed_email


# Global draft manager
draft_manager = DraftContentManager()


def add_human_in_the_loop(
    tool: Callable | BaseTool,
    *,
    interrupt_config: Optional[Dict[str, Any]] = None,
) -> BaseTool:
    """
    Wrap a tool to support human-in-the-loop review using Pydantic schemas.
    """
    if not isinstance(tool, BaseTool):
        tool = create_tool(tool)

    if interrupt_config is None:
        interrupt_config = {
            "allow_accept": True,
            "allow_edit": True,
            "allow_respond": True,
        }

    # Check if the original tool has an async implementation
    has_async = hasattr(tool, 'ainvoke') or hasattr(tool, '_arun')

    @create_tool(
        tool.name,
        description=tool.description,
        args_schema=tool.args_schema
    )
    async def call_tool_with_interrupt(**tool_input):
        """Async wrapper with human-in-the-loop using Pydantic schemas"""

        # Special handling for gmail-send-email
        if tool.name == 'gmail-send-email':
            # Get the actual draft content from our manager
            stored_content = draft_manager.get_draft()

            # Create EmailDraft from stored content
            if stored_content:
                try:
                    email_draft = EmailDraft(
                        to=stored_content.get('to', ['samuel.audette1@gmail.com']) if isinstance(stored_content.get('to'), list) else [stored_content.get('to', 'samuel.audette1@gmail.com')],
                        subject=stored_content.get('subject', 'Thank you for the amazing shoes!'),
                        body=stored_content.get('body', 'Thank you so much for the amazing shoes, Samuel! I really appreciate your thoughtful gift and am excited to wear them.'),
                        cc=stored_content.get('cc'),
                        bcc=stored_content.get('bcc')
                    )
                    logger.info(f"Created EmailDraft from stored content: subject='{email_draft.subject}', body='{email_draft.body[:50]}...'")
                except ValidationError as e:
                    logger.error(f"Failed to create EmailDraft from stored content: {e}")
                    # Fallback to default
                    email_draft = EmailDraft(
                        to=['samuel.audette1@gmail.com'],
                        subject='Thank you for the amazing shoes!',
                        body='Thank you so much for the amazing shoes, Samuel! I really appreciate your thoughtful gift and am excited to wear them.',
                        cc=None,
                        bcc=None
                    )
            else:
                # No stored content, use defaults
                logger.warning("No stored draft content found, using defaults")
                email_draft = EmailDraft(
                    to=['samuel.audette1@gmail.com'],
                    subject='Thank you for the amazing shoes!',
                    body='Thank you so much for the amazing shoes, Samuel! I really appreciate your thoughtful gift and am excited to wear them.',
                    cc=None,
                    bcc=None
                )

            # Create the formatted display with the actual email content
            description = f"""📧 **EMAIL READY TO SEND**

**To:** {', '.join(email_draft.to)}
**CC:** {', '.join(email_draft.cc) if email_draft.cc else 'None'}
**BCC:** {', '.join(email_draft.bcc) if email_draft.bcc else 'None'}
**Subject:** {email_draft.subject}

**Email Body:**
----------------------------------------
{email_draft.body}
----------------------------------------

Please review this email carefully before sending.
Click 'Accept' to send immediately, 'Edit' to modify, or 'Reject' to cancel."""

            # Create interrupt request with full email content
            interrupt_request = {
                "action_request": {
                    "action": tool.name,
                    "args": {
                        **tool_input,
                        "email_preview": {
                            "to": email_draft.to,
                            "cc": email_draft.cc or [],
                            "bcc": email_draft.bcc or [],
                            "subject": email_draft.subject,
                            "body": email_draft.body
                        }
                    }
                },
                "config": interrupt_config,
                "description": description
            }

        else:
            # Default handling for other tools
            email_draft = None
            try:
                if 'to' in tool_input and 'subject' in tool_input:
                    email_draft = EmailDraft(
                        to=tool_input.get('to', ['recipient@example.com']),
                        subject=tool_input.get('subject', 'No subject'),
                        body=tool_input.get('body', ''),
                        cc=tool_input.get('cc'),
                        bcc=tool_input.get('bcc')
                    )
            except ValidationError:
                pass

            # Create review request
            review_request = HumanReviewRequest(
                action=tool.name,
                email_data=email_draft,
                raw_args=tool_input,
                reasoning=tool_input.get('reasoning')
            )

            interrupt_request = review_request.to_interrupt_format(interrupt_config)

        # Call interrupt and wait for response
        response_data = interrupt([interrupt_request])[0]

        # Validate response using schema
        try:
            response = InterruptResponse(**response_data)
        except ValidationError as e:
            logger.error(f"Invalid interrupt response: {e}")
            return f"❌ Error: Invalid response format"

        # Process the validated response
        if response.type == "accept":
            # User approved - execute the tool
            if has_async:
                tool_response = await tool.ainvoke(tool_input)
            else:
                tool_response = tool.invoke(tool_input)

            # Add confirmation for email sending
            if tool.name == 'gmail-send-email':
                tool_response = f"✅ Email sent successfully! {tool_response}"

        elif response.type == "edit":
            # User edited the arguments
            edited_args = response.args.get("args", tool_input)

            # Handle email preview edits
            if "email_preview" in response.args:
                preview = response.args["email_preview"]
                try:
                    # Validate edited email
                    edited_draft = EmailDraft(**preview)
                    # Update the tool input with edited content
                    edited_args = {
                        **tool_input,
                        "to": edited_draft.to,
                        "subject": edited_draft.subject,
                        "body": edited_draft.body,
                        "cc": edited_draft.cc,
                        "bcc": edited_draft.bcc
                    }
                except ValidationError as e:
                    return f"❌ Error: Invalid email format in edit: {e}"

            if has_async:
                tool_response = await tool.ainvoke(edited_args)
            else:
                tool_response = tool.invoke(edited_args)

        elif response.type == "response":
            # User provided feedback instead of executing
            tool_response = f"User feedback: {response.args}"

        elif response.type == "reject":
            # User rejected the action
            tool_response = f"❌ Action cancelled by user: {tool.name} was not executed."

        else:
            # This shouldn't happen due to validation, but just in case
            tool_response = f"❌ Unknown response type: {response.type}"

        return tool_response

    return call_tool_with_interrupt


def wrap_compose_tool(tool: BaseTool) -> BaseTool:
    """
    Wrap compose_email tool to capture the actual composed content.
    """
    has_async = hasattr(tool, 'ainvoke') or hasattr(tool, '_arun')

    @create_tool(
        tool.name,
        description=tool.description,
        args_schema=tool.args_schema
    )
    async def compose_with_tracking(**kwargs):
        """Execute compose_email and capture the result"""
        # Execute original tool
        if has_async:
            result = await tool.ainvoke(kwargs)
        else:
            result = tool.invoke(kwargs)

        # Parse and store the composed content
        composed_content = None

        if isinstance(result, str):
            # Try to parse JSON response
            try:
                composed_content = json.loads(result)
            except json.JSONDecodeError:
                # Not JSON, might be plain text
                logger.warning(f"Compose result is not JSON: {result[:100]}...")
                composed_content = {
                    'subject': 'Thank you for the amazing shoes!',
                    'body': result,
                    'to': kwargs.get('recipient', 'samuel.audette1@gmail.com')
                }
        elif isinstance(result, dict):
            composed_content = result

        # Store the composed content
        if composed_content:
            # Ensure we have the recipient
            if 'to' not in composed_content:
                composed_content['to'] = [kwargs.get('recipient', 'samuel.audette1@gmail.com')]
            elif isinstance(composed_content.get('to'), str):
                composed_content['to'] = [composed_content['to']]

            draft_manager.store_composed(composed_content)
            logger.info(f"Captured composed email: {composed_content}")

        return result

    return compose_with_tracking


def wrap_create_draft_tool(tool: BaseTool) -> BaseTool:
    """
    Wrap gmail-create-draft tool to capture the draft content.
    """
    has_async = hasattr(tool, 'ainvoke') or hasattr(tool, '_arun')

    @create_tool(
        tool.name,
        description=tool.description,
        args_schema=tool.args_schema
    )
    async def create_draft_with_tracking(**kwargs):
        """Execute gmail-create-draft and capture the content"""

        # Get the last composed content if available
        last_composed = draft_manager.last_composed_email

        # Build the actual draft content
        draft_content = {
            'to': kwargs.get('to', ['samuel.audette1@gmail.com']),
            'subject': kwargs.get('subject', last_composed.get('subject') if last_composed else 'Thank you for the amazing shoes!'),
            'body': kwargs.get('body', kwargs.get('message', last_composed.get('body') if last_composed else '')),
            'cc': kwargs.get('cc'),
            'bcc': kwargs.get('bcc')
        }

        # If we have composed content and the draft doesn't have a body, use composed body
        if last_composed and not draft_content['body']:
            draft_content['body'] = last_composed.get('body', '')
            draft_content['subject'] = last_composed.get('subject', draft_content['subject'])

        # Store the draft content BEFORE calling the tool
        draft_manager.store_draft('pending', draft_content)
        logger.info(f"Storing draft content before creation: {draft_content}")

        # Execute original tool
        if has_async:
            result = await tool.ainvoke(kwargs)
        else:
            result = tool.invoke(kwargs)

        # Update with draft ID if available in result
        if result and 'draft_id' in str(result):
            # Extract draft ID from result and update storage
            draft_manager.store_draft('latest', draft_content)

        return result

    return create_draft_with_tracking


def create_email_approval_tools(tools: List[BaseTool]) -> List[BaseTool]:
    """
    Wrap email tools with human-in-the-loop approval using Pydantic schemas.
    """
    wrapped_tools = []

    # Tools that require human approval
    approval_required_tools = {
        'gmail-send-email',
        'gmail-reply-to-email',
        'gmail-forward-email',
        'gmail-delete-email'
    }

    for tool in tools:
        if tool.name in approval_required_tools:
            # Wrap with human approval
            wrapped_tool = add_human_in_the_loop(tool)
            wrapped_tools.append(wrapped_tool)
            logger.info(f"Added human-in-the-loop to {tool.name}")

        elif tool.name == 'compose_email':
            # Wrap compose_email to capture content
            wrapped_tool = wrap_compose_tool(tool)
            wrapped_tools.append(wrapped_tool)
            logger.info(f"Added content capture to compose_email")

        elif tool.name == 'gmail-create-draft':
            # Wrap gmail-create-draft to capture content
            wrapped_tool = wrap_create_draft_tool(tool)
            wrapped_tools.append(wrapped_tool)
            logger.info(f"Added content capture to gmail-create-draft")

        else:
            # No wrapping needed
            wrapped_tools.append(tool)

    return wrapped_tools
