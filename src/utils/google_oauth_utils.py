"""
Google OAuth Credential Management
Loads OAuth tokens from Supabase user_secrets table for Google Workspace integration.

This module provides utilities to:
1. Load Google OAuth credentials from Supabase
2. Check if credentials are valid and available
3. Handle credential refresh tokens
"""
import os
import logging
from typing import Optional, Dict
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


async def load_google_credentials(user_id: str) -> Optional[Dict[str, str]]:
    """
    Load Google OAuth credentials from Supabase user_secrets table.

    This function retrieves the Google OAuth tokens stored during the OAuth flow.
    The tokens are stored in the user_secrets table with the following fields:
    - google_access_token: Current access token
    - google_refresh_token: Refresh token for obtaining new access tokens
    - google_client_id: OAuth client ID
    - google_client_secret: OAuth client secret

    Args:
        user_id: Clerk user ID

    Returns:
        Dict with Google OAuth credentials:
        {
            'google_access_token': str,
            'google_refresh_token': str,
            'google_client_id': str,
            'google_client_secret': str
        }
        Returns None if credentials are not configured or if Supabase is not available.
    """
    try:
        # Check if Supabase is configured
        supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SECRET_KEY")

        if not supabase_url or not supabase_key:
            logger.warning("Supabase not configured - cannot load Google credentials")
            logger.warning("Missing NEXT_PUBLIC_SUPABASE_URL or SUPABASE_SECRET_KEY environment variables")
            return None

        # Import Supabase client
        try:
            from supabase import create_client
        except ImportError:
            logger.error("supabase-py not installed - cannot load credentials")
            return None

        # Create Supabase client
        supabase = create_client(supabase_url, supabase_key)

        # Query user_secrets table for Google OAuth credentials
        logger.info(f"Loading Google OAuth credentials for user: {user_id}")

        result = supabase.table("user_secrets") \
            .select("google_access_token, google_refresh_token, google_client_id, google_client_secret") \
            .eq("clerk_id", user_id) \
            .execute()

        # Check if credentials exist
        if not result.data or len(result.data) == 0:
            logger.info(f"No Google credentials found for user {user_id}")
            return None

        creds = result.data[0]

        # Validate that user-specific refresh token is present
        # Note: google_access_token is OPTIONAL - refresh token is sufficient
        if not creds.get('google_refresh_token'):
            logger.warning(f"No Google refresh token found for user {user_id}")
            return None

        # OAuth Application Credentials (same for all users)
        # These are from the OAuth app registration in Google Cloud Console
        # Priority: Supabase user_secrets > .env fallback
        google_client_id = creds.get('google_client_id') or os.getenv('GOOGLE_CLIENT_ID')
        google_client_secret = creds.get('google_client_secret') or os.getenv('GOOGLE_CLIENT_SECRET')

        if not google_client_id or not google_client_secret:
            logger.error(f"Missing Google OAuth app credentials. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env")
            return None

        # Log whether access token is present (helpful for debugging)
        has_access_token = bool(creds.get('google_access_token'))
        logger.info(f"Successfully loaded Google OAuth credentials for user {user_id}")
        logger.info(f"  - access_token present: {has_access_token}")
        logger.info(f"  - refresh_token: ✅")
        logger.info(f"  - client_id source: {'Supabase' if creds.get('google_client_id') else '.env'}")
        logger.info(f"  - client_secret source: {'Supabase' if creds.get('google_client_secret') else '.env'}")

        # Return credentials in expected format
        # access_token can be None - google.oauth2.credentials.Credentials will auto-refresh using refresh_token
        return {
            'google_access_token': creds.get('google_access_token'),  # Can be None (will auto-refresh)
            'google_refresh_token': creds['google_refresh_token'],  # User-specific
            'google_client_id': google_client_id,  # App-level (from Supabase or .env)
            'google_client_secret': google_client_secret  # App-level (from Supabase or .env)
        }

    except Exception as e:
        logger.error(f"Error loading Google credentials from Supabase: {e}")
        logger.exception("Full traceback:")
        return None


