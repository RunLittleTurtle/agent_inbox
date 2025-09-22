# router_nodes.py
"""
Router nodes for email agent StateGraph.

- human_input_analyser_node: async node that classifies the human request and
  sets state["router"] = {"target": "triage"|"draft"|"simple", "reason": "..."}
- router_decision: routing function to return the next node name based on state["router"]
- simple_tools_entry: minimal placeholder that calls mock tools (list_email/list_draft)

This file expects your project to expose list_email and list_draft (mocked tools).
If they live elsewhere, adjust the import.
"""

import json
from typing import Any, Dict

from langchain_core.messages import HumanMessage, ToolMessage
from langchain_anthropic import ChatAnthropic

# Import mock tools (adjust path if needed)
try:
    from .tools import list_email, list_draft
except Exception:
    # if relative import fails, try top-level; if fails, define local fallbacks
    try:
        from tools import list_email, list_draft  # type: ignore
    except Exception:
        # local fallback mock functions
        async def list_email() -> str:
            return "📧 mock inbox: no real emails"

        async def list_draft() -> str:
            return "📝 mock drafts: none"


# Defensive State typing
try:
    from eaia.schemas import State
except Exception:
    State = dict  # type: ignore


async def human_input_analyser_node(state: State) -> Dict[str, Any]:
    """
    Analyze the latest human message and set state["router"] = {"target": ..., "reason": ...}

    target: one of "triage", "draft", "simple"
    - "triage": go to triage_input (default)
    - "draft": bypass triage and go directly to draft_response
    - "simple": use simple tools flow (list drafts/inbox/etc.)
    """
    # extract last human text
    human_text = ""
    messages = state.get("messages", []) if isinstance(state, dict) else []
    if messages:
        last = messages[-1]
        if hasattr(last, "content"):
            human_text = getattr(last, "content", "") or ""
        elif isinstance(last, dict):
            human_text = last.get("content", "") or ""

    if not human_text:
        human_text = state.get("human_text", "") if isinstance(state, dict) else ""

    # Prompt Claude to return JSON with target field
    prompt = (
        "You are a strict router. Given the user's request, return ONLY valid JSON "
        "with these fields: {\"target\": \"triage\" | \"draft\" | \"simple\", \"reason\": \"one short sentence\"}.\n\n"
        "Definitions:\n"
        "- triage: run the full triage flow (determine if email / notify / ignore etc.)\n"
        "- draft: bypass triage and go straight to composing/rewriting/sending a draft (user asked to write/send/reply)\n"
        "- simple: user wants simple tool actions (list drafts, show inbox, get last draft, list unread)\n\n"
        "Rules:\n"
        "- If the user asks to send an email now, reply, or compose a new message OR references a specific email -> prefer \"draft\".\n"
        "- If the user explicitly asks for listing or retrieving things (\"list drafts\", \"show inbox\", \"last draft\") -> \"simple\".\n"
        "- Otherwise prefer \"triage\" when unsure.\n\n"
        f"User request:\n\n{human_text}\n\n"
        "Return only JSON. Example: {\"target\":\"draft\",\"reason\":\"user asked to reply to specific message\"}"
    )

    # call anthropic (Claude Sonnet 4) - requires credentials/environment
    try:
        claude = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0.0)
        resp = await claude.agenerate(messages=[HumanMessage(content=prompt)])
        try:
            text = resp.generations[0][0].text
        except Exception:
            text = str(resp)
    except Exception as e:
        # fallback heuristic
        lower = (human_text or "").lower()
        if any(w in lower for w in ["list", "draft", "inbox", "show", "last", "unread"]):
            return {"router": {"target": "simple", "reason": f"llm_error_fallback: {e}"}}
        if any(w in lower for w in ["send", "reply", "compose", "respond", "répondre", "envoyer"]):
            return {"router": {"target": "draft", "reason": f"llm_error_fallback: {e}"}}
        return {"router": {"target": "triage", "reason": f"llm_error_fallback: {e}"}}

    # parse model response
    try:
        parsed = json.loads(text)
        target = parsed.get("target", "triage")
        reason = parsed.get("reason", "")
    except Exception:
        lower = (human_text or "").lower()
        if any(w in lower for w in ["list", "draft", "inbox", "show", "last", "unread"]):
            target = "simple"
            reason = "keyword_fallback"
        elif any(w in lower for w in ["send", "reply", "compose", "respond", "répondre", "envoyer"]):
            target = "draft"
            reason = "keyword_fallback"
        else:
            target = "triage"
            reason = "could_not_parse_llm_response; default to triage"

    target = str(target).strip().lower()
    if target not in ("triage", "draft", "simple"):
        # normalize: if it starts with 'd' -> draft, 's' -> simple, else triage
        if target.startswith("d"):
            target = "draft"
        elif target.startswith("s"):
            target = "simple"
        else:
            target = "triage"

    return {"router": {"target": target, "reason": reason}}


def router_decision(state: State) -> str:
    """
    Return the node name to route to:
      - "triage_input" for triage
      - "draft_response" for direct draft/bypass
      - "simple_tools_entry" for simple tools
    """
    router = state.get("router", {}) if isinstance(state, dict) else {}
    target = (router.get("target") or "").strip().lower()
    if target == "simple":
        return "simple_tools_entry"
    if target == "draft":
        return "draft_response"
    # default
    return "triage_input"


def simple_tools_entry(state: State):
    """
    Minimal simple tools entry:
    - tries to detect which simple tool the user requested and calls it (mock).
    - returns a ToolMessage with the tool result.
    """
    human_text = ""
    messages = state.get("messages", []) if isinstance(state, dict) else []
    if messages:
        last = messages[-1]
        if hasattr(last, "content"):
            human_text = getattr(last, "content", "") or ""
        elif isinstance(last, dict):
            human_text = last.get("content", "") or ""
    if not human_text:
        human_text = state.get("human_text", "") if isinstance(state, dict) else ""

    lower = (human_text or "").lower()
    # determine simple intent
    if "draft" in lower and "last" in lower:
        # call get last draft mock
        try:
            res = list_draft()  # could be async or sync mock
            if hasattr(res, "__await__"):
                import asyncio
                res = asyncio.get_event_loop().run_until_complete(res)
        except Exception:
            res = "mock: error calling list_draft"
        content = f"Simple tools -> last draft result:\n{res}"
    elif any(w in lower for w in ["list", "inbox", "unread", "show"]):
        try:
            res = list_email()
            if hasattr(res, "__await__"):
                import asyncio
                res = asyncio.get_event_loop().run_until_complete(res)
        except Exception:
            res = "mock: error calling list_email"
        content = f"Simple tools -> inbox listing:\n{res}"
    else:
        content = (
            "Routed to simple tools, but I couldn't detect which tool. "
            "Try: 'list drafts', 'get last draft', or 'show inbox'."
        )

    return {"messages": [ToolMessage(content=content, tool_call_id="simple_tools_router")]}