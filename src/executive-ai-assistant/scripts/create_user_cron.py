#!/usr/bin/env python3
"""
Create Per-User Cron Jobs for Executive AI Assistant

This script manually creates LangGraph Platform cron jobs for existing users.
It follows the 2025 multi-tenant pattern where each user gets their own cron job.

Usage:
    # Create cron for a single user
    python scripts/create_user_cron.py --user-id user_33Z8MWmIOt29U9ii3uA54m3FoU5 --email info@800m.ca

    # Create crons for ALL users with Gmail connected
    python scripts/create_user_cron.py --all-users

    # Custom schedule (default is every 15 minutes)
    python scripts/create_user_cron.py --user-id USER_ID --email EMAIL --schedule "*/30 * * * *"
"""
import asyncio
import argparse
import os
import sys
from pathlib import Path

# Add parent directory to Python path
script_dir = Path(__file__).parent.parent
sys.path.insert(0, str(script_dir.parent.parent))

from dotenv import load_dotenv

# Load environment variables
env_path = script_dir.parent.parent / '.env'
load_dotenv(env_path)

import httpx


async def create_cron_via_api(user_id: str, email: str, schedule: str = "* * * * *"):
    """
    Create cron job via Config API webhook endpoint

    This calls the Railway-deployed FastAPI endpoint that:
    1. Creates LangGraph Platform cron job
    2. Stores cron_id in Supabase user_crons table
    """
    config_api_url = os.getenv(
        "CONFIG_API_URL",
        "https://agentinbox-production.up.railway.app"
    )

    webhook_url = f"{config_api_url}/api/webhooks/gmail-connected"

    print(f"\n=== Creating Cron for User ===")
    print(f"User ID: {user_id}")
    print(f"Email: {email}")
    print(f"Schedule: {schedule}")
    print(f"Webhook URL: {webhook_url}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                webhook_url,
                json={
                    "user_id": user_id,
                    "email": email,
                    "schedule": schedule
                }
            )

            response.raise_for_status()
            result = response.json()

            print(f"\n✓ Success!")
            print(f"  Cron ID: {result.get('cron_id')}")
            print(f"  Assistant ID: {result.get('assistant_id')}")
            print(f"  Schedule: {result.get('schedule')}")

            return result

    except httpx.HTTPStatusError as e:
        print(f"\n✗ HTTP Error {e.response.status_code}")
        print(f"  Response: {e.response.text}")
        return None
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return None


async def create_crons_for_all_users():
    """
    Query Supabase for all users with Gmail connected,
    then create cron jobs for each
    """
    from supabase import create_client

    supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SECRET_KEY")

    if not supabase_url or not supabase_key:
        print("✗ Error: Missing Supabase credentials")
        print("  Set NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SECRET_KEY in .env")
        return

    supabase = create_client(supabase_url, supabase_key)

    print("\n=== Fetching Users with Gmail Connected ===")

    try:
        # Query user_secrets for users with gmail_refresh_token
        result = supabase.table("user_secrets") \
            .select("clerk_id, gmail_refresh_token") \
            .not_.is_("gmail_refresh_token", "null") \
            .execute()

        users = result.data if result and result.data else []

        print(f"Found {len(users)} users with Gmail connected")

        if not users:
            print("No users found. Make sure users have completed Gmail OAuth.")
            return

        # For each user, we need to get their email address
        # This requires querying Gmail API or storing email in user_secrets
        print("\nNote: Email addresses must be provided manually for now.")
        print("In production, store email in user_secrets during OAuth.")

        for user in users:
            user_id = user["clerk_id"]
            print(f"\n  User: {user_id}")
            print(f"    Gmail token exists: ✓")
            print(f"    Email: [Need to provide manually]")

    except Exception as e:
        print(f"✗ Error querying Supabase: {e}")


async def main():
    parser = argparse.ArgumentParser(
        description="Create per-user cron jobs for Executive AI Assistant"
    )
    parser.add_argument(
        "--user-id",
        type=str,
        help="Clerk user ID (e.g., user_33Z8MWmIOt29U9ii3uA54m3FoU5)"
    )
    parser.add_argument(
        "--email",
        type=str,
        help="Gmail address for this user"
    )
    parser.add_argument(
        "--schedule",
        type=str,
        default="* * * * *",
        help="Cron schedule (default: every 1 minute)"
    )
    parser.add_argument(
        "--all-users",
        action="store_true",
        help="Create crons for all users with Gmail connected"
    )

    args = parser.parse_args()

    if args.all_users:
        await create_crons_for_all_users()
    elif args.user_id and args.email:
        await create_cron_via_api(args.user_id, args.email, args.schedule)
    else:
        print("Error: Must provide either:")
        print("  --user-id and --email")
        print("  OR --all-users")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