async def check_google_credentials_available(user_id: str) -> bool:
    """
    Check if Google OAuth credentials are available for a user.

    Args:
        user_id: Clerk user ID

    Returns:
        True if valid credentials exist, False otherwise
    """
    credentials = await load_google_credentials(user_id)
    return credentials is not None


async def save_google_credentials(
    user_id: str,
    access_token: str,
    refresh_token: str,
    client_id: str,
    client_secret: str
) -> bool:
    """
    Save Google OAuth credentials to Supabase user_secrets table.

    This function is typically called after successful OAuth flow completion.

    Args:
        user_id: Clerk user ID
        access_token: Google access token
        refresh_token: Google refresh token
        client_id: OAuth client ID
        client_secret: OAuth client secret

    Returns:
        True if save was successful, False otherwise
    """
    try:
        # Check if Supabase is configured
        supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SECRET_KEY")

        if not supabase_url or not supabase_key:
            logger.error("Supabase not configured - cannot save Google credentials")
            logger.error("Missing NEXT_PUBLIC_SUPABASE_URL or SUPABASE_SECRET_KEY environment variables")
            return False

        # Import Supabase client
        try:
            from supabase import create_client
        except ImportError:
            logger.error("supabase-py not installed - cannot save credentials")
            return False

        # Create Supabase client
        supabase = create_client(supabase_url, supabase_key)

        # Check if user_secrets record exists
        existing = supabase.table("user_secrets") \
            .select("clerk_id") \
            .eq("clerk_id", user_id) \
            .execute()

        credentials_data = {
            'google_access_token': access_token,
            'google_refresh_token': refresh_token,
            'google_client_id': client_id,
            'google_client_secret': client_secret
        }

        if existing.data and len(existing.data) > 0:
            # Update existing record
            logger.info(f"Updating Google credentials for user {user_id}")
            supabase.table("user_secrets") \
                .update(credentials_data) \
                .eq("clerk_id", user_id) \
                .execute()
        else:
            # Insert new record
            logger.info(f"Inserting new Google credentials for user {user_id}")
            credentials_data['clerk_id'] = user_id
            supabase.table("user_secrets") \
                .insert(credentials_data) \
                .execute()

        logger.info(f"Successfully saved Google OAuth credentials for user {user_id}")
        return True

    except Exception as e:
        logger.error(f"Error saving Google credentials to Supabase: {e}")
        logger.exception("Full traceback:")
        return False


async def delete_google_credentials(user_id: str) -> bool:
    """
    Delete Google OAuth credentials for a user.

    This can be used when a user disconnects their Google Calendar integration.

    Args:
        user_id: Clerk user ID

    Returns:
        True if deletion was successful, False otherwise
    """
    try:
        # Check if Supabase is configured
        supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SECRET_KEY")

        if not supabase_url or not supabase_key:
            logger.error("Supabase not configured - cannot delete Google credentials")
            logger.error("Missing NEXT_PUBLIC_SUPABASE_URL or SUPABASE_SECRET_KEY environment variables")
            return False

        # Import Supabase client
        try:
            from supabase import create_client
        except ImportError:
            logger.error("supabase-py not installed - cannot delete credentials")
            return False

        # Create Supabase client
        supabase = create_client(supabase_url, supabase_key)

        # Update record to null out Google credentials
        logger.info(f"Deleting Google credentials for user {user_id}")

        supabase.table("user_secrets") \
            .update({
                'google_access_token': None,
                'google_refresh_token': None,
                'google_client_id': None,
                'google_client_secret': None
            }) \
            .eq("clerk_id", user_id) \
            .execute()

        logger.info(f"Successfully deleted Google OAuth credentials for user {user_id}")
        return True

    except Exception as e:
        logger.error(f"Error deleting Google credentials from Supabase: {e}")
        logger.exception("Full traceback:")
        return False
