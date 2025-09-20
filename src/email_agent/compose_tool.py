"""
Email composition tool using powerful LLM
"""
from typing import Dict, Any, Optional, List
from langchain_core.tools import tool
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from .schemas import EmailCompositionRequest, ComposedEmail
from .prompt import COMPOSE_TOOL_PROMPT


# Initialize powerful LLM for email composition
composition_model = ChatAnthropic(
    model="claude-sonnet-4-20250514",
    temperature=0.3,  # Slightly creative but consistent
    max_tokens=4000
)



@tool
def compose_email(
    recipient: str,
    purpose: str,
    context: Optional[str] = None,
    tone: str = "professional",
    key_points: Optional[List[str]] = None,
    call_to_action: Optional[str] = None,
    sender_name: str = "Samuel"
) -> str:
    """
    Compose an email using AI assistance before creating a draft.

    This tool uses a powerful LLM to craft professional, effective emails
    tailored to the specific recipient, purpose, and desired tone.

    Args:
        recipient: Who is receiving this email (name/role/company)
        purpose: The main goal or reason for sending this email
        context: Additional background information or previous interactions
        tone: Desired tone (professional, friendly, formal, urgent, appreciative)
        key_points: List of specific points to include in the email
        call_to_action: Specific action or response requested from recipient
        sender_name: Name of the sender (default: Samuel)

    Returns:
        JSON string containing composed email with subject, body, and reasoning
    """

    # Create composition request
    request = EmailCompositionRequest(
        recipient=recipient,
        purpose=purpose,
        context=context,
        tone=tone,
        key_points=key_points or [],
        call_to_action=call_to_action,
        sender_name=sender_name
    )

    # Build the composition prompt
    composition_prompt = f"""
    Compose an email with the following requirements:

    **Recipient**: {request.recipient}
    **Purpose**: {request.purpose}
    **Desired Tone**: {request.tone}
    **Sender**: {request.sender_name}

    """

    if request.context:
        composition_prompt += f"**Context/Background**: {request.context}\n\n"

    if request.key_points:
        composition_prompt += "**Key Points to Include**:\n"
        for i, point in enumerate(request.key_points, 1):
            composition_prompt += f"{i}. {point}\n"
        composition_prompt += "\n"

    if request.call_to_action:
        composition_prompt += f"**Call to Action**: {request.call_to_action}\n\n"

    composition_prompt += """
    Please compose an email that:
    1. Has an effective subject line
    2. Follows the structure guidelines in your system prompt
    3. Matches the requested tone appropriately
    4. Includes all key points naturally
    5. Has a clear call to action if specified

    Respond in this exact JSON format:
    {
        "subject": "Your subject line here",
        "body": "Your complete email body here",
        "reasoning": "Brief explanation of your composition choices",
        "tone_used": "The actual tone you applied"
    }
    """

    # Compose the email using the LLM
    messages = [
        SystemMessage(content=COMPOSE_TOOL_PROMPT),
        HumanMessage(content=composition_prompt)
    ]

    try:
        response = composition_model.invoke(messages)

        # Parse the JSON response
        import json
        try:
            composed_data = json.loads(response.content)
            composed_email = ComposedEmail(**composed_data)

            # Return formatted result
            result = {
                "status": "success",
                "composed_email": {
                    "subject": composed_email.subject,
                    "body": composed_email.body,
                    "reasoning": composed_email.reasoning,
                    "tone_used": composed_email.tone_used
                },
                "next_steps": "Email composed successfully. Ready to create draft with gmail-create-draft."
            }

            return json.dumps(result, indent=2)

        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return f"""
Email composition completed:

SUBJECT: {response.content.split('subject')[1].split('\n')[0] if 'subject' in response.content else 'Re: ' + purpose}

BODY:
{response.content}

Next step: Use gmail-create-draft to create the email draft.
"""

    except Exception as e:
        return f"❌ Email composition failed: {str(e)}"


@tool
def revise_email(
    original_subject: str,
    original_body: str,
    revision_request: str,
    tone: str = "professional"
) -> str:
    """
    Revise an existing email based on feedback or new requirements.

    Args:
        original_subject: The current email subject
        original_body: The current email body
        revision_request: What changes or improvements are needed
        tone: Desired tone for the revision

    Returns:
        JSON string with revised email
    """

    revision_prompt = f"""
    Please revise the following email based on the revision request:

    **Current Subject**: {original_subject}

    **Current Body**:
    {original_body}

    **Revision Request**: {revision_request}
    **Desired Tone**: {tone}

    Please provide the revised email in this JSON format:
    {{
        "subject": "Revised subject line",
        "body": "Revised email body",
        "reasoning": "Summary of what was changed and why",
        "tone_used": "The tone applied in revision"
    }}
    """

    messages = [
        SystemMessage(content=COMPOSE_TOOL_PROMPT),
        HumanMessage(content=revision_prompt)
    ]

    try:
        response = composition_model.invoke(messages)

        import json
        try:
            revised_data = json.loads(response.content)

            result = {
                "status": "success",
                "revised_email": revised_data,
                "next_steps": "Email revised successfully. Ready to create new draft."
            }

            return json.dumps(result, indent=2)

        except json.JSONDecodeError:
            return f"Email revision completed:\n\n{response.content}\n\nNext step: Use gmail-create-draft with the revised content."

    except Exception as e:
        return f"❌ Email revision failed: {str(e)}"
