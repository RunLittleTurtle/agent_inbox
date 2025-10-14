"""
Tool Executor Factory - Generic Google OAuth
Creates Google Workspace executor with OAuth credentials from Supabase.

This factory is 100% REUSABLE across all Google OAuth agents.
Only the tools created from the executor need to be domain-specific.

OAuth Architecture:
1. User-specific refresh_token stored in Supabase user_secrets table
2. Shared client_id/secret from environment variables (.env)
3. GoogleWorkspaceExecutor builds Google Credentials object
4. Domain-specific tools wrap the executor methods
"""
import os
import logging
from typing import Optional, List, Tuple
from langchain_core.tools import BaseTool

from .google_workspace_executor import GoogleWorkspaceExecutor

# Import tool wrapper utility
# TODO: This import will fail until you implement google_workspace_tools.py
try:
    from .google_workspace_tools import create_google_workspace_tools
    GOOGLE_WORKSPACE_TOOLS_AVAILABLE = True
    logging.info("google_workspace_tools imported successfully")
except ImportError as e:
    logging.error(f"google_workspace_tools import failed - READ tools disabled. {e}")
    GOOGLE_WORKSPACE_TOOLS_AVAILABLE = False
except Exception as e:
    logging.error(f"Unexpected error importing google_workspace_tools: {e}")
    GOOGLE_WORKSPACE_TOOLS_AVAILABLE = False

# Import OAuth utilities
try:
    from utils.google_oauth_utils import load_google_credentials
    GOOGLE_OAUTH_AVAILABLE = True
except ImportError:
    logging.warning("google_oauth_utils not available - Google Workspace executor disabled")
    GOOGLE_OAUTH_AVAILABLE = False


logger = logging.getLogger(__name__)


class ExecutorFactory:
    """Factory for creating Google Workspace executor with OAuth"""

    @staticmethod
    async def create_executor(
        user_id: str
    ) -> Tuple[Optional[GoogleWorkspaceExecutor], List[BaseTool]]:
        """
        Create Google Workspace executor AND tools.

        Args:
            user_id: Clerk user ID for loading OAuth credentials from Supabase

        Returns:
            Tuple of (executor, tools):
            - executor: GoogleWorkspaceExecutor for API operations, or None if credentials missing
            - tools: List of LangChain tools for agent, or empty list if no executor

        Note:
            Returns (None, []) gracefully when Google OAuth credentials are not available,
            allowing the agent to display user guidance instead of crashing.
        """
        logger.info(f"Creating Google Workspace executor for user_id={user_id}")

        # Create Google Workspace executor (graceful - returns None if credentials missing)
        executor = await ExecutorFactory._create_google_executor(user_id, required=False)

        # Get tools from executor
        tools = await ExecutorFactory._get_tools(executor)

        return executor, tools

    @staticmethod
    async def _create_google_executor(
        user_id: str,
        required: bool = False
    ) -> Optional[GoogleWorkspaceExecutor]:
        """
        Create Google Workspace executor with OAuth refresh_token from Supabase.

        Simple & Direct OAuth Flow:
        1. Fetch refresh_token from Supabase user_secrets table (per-user)
        2. Get client_id/secret from .env (shared across users)
        3. Create Google Credentials object
        4. Build Google API service

        Args:
            user_id: Clerk user ID
            required: If True, raise error if credentials not available

        Returns:
            GoogleWorkspaceExecutor or None

        Raises:
            ValueError: If required=True and credentials not available
        """
        logger.info(f"Creating Google Workspace executor for user: {user_id}")

        if not GOOGLE_OAUTH_AVAILABLE:
            error_msg = "Google OAuth utilities not available. Install google-auth and google-api-python-client."
            if required:
                raise ValueError(error_msg)
            logger.error(error_msg)
            return None

        if not user_id:
            if required:
                raise ValueError("user_id required for Google Workspace executor")
            logger.info("No user_id provided, skipping Google Workspace executor")
            return None

        # Fetch refresh_token from Supabase (simple!)
        try:
            logger.info(f"Fetching Google refresh_token from Supabase for user: {user_id}")
            refresh_token = await load_google_credentials(user_id)

            if not refresh_token:
                logger.warning(f"No Google refresh_token for user {user_id}")
                error_msg = f"No Google refresh_token found. Please connect Google account in config app."
                if required:
                    raise ValueError(error_msg)
                return None

            logger.info(f"Found Google refresh_token for user {user_id}")

            # Get OAuth app credentials from .env (shared across users)
            client_id = os.getenv("GOOGLE_CLIENT_ID")
            client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

            if not client_id or not client_secret:
                error_msg = "Missing GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET in .env"
                logger.error(error_msg)
                if required:
                    raise ValueError(error_msg)
                return None

            logger.info("Found Google OAuth app credentials in .env")

            # Build credentials dict for GoogleWorkspaceExecutor
            google_creds = {
                'google_refresh_token': refresh_token,
                'google_client_id': client_id,
                'google_client_secret': client_secret
            }

            logger.info("Creating GoogleWorkspaceExecutor...")
            executor = GoogleWorkspaceExecutor(google_creds)
            logger.info("GoogleWorkspaceExecutor created successfully")
            return executor

        except Exception as e:
            logger.error(f"Error creating Google Workspace executor: {e}")
            import traceback
            traceback.print_exc()
            if required:
                raise ValueError(f"Failed to create Google Workspace executor: {e}")
            return None

    @staticmethod
    async def _get_tools(executor: Optional[GoogleWorkspaceExecutor]) -> List[BaseTool]:
        """
        Get LangChain tools from Google Workspace executor.

        Args:
            executor: GoogleWorkspaceExecutor instance, or None if no credentials available

        Returns:
            List of LangChain tools for agent use,
            or empty list if executor is None
        """
        logger.info("Getting tools from executor")

        if executor is None:
            logger.info("No executor available (missing Google OAuth credentials)")
            return []

        if not isinstance(executor, GoogleWorkspaceExecutor):
            logger.error(f"Expected GoogleWorkspaceExecutor, got {type(executor).__name__}")
            return []

        if not GOOGLE_WORKSPACE_TOOLS_AVAILABLE:
            logger.warning("google_workspace_tools module not available - returning empty tool list")
            return []

        try:
            logger.info("Creating Google Workspace tools...")
            tools = create_google_workspace_tools(executor)
            logger.info(f"Created {len(tools)} Google Workspace tools:")
            for tool in tools:
                logger.info(f"   - {tool.name}")
            return tools
        except Exception as e:
            logger.error(f"Error creating Google Workspace tools: {e}")
            import traceback
            traceback.print_exc()
            return []
