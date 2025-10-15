#!/usr/bin/env python3
"""
Backfill owner metadata to existing executive_main threads

This script adds the missing "owner" field to threads that were created
before the owner metadata fix was deployed. This makes them visible in
the Agent Inbox UI when filtered by user.

Usage:
    python scripts/backfill_owner_metadata.py --user-id user_33Z8MWmIOt29U9ii3uA54m3FoU5
"""
import asyncio
import argparse
from langgraph_sdk import get_client


async def backfill_owner_metadata(user_id: str, url: str, dry_run: bool = False):
    """Add owner metadata to executive_main threads missing it"""

    client = get_client(url=url)

    print(f"Fetching executive_main threads...")
    threads = await client.threads.search(
        metadata={'graph_id': 'executive_main'},
        limit=100
    )

    print(f"Found {len(threads)} threads")

    needs_update = []
    already_has_owner = []

    for thread in threads:
        metadata = thread.get('metadata', {})
        thread_id = thread['thread_id']

        if 'owner' in metadata:
            already_has_owner.append(thread_id)
        else:
            needs_update.append((thread_id, metadata))

    print(f"\nThreads already with owner: {len(already_has_owner)}")
    print(f"Threads needing update: {len(needs_update)}")

    if not needs_update:
        print("\nAll threads already have owner metadata!")
        return

    if dry_run:
        print("\n=== DRY RUN MODE ===")
        print("Would update the following threads:")
        for thread_id, metadata in needs_update:
            print(f"  {thread_id[:8]}... - current metadata: {metadata}")
        return

    print(f"\nUpdating {len(needs_update)} threads...")
    updated = 0

    for thread_id, metadata in needs_update:
        # Add owner to existing metadata
        metadata['owner'] = user_id

        try:
            await client.threads.update(
                thread_id,
                metadata=metadata
            )
            updated += 1
            print(f"✓ Updated thread {thread_id[:8]}...")
        except Exception as e:
            print(f"✗ Failed to update thread {thread_id[:8]}: {e}")

    print(f"\n=== COMPLETE ===")
    print(f"Successfully updated {updated}/{len(needs_update)} threads")
    print(f"All executive_main threads now have owner: {user_id}")


def main():
    parser = argparse.ArgumentParser(description='Backfill owner metadata to executive_main threads')
    parser.add_argument('--user-id', required=True, help='Clerk user ID (e.g., user_33Z8MWmIOt29U9ii3uA54m3FoU5)')
    parser.add_argument('--url', default='https://multi-agent-app-1d1e061875eb5640a47e3bb201edb076.us.langgraph.app',
                        help='LangGraph deployment URL')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be updated without making changes')

    args = parser.parse_args()

    print(f"=== Backfill Owner Metadata ===")
    print(f"User ID: {args.user_id}")
    print(f"URL: {args.url}")
    print(f"Dry run: {args.dry_run}\n")

    asyncio.run(backfill_owner_metadata(args.user_id, args.url, args.dry_run))


if __name__ == '__main__':
    main()
