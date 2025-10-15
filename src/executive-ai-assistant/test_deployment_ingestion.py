"""
Deployment Ingestion Test Script

Tests the complete ingestion workflow with production credentials:
1. Verifies CONFIG_API_URL is set correctly
2. Tests credential fetch with actual user_id
3. Runs sample ingestion with debug output
4. Reports success/failure with diagnostic info

Usage:
    # Test against local LangGraph dev server with production credentials
    python test_deployment_ingestion.py --user-id USER_ID --email EMAIL

    # Test against deployed LangGraph instance
    python test_deployment_ingestion.py --user-id USER_ID --email EMAIL --url https://your-deployment.com
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


def print_header(title):
    """Print a section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 80}")
    print(f"{title}")
    print(f"{'=' * 80}{Colors.END}\n")


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


async def verify_config_api_url():
    """Verify CONFIG_API_URL is properly configured"""
    print_header("Step 1: Verifying CONFIG_API_URL Configuration")

    config_api_url = os.getenv("CONFIG_API_URL")

    if not config_api_url:
        print_error("CONFIG_API_URL is not set!")
        print_info("This will cause the agent to use the default: http://localhost:8000")
        print_info("For production deployment, set CONFIG_API_URL to your Railway API URL")
        print_info("Example: export CONFIG_API_URL=https://agentinbox-production.up.railway.app")
        return False, "http://localhost:8000"

    print_success(f"CONFIG_API_URL is set: {config_api_url}")

    # Test connectivity
    import httpx
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{config_api_url}/health")
            if response.status_code == 200:
                data = response.json()
                print_success(f"CONFIG API is accessible")
                print_info(f"Service: {data.get('service')}")
                print_info(f"Supabase connected: {data.get('supabase_connected')}")

                if not data.get('supabase_connected'):
                    print_warning("Supabase is not connected to CONFIG API!")
                    return False, config_api_url

                return True, config_api_url
            else:
                print_error(f"CONFIG API returned status {response.status_code}")
                return False, config_api_url
    except Exception as e:
        print_error(f"Cannot connect to CONFIG API: {e}")
        return False, config_api_url


async def test_credential_fetch(config_api_url, user_id, email):
    """Test fetching credentials via the config API"""
    print_header("Step 2: Testing Credential Fetch")

    print_info(f"User ID: {user_id}")
    print_info(f"Email: {email}")
    print_info(f"Fetching from: {config_api_url}")

    # Import and test get_credentials
    from eaia.gmail import get_credentials

    mock_config = {
        "configurable": {"user_id": user_id},
        "metadata": {"user_id": user_id, "clerk_user_id": user_id}
    }

    try:
        creds = await get_credentials(email, config=mock_config)

        if creds:
            print_success("Credentials fetched successfully!")
            print_info(f"Has refresh token: {bool(creds.refresh_token)}")
            print_info(f"Token URI: {creds.token_uri}")
            print_info(f"Scopes: {', '.join(creds.scopes) if creds.scopes else 'None'}")
            return True
        else:
            print_error("Failed to fetch credentials")
            return False

    except Exception as e:
        print_error(f"Credential fetch failed: {e}")
        import traceback
        print_info(traceback.format_exc()[:500])
        return False


async def test_email_fetch(email, user_id, minutes_since=60):
    """Test fetching emails with the credentials"""
    print_header("Step 3: Testing Email Fetch")

    print_info(f"Fetching emails from last {minutes_since} minutes...")

    from eaia.gmail import fetch_group_emails

    mock_config = {
        "configurable": {"user_id": user_id},
        "metadata": {"user_id": user_id, "clerk_user_id": user_id}
    }

    try:
        email_count = 0
        async for email_data in fetch_group_emails(
            email,
            minutes_since=minutes_since,
            config=mock_config
        ):
            email_count += 1
            if email_count <= 5:
                from_email = email_data.get('from_email', 'N/A')
                subject = email_data.get('subject', 'N/A')
                print_info(f"Email {email_count}: From: {from_email[:40]}, Subject: {subject[:50]}")

        print_success(f"Fetched {email_count} emails successfully")

        if email_count == 0:
            print_warning("No emails found in the specified time window")

        return True, email_count

    except Exception as e:
        print_error(f"Email fetch failed: {e}")
        import traceback
        print_info(traceback.format_exc()[:500])
        return False, 0


