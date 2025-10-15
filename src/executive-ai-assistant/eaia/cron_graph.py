from typing import TypedDict
from eaia.gmail import fetch_group_emails
from langgraph_sdk import get_client
import httpx
import uuid
import hashlib
from langgraph.graph import StateGraph, START, END
from eaia.main.config import get_config

client = get_client()


class JobKickoff(TypedDict):
    minutes_since: int


async def main(state: JobKickoff, config):
    """
    Process emails for a SINGLE user (2025 multi-tenant pattern)

    This cron runs PER-USER with user context passed via config:
    - config["configurable"]["user_id"] set by LangGraph Platform
    - config["configurable"]["email"] set by LangGraph Platform
    - Each user has their own cron job created via /api/webhooks/gmail-connected

    No longer loops through users - that's handled by having multiple cron jobs!
    """
    minutes_since: int = state["minutes_since"]

    # User context comes from the cron job's assistant config
    # (set during cron creation in config_api/main.py)
    config_data = await get_config(config)
    email_address = config_data["email"]
    user_id = config_data.get("user_id")

    if not user_id:
        print("[ERROR] No user_id in cron config - this should never happen!")
        print(f"[ERROR] Config data: {config_data}")
        return  # Exit gracefully

    print(f"[CRON] Processing emails for user {user_id} ({email_address})")
    print(f"[CRON] Fetching emails from last {minutes_since} minutes")

    # Ensure user_id is in config for OAuth credential fetching
    if "configurable" not in config:
        config["configurable"] = {}
    config["configurable"]["user_id"] = user_id
    config["metadata"] = {"user_id": user_id, "clerk_user_id": user_id}

    email_count = 0
    processed_count = 0

    async for email in fetch_group_emails(email_address, minutes_since=minutes_since, config=config):
        email_count += 1
        print(f"[CRON] Email {email_count}: {email.get('subject', 'No Subject')[:50]}")
        thread_id = str(
            uuid.UUID(hex=hashlib.md5(email["thread_id"].encode("UTF-8")).hexdigest())
        )
        try:
            thread_info = await client.threads.get(thread_id)
        except httpx.HTTPStatusError as e:
            if "user_respond" in email:
                continue
            if e.response.status_code == 404:
                # Create thread with graph_id and owner metadata for Agent Inbox filtering
                thread_info = await client.threads.create(
                    thread_id=thread_id,
                    metadata={
                        "graph_id": "executive_main",
                        "owner": user_id  # Required for auth.py multi-tenant filtering
                    }
                )
            else:
                raise e
        if "user_respond" in email:
            await client.threads.update_state(thread_id, None, as_node="__end__")
            continue
        recent_email = thread_info["metadata"].get("email_id")
        if recent_email == email["id"]:
            break
        await client.threads.update(thread_id, metadata={
            "graph_id": "executive_main",  # Preserve graph_id for inbox filtering
            "owner": user_id,  # Preserve owner for auth.py multi-tenant filtering
            "email_id": email["id"]
        })

        await client.runs.create(
            thread_id,
            "executive_main",
            input={"email": email},
            config={
                "configurable": {
                    "user_id": user_id
                }
            },
            multitask_strategy="rollback",
        )
        processed_count += 1
        print(f"[CRON] Created workflow run for thread {thread_id}")

    # Final summary
    print(f"[CRON] Completed for user {user_id}: {processed_count}/{email_count} emails processed")


graph = StateGraph(JobKickoff)
graph.add_node(main)
graph.add_edge(START, "main")
graph.add_edge("main", END)
graph = graph.compile()
