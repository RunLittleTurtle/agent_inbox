#!/usr/bin/env python3
"""
Setup script to create proper Google OAuth credentials with correct scopes.
Based on: https://github.com/langchain-ai/agents-from-scratch/blob/main/src/email_assistant/tools/gmail/setup_gmail.py
"""
import json
import os
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# OAuth scopes required by the executive assistant
SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar",
]


def setup_google_oauth():
    """Set up Google OAuth credentials with proper scopes."""

    # Get credentials from environment
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("Error: Missing GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET environment variables")
        return False

    # Create client secrets structure
    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uris": ["http://localhost"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
        }
    }

    print("Setting up Google OAuth with scopes:")
    for scope in SCOPES:
        print(f"  - {scope}")

    try:
        # Create OAuth flow
        flow = InstalledAppFlow.from_client_config(client_config, SCOPES)

        # Run the OAuth flow
        print("\nStarting OAuth flow...")
        print("This will open a browser window for authentication.")
        print("Please authorize the application in your browser.")

        creds = flow.run_local_server(port=0)

        # Extract the refresh token
        refresh_token = creds.refresh_token

        if not refresh_token:
            print("Error: No refresh token received. This might happen if you've already granted permissions.")
            print("Try revoking access at https://myaccount.google.com/permissions and run this script again.")
            return False

        print(f"\n✅ OAuth setup successful!")
        print(f"Refresh token: {refresh_token}")
        print(f"\nAdd this to your .env file:")
        print(f"GMAIL_REFRESH_TOKEN={refresh_token}")

        return True

    except Exception as e:
        print(f"❌ Error during OAuth setup: {e}")
        return False


if __name__ == "__main__":
    success = setup_google_oauth()
    if not success:
        exit(1)
