"""
Tool Executor Factory - Google Workspace Only
Creates Google Workspace executor with OAuth credentials from Supabase.

This factory implements the Strategy pattern for future provider additions
(Microsoft Graph, Apple Calendar, etc.) without changing booking_node or calendar_orchestrator.
"""
import os
import logging
from typing import Optional, List, Tuple
from langchain_core.tools import BaseTool

from .google_workspace_executor import GoogleWorkspaceExecutor

# Import tool wrapper utility
try:
    from .google_workspace_tools import create_google_workspace_read_tools
    GOOGLE_WORKSPACE_TOOLS_AVAILABLE = True
    print("[EXECUTOR_FACTORY] ✅ google_workspace_tools imported successfully")
except ImportError as e:
    print(f"[EXECUTOR_FACTORY] ❌ ImportError for google_workspace_tools: {e}")
    print(f"[EXECUTOR_FACTORY] Import traceback:")
    import traceback
    traceback.print_exc()
    logging.warning(f"google_workspace_tools not available - READ tools disabled. Error: {e}")
    GOOGLE_WORKSPACE_TOOLS_AVAILABLE = False
except Exception as e:
    print(f"[EXECUTOR_FACTORY] ❌ Unexpected error importing google_workspace_tools: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    logging.error(f"Unexpected error importing google_workspace_tools: {e}")
    GOOGLE_WORKSPACE_TOOLS_AVAILABLE = False

# Import OAuth utilities
try:
    from utils.google_oauth_utils import load_google_credentials, check_google_credentials_available
    GOOGLE_OAUTH_AVAILABLE = True
except ImportError:
    logging.warning("google_oauth_utils not available - Google Workspace executor disabled")
    GOOGLE_OAUTH_AVAILABLE = False


logger = logging.getLogger(__name__)


class ExecutorFactory:
    """Factory for creating Google Workspace calendar executor"""

    @staticmethod
    async def create_executor(
        user_id: str
    ) -> Tuple[Optional[GoogleWorkspaceExecutor], List[BaseTool]]:
        """
        Create Google Workspace executor AND read-only tools.

        Args:
            user_id: Clerk user ID for loading OAuth credentials from Supabase

        Returns:
            Tuple of (executor, read_tools):
            - executor: GoogleWorkspaceExecutor for WRITE operations (bookings), or None if credentials missing
            - read_tools: List of READ-ONLY tools for calendar_agent node, or empty list if no executor

        Note:
            Returns (None, []) gracefully when Google OAuth credentials are not available,
            allowing the agent to display user guidance instead of crashing.
        """
        logger.info(f"Creating Google Workspace executor for user_id={user_id}")

        # Create Google Workspace executor (graceful - returns None if credentials missing)
        executor = await ExecutorFactory._create_google_executor(user_id, required=False)

        # Get read-only tools from executor
        read_tools = await ExecutorFactory._get_read_tools(executor)

        return executor, read_tools

    @staticmethod
    async def _create_google_executor(
        user_id: str,
        required: bool = True
    ) -> Optional[GoogleWorkspaceExecutor]:
        """
        Create Google Workspace executor with OAuth refresh_token from Supabase.

        Simple & Direct - follows same pattern as MCP auth:
        1. Fetch refresh_token from Supabase
        2. Get client_id/secret from .env
        3. Create Google Credentials object
        4. Done!

        Args:
            user_id: Clerk user ID
            required: If True, raise error if credentials not available

        Returns:
            GoogleWorkspaceExecutor or None

        Raises:
            ValueError: If required=True and credentials not available
        """
        print(f"\n[EXECUTOR_FACTORY] Creating Google Workspace executor for user: {user_id}")

        if not GOOGLE_OAUTH_AVAILABLE:
            print(f"[EXECUTOR_FACTORY] ❌ Google OAuth utilities not available")
            error_msg = "Google OAuth utilities not available. Install google-auth and google-api-python-client."
            if required:
                raise ValueError(error_msg)
            return None

        if not user_id:
            print(f"[EXECUTOR_FACTORY] ❌ No user_id provided")
            if required:
                raise ValueError("user_id required for Google Workspace executor")
            logger.info("No user_id provided, skipping Google Workspace executor")
            return None

        # Fetch refresh_token from Supabase (simple!)
        try:
            print(f"[EXECUTOR_FACTORY] ===== GOOGLE OAUTH DEBUG =====")
            print(f"[EXECUTOR_FACTORY] user_id being queried: {user_id}")
            print(f"[EXECUTOR_FACTORY] Fetching Google refresh_token from Supabase...")
            refresh_token = await load_google_credentials(user_id)
            print(f"[EXECUTOR_FACTORY] Query result: {'FOUND ✅' if refresh_token else 'NOT FOUND ❌'}")

            if not refresh_token:
                print(f"[EXECUTOR_FACTORY] ❌ No Google refresh_token for user {user_id}")
                print(f"[EXECUTOR_FACTORY] ===== END DEBUG =====")

                error_msg = f"No Google refresh_token found. Please connect Google Calendar in config app."
                if required:
                    raise ValueError(error_msg)
                return None

            print(f"[EXECUTOR_FACTORY] ✅ Found Google refresh_token")

            # Get OAuth app credentials from .env (shared across users)
            client_id = os.getenv("GOOGLE_CLIENT_ID")
            client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

            if not client_id or not client_secret:
                print(f"[EXECUTOR_FACTORY] ❌ Missing GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET in .env")
                error_msg = "Missing GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET in .env"
                if required:
                    raise ValueError(error_msg)
                return None

            print(f"[EXECUTOR_FACTORY] ✅ Found Google OAuth app credentials in .env")

            # Build credentials dict for GoogleWorkspaceExecutor
            google_creds = {
                'google_refresh_token': refresh_token,
                'google_client_id': client_id,
                'google_client_secret': client_secret
            }

            print(f"[EXECUTOR_FACTORY] Creating GoogleWorkspaceExecutor...")
            executor = GoogleWorkspaceExecutor(google_creds)
            print(f"[EXECUTOR_FACTORY] ✅ GoogleWorkspaceExecutor created successfully")
            return executor

        except Exception as e:
            print(f"[EXECUTOR_FACTORY] ❌ Exception: {e}")
            logger.error(f"Error creating Google Workspace executor: {e}")
            import traceback
            traceback.print_exc()
            if required:
                raise ValueError(f"Failed to create Google Workspace executor: {e}")
            return None

    @staticmethod
    async def _get_read_tools(executor: Optional[GoogleWorkspaceExecutor]) -> List[BaseTool]:
        """
        Get READ-ONLY tools from Google Workspace executor.

        Args:
            executor: GoogleWorkspaceExecutor instance, or None if no credentials available

        Returns:
            List of READ-ONLY LangChain tools (list-events, get-event, list-calendars),
            or empty list if executor is None
        """
        print(f"\n[EXECUTOR_FACTORY] Getting READ tools from executor")

        if executor is None:
            print(f"[EXECUTOR_FACTORY] ℹ️  No executor available (missing Google OAuth credentials)")
            logger.info("No executor available - returning empty tool list")
            return []

        print(f"[EXECUTOR_FACTORY] Executor type: {type(executor).__name__}")

        if not isinstance(executor, GoogleWorkspaceExecutor):
            print(f"[EXECUTOR_FACTORY] ❌ Expected GoogleWorkspaceExecutor, got {type(executor).__name__}")
            return []

        if not GOOGLE_WORKSPACE_TOOLS_AVAILABLE:
            print(f"[EXECUTOR_FACTORY] ❌ google_workspace_tools module not available!")
            logger.warning("google_workspace_tools not available - returning empty tool list")
            return []

        try:
            print(f"[EXECUTOR_FACTORY] Creating Google Workspace READ tools...")
            read_tools = create_google_workspace_read_tools(executor)
            print(f"[EXECUTOR_FACTORY] ✅ Created {len(read_tools)} Google Workspace READ tools:")
            for tool in read_tools:
                print(f"[EXECUTOR_FACTORY]    - {tool.name}")
            logger.info(f"Created {len(read_tools)} Google Workspace READ tools")
            return read_tools
        except Exception as e:
            print(f"[EXECUTOR_FACTORY] ❌ EXCEPTION creating Google Workspace tools:")
            logger.error(f"Error creating Google Workspace tools: {e}")
            import traceback
            traceback.print_exc()
            return []
