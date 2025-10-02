"""
Test if Supabase credentials work with LangGraph Platform config flow.
This simulates how the deployed agent fetches credentials.
"""
import asyncio
import os

async def test_platform_flow():
    from eaia.gmail import fetch_group_emails
    
    # Simulate LangGraph Platform config (how it's passed in production)
    mock_config = {
        "configurable": {
            "user_id": "user_2rUmCuJKMHSBiPjj4zBB88cxLhE"
        }
    }
    
    email = "info@800m.ca"
    
    print("=" * 80)
    print("Testing Gmail with SUPABASE credentials (Platform simulation)")
    print("=" * 80)
    print(f"User ID: {mock_config['configurable']['user_id']}")
    print(f"Email: {email}")
    print()
    
    try:
        count = 0
        async for email_data in fetch_group_emails(
            email, 
            minutes_since=10080,  # 7 days
            config=mock_config  # ✅ Pass config to force Supabase fetch
        ):
            count += 1
            if count <= 3:
                print(f"📧 Email {count}:")
                print(f"   From: {email_data.get('from_email', 'N/A')[:50]}")
                print(f"   Subject: {email_data.get('subject', 'N/A')[:60]}")
        
        print(f"\n✅ SUCCESS! Supabase credentials work! Found {count} emails")
        
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test_platform_flow())
