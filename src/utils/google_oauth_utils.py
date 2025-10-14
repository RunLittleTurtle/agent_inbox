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
        logger.info(f"[Google OAuth] ===== GOOGLE OAUTH TOKEN FETCH DEBUG =====")
        logger.info(f"[Google OAuth] user_id being queried: '{user_id}'")
        logger.info(f"[Google OAuth] user_id type: {type(user_id)}")
        logger.info(f"[Google OAuth] user_id length: {len(user_id) if user_id else 0}")

        supabase = get_supabase_client()

        logger.info(f"[Google OAuth] Supabase client initialized")
        logger.info(f"[Google OAuth] Querying table: user_secrets")
        logger.info(f"[Google OAuth] Query: SELECT google_refresh_token WHERE clerk_id = '{user_id}'")

        # Fetch refresh_token from Supabase (same pattern as MCP auth)
        result = supabase.table("user_secrets") \
            .select("google_refresh_token, clerk_id, email") \
            .eq("clerk_id", user_id) \
            .maybe_single() \
            .execute()

        logger.info(f"[Google OAuth] Query executed")

        # Check if result is None (Supabase client error)
        if result is None:
            logger.error(f"[Google OAuth] ❌ Supabase query returned None - connection failed")
            return None

        logger.info(f"[Google OAuth] result.data type: {type(result.data)}")
        logger.info(f"[Google OAuth] result.data is None: {result.data is None}")

        # Sanitize sensitive data for logging (only show structure, not full token)
        if result.data:
            safe_data = {k: (v[:20] + "..." if k == "google_refresh_token" and v else v) for k, v in result.data.items()}
            logger.info(f"[Google OAuth] result.data (sanitized): {safe_data}")
        else:
            logger.info(f"[Google OAuth] result.data: None")

        if not result.data:
            logger.warning(f"[Google OAuth] ❌ No user_secrets row found for clerk_id='{user_id}'")
            logger.warning(f"[Google OAuth] This means either:")
            logger.warning(f"[Google OAuth]   1. User has not connected Google Calendar yet")
            logger.warning(f"[Google OAuth]   2. clerk_id mismatch (check case sensitivity)")
            logger.warning(f"[Google OAuth]   3. Wrong Supabase environment")
            logger.info(f"[Google OAuth] ===== END DEBUG =====")
            return None

        logger.info(f"[Google OAuth] ✅ Found user_secrets row")
        logger.info(f"[Google OAuth] clerk_id in DB: '{result.data.get('clerk_id')}'")
        logger.info(f"[Google OAuth] email in DB: '{result.data.get('email')}'")

        refresh_token = result.data.get("google_refresh_token")

        if not refresh_token:
            logger.warning(f"[Google OAuth] ❌ google_refresh_token column is NULL/empty")
            logger.warning(f"[Google OAuth] User found but token not saved - OAuth flow incomplete?")
            logger.info(f"[Google OAuth] ===== END DEBUG =====")
            return None

        token_preview = refresh_token[:20] + "..." if len(refresh_token) > 20 else refresh_token
        logger.info(f"[Google OAuth] ✅ Found refresh_token")
        logger.info(f"[Google OAuth] Token length: {len(refresh_token)} chars")
        logger.info(f"[Google OAuth] Token preview: {token_preview}")
        logger.info(f"[Google OAuth] ===== END DEBUG =====")

        return refresh_token

    except ValueError as ve:
        logger.error(f"[Google OAuth] ❌ Supabase configuration error: {ve}")
        logger.error(f"[Google OAuth] Check NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SECRET_KEY in .env")
        return None
    except Exception as e:
        logger.error(f"[Google OAuth] ❌ Error loading refresh_token: {e}")
        import traceback
        logger.error(f"[Google OAuth] Traceback:\n{traceback.format_exc()}")
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
