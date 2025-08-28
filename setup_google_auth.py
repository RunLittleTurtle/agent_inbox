#!/usr/bin/env python3
"""
Google OAuth 2.0 Setup Helper
Run this script to authenticate and get tokens for all required Google Workspace APIs
"""

import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import json

# All scopes needed for your agents
# Based on https://developers.google.com/identity/protocols/oauth2/scopes
SCOPES = [
    # Gmail API - Full access for reading, sending, and modifying emails
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.labels',
    
    # Calendar API - Read calendar and manage events
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/calendar',  # Full calendar access
    
    # Drive API - Read files and metadata
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/drive.metadata.readonly',
    'https://www.googleapis.com/auth/drive.file',  # Access to files created by the app
    
    # People API (Contacts) - Read contact information
    'https://www.googleapis.com/auth/contacts.readonly',
    'https://www.googleapis.com/auth/contacts',  # Full contacts access if needed
    
    # Additional useful scopes
    'https://www.googleapis.com/auth/userinfo.email',  # Access user's email address
    'https://www.googleapis.com/auth/userinfo.profile',  # Access basic profile info
]

def setup_credentials():
    """Setup Google OAuth 2.0 credentials for all services"""
    
    print("🚀 Google Workspace OAuth 2.0 Setup")
    print("=" * 50)
    
    # Check if credentials.json exists
    if not os.path.exists('credentials.json'):
        print("❌ ERROR: credentials.json not found!")
        print("\n📋 Steps to get credentials.json:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Select your project")
        print("3. Go to 'APIs & Services' > 'Credentials'")
        print("4. Click on your OAuth 2.0 Client ID (Web client)")
        print("5. Click 'Download JSON'")
        print("6. Save as 'credentials.json' in this directory")
        return None
    
    print("✅ credentials.json found")
    
    creds = None
    
    # Try to load existing token
    if os.path.exists('token_master.pickle'):
        print("🔄 Loading existing token...")
        try:
            with open('token_master.pickle', 'rb') as token:
                creds = pickle.load(token)
                print("✅ Existing token loaded")
        except Exception as e:
            print(f"⚠️ Error loading token: {e}")
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired token...")
            try:
                creds.refresh(Request())
                print("✅ Token refreshed successfully")
            except Exception as e:
                print(f"❌ Error refreshing token: {e}")
                creds = None
        
        if not creds:
            print("🌐 Starting OAuth 2.0 flow...")
            print("📝 Required scopes:")
            for scope in SCOPES:
                print(f"   • {scope}")
            print("\n🔗 Your browser will open for authentication...")
            
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                # Force consent to handle scope changes
                creds = flow.run_local_server(port=8080, prompt='consent')
                print("✅ Authentication successful!")
            except Exception as e:
                print(f"❌ Authentication failed: {e}")
                return None
        
        # Save the credentials for the next run
        try:
            with open('token_master.pickle', 'wb') as token:
                pickle.dump(creds, token)
            print("💾 Credentials saved to token_master.pickle")
        except Exception as e:
            print(f"⚠️ Error saving credentials: {e}")
    
    # Extract credentials for .env file
    if creds and creds.valid:
        print("\n🔑 Credentials for .env file:")
        print("=" * 30)
        print(f"GOOGLE_CLIENT_ID={creds.client_id}")
        print(f"GOOGLE_CLIENT_SECRET={creds.client_secret}")
        print(f"GMAIL_REFRESH_TOKEN={creds.refresh_token}")
        
        # Create .env entries
        env_content = f"""
# Google Workspace OAuth 2.0 Credentials
GOOGLE_CLIENT_ID={creds.client_id}
GOOGLE_CLIENT_SECRET={creds.client_secret}
GMAIL_REFRESH_TOKEN={creds.refresh_token}
"""
        
        # Write to .env file (append if exists)
        try:
            with open('.env', 'a') as env_file:
                env_file.write(env_content)
            print("✅ Credentials added to .env file")
        except Exception as e:
            print(f"⚠️ Error writing to .env: {e}")
            print("Please manually add the above credentials to your .env file")
        
        # Test the credentials
        print("\n🧪 Testing API access...")
        test_apis(creds)
        
        return creds
    else:
        print("❌ Failed to obtain valid credentials")
        return None

def test_apis(creds):
    """Test access to all required APIs"""
    from googleapiclient.discovery import build
    
    services_to_test = [
        ('gmail', 'v1', 'Gmail'),
        ('calendar', 'v3', 'Calendar'),
        ('drive', 'v3', 'Drive'),
        ('people', 'v1', 'Contacts')
    ]
    
    for service_name, version, display_name in services_to_test:
        try:
            service = build(service_name, version, credentials=creds)
            
            # Simple test calls
            if service_name == 'gmail':
                service.users().getProfile(userId='me').execute()
            elif service_name == 'calendar':
                service.calendarList().list().execute()
            elif service_name == 'drive':
                service.files().list(pageSize=1).execute()
            elif service_name == 'people':
                service.people().connections().list(resourceName='people/me', pageSize=1).execute()
            
            print(f"✅ {display_name} API - OK")
            
        except Exception as e:
            print(f"❌ {display_name} API - Error: {e}")

if __name__ == "__main__":
    creds = setup_credentials()
    if creds:
        print("\n🎉 Setup complete!")
        print("Your agents should now be able to authenticate properly.")
        print("Run your test script again to verify everything works.")
    else:
        print("\n❌ Setup failed. Please check the errors above.")
