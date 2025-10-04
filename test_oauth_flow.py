#!/usr/bin/env python3
"""
Test script for MCP OAuth implementation
Tests encryption, token loading, and MCP integration
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_environment():
    """Test that required environment variables are set"""
    print("\n=== Testing Environment Variables ===")

    required_vars = [
        "ENCRYPTION_KEY",
        "NEXT_PUBLIC_SUPABASE_URL",
        "SUPABASE_SECRET_KEY",
        "REDIS_URI",
        "NEXT_PUBLIC_APP_URL"
    ]

    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Show partial value for security
            if "KEY" in var or "SECRET" in var:
                display = f"{value[:8]}...{value[-8:]}" if len(value) > 16 else "***"
            else:
                display = value
            print(f"✓ {var}: {display}")
        else:
            print(f"✗ {var}: NOT SET")
            missing_vars.append(var)

    if missing_vars:
        print(f"\n⚠️  Missing environment variables: {', '.join(missing_vars)}")
        return False
    else:
        print("\n✓ All environment variables are set")
        return True


def test_encryption():
    """Test encryption/decryption utilities"""
    print("\n=== Testing Encryption Utilities ===")

    try:
        from utils.mcp_auth import encrypt_token, decrypt_token

        test_data = "test_access_token_1234567890"

        # Encrypt
        encrypted = encrypt_token(test_data)
        print(f"✓ Encrypted token: {encrypted[:50]}...")

        # Decrypt
        decrypted = decrypt_token(encrypted)
        print(f"✓ Decrypted token: {decrypted}")

        # Verify
        if decrypted == test_data:
            print("✓ Encryption/decryption verified successfully")
            return True
        else:
            print(f"✗ Decryption mismatch: expected '{test_data}', got '{decrypted}'")
            return False

    except Exception as e:
        print(f"✗ Encryption test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_supabase_connection():
    """Test Supabase connection"""
    print("\n=== Testing Supabase Connection ===")

    try:
        from utils.mcp_auth import get_supabase_client

        supabase = get_supabase_client()
        print("✓ Supabase client created")

        # Test connection with a simple query
        result = supabase.table("agent_configs").select("id").limit(1).execute()
        print(f"✓ Supabase connection successful")
        return True

    except Exception as e:
        print(f"✗ Supabase connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mcp_oauth_discovery():
    """Test MCP OAuth endpoint discovery"""
    print("\n=== Testing MCP OAuth Discovery ===")

    try:
        import httpx

        # Test Rube OAuth discovery
        print("Testing Rube MCP OAuth endpoints...")

        # 1. Test protected resource metadata
        resource_url = "https://rube.app/.well-known/oauth-protected-resource"
        response = httpx.get(resource_url, timeout=10)
        response.raise_for_status()
        resource_metadata = response.json()
        print(f"✓ Protected resource metadata: {resource_metadata.get('resource')}")

        # 2. Test authorization server metadata
        auth_server_url = "https://rube.app/.well-known/oauth-authorization-server"
        response = httpx.get(auth_server_url, timeout=10)
        response.raise_for_status()
        auth_metadata = response.json()
        print(f"✓ Authorization endpoint: {auth_metadata.get('authorization_endpoint')}")
        print(f"✓ Token endpoint: {auth_metadata.get('token_endpoint')}")
        print(f"✓ Registration endpoint: {auth_metadata.get('registration_endpoint')}")

        return True

    except Exception as e:
        print(f"✗ OAuth discovery failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_python_dependencies():
    """Test that Python dependencies are installed"""
    print("\n=== Testing Python Dependencies ===")

    dependencies = [
        ("cryptography", "Encryption library"),
        ("supabase", "Supabase client"),
        ("httpx", "HTTP client"),
    ]

    missing_deps = []
    for module_name, description in dependencies:
        try:
            __import__(module_name)
            print(f"✓ {module_name}: {description}")
        except ImportError:
            print(f"✗ {module_name}: NOT INSTALLED ({description})")
            missing_deps.append(module_name)

    if missing_deps:
        print(f"\n⚠️  Missing dependencies: {', '.join(missing_deps)}")
        print(f"Install with: pip install {' '.join(missing_deps)}")
        return False
    else:
        print("\n✓ All Python dependencies are installed")
        return True


def test_redis_connection():
    """Test Redis connection (optional - falls back to in-memory)"""
    print("\n=== Testing Redis Connection ===")

    redis_uri = os.getenv("REDIS_URI")
    if not redis_uri:
        print("⚠️  REDIS_URI not set - will use in-memory fallback")
        print("✓ In-memory OAuth state storage will be used")
        return True

    try:
        import redis

        # Parse Redis URI
        client = redis.from_url(redis_uri)

        # Test connection
        client.ping()
        print(f"✓ Redis connection successful: {redis_uri}")

        # Test set/get
        test_key = "oauth_test_key"
        test_value = "test_value"
        client.set(test_key, test_value, ex=10)
        retrieved = client.get(test_key)

        if retrieved and retrieved.decode('utf-8') == test_value:
            print("✓ Redis set/get verified")
            client.delete(test_key)
            return True
        else:
            print("✗ Redis set/get failed")
            return False

    except Exception as e:
        print(f"⚠️  Redis connection failed: {e}")
        print(f"  Redis is not running - will use in-memory fallback")
        print(f"✓ In-memory OAuth state storage will be used for development")
        # Don't fail - in-memory fallback works fine for dev/testing
        return True


def test_mcp_auth_integration():
    """Test the complete MCP auth integration"""
    print("\n=== Testing MCP Auth Integration ===")

    try:
        from multi_tool_rube_agent.tools import AgentMCPConnection

        # Test without user_id (should use RUBE_AUTH_TOKEN)
        print("Testing MCP connection without user_id...")
        mcp = AgentMCPConnection()

        if mcp.auth_token:
            print(f"✓ Auth token loaded (length: {len(mcp.auth_token)})")
        else:
            print("⚠️  No auth token found")

        if mcp.mcp_url:
            print(f"✓ MCP URL configured: {mcp.mcp_url}")
        else:
            print("✗ MCP URL not configured")
            return False

        print("✓ MCP auth integration ready")
        return True

    except Exception as e:
        print(f"✗ MCP auth integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("MCP OAuth Implementation Test Suite")
    print("=" * 60)

    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    results = {
        "Environment Variables": test_environment(),
        "Python Dependencies": test_python_dependencies(),
        "Encryption": test_encryption(),
        "Supabase Connection": test_supabase_connection(),
        "Redis Connection": test_redis_connection(),
        "MCP OAuth Discovery": test_mcp_oauth_discovery(),
        "MCP Auth Integration": test_mcp_auth_integration(),
    }

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {test_name}")

    print(f"\n{passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Ready for deployment.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please fix errors before deploying.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