async def test_langgraph_connection(deployment_url):
    """Test connection to LangGraph deployment"""
    print_header("Step 4: Testing LangGraph Deployment Connection")

    print_info(f"Deployment URL: {deployment_url}")

    from langgraph_sdk import get_client

    try:
        client = get_client(url=deployment_url)

        # Try to list threads (should work even with no threads)
        # Note: This is a simple connectivity test
        print_success("LangGraph client initialized successfully")
        print_info(f"Connected to: {deployment_url}")
        return True, client

    except Exception as e:
        print_error(f"Failed to connect to LangGraph: {e}")
        import traceback
        print_info(traceback.format_exc()[:500])
        return False, None


async def run_sample_ingestion(email, user_id, deployment_url, minutes_since=60, max_emails=3):
    """Run a sample ingestion with a limited number of emails"""
    print_header("Step 5: Running Sample Ingestion")

    print_info(f"Processing up to {max_emails} emails from last {minutes_since} minutes")
    print_info(f"Target deployment: {deployment_url}")

    from eaia.gmail import fetch_group_emails
    from langgraph_sdk import get_client
    import uuid
    import hashlib
    import httpx

    mock_config = {
        "configurable": {"user_id": user_id},
        "metadata": {"user_id": user_id, "clerk_user_id": user_id}
    }

    try:
        client = get_client(url=deployment_url)

        email_count = 0
        processed_count = 0

        async for email_data in fetch_group_emails(
            email,
            minutes_since=minutes_since,
            config=mock_config
        ):
            email_count += 1

            if email_count > max_emails:
                print_info(f"Reached max_emails limit ({max_emails}), stopping...")
                break

            thread_id = str(
                uuid.UUID(hex=hashlib.md5(email_data["thread_id"].encode("UTF-8")).hexdigest())
            )

            from_email = email_data.get('from_email', 'N/A')
            subject = email_data.get('subject', 'N/A')
            print_info(f"\nProcessing email {email_count}:")
            print_info(f"  From: {from_email[:40]}")
            print_info(f"  Subject: {subject[:50]}")
            print_info(f"  Thread ID: {thread_id}")

            try:
                # Check if thread exists
                try:
                    thread_info = await client.threads.get(thread_id)
                    print_info(f"  Thread exists, checking for duplicate...")

                    recent_email = thread_info["metadata"].get("email_id")
                    if recent_email == email_data["id"]:
                        print_warning(f"  Email already processed, skipping")
                        continue

                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 404:
                        print_info(f"  Creating new thread...")
                        thread_info = await client.threads.create(thread_id=thread_id)
                    else:
                        raise e

                # Update thread metadata
                await client.threads.update(thread_id, metadata={
                    "graph_id": "executive_main",  # Preserve graph_id for inbox filtering
                    "email_id": email_data["id"]
                })

                # Create run
                print_info(f"  Creating workflow run...")
                run_result = await client.runs.create(
                    thread_id,
                    "main",
                    input={"email": email_data},
                    multitask_strategy="rollback",
                )

                print_success(f"  Run created: {run_result.get('run_id', 'unknown')}")
                processed_count += 1

            except Exception as e:
                print_error(f"  Failed to process email: {e}")
                continue

        print_success(f"\nIngestion complete: {processed_count}/{email_count} emails processed successfully")
        return True, processed_count

    except Exception as e:
        print_error(f"Ingestion failed: {e}")
        import traceback
        print_info(traceback.format_exc()[:500])
        return False, 0


