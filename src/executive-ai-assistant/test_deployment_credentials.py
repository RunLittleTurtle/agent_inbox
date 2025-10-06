"""
End-to-End Deployment Credential Flow Test

Tests the complete credential flow:
1. Railway API health and connectivity
2. Supabase credential retrieval via CONFIG API
3. Gmail API authentication with fetched credentials
4. Email fetching capability

Usage:
    python test_deployment_credentials.py --user-id USER_ID --email EMAIL
"""
import asyncio
import os
import sys
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(env_path)


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_step(step_num, description):
    """Print a test step header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}[STEP {step_num}]{Colors.END} {description}")
    print("=" * 80)


def print_success(message):
    """Print a success message"""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")


def print_error(message):
    """Print an error message"""
    print(f"{Colors.RED}✗ {message}{Colors.END}")


def print_warning(message):
    """Print a warning message"""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")


def print_info(message):
    """Print an info message"""
    print(f"  {message}")


async def test_config_api_health(config_api_url):
    """Test 1: Check if Railway CONFIG API is accessible"""
    import httpx

    print_step(1, "Testing Railway CONFIG API Health")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{config_api_url}/health")

            if response.status_code == 200:
                data = response.json()
                print_success(f"Railway API is healthy")
                print_info(f"Service: {data.get('service')}")
                print_info(f"Version: {data.get('version')}")
                print_info(f"Supabase connected: {data.get('supabase_connected')}")

                if not data.get('supabase_connected'):
                    print_error("Supabase is NOT connected to Railway API!")
                    return False

                return True
            else:
                print_error(f"Railway API returned status {response.status_code}")
                return False

    except Exception as e:
        print_error(f"Failed to connect to Railway API: {e}")
        print_info(f"URL: {config_api_url}/health")
        return False


async def test_credential_retrieval(config_api_url, user_id):
    """Test 2: Retrieve credentials from Supabase via CONFIG API"""
    import httpx

    print_step(2, "Testing Credential Retrieval from Supabase")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{config_api_url}/api/config/values",
                params={"agent_id": "global", "user_id": user_id}
            )

            if response.status_code == 200:
                data = response.json()
                google_workspace = data.get("google_workspace", {})

                has_client_id = bool(google_workspace.get("google_client_id"))
                has_client_secret = bool(google_workspace.get("google_client_secret"))
                # Note: google_refresh_token is hidden from API response for security

                print_success(f"Retrieved config for user {user_id}")
                print_info(f"Has google_client_id: {has_client_id}")
                print_info(f"Has google_client_secret: {has_client_secret}")

                if not has_client_id or not has_client_secret:
                    print_warning("Missing Google OAuth credentials in Supabase!")
                    print_info("User needs to add credentials in config-app UI")
                    return None

                # Mask sensitive data
                client_id = google_workspace.get("google_client_id", "")
                client_secret = google_workspace.get("google_client_secret", "")

                print_info(f"Client ID: {client_id[:20]}..." if len(client_id) > 20 else f"Client ID: {client_id}")
                print_info(f"Client Secret: {client_secret[:10]}..." if len(client_secret) > 10 else "No secret")

                return google_workspace
            else:
                print_error(f"API returned status {response.status_code}")
                print_info(f"Response: {response.text[:200]}")
                return None

    except Exception as e:
        print_error(f"Failed to retrieve credentials: {e}")
        import traceback
        print_info(traceback.format_exc()[:500])
        return None


async def test_gmail_authentication(user_email, config):
    """Test 3: Authenticate with Gmail API using retrieved credentials"""
    from eaia.gmail import get_credentials
    from googleapiclient.discovery import build

    print_step(3, "Testing Gmail API Authentication")

    try:
        # Simulate LangGraph config structure
        mock_config = {
            "configurable": config.get("configurable", {}),
            "metadata": config.get("metadata", {})
        }

        print_info(f"Attempting authentication for {user_email}...")
        creds = await get_credentials(user_email, config=mock_config)

        if not creds:
            print_error("Failed to get credentials")
            return False

        print_success("Credentials obtained successfully")
        print_info(f"Token URI: {creds.token_uri}")
        print_info(f"Has refresh token: {bool(creds.refresh_token)}")
        print_info(f"Scopes: {', '.join(creds.scopes) if creds.scopes else 'None'}")

        # Try to build Gmail service
        print_info("Building Gmail API service...")
        service = await asyncio.to_thread(build, "gmail", "v1", credentials=creds)

        print_success("Gmail API service created successfully")
        return True

    except Exception as e:
        print_error(f"Gmail authentication failed: {e}")
        import traceback
        print_info(traceback.format_exc()[:500])
        return False


async def test_email_fetching(user_email, config):
    """Test 4: Fetch emails using Gmail API"""
    from eaia.gmail import fetch_group_emails

    print_step(4, "Testing Email Fetching")

    try:
        # Simulate LangGraph config structure
        mock_config = {
            "configurable": config.get("configurable", {}),
            "metadata": config.get("metadata", {})
        }

        print_info(f"Fetching emails from last 24 hours for {user_email}...")

        email_count = 0
        async for email_data in fetch_group_emails(
            user_email,
            minutes_since=1440,  # 24 hours
            config=mock_config
        ):
            email_count += 1
            if email_count <= 3:
                from_email = email_data.get('from_email', 'N/A')
                subject = email_data.get('subject', 'N/A')
                print_info(f"Email {email_count}: From: {from_email[:40]}, Subject: {subject[:50]}")

        print_success(f"Successfully fetched {email_count} emails")

        if email_count == 0:
            print_warning("No emails found in the last 24 hours")
            print_info("This is normal if the inbox is empty or all emails are older")

        return True

    except Exception as e:
        print_error(f"Email fetching failed: {e}")
        import traceback
        print_info(traceback.format_exc()[:500])
        return False


async def run_all_tests(user_id, user_email, config_api_url):
    """Run all tests in sequence"""

    print(f"\n{Colors.BOLD}{'=' * 80}")
    print(f"Executive AI Assistant - Deployment Credential Flow Test")
    print(f"{'=' * 80}{Colors.END}\n")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"CONFIG_API_URL: {config_api_url}")
    print(f"User ID: {user_id}")
    print(f"Email: {user_email}")

    results = {}

    # Test 1: API Health
    results['api_health'] = await test_config_api_health(config_api_url)
    if not results['api_health']:
        print_error("\n⚠ Cannot proceed - Railway API is not accessible")
        return results

    # Test 2: Credential Retrieval
    credentials = await test_credential_retrieval(config_api_url, user_id)
    results['credential_retrieval'] = credentials is not None
    if not credentials:
        print_error("\n⚠ Cannot proceed - Failed to retrieve credentials")
        print_info("Make sure the user has added Google credentials in config-app")
        return results

    # Build config for subsequent tests
    config = {
        "configurable": {"user_id": user_id},
        "metadata": {"user_id": user_id, "clerk_user_id": user_id}
    }

    # Test 3: Gmail Authentication
    results['gmail_auth'] = await test_gmail_authentication(user_email, config)
    if not results['gmail_auth']:
        print_error("\n⚠ Cannot proceed - Gmail authentication failed")
        return results

    # Test 4: Email Fetching
    results['email_fetching'] = await test_email_fetching(user_email, config)

    # Summary
    print(f"\n{Colors.BOLD}{'=' * 80}")
    print("Test Summary")
    print(f"{'=' * 80}{Colors.END}\n")

    total_tests = len(results)
    passed_tests = sum(1 for r in results.values() if r)

    for test_name, result in results.items():
        status = f"{Colors.GREEN}PASS{Colors.END}" if result else f"{Colors.RED}FAIL{Colors.END}"
        print(f"{test_name.replace('_', ' ').title()}: {status}")

    print(f"\n{Colors.BOLD}Result: {passed_tests}/{total_tests} tests passed{Colors.END}")

    if passed_tests == total_tests:
        print_success("\n✓ All tests passed! Deployment credential flow is working correctly.")
    else:
        print_error("\n✗ Some tests failed. Review the output above for details.")

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Test executive-ai-assistant deployment credential flow"
    )
    parser.add_argument(
        "--user-id",
        type=str,
        default="user_2rUmCuJKMHSBiPjj4zBB88cxLhE",
        help="Clerk user ID (default: test user)"
    )
    parser.add_argument(
        "--email",
        type=str,
        default="info@800m.ca",
        help="Email address to test (default: info@800m.ca)"
    )
    parser.add_argument(
        "--config-api-url",
        type=str,
        default=None,
        help="CONFIG_API_URL (defaults to environment variable or Railway production)"
    )

    args = parser.parse_args()

    # Determine CONFIG_API_URL
    config_api_url = args.config_api_url or os.getenv(
        "CONFIG_API_URL",
        "https://agentinbox-production.up.railway.app"
    )

    # Run tests
    try:
        results = asyncio.run(run_all_tests(args.user_id, args.email, config_api_url))

        # Exit with appropriate code
        all_passed = all(results.values())
        sys.exit(0 if all_passed else 1)

    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Test interrupted by user{Colors.END}")
        sys.exit(130)


if __name__ == "__main__":
    main()
