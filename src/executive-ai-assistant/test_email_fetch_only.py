"""
Test email fetching only (no LangGraph runs)
This script tests the refactored OAuth integration by fetching emails
without creating workflow runs.
"""
import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, '/Users/samuelaudette/Documents/code_projects/agent_inbox_1.18/src')
sys.path.insert(0, '/Users/samuelaudette/Documents/code_projects/agent_inbox_1.18/src/executive-ai-assistant')

from dotenv import load_dotenv
load_dotenv('/Users/samuelaudette/Documents/code_projects/agent_inbox_1.18/.env')

from eaia.gmail import fetch_group_emails


async def test_email_fetch():
    """Test fetching emails with refactored OAuth"""

    print("=" * 80)
    print("Testing Email Fetching with Refactored OAuth")
    print("=" * 80)
    print()

    # User configuration
    user_id = "user_33Z8MWmIOt29U9ii3uA54m3FoU5"
    email = "info@800m.ca"
    minutes_since = 10080  # 7 days

    # Build config for OAuth
    config = {
        "configurable": {"user_id": user_id},
        "metadata": {"user_id": user_id, "clerk_user_id": user_id}
    }

    print(f"User ID: {user_id}")
    print(f"Email: {email}")
    print(f"Fetching last {minutes_since} minutes ({minutes_since // 1440} days)")
    print()
    print("-" * 80)
    print()

    # Fetch emails
    email_count = 0
    try:
        async for email_data in fetch_group_emails(
            email,
            minutes_since=minutes_since,
            config=config
        ):
            email_count += 1

            # Display email info
            from_email = email_data.get('from_email', 'Unknown')
            subject = email_data.get('subject', 'No Subject')
            email_id = email_data.get('id', 'Unknown')
            thread_id = email_data.get('thread_id', 'Unknown')

            print(f"[{email_count}] Email ID: {email_id}")
            print(f"    From: {from_email[:60]}")
            print(f"    Subject: {subject[:80]}")
            print(f"    Thread: {thread_id}")
            print()

            # Stop after 10 emails for testing
            if email_count >= 10:
                print(f"(Stopping after {email_count} emails for testing)")
                break

        print("-" * 80)
        print()
        print(f"✅ SUCCESS! Fetched {email_count} emails")
        print()
        print("Next Steps:")
        print("1. These emails would be sent to the 'main' graph for processing")
        print("2. Main graph: triage → draft_response → rewrite → human approval")
        print("3. Each email gets its own LangGraph thread")
        print()

        return True

    except Exception as e:
        print("-" * 80)
        print()
        print(f"❌ FAILED: {type(e).__name__}: {e}")
        print()
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(test_email_fetch())
    sys.exit(0 if result else 1)