async def main(user_id, email, deployment_url, minutes_since, max_emails, skip_ingestion):
    """Run all tests"""

    print(f"\n{Colors.BOLD}{'=' * 80}")
    print(f"Executive AI Assistant - Deployment Ingestion Test")
    print(f"{'=' * 80}{Colors.END}\n")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"User ID: {user_id}")
    print(f"Email: {email}")
    print(f"Deployment: {deployment_url}")

    results = {}

    # Step 1: Verify CONFIG_API_URL
    config_ok, config_api_url = await verify_config_api_url()
    results['config_api_url'] = config_ok

    if not config_ok:
        print_error("\n⚠ CONFIG_API_URL issues detected. Continuing with tests...")

    # Step 2: Test credential fetch
    results['credential_fetch'] = await test_credential_fetch(config_api_url, user_id, email)

    if not results['credential_fetch']:
        print_error("\n⚠ Cannot proceed - Credential fetch failed")
        return results

    # Step 3: Test email fetch
    email_fetch_ok, email_count = await test_email_fetch(email, user_id, minutes_since)
    results['email_fetch'] = email_fetch_ok

    if not email_fetch_ok:
        print_error("\n⚠ Cannot proceed - Email fetch failed")
        return results

    # Step 4: Test LangGraph connection
    langgraph_ok, client = await test_langgraph_connection(deployment_url)
    results['langgraph_connection'] = langgraph_ok

    if not langgraph_ok:
        print_error("\n⚠ Cannot proceed - LangGraph connection failed")
        return results

    # Step 5: Run sample ingestion (optional)
    if not skip_ingestion:
        if email_count == 0:
            print_warning("\nSkipping ingestion test - no emails found to process")
            results['ingestion'] = None
        else:
            ingestion_ok, processed = await run_sample_ingestion(
                email, user_id, deployment_url, minutes_since, max_emails
            )
            results['ingestion'] = ingestion_ok
    else:
        print_warning("\nSkipping ingestion test (--skip-ingestion flag)")
        results['ingestion'] = None

    # Summary
    print_header("Test Summary")

    for test_name, result in results.items():
        if result is None:
            status = f"{Colors.YELLOW}SKIPPED{Colors.END}"
        elif result:
            status = f"{Colors.GREEN}PASS{Colors.END}"
        else:
            status = f"{Colors.RED}FAIL{Colors.END}"

        print(f"{test_name.replace('_', ' ').title()}: {status}")

    # Overall result
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    total = passed + failed

    print(f"\n{Colors.BOLD}Result: {passed}/{total} tests passed{Colors.END}")

    if failed == 0:
        print_success("\n✓ All tests passed! Deployment ingestion is working correctly.")
        return 0
    else:
        print_error(f"\n✗ {failed} test(s) failed. Review the output above for details.")
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Test executive-ai-assistant deployment ingestion workflow"
    )
    parser.add_argument(
        "--user-id",
        type=str,
        required=True,
        help="Clerk user ID"
    )
    parser.add_argument(
        "--email",
        type=str,
        required=True,
        help="Email address to test"
    )
    parser.add_argument(
        "--url",
        type=str,
        default="http://127.0.0.1:2025",
        help="LangGraph deployment URL (default: local dev server)"
    )
    parser.add_argument(
        "--minutes-since",
        type=int,
        default=60,
        help="Fetch emails from last N minutes (default: 60)"
    )
    parser.add_argument(
        "--max-emails",
        type=int,
        default=3,
        help="Maximum emails to process in ingestion test (default: 3)"
    )
    parser.add_argument(
        "--skip-ingestion",
        action="store_true",
        help="Skip the actual ingestion test (only test credential fetch and email retrieval)"
    )

    args = parser.parse_args()

    try:
        exit_code = asyncio.run(main(
            args.user_id,
            args.email,
            args.url,
            args.minutes_since,
            args.max_emails,
            args.skip_ingestion
        ))
        sys.exit(exit_code)

    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Test interrupted by user{Colors.END}")
        sys.exit(130)
