import argparse
import asyncio
import os
import sys
from typing import Optional

# Add src to Python path for module imports
script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(script_dir, '..', '..', '..')
sys.path.insert(0, src_dir)

# Load environment variables from .env file
from dotenv import load_dotenv

# Load .env from project root
env_path = os.path.join(script_dir, '..', '..', '..', '.env')
load_dotenv(env_path)

# Debug: Check if credentials are loaded
print(f"GOOGLE_CLIENT_ID: {os.getenv('GOOGLE_CLIENT_ID')[:20] if os.getenv('GOOGLE_CLIENT_ID') else 'None'}...")
print(f"GOOGLE_CLIENT_SECRET: {os.getenv('GOOGLE_CLIENT_SECRET')[:20] if os.getenv('GOOGLE_CLIENT_SECRET') else 'None'}...")
print(f"GMAIL_REFRESH_TOKEN: {os.getenv('GMAIL_REFRESH_TOKEN')[:20] if os.getenv('GMAIL_REFRESH_TOKEN') else 'None'}...")

from eaia.gmail import fetch_group_emails
from eaia.main.config import get_config
from langgraph_sdk import get_client
import httpx
import uuid
import hashlib


async def main(
    url: Optional[str] = None,
    minutes_since: int = 60,
    gmail_token: Optional[str] = None,
    gmail_secret: Optional[str] = None,
    early: bool = True,
    rerun: bool = False,
    email: Optional[str] = None,
    user_id: Optional[str] = None,
):
    # Build config with user_id for OAuth credential fetching
    config = {"configurable": {}}
    if user_id:
        config["configurable"]["user_id"] = user_id
        config["metadata"] = {"user_id": user_id, "clerk_user_id": user_id}
        print(f"[CONFIG] Using user_id: {user_id}")

    if email is None:
        config_data = await get_config(config)
        email_address = config_data["email"]
    else:
        email_address = email

    if url is None:
        client = get_client(url="http://127.0.0.1:2025")
    else:
        client = get_client(
            url=url
        )

    print(f"[INBOX] Fetching emails for {email_address} from last {minutes_since} minutes...")

    email_count = 0
    async for email in fetch_group_emails(
        email_address,
        minutes_since=minutes_since,
        config=config,  # Pass config for OAuth credentials
        gmail_token=gmail_token,
        gmail_secret=gmail_secret,
    ):
        email_count += 1
        print(f"[INBOX] Email {email_count}: {email.get('subject', 'No Subject')} from {email.get('from_email', 'Unknown')}")

        thread_id = str(
            uuid.UUID(hex=hashlib.md5(email["thread_id"].encode("UTF-8")).hexdigest())
        )
        try:
            thread_info = await client.threads.get(thread_id)
        except httpx.HTTPStatusError as e:
            if "user_respond" in email:
                continue
            if e.response.status_code == 404:
                thread_info = await client.threads.create(thread_id=thread_id)
            else:
                raise e
        if "user_respond" in email:
            await client.threads.update_state(thread_id, None, as_node="__end__")
            continue
        recent_email = thread_info["metadata"].get("email_id")
        if recent_email == email["id"]:
            if early:
                break
            else:
                if rerun:
                    pass
                else:
                    continue
        await client.threads.update(thread_id, metadata={"email_id": email["id"]})

        print(f" Creating workflow run for thread {thread_id} with graph main")
        run_result = await client.runs.create(
            thread_id,
            "main",
            input={"email": email},
            multitask_strategy="rollback",
        )
        print(f" Workflow run created: {run_result['run_id'] if run_result else 'Unknown'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--url",
        type=str,
        default=None,
        help="URL to run against",
    )
    parser.add_argument(
        "--early",
        type=int,
        default=1,
        help="whether to break when encountering seen emails",
    )
    parser.add_argument(
        "--rerun",
        type=int,
        default=0,
        help="whether to rerun all emails",
    )
    parser.add_argument(
        "--minutes-since",
        type=int,
        default=60,
        help="Only process emails that are less than this many minutes old.",
    )
    parser.add_argument(
        "--gmail-token",
        type=str,
        default=None,
        help="The token to use in communicating with the Gmail API.",
    )
    parser.add_argument(
        "--gmail-secret",
        type=str,
        default=None,
        help="The creds to use in communicating with the Gmail API.",
    )
    parser.add_argument(
        "--email",
        type=str,
        default=None,
        help="The email address to use",
    )
    parser.add_argument(
        "--user-id",
        type=str,
        default=None,
        help="Clerk user ID for OAuth credential fetching",
    )

    args = parser.parse_args()
    asyncio.run(
        main(
            url=args.url,
            minutes_since=args.minutes_since,
            gmail_token=args.gmail_token,
            gmail_secret=args.gmail_secret,
            early=bool(args.early),
            rerun=bool(args.rerun),
            email=args.email,
            user_id=args.user_id,
        )
    )
