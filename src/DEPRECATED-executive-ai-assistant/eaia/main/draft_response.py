"""Core agent responsible for drafting email."""

import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore

from eaia.schemas import (
    State,
    NewEmailDraft,
    ResponseEmailDraft,
    Question,
    MeetingAssistant,
    SendCalendarInvite,
    Ignore,
    email_template,
)
from eaia.main.config import get_config
from eaia.llm_utils import get_llm, bind_tools_with_choice

logger = logging.getLogger(__name__)

EMAIL_WRITING_INSTRUCTIONS = """You are {full_name}'s executive assistant. You are a top-notch executive assistant who cares about {name} performing as well as possible.

{background}

Current date and time: {current_date} at {current_time} {tz}

{name} gets lots of emails. This has been determined to be an email that is worth {name} responding to.

Your job is to help {name} respond. You can do this in a few ways.

# Using the `Question` tool

First, get all required information to respond. You can use the Question tool to ask {name} for information if you do not know it.

When drafting emails (either to response on thread or , if you do not have all the information needed to respond in the most appropriate way, call the `Question` tool until you have that information. Do not put placeholders for names or emails or information - get that directly from {name}!
You can get this information by calling `Question`. Again - do not, under any circumstances, draft an email with placeholders or you will get fired.

If people ask {name} if he can attend some event or meet with them, do not agree to do so unless he has explicitly okayed it!

Remember, if you don't have enough information to respond, you can ask {name} for more information. Use the `Question` tool for this.
Never just make things up! So if you do not know something, or don't know what {name} would prefer, don't hesitate to ask him.
Never use the Question tool to ask {name} when they are free - instead, just ask the MeetingAssistant

# Using the `ResponseEmailDraft` tool

Next, if you have enough information to respond, you can draft an email for {name}. Use the `ResponseEmailDraft` tool for this.

ALWAYS draft emails as if they are coming from {name}. Never draft them as "{name}'s assistant" or someone else.

When adding new recipients - only do that if {name} explicitly asks for it and you know their emails. If you don't know the right emails to add in, then ask {name}. You do NOT need to add in people who are already on the email! Do NOT make up emails.

{response_preferences}

# Using the `SendCalendarInvite` tool

Sometimes you will want to schedule a calendar event. You can do this with the `SendCalendarInvite` tool.
If you are sure that {name} would want to schedule a meeting, and you know that {name}'s calendar is free, you can schedule a meeting by calling the `SendCalendarInvite` tool. {name} trusts you to pick good times for meetings. You shouldn't ask {name} for what meeting times are preferred, but you should make sure he wants to meet.

{schedule_preferences}

# Using the `NewEmailDraft` tool

Sometimes you will need to start a new email thread. If you have all the necessary information for this, use the `NewEmailDraft` tool for this.

If {name} asks someone if it's okay to introduce them, and they respond yes, you should draft a new email with that introduction.

# Using the `MeetingAssistant` tool

If the email is from a legitimate person and is working to schedule a meeting, call the MeetingAssistant to get a response from a specialist!
You should not ask {name} for meeting times (unless the Meeting Assistant is unable to find any).
If they ask for times from {name}, first ask the MeetingAssistant by calling the `MeetingAssistant` tool.
Note that you should only call this if working to schedule a meeting - if a meeting has already been scheduled, and they are referencing it, no need to call this.

# Background information: information you may find helpful when responding to emails or deciding what to do.

{random_preferences}"""
draft_prompt = """{instructions}

CRITICAL TOOL CALLING INSTRUCTIONS:
- You MUST call EXACTLY ONE tool at a time - no more, no less
- Choose the single most appropriate tool for this situation
- Do NOT call multiple tools simultaneously
- Use the specified tool names exactly - do not add `functions::` to the start
- Pass all required arguments for the tool you choose

Here is the email thread. Note that this is the full email thread. Pay special attention to the most recent email.

{email}"""


