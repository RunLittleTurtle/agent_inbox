"""Agent responsible for managing calendar and finding meeting time."""

from datetime import datetime
from zoneinfo import ZoneInfo

from langgraph.prebuilt import create_react_agent
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableConfig

from eaia.gmail import get_events_for_days
from eaia.llm_utils import get_llm
from eaia.schemas import State

from eaia.main.config import get_config

meeting_prompts = """You are {full_name}'s executive assistant. You are a top-notch executive assistant who cares about {name} performing as well as possible.

The below email thread has been flagged as requesting time to meet. Your SOLE purpose is to survey {name}'s calendar and schedule meetings for {name}.

If the email is suggesting some specific times, then check if {name} is available then.

If the emails asks for time, use the tool to find valid times to meet (always suggest them in {tz}).

If they express preferences in their email thread, try to abide by those. Do not suggest times they have already said won't work.

Try to send available spots in as big of chunks as possible. For example, if {name} has 1pm-3pm open, send:

```
1pm-3pm
```

NOT

```
1-1:30pm
1:30-2pm
2-2:30pm
2:30-3pm
```

Do not send time slots less than 15 minutes in length.

Your response should be extremely high density. You should not respond directly to the email, but rather just say factually whether {name} is free, and what time slots. Do not give any extra commentary. Examples of good responses include:

<examples>

Example 1:

> {name} is free 9:30-10

Example 2:

> {name} is not free then. But he is free at 10:30

</examples>

Current date and time: {current_date} at {current_time} {tz}

Here is the email thread:

From: {author}
Subject: {subject}

{email_thread}"""


async def find_meeting_time(state: State, config: RunnableConfig):
    """Write an email to a customer."""
    # Get scheduling-specific model configuration from config.yaml
    # NOTE: The hardcoded values below are FALLBACK DEFAULTS only, used if config.yaml is missing
    # The actual model/temperature values are loaded from config.yaml via get_config()
    prompt_config = await get_config(config)
    model = prompt_config.get("scheduling_model", "gpt-4o")  # Fallback default
    temperature = prompt_config.get("scheduling_temperature", 0.1)  # Fallback default

    # Load per-user API keys from config
    anthropic_api_key = prompt_config.get("anthropic_api_key")
    openai_api_key = prompt_config.get("openai_api_key")

    llm = get_llm(model, temperature=temperature, anthropic_api_key=anthropic_api_key, openai_api_key=openai_api_key)
    agent = create_react_agent(llm, [get_events_for_days], name="meeting_time_finder")

    # Get timezone-aware current datetime from config.yaml
    timezone = prompt_config.get("timezone", "America/Toronto")
    tz = ZoneInfo(timezone)
    current_datetime = datetime.now(tz)

    input_message = meeting_prompts.format(
        email_thread=state["email"]["page_content"],
        author=state["email"]["from_email"],
        subject=state["email"]["subject"],
        current_date=current_datetime.strftime("%A, %B %d, %Y"),
        current_time=current_datetime.strftime("%I:%M %p"),
        name=prompt_config["name"],
        full_name=prompt_config["full_name"],
        tz=timezone,
    )
    messages = state.get("messages") or []
    # we do this because theres currently a tool call just for routing
    messages = messages[:-1]
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": input_message}] + messages}
    )
    prediction = state["messages"][-1]
    tool_call = prediction.tool_calls[0]
    return {
        "messages": [
            ToolMessage(
                content=result["messages"][-1].content, tool_call_id=tool_call["id"]
            )
        ]
    }
