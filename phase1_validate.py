#!/usr/bin/env python3
"""
Phase 1 Validation: Test Supabase config loading for MCP URLs
Tests database queries with real user data to validate MCP configuration loading
"""
import os
import asyncio
import json
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

def get_supabase_client() -> Client:
    """Get Supabase client with service role key"""
    supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SECRET_KEY")

    if not supabase_url or not supabase_key:
        raise ValueError("Missing Supabase credentials in .env")

    return create_client(supabase_url, supabase_key)


def find_user_by_email(email: str):
    """Find user ID (clerk_id) by email address"""
    print(f"\n{'='*80}")
    print(f"🔍 Searching for user: {email}")
    print(f"{'='*80}")

    supabase = get_supabase_client()

    # Try user_secrets table first (most likely to have email)
    try:
        print(f"\n📋 Checking user_secrets table")
        result = supabase.table("user_secrets").select("*").execute()

        if result.data:
            print(f"   ✅ Found {len(result.data)} user records")
            print(f"   Columns: {list(result.data[0].keys())}")

            # Look for matching email
            for row in result.data:
                row_email = row.get("email") or row.get("user_email")
                if row_email and row_email.lower() == email.lower():
                    clerk_id = row.get("clerk_id")
                    print(f"\n   🎯 MATCH FOUND!")
                    print(f"   Email: {row_email}")
                    print(f"   Clerk ID: {clerk_id}")
                    return clerk_id
        else:
            print(f"   ⚠️  Table empty")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    return None


def inspect_agent_configs():
    """Inspect the agent_configs table"""
    print(f"\n{'='*80}")
    print(f"📊 Inspecting agent_configs table")
    print(f"{'='*80}")

    supabase = get_supabase_client()

    try:
        result = supabase.table("agent_configs").select("*").execute()

        if result.data:
            print(f"\n✅ Found {len(result.data)} agent configs")

            for i, config in enumerate(result.data, 1):
                print(f"\n--- Config {i} ---")
                print(f"Clerk ID: {config.get('clerk_id')}")
                print(f"Agent ID: {config.get('agent_id')}")

                config_data = config.get('config_data')
                if config_data and isinstance(config_data, dict):
                    mcp_integration = config_data.get('mcp_integration', {})
                    mcp_url = mcp_integration.get('mcp_server_url')
                    if mcp_url:
                        print(f"  ✅ MCP URL: {mcp_url[:60]}...")
                    else:
                        print(f"  ⚠️  No MCP URL configured")
        else:
            print("⚠️  No agent configs found")

    except Exception as e:
        print(f"❌ Error: {e}")


def test_config_query(clerk_id: str, agent_id: str):
    """Test the exact query from config_utils.py"""
    print(f"\n{'='*80}")
    print(f"🧪 Testing config query")
    print(f"   User: {clerk_id}")
    print(f"   Agent: {agent_id}")
    print(f"{'='*80}")

    supabase = get_supabase_client()

    try:
        # Exact query from config_utils.py:68-73
        result = supabase.table("agent_configs")\
            .select("config_data")\
            .eq("clerk_id", clerk_id)\
            .eq("agent_id", agent_id)\
            .maybe_single()\
            .execute()

        if result.data:
            config_data = result.data.get("config_data")
            print(f"\n✅ Config loaded!")

            if isinstance(config_data, dict):
                mcp_integration = config_data.get("mcp_integration", {})
                mcp_url = mcp_integration.get("mcp_server_url")
                print(f"   MCP URL: {mcp_url if mcp_url else '❌ Not configured'}")
                return mcp_url
            else:
                print(f"   ⚠️  config_data is not a dict")
        else:
            print(f"\n⚠️  No config found for this user/agent")

        return None

    except Exception as e:
        print(f"\n❌ Query error: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_config_api(user_id: str, agent_id: str):
    """Test CONFIG API endpoint (Railway)"""
    print(f"\n{'='*80}")
    print(f"🌐 Testing CONFIG API")
    print(f"{'='*80}")

    import httpx

    railway_url = os.getenv("RAILWAY_URL", "agentinbox-production.up.railway.app")
    api_url = f"https://{railway_url}"

    print(f"\n📡 API URL: {api_url}")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{api_url}/api/config/values",
                params={"agent_id": agent_id, "user_id": user_id}
            )

            print(f"   Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success!")
                values = data.get("values", {})
                print(f"   Config sections: {list(values.keys())}")
                return data
            else:
                print(f"   ❌ Failed: {response.text[:200]}")

    except Exception as e:
        print(f"   ❌ Error: {e}")

    return None


def main():
    """Run Phase 1 validation"""
    print("\n" + "="*80)
    print("🚀 PHASE 1 VALIDATION: Supabase MCP Config Testing")
    print("="*80)

    # Test users
    test_emails = [
        "info@800m.ca",  # Should have MCP configs
        "samuel.audette1@gmail.com"  # Should NOT have MCP configs
    ]

    # Step 1: Find user IDs
    print("\n\n" + "="*80)
    print("STEP 1: Finding User IDs")
    print("="*80)

    user_mapping = {}
    for email in test_emails:
        clerk_id = find_user_by_email(email)
        if clerk_id:
            user_mapping[email] = clerk_id

    print(f"\n\n📝 USER MAPPING:")
    for email, clerk_id in user_mapping.items():
        print(f"   {email:30s} → {clerk_id}")

    # Step 2: Inspect agent_configs
    print("\n\n" + "="*80)
    print("STEP 2: Inspecting agent_configs Table")
    print("="*80)
    inspect_agent_configs()

    # Step 3: Test config queries
    print("\n\n" + "="*80)
    print("STEP 3: Testing Config Queries")
    print("="*80)

    results = {}
    for email, clerk_id in user_mapping.items():
        print(f"\n\n--- Testing: {email} ---")
        results[email] = {}

        for agent_id in ["calendar_agent", "multi_tool_rube_agent"]:
            mcp_url = test_config_query(clerk_id, agent_id)
            results[email][agent_id] = mcp_url

    # Step 4: Test CONFIG API
    if user_mapping:
        print("\n\n" + "="*80)
        print("STEP 4: Testing CONFIG API")
        print("="*80)

        email = list(user_mapping.keys())[0]
        clerk_id = user_mapping[email]
        asyncio.run(test_config_api(clerk_id, "calendar_agent"))

    # Summary
    print("\n\n" + "="*80)
    print("📊 PHASE 1 VALIDATION SUMMARY")
    print("="*80)

    for email, agents in results.items():
        print(f"\n{email}:")
        for agent_id, mcp_url in agents.items():
            status = "✅ HAS MCP" if mcp_url else "⚠️  NO MCP"
            print(f"   {agent_id:25s}: {status}")

    print("\n" + "="*80)
    print("✅ Phase 1 Complete!")
    print("="*80)


if __name__ == "__main__":
    main()
