"""
Human-in-the-loop integration for agent_inbox
Parts of the graph that require human input.
"""

import uuid
from typing import TypedDict, Literal, Union, Optional

from langsmith import traceable
from langgraph.types import interrupt
from langgraph.store.base import BaseStore
from langgraph_sdk import get_client

# TODO: Replace with your agent's state if needed, or use MessagesState
# from .schemas import State

LGC = get_client()


class HumanInterruptConfig(TypedDict):
    allow_ignore: bool
    allow_respond: bool
    allow_edit: bool
    allow_accept: bool


class ActionRequest(TypedDict):
    action: str
    args: dict


class HumanInterrupt(TypedDict):
    action_request: ActionRequest
    config: HumanInterruptConfig
    description: Optional[str]


class HumanResponse(TypedDict):
    type: Literal["accept", "ignore", "response", "edit"]
    args: Union[None, str, ActionRequest]


def create_human_interrupt(
    action: str,
    args: dict,
    description: str = None,
    allow_ignore: bool = True,
    allow_respond: bool = True,
    allow_edit: bool = True,
    allow_accept: bool = True
) -> None:
    """
    Create a human interrupt for agent_inbox integration

    Args:
        action: The action to be approved
        args: Arguments for the action
        description: Human-readable description
        allow_*: What actions the human can take
    """

    interrupt_data = HumanInterrupt(
        action_request=ActionRequest(action=action, args=args),
        config=HumanInterruptConfig(
            allow_ignore=allow_ignore,
            allow_respond=allow_respond,
            allow_edit=allow_edit,
            allow_accept=allow_accept
        ),
        description=description
    )

    # Create the interrupt
    interrupt(interrupt_data)
