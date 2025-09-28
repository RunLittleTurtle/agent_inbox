"""Agent responsible for rewriting the email in a better tone."""

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic


def get_llm(model_name: str, temperature: float = 0, **kwargs):
    """Get the appropriate LLM based on model name."""
    if model_name.startswith('claude') or model_name.startswith('opus'):
        return ChatAnthropic(model=model_name, temperature=temperature, **kwargs)
    else:  # OpenAI models (gpt-*, o3)
        return ChatOpenAI(model=model_name, temperature=temperature, **kwargs)

from eaia.schemas import State, ReWriteEmail

from eaia.main.config import get_config


rewrite_prompt = """You job is to rewrite an email draft to sound more like {name}.

{name}'s assistant just drafted an email. It is factually correct, but it may not sound like {name}. \
Your job is to rewrite the email keeping the information the same (do not add anything that is made up!) \
but adjusting the tone.

{instructions}

Here is the assistant's current draft:

<draft>
{draft}
</draft>

Here is the email thread:

From: {author}
To: {to}
Subject: {subject}

{email_thread}"""


async def rewrite(state: State, config, store):
    # Get rewrite-specific model configuration from config.yaml
    # NOTE: The hardcoded values below are FALLBACK DEFAULTS only, used if config.yaml is missing
    # The actual model/temperature values are loaded from config.yaml via get_config()
    prompt_config = await get_config(config)
    model = prompt_config.get("rewrite_model", "claude-sonnet-4-20250514")  # Fallback default
    temperature = prompt_config.get("rewrite_temperature", 0.3)  # Fallback default
    llm = get_llm(model, temperature=temperature)
    prev_message = state["messages"][-1]
    draft = prev_message.tool_calls[0]["args"]["content"]
    namespace = (config["configurable"].get("assistant_id", "default"),)
    result = await store.aget(namespace, "rewrite_instructions")
    if result and "data" in result.value:
        _prompt = result.value["data"]
    else:
        await store.aput(
            namespace,
            "rewrite_instructions",
            {"data": prompt_config["rewrite_preferences"]},
        )
        _prompt = prompt_config["rewrite_preferences"]
    input_message = rewrite_prompt.format(
        email_thread=state["email"]["page_content"],
        author=state["email"]["from_email"],
        subject=state["email"]["subject"],
        to=state["email"]["to_email"],
        draft=draft,
        instructions=_prompt,
        name=prompt_config["name"],
    )
    model = llm.with_structured_output(ReWriteEmail).bind(
        tool_choice={"type": "function", "function": {"name": "ReWriteEmail"}}
    )
    response = await model.ainvoke(input_message)
    tool_calls = [
        {
            "id": prev_message.tool_calls[0]["id"],
            "name": prev_message.tool_calls[0]["name"],
            "args": {
                **prev_message.tool_calls[0]["args"],
                **{"content": response.rewritten_content},
            },
        }
    ]
    prev_message = {
        "role": "assistant",
        "id": prev_message.id,
        "content": prev_message.content,
        "tool_calls": tool_calls,
    }
    return {"messages": [prev_message]}
