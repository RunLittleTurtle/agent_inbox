"""Overall agent."""
import json
from typing import TypedDict, Literal
from langgraph.graph import END, StateGraph
from langchain_core.messages import HumanMessage
from eaia.create_draft_workflow.triage import (
    triage_input,
)
from eaia.create_draft_workflow.draft_response import draft_response
from eaia.create_draft_workflow.find_meeting_time import find_meeting_time
from eaia.create_draft_workflow.rewrite import rewrite
from eaia.create_draft_workflow.config import get_config
from langchain_core.messages import ToolMessage
from eaia.create_draft_workflow.human_inbox import (
    send_message,
    send_email_draft,
    notify,
    send_cal_invite,
)
from eaia.gmail import (
    send_email,
    mark_as_read,
    send_calendar_invite,
)
from eaia.schemas import (
    State,
)


def route_after_triage(
    state: State,
) -> Literal["draft_response", "mark_as_read_node", "notify"]:
    if state["triage"].response == "email":
        return "draft_response"
    elif state["triage"].response == "no":
        return "mark_as_read_node"
    elif state["triage"].response == "notify":
        return "notify"
    elif state["triage"].response == "question":
        return "draft_response"
    else:
        raise ValueError


def take_action(
    state: State,
) -> Literal[
    "send_message",
    "rewrite",
    "find_meeting_time",
    "send_cal_invite",
    "bad_tool_name",
]:
    prediction = state["messages"][-1]
    if len(prediction.tool_calls) != 1:
        raise ValueError
    tool_call = prediction.tool_calls[0]
    if tool_call["name"] == "Question":
        return "send_message"
    elif tool_call["name"] == "ResponseEmailDraft":
        return "rewrite"
    elif tool_call["name"] == "Ignore":
        # For live interactions, ignore means end workflow - handle in human_node routing
        return "bad_tool_name"  # This will go to bad_tool_name, then back to draft_response
    elif tool_call["name"] == "MeetingAssistant":
        return "find_meeting_time"
    elif tool_call["name"] == "SendCalendarInvite":
        return "send_cal_invite"
    else:
        return "bad_tool_name"


def bad_tool_name(state: State):
    tool_call = state["messages"][-1].tool_calls[0]
    message = f"Could not find tool with name `{tool_call['name']}`. Make sure you are calling one of the allowed tools!"
    last_message = state["messages"][-1]
    last_message.tool_calls[0]["name"] = last_message.tool_calls[0]["name"].replace(
        ":", ""
    )
    return {
        "messages": [
            last_message,
            ToolMessage(content=message, tool_call_id=tool_call["id"]),
        ]
    }


def enter_after_human(
    state,
) -> Literal[
    "draft_response", "send_email_node", "send_cal_invite_node"
]:
    messages = state.get("messages") or []
    if len(messages) == 0:
        # For live interactions, always go back to draft_response if no messages
        return "draft_response"
    else:
        if isinstance(messages[-1], (ToolMessage, HumanMessage)):
            return "draft_response"
        else:
            execute = messages[-1].tool_calls[0]
            if execute["name"] == "ResponseEmailDraft":
                return "send_email_node"
            elif execute["name"] == "SendCalendarInvite":
                return "send_cal_invite_node"
            elif execute["name"] == "Ignore":
                # For live interactions, ignore ends the workflow - but this shouldn't be reached
                # because Ignore goes through take_action first
                return "draft_response"
            elif execute["name"] == "Question":
                return "draft_response"
            else:
                raise ValueError


async def send_cal_invite_node(state, config):
    tool_call = state["messages"][-1].tool_calls[0]
    _args = tool_call["args"]
    config_data = await get_config(config)
    email = config_data["email"]
    try:
        await send_calendar_invite(
            _args["emails"],
            _args["title"],
            _args["start_time"],
            _args["end_time"],
            email,
        )
        message = "Sent calendar invite!"
    except Exception as e:
        message = f"Got the following error when sending a calendar invite: {e}"
    return {"messages": [ToolMessage(content=message, tool_call_id=tool_call["id"])]}


async def send_email_node(state, config):
    tool_call = state["messages"][-1].tool_calls[0]
    _args = tool_call["args"]
    config_data = await get_config(config)
    email = config_data["email"]
    new_receipients = _args["new_recipients"]
    if isinstance(new_receipients, str):
        new_receipients = json.loads(new_receipients)
    await send_email(
        state["email"]["id"],
        _args["content"],
        email,
        addn_receipients=new_receipients,
    )


async def mark_as_read_node(state, config):
    config_data = await get_config(config)
    email = config_data["email"]
    await mark_as_read(state["email"]["id"], email)


def human_node(state: State):
    pass


class ConfigSchema(TypedDict):
    db_id: int
    model: str


# Live interactions StateGraph - simplified for email_agent orchestrator
graph_builder = StateGraph(State, config_schema=ConfigSchema)

# Essential nodes for live interactions
graph_builder.add_node(human_node)
graph_builder.add_node(draft_response)
graph_builder.add_node(send_message)
graph_builder.add_node(rewrite)
graph_builder.add_node(send_email_draft)
graph_builder.add_node(send_email_node)
graph_builder.add_node(bad_tool_name)
graph_builder.add_node(notify)  # For user notifications/alerts
graph_builder.add_node(send_cal_invite_node)
graph_builder.add_node(send_cal_invite)
graph_builder.add_node(find_meeting_time)  # For calendar functionality

# Set entry point for live interactions (bypass triage)
graph_builder.set_entry_point("draft_response")

# Core workflow edges
graph_builder.add_conditional_edges("draft_response", take_action)
graph_builder.add_edge("send_message", "human_node")
graph_builder.add_edge("send_cal_invite", "human_node")
graph_builder.add_edge("find_meeting_time", "draft_response")
graph_builder.add_edge("bad_tool_name", "draft_response")
graph_builder.add_edge("send_cal_invite_node", "draft_response")
graph_builder.add_edge("rewrite", "send_email_draft")
graph_builder.add_edge("send_email_draft", "human_node")

# Live interactions: send email then end (no mark_as_read for live mode)
graph_builder.add_edge("send_email_node", END)

# User notifications and human interaction routing
graph_builder.add_edge("notify", "human_node")
graph_builder.add_conditional_edges("human_node", enter_after_human)
# Compile graph - LangGraph server will automatically provide store from langgraph.json configuration
# The email_agent langgraph.json defines: "store": {"index": {"embed": "openai:text-embedding-3-small", "dims": 1536}}
graph = graph_builder.compile()
