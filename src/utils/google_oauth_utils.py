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
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not supabase_url or not supabase_key:
            logger.warning("Supabase not configured - cannot load Google credentials")
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

        # Validate that all required fields are present
        required_fields = ['google_access_token', 'google_refresh_token', 'google_client_id', 'google_client_secret']
        missing_fields = [field for field in required_fields if not creds.get(field)]

        if missing_fields:
            logger.warning(f"Incomplete Google credentials for user {user_id}: missing {missing_fields}")
            return None

        logger.info(f"Successfully loaded Google OAuth credentials for user {user_id}")

        # Return credentials in expected format
        return {
            'google_access_token': creds['google_access_token'],
            'google_refresh_token': creds['google_refresh_token'],
            'google_client_id': creds['google_client_id'],
            'google_client_secret': creds['google_client_secret']
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
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not supabase_url or not supabase_key:
            logger.error("Supabase not configured - cannot save Google credentials")
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
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not supabase_url or not supabase_key:
            logger.error("Supabase not configured - cannot delete Google credentials")
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
