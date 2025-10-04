#!/usr/bin/env python3
"""
OS-level cron job script for Executive AI Assistant

This script is designed to be called by the OS cron daemon to periodically
check for new emails and process them through the executive assistant.

Usage:
    python scripts/run_cron_job.py --minutes-since 30 --url http://127.0.0.1:2025
"""
import asyncio
import argparse
import sys
import os
from datetime import datetime
from pathlib import Path

# Add the parent directory to Python path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
load_dotenv(env_path)

from langgraph_sdk import get_client
import httpx


async def check_server_health(url: str) -> bool:
    """Check if the LangGraph server is running and responsive"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{url}/docs")
            return response.status_code == 200
    except Exception as e:
        print(f" Server health check failed: {e}")
        return False


async def run_cron_graph(url: str, minutes_since: int) -> None:
    """Run the cron graph to check and process emails"""
    try:
        # Check server health first
        if not await check_server_health(url):
            print(f" LangGraph server at {url} is not available, skipping email check")
            return

        # Initialize LangGraph client
        client = get_client(url=url)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f" [{timestamp}] Starting email check via cron graph...")

        # Create a run for the cron graph
        run_result = await client.runs.create(
            None,  # No specific thread ID needed for cron graph
            "cron",  # Use the cron graph
            input={"minutes_since": minutes_since},
            multitask_strategy="rollback",
        )

        run_id = run_result.get('run_id', 'Unknown')
        print(f" Cron graph run created successfully: {run_id}")

        print(f" Email check completed via cron graph")

    except Exception as e:
        print(f" Error running cron graph: {e}")
        sys.exit(1)


async def main():
    parser = argparse.ArgumentParser(description="OS-level cron job for Executive AI Assistant")
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

    await run_cron_graph(args.url, args.minutes_since)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n Cron job interrupted")
        sys.exit(0)
    except Exception as e:
        print(f" Fatal error in cron job: {e}")
        sys.exit(1)