async def draft_response(state: State, config: RunnableConfig, store: BaseStore):
    """Write an email to a customer."""
    # Get draft-specific model configuration from config.yaml
    # NOTE: The hardcoded values below are FALLBACK DEFAULTS only, used if config.yaml is missing
    # The actual model/temperature values are loaded from config.yaml via get_config()
    prompt_config = await get_config(config)
    model_name = prompt_config.get("draft_model", "claude-sonnet-4-20250514")  # Fallback default
    temperature = prompt_config.get("draft_temperature", 0.2)  # Fallback default

    # Load per-user API keys from config
    anthropic_api_key = prompt_config.get("anthropic_api_key")
    openai_api_key = prompt_config.get("openai_api_key")

    llm = get_llm(model_name, temperature=temperature, anthropic_api_key=anthropic_api_key, openai_api_key=openai_api_key)
    tools = [
        NewEmailDraft,
        ResponseEmailDraft,
        Question,
        MeetingAssistant,
        SendCalendarInvite,
    ]
    messages = state.get("messages") or []
    if len(messages) > 0:
        tools.append(Ignore)
    namespace = (config["configurable"].get("assistant_id", "default"),)
    key = "schedule_preferences"
    result = await store.aget(namespace, key)
    if result and "data" in result.value:
        schedule_preferences = result.value["data"]
    else:
        await store.aput(namespace, key, {"data": prompt_config["schedule_preferences"]})
        schedule_preferences = prompt_config["schedule_preferences"]
    key = "random_preferences"
    result = await store.aget(namespace, key)
    if result and "data" in result.value:
        random_preferences = result.value["data"]
    else:
        await store.aput(
            namespace, key, {"data": prompt_config["background_preferences"]}
        )
        random_preferences = prompt_config["background_preferences"]
    key = "response_preferences"
    result = await store.aget(namespace, key)
    if result and "data" in result.value:
        response_preferences = result.value["data"]
    else:
        await store.aput(namespace, key, {"data": prompt_config["response_preferences"]})
        response_preferences = prompt_config["response_preferences"]

    # Get timezone-aware current datetime from config.yaml
    timezone = prompt_config.get("timezone", "America/Toronto")
    tz = ZoneInfo(timezone)
    current_datetime = datetime.now(tz)

    _prompt = EMAIL_WRITING_INSTRUCTIONS.format(
        schedule_preferences=schedule_preferences,
        random_preferences=random_preferences,
        response_preferences=response_preferences,
        name=prompt_config["name"],
        full_name=prompt_config["full_name"],
        background=prompt_config["background"],
        current_date=current_datetime.strftime("%A, %B %d, %Y"),
        current_time=current_datetime.strftime("%I:%M %p"),
        tz=timezone,
    )
    input_message = draft_prompt.format(
        instructions=_prompt,
        email=email_template.format(
            email_thread=state["email"]["page_content"],
            author=state["email"]["from_email"],
            subject=state["email"]["subject"],
            to=state["email"].get("to_email", ""),
        ),
    )

    # Bind tools with provider-specific parameters (requires any tool to be called)
    bound_model = bind_tools_with_choice(
        llm,
        model_name,
        tools,
        tool_name=None,  # Allow any tool
        parallel_tool_calls=False  # Disable parallel calls
    )

    messages = [{"role": "user", "content": input_message}] + messages

    # Get email context for logging
    email_id = state.get("email", {}).get("id", "unknown")
    email_subject = state.get("email", {}).get("subject", "unknown")

    logger.info(f"[draft_response] Starting for email_id={email_id}, subject='{email_subject}'")

    i = 0
    max_retries = 5
    while i < max_retries:
        response = await bound_model.ainvoke(messages)
        num_tool_calls = len(response.tool_calls) if hasattr(response, 'tool_calls') else 0

        logger.info(
            f"[draft_response] Attempt {i+1}/{max_retries}: "
            f"num_tool_calls={num_tool_calls}, "
            f"email_id={email_id}"
        )

        if num_tool_calls != 1:
            i += 1

            # Log the specific error
            if num_tool_calls == 0:
                logger.warning(
                    f"[draft_response] LLM returned 0 tool calls (expected 1). "
                    f"email_id={email_id}, attempt={i}/{max_retries}"
                )
                retry_msg = (
                    f"You must call EXACTLY ONE tool. You called 0 tools. "
                    f"Choose the single most appropriate tool from: "
                    f"{', '.join(t.__name__ for t in tools)}"
                )
            else:  # num_tool_calls > 1
                tool_names = [tc['name'] for tc in response.tool_calls]
                logger.warning(
                    f"[draft_response] LLM returned {num_tool_calls} tool calls (expected 1). "
                    f"tools={tool_names}, email_id={email_id}, attempt={i}/{max_retries}"
                )
                retry_msg = (
                    f"You called {num_tool_calls} tools: {', '.join(tool_names)}. "
                    f"You must call EXACTLY ONE tool - choose the single most appropriate one."
                )

            messages += [{"role": "user", "content": retry_msg}]
        else:
            tool_name = response.tool_calls[0]['name']
            logger.info(
                f"[draft_response] SUCCESS: tool={tool_name}, "
                f"email_id={email_id}, attempts={i+1}"
            )
            break

    # Check if we exhausted retries
    if len(response.tool_calls) != 1:
        logger.error(
            f"[draft_response] EXHAUSTED RETRIES: Still got {len(response.tool_calls)} tool calls "
            f"after {max_retries} attempts. email_id={email_id}, subject='{email_subject}'. "
            f"This will cause ValueError in take_action()!"
        )

    return {"draft": response, "messages": [response]}
