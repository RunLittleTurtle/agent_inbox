#!/usr/bin/env python3
"""
Local Cron Timer for Executive AI Assistant

This script runs a timer-based cron job that periodically checks for new emails
and sends them to the executive assistant for processing. It's designed for local
development and doesn't modify any deployment-ready code.

Usage:
    python scripts/local_cron_timer.py --interval 15 --minutes-since 30
"""
import asyncio
import argparse
import signal
import sys
import os
from datetime import datetime
from typing import Optional
import httpx
from pathlib import Path

# Add the parent directory to Python path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
load_dotenv(env_path)

from eaia.gmail import fetch_group_emails
from eaia.main.config import get_config
from langgraph_sdk import get_client
import uuid
import hashlib


class LocalCronTimer:
    def __init__(self, interval_minutes: int = 15, minutes_since: int = 30, url: str = "http://127.0.0.1:2025"):
        self.interval_minutes = interval_minutes
        self.minutes_since = minutes_since
        self.url = url
        self.running = True
        self.client = None

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\n[STOP] Received signal {signum}, shutting down local cron timer...")
        self.running = False

    async def _check_server_health(self) -> bool:
        """Check if the LangGraph server is running and responsive"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Use the docs endpoint which exists on LangGraph servers
                response = await client.get(f"{self.url}/docs")
                return response.status_code == 200
        except Exception:
            return False

    async def _run_email_ingestion(self) -> None:
        """Run the email ingestion process (adapted from run_ingest.py)"""
        try:
            # Get user config
            config_data = await get_config({"configurable": {}})
            email_address = config_data["email"]

            # Initialize LangGraph client
            if not self.client:
                self.client = get_client(url=self.url)

            print(f" Fetching emails for {email_address} from last {self.minutes_since} minutes...")

            email_count = 0
            processed_count = 0

            async for email in fetch_group_emails(
                email_address,
                minutes_since=self.minutes_since,
            ):
                email_count += 1
                print(f"[EMAIL] Email {email_count}: {email.get('subject', 'No Subject')} from {email.get('from_email', 'Unknown')}")

                thread_id = str(
                    uuid.UUID(hex=hashlib.md5(email["thread_id"].encode("UTF-8")).hexdigest())
                )

                try:
                    thread_info = await self.client.threads.get(thread_id)
                except httpx.HTTPStatusError as e:
                    if "user_respond" in email:
                        continue
                    if e.response.status_code == 404:
                        thread_info = await self.client.threads.create(thread_id=thread_id)
                    else:
                        print(f" Error getting thread: {e}")
                        continue

                if "user_respond" in email:
                    await self.client.threads.update_state(thread_id, None, as_node="__end__")
                    continue

                recent_email = thread_info["metadata"].get("email_id")
                if recent_email == email["id"]:
                    print(f"  Email already processed, skipping...")
                    break

                await self.client.threads.update(thread_id, metadata={"email_id": email["id"]})

                print(f" Creating workflow run for thread {thread_id}")
                run_result = await self.client.runs.create(
                    thread_id,
                    "main",  # Use the correct graph name for local setup
                    input={"email": email},
                    multitask_strategy="rollback",
                )
                processed_count += 1
                print(f" Workflow run created: {run_result.get('run_id', 'Unknown')}")

            if email_count == 0:
                print(" No new emails found")
            else:
                print(f" Processed {processed_count} out of {email_count} emails")

        except Exception as e:
            print(f" Error during email ingestion: {e}")

    async def run(self) -> None:
        """Main timer loop"""
        print(f" Starting Local Cron Timer")
        print(f"    Interval: Every {self.interval_minutes} minutes")
        print(f"    Email window: Last {self.minutes_since} minutes")
        print(f"    LangGraph URL: {self.url}")
        print(f"    Press Ctrl+C to stop")
        print()

        # Run initial email check
        if await self._check_server_health():
            print(" LangGraph server is running, performing initial email check...")
            await self._run_email_ingestion()
        else:
            print(" LangGraph server not available, waiting for next interval...")

        # Main timer loop
        while self.running:
            try:
                # Wait for the specified interval
                for i in range(self.interval_minutes * 60):  # Convert minutes to seconds
                    if not self.running:
                        break
                    await asyncio.sleep(1)

                if not self.running:
                    break

                # Check server health before processing
                if await self._check_server_health():
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(f"\n [{timestamp}] Timer triggered - checking for new emails...")
                    await self._run_email_ingestion()
                else:
                    print(f"\n [{datetime.now().strftime('%H:%M:%S')}] LangGraph server not available, skipping this cycle...")

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f" Unexpected error in timer loop: {e}")
                # Continue running even if there's an error

        print(" Local Cron Timer stopped")


async def main():
    parser = argparse.ArgumentParser(description="Local Cron Timer for Executive AI Assistant")
    parser.add_argument(
        "--interval",
        type=int,
        default=15,
        help="Interval in minutes between email checks (default: 15)"
    )
    parser.add_argument(
        "--minutes-since",
        type=int,
        default=30,
        help="Only process emails from the last N minutes (default: 30)"
    )
    parser.add_argument(
        "--url",
        type=str,
        default="http://127.0.0.1:2025",
        help="LangGraph server URL (default: http://127.0.0.1:2025)"
    )

    args = parser.parse_args()

    # Create and run the timer
    timer = LocalCronTimer(
        interval_minutes=args.interval,
        minutes_since=args.minutes_since,
        url=args.url
    )

    await timer.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n Goodbye!")
    except Exception as e:
        print(f" Fatal error: {e}")
        sys.exit(1)