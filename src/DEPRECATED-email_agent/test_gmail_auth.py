#!/usr/bin/env python3
"""
Test script to verify Gmail authentication is working properly.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add the src path to import eaia modules
sys.path.insert(0, str(Path(__file__).parent))

from eaia.gmail import fetch_group_emails


async def test_gmail_auth():
    """Test Gmail authentication and email fetching."""
    print("Testing Gmail authentication...")

    # Get email from environment
    email = os.getenv("EMAIL_ASSOCIATED") or os.getenv("USER_GOOGLE_EMAIL")
    if not email:
        print("Error: No email address found in environment variables")
        print("Please set EMAIL_ASSOCIATED or USER_GOOGLE_EMAIL")
        return False

    print(f"Using email: {email}")

    try:
        # Test fetching recent emails (last 60 minutes)
        print("Fetching recent emails...")
        emails = []
        async for email_data in fetch_group_emails(email, minutes_since=60):
            emails.append(email_data)
            print(f"Found email: {email_data.get('subject', 'No subject')}")

        print(f"\nTotal emails found: {len(emails)}")

        if len(emails) > 0:
            print("✅ Gmail authentication and email fetching working!")
            return True
        else:
            print("⚠️ Gmail authentication works but no recent emails found")
            return True

    except Exception as e:
        print(f"❌ Error testing Gmail: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_gmail_auth())
    if not success:
        sys.exit(1)
    print("✅ Gmail authentication test completed successfully!")
