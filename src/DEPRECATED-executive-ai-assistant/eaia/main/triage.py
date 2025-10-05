"""Agent responsible for triaging the email, can either ignore it, try to respond, or notify user."""

from datetime import datetime
from zoneinfo import ZoneInfo
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import RemoveMessage
from langgraph.store.base import BaseStore

from eaia.schemas import (
    State,
    RespondTo,
)
from eaia.main.fewshot import get_few_shot_examples
from eaia.main.config import get_config
from eaia.llm_utils import get_llm, get_tool_choice


triage_prompt = """You are {full_name}'s executive assistant. You are a top-notch executive assistant who cares about {name} performing as well as possible.

{background}.

Current date and time: {current_date} at {current_time} {tz}

{name} gets lots of emails. Your job is to categorize the below email to see whether is it worth responding to.

Emails that are not worth responding to:
{triage_no}

Emails that are worth responding to:
{triage_email}

There are also other things that {name} should know about, but don't require an email response. For these, you should notify {name} (using the `notify` response). Examples of this include:
{triage_notify}

For emails not worth responding to, respond `no`. For something where {name} should respond over email, respond `email`. If it's important to notify {name}, but no email is required, respond `notify`. \

If unsure, opt to `notify` {name} - you will learn from this in the future.

{fewshotexamples}

Please determine how to handle the below email thread:

From: {author}
To: {to}
Subject: {subject}

{email_thread}"""


async def triage_input(state: State, config: RunnableConfig, store: BaseStore):
    # Get triage-specific model configuration from config.yaml
    # NOTE: The hardcoded values below are FALLBACK DEFAULTS only, used if config.yaml is missing
    # The actual model/temperature values are loaded from config.yaml via get_config()
    prompt_config = await get_config(config)
    model_name = prompt_config.get("triage_model", "claude-3-5-haiku-20241022")  # Fallback default
    temperature = prompt_config.get("triage_temperature", 0.1)  # Fallback default

    # Load per-user API keys from config
    anthropic_api_key = prompt_config.get("anthropic_api_key")
    openai_api_key = prompt_config.get("openai_api_key")

    llm = get_llm(model_name, temperature=temperature, anthropic_api_key=anthropic_api_key, openai_api_key=openai_api_key)
    examples = await get_few_shot_examples(state["email"], store, config)

    # Get timezone-aware current datetime from config.yaml
    timezone = prompt_config.get("timezone", "America/Toronto")
    tz = ZoneInfo(timezone)
    current_datetime = datetime.now(tz)

    input_message = triage_prompt.format(
        email_thread=state["email"]["page_content"],
        author=state["email"]["from_email"],
        to=state["email"].get("to_email", ""),
        subject=state["email"]["subject"],
        fewshotexamples=examples,
        name=prompt_config["name"],
        full_name=prompt_config["full_name"],
        background=prompt_config["background"],
        triage_no=prompt_config["triage_no"],
        triage_email=prompt_config["triage_email"],
        triage_notify=prompt_config["triage_notify"],
        current_date=current_datetime.strftime("%A, %B %d, %Y"),
        current_time=current_datetime.strftime("%I:%M %p"),
        tz=timezone,
    )
    model = llm.with_structured_output(RespondTo).bind(
        tool_choice=get_tool_choice(model_name, "RespondTo")
    )
    response = await model.ainvoke(input_message)
    if len(state["messages"]) > 0:
        delete_messages = [RemoveMessage(id=m.id) for m in state["messages"]]
        return {"triage": response, "messages": delete_messages}
    else:
        return {"triage": response}
