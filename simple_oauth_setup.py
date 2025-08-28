#!/usr/bin/env python3
"""
Simple OAuth 2.0 Setup for Google Workspace APIs
Direct approach without cached tokens
"""

import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import json

# Minimal essential scopes
SCOPES = [
    # Gmail - Read and SEND emails
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',  # 🔑 CRITICAL: Need this for sending emails
    
    # Other APIs - readonly access
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/contacts.readonly',
]

def fresh_oauth_setup():
    """Setup OAuth with completely fresh credentials"""
    
    print("🚀 Simple Google OAuth Setup")
    print("=" * 40)
    
    if not os.path.exists('credentials.json'):
        print("❌ credentials.json not found")
        return None
    
    print("✅ credentials.json found")
    print("🌐 Starting fresh OAuth flow...")
    
    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', 
            SCOPES,
            redirect_uri='http://localhost:8080'
        )
        
        # Run the OAuth flow
        creds = flow.run_local_server(
            port=8080,
            prompt='consent',  # Force fresh consent
            access_type='offline'
        )
        
        print("✅ OAuth completed successfully!")
        
        # Save credentials
        with open('fresh_token.pickle', 'wb') as token:
            pickle.dump(creds, token)
        
        print("💾 Token saved to fresh_token.pickle")
        
        # Test basic API access
        print("\n🧪 Testing API access...")
        test_basic_apis(creds)
        
        # Extract for .env
        print_env_vars(creds)
        
        return creds
        
    except Exception as e:
        print(f"❌ OAuth failed: {e}")
        return None

def test_basic_apis(creds):
    """Test basic API access"""
    
    services = [
        ('gmail', 'v1'),
        ('calendar', 'v3'), 
        ('drive', 'v3'),
        ('people', 'v1')
    ]
    
    for service_name, version in services:
        try:
            service = build(service_name, version, credentials=creds)
            
            # Simple test calls
            if service_name == 'gmail':
                result = service.users().getProfile(userId='me').execute()
                print(f"✅ Gmail API - Email: {result.get('emailAddress', 'N/A')}")
                
            elif service_name == 'calendar':
                result = service.calendarList().list(maxResults=1).execute()
                calendars = result.get('items', [])
                print(f"✅ Calendar API - Found {len(calendars)} calendar(s)")
                
            elif service_name == 'drive':
                result = service.files().list(pageSize=1).execute()
                files = result.get('files', [])
                print(f"✅ Drive API - Found {len(files)} file(s)")
                
            elif service_name == 'people':
                result = service.people().connections().list(
                    resourceName='people/me', 
                    pageSize=1
                ).execute()
                contacts = result.get('connections', [])
                print(f"✅ Contacts API - Found {len(contacts)} contact(s)")
                
        except Exception as e:
            print(f"❌ {service_name} API failed: {e}")

def print_env_vars(creds):
    """Print environment variables for .env file"""
    
    print("\n🔑 Add these to your .env file:")
    print("=" * 40)
    print(f"GOOGLE_CLIENT_ID={creds.client_id}")
    print(f"GOOGLE_CLIENT_SECRET={creds.client_secret}")  
    print(f"GMAIL_REFRESH_TOKEN={creds.refresh_token}")
    
    # Try to append to .env
    try:
        with open('.env', 'r') as f:
            env_content = f.read()
        
        # Remove existing Google entries
        lines = []
        for line in env_content.split('\n'):
            if not any(key in line for key in ['GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET', 'GMAIL_REFRESH_TOKEN']):
                lines.append(line)
        
        # Add new entries
        lines.extend([
            '',
            '# Google Workspace OAuth Credentials (Fresh)',
            f'GOOGLE_CLIENT_ID={creds.client_id}',
            f'GOOGLE_CLIENT_SECRET={creds.client_secret}',
            f'GMAIL_REFRESH_TOKEN={creds.refresh_token}',
            ''
        ])
        
        with open('.env', 'w') as f:
            f.write('\n'.join(lines))
            
        print("✅ .env file updated with fresh credentials")
        
    except Exception as e:
        print(f"⚠️ Could not update .env: {e}")
        print("Please manually add the above credentials to your .env file")

if __name__ == "__main__":
    creds = fresh_oauth_setup()
    if creds:
        print("\n🎉 OAuth setup complete!")
        print("Your Google Workspace APIs are now properly authenticated.")
    else:
        print("\n❌ OAuth setup failed")
