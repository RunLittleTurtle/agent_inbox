"""
Google OAuth Token Management - Simple & Direct
Fetches Google refresh_token from Supabase following OAuth 2.0 best practices.

This module uses the same pattern as MCP OAuth (utils/mcp_auth.py) but simpler:
- No encryption needed (Supabase RLS protects tokens)
- Only refresh_token required (OAuth 2.0 best practice)
- Google client credentials from .env (shared across users)
"""
import os
import logging
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def get_supabase_client():
    """Get Supabase client"""
    from supabase import create_client

    url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    key = os.getenv("SUPABASE_SECRET_KEY")

    if not url or not key:
        raise ValueError("NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SECRET_KEY required")

    return create_client(url, key)


async def load_google_credentials(user_id: str) -> Optional[str]:
    """
    Load Google refresh_token from Supabase - Simple & Direct!

    Following OAuth 2.0 best practices:
    - Only refresh_token is stored per-user
    - Access tokens auto-refresh via google-auth library
    - Client ID/secret from .env (shared OAuth app)

    Args:
        user_id: Clerk user ID

    Returns:
        Google refresh_token string, or None if not found
    """
    try:
        supabase = get_supabase_client()

        logger.info(f"[Google OAuth] Loading refresh_token for user: {user_id}")

        # Fetch refresh_token from Supabase (same pattern as MCP auth)
        result = supabase.table("user_secrets") \
            .select("google_refresh_token") \
            .eq("clerk_id", user_id) \
            .maybe_single() \
            .execute()

        if not result.data:
            logger.info(f"[Google OAuth] No user_secrets found for user {user_id}")
            return None

        refresh_token = result.data.get("google_refresh_token")

        if not refresh_token:
            logger.info(f"[Google OAuth] No Google refresh_token for user {user_id}")
            return None

        logger.info(f"[Google OAuth] ✅ Found refresh_token for user {user_id}")
        return refresh_token

    except Exception as e:
        logger.error(f"[Google OAuth] Error loading refresh_token: {e}")
        return None


async def check_google_credentials_available(user_id: str) -> bool:
    """
    Check if Google refresh_token is available for a user.

    Args:
        user_id: Clerk user ID

    Returns:
        True if refresh_token exists, False otherwise
    """
    refresh_token = await load_google_credentials(user_id)
    return refresh_token is not None
