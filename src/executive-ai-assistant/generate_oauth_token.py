#!/usr/bin/env python3
"""
Generate Google OAuth refresh token for Gmail and Calendar access.

Usage:
    python generate_oauth_token.py

This will open a browser for Google OAuth consent, then print the refresh token.
"""

from google_auth_oauthlib.flow import InstalledAppFlow
from pathlib import Path

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar",
]

def main():
    print("=" * 80)
    print("Google OAuth Token Generator")
    print("=" * 80)
    print()
    print("Before running this script, you need:")
    print("1. OAuth client credentials (client_id and client_secret)")
    print("2. Gmail API and Calendar API enabled in Google Cloud Console")
    print()

    # Get credentials from user
    client_id = input("Enter your Google OAuth Client ID: ").strip()
    client_secret = input("Enter your Google OAuth Client Secret: ").strip()

    # Create client config
    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"]
        }
    }

    print()
    print("Starting OAuth flow...")
    print("A browser window will open. Please authorize the application.")
    print()

    # Run the OAuth flow
    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    creds = flow.run_local_server(port=0)

    print()
    print("=" * 80)
    print("SUCCESS! Here are your credentials:")
    print("=" * 80)
    print()
    print(f"google_client_id: {client_id}")
    print(f"google_client_secret: {client_secret}")
    print(f"google_refresh_token: {creds.refresh_token}")
    print()
    print("Copy these values into your Supabase user_secrets table:")
    print("- Replace the test-client-id with the real client_id")
    print("- Replace GOCSPX-test-secret with the real client_secret")
    print("- Replace the test-refresh-token with the real refresh_token")
    print()
    print("=" * 80)

if __name__ == "__main__":
    main()
