#!/usr/bin/env python3
"""
CONFIG_API_URL Verification Helper

Quick utility to verify that CONFIG_API_URL is properly configured
and that the agent can reach the Railway FastAPI bridge.

Usage:
    python verify_config_api.py
    python verify_config_api.py --url https://custom-url.railway.app
"""
import os
import sys
import asyncio
import argparse
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(env_path)


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


async def verify_config_api(url=None):
    """Verify CONFIG_API_URL connectivity and configuration"""

    # Determine URL
    if url:
        config_api_url = url
        print(f"{Colors.BLUE}Using provided URL: {config_api_url}{Colors.END}\n")
    else:
        config_api_url = os.getenv("CONFIG_API_URL")
        if config_api_url:
            print(f"{Colors.GREEN}✓ CONFIG_API_URL environment variable is set{Colors.END}")
            print(f"  Value: {config_api_url}\n")
        else:
            print(f"{Colors.YELLOW}⚠ CONFIG_API_URL is NOT set in environment{Colors.END}")
            print(f"  Will use default: http://localhost:8000")
            print(f"  For production, set: export CONFIG_API_URL=https://your-railway-url.app\n")
            config_api_url = "http://localhost:8000"

    # Test connectivity
    import httpx

    print(f"{Colors.BOLD}Testing connectivity to CONFIG API...{Colors.END}")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test health endpoint
            print(f"  Checking {config_api_url}/health ...")
            response = await client.get(f"{config_api_url}/health")

            if response.status_code == 200:
                print(f"{Colors.GREEN}✓ Health check passed{Colors.END}")

                data = response.json()
                print(f"\n{Colors.BOLD}API Information:{Colors.END}")
                print(f"  Service: {data.get('service')}")
                print(f"  Status: {data.get('status')}")
                print(f"  Version: {data.get('version')}")
                print(f"  Supabase Connected: {data.get('supabase_connected')}")

                if not data.get('supabase_connected'):
                    print(f"\n{Colors.RED}✗ ISSUE: Supabase is NOT connected!{Colors.END}")
                    print(f"  The API cannot fetch credentials from the database.")
                    print(f"  Check Railway environment variables:")
                    print(f"    - NEXT_PUBLIC_SUPABASE_URL")
                    print(f"    - SUPABASE_SECRET_KEY")
                    return False

                # Test schemas endpoint
                print(f"\n{Colors.BOLD}Testing API endpoints...{Colors.END}")
                print(f"  Checking /api/config/schemas ...")
                schemas_response = await client.get(f"{config_api_url}/api/config/schemas")

                if schemas_response.status_code == 200:
                    print(f"{Colors.GREEN}✓ Schemas endpoint working{Colors.END}")
                    schemas_data = schemas_response.json()
                    agent_count = len(schemas_data.get('agents', []))
                    print(f"  Found {agent_count} agent configurations")
                else:
                    print(f"{Colors.YELLOW}⚠ Schemas endpoint returned {schemas_response.status_code}{Colors.END}")

                print(f"\n{Colors.GREEN}{Colors.BOLD}✓ CONFIG API is properly configured and accessible!{Colors.END}")
                return True

            else:
                print(f"{Colors.RED}✗ Health check failed: Status {response.status_code}{Colors.END}")
                print(f"  Response: {response.text[:200]}")
                return False

    except httpx.TimeoutException:
        print(f"{Colors.RED}✗ Connection timed out{Colors.END}")
        print(f"  The API at {config_api_url} is not responding.")
        print(f"  Check that the URL is correct and the service is running.")
        return False

    except httpx.ConnectError as e:
        print(f"{Colors.RED}✗ Connection failed: {e}{Colors.END}")
        print(f"  Cannot connect to {config_api_url}")
        print(f"  Possible issues:")
        print(f"    - URL is incorrect")
        print(f"    - Service is not running")
        print(f"    - Firewall/network issue")
        return False

    except Exception as e:
        print(f"{Colors.RED}✗ Unexpected error: {e}{Colors.END}")
        import traceback
        print(f"  {traceback.format_exc()[:300]}")
        return False


def print_recommendations():
    """Print configuration recommendations"""

    print(f"\n{Colors.BOLD}Configuration Recommendations:{Colors.END}\n")

    print(f"{Colors.BLUE}For Local Development:{Colors.END}")
    print(f"  export CONFIG_API_URL=http://localhost:8000")
    print(f"  # Start FastAPI: cd src/config_api && uvicorn main:app --reload")

    print(f"\n{Colors.BLUE}For Production (Railway):{Colors.END}")
    print(f"  export CONFIG_API_URL=https://agentinbox-production.up.railway.app")

    print(f"\n{Colors.BLUE}For LangGraph Cloud Deployment:{Colors.END}")
    print(f"  1. Navigate to your deployment settings")
    print(f"  2. Add environment variable:")
    print(f"     Key: CONFIG_API_URL")
    print(f"     Value: https://agentinbox-production.up.railway.app")
    print(f"  3. Redeploy your agent")

    print(f"\n{Colors.BLUE}To test with your credentials:{Colors.END}")
    print(f"  python test_deployment_credentials.py --user-id YOUR_USER_ID --email YOUR_EMAIL")


def main():
    parser = argparse.ArgumentParser(
        description="Verify CONFIG_API_URL configuration"
    )
    parser.add_argument(
        "--url",
        type=str,
        default=None,
        help="Custom CONFIG_API_URL to test (overrides environment variable)"
    )

    args = parser.parse_args()

    print(f"\n{Colors.BOLD}{'=' * 80}")
    print(f"CONFIG_API_URL Verification")
    print(f"{'=' * 80}{Colors.END}\n")

    try:
        result = asyncio.run(verify_config_api(args.url))

        if not result:
            print_recommendations()

        sys.exit(0 if result else 1)

    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Verification interrupted by user{Colors.END}")
        sys.exit(130)


if __name__ == "__main__":
    main()
