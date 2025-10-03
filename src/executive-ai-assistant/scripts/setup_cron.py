"""Set up a cron job that runs every 10 minutes to check for emails"""
import argparse
import asyncio
from typing import Optional
from langgraph_sdk import get_client


async def main(
    url: Optional[str] = None,
    minutes_since: int = 60,
):
    import os
    api_key = os.getenv("LANGSMITH_API_KEY")

    if url is None:
        client = get_client(url="http://127.0.0.1:2025")
    else:
        client = get_client(
            url=url,
            api_key=api_key  # Add API key for authentication
        )
    await client.crons.create("executive_cron", schedule="*/10 * * * *", input={"minutes_since": minutes_since})



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--url",
        type=str,
        default=None,
        help="URL to run against",
    )
    parser.add_argument(
        "--minutes-since",
        type=int,
        default=60,
        help="Only process emails that are less than this many minutes old.",
    )

    args = parser.parse_args()
    asyncio.run(
        main(
            url=args.url,
            minutes_since=args.minutes_since,
        )
    )
