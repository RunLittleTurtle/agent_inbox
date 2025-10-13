"""
Tool Executor Factory - Google Workspace Only
Creates Google Workspace executor with OAuth credentials from Supabase.

This factory implements the Strategy pattern for future provider additions
(Microsoft Graph, Apple Calendar, etc.) without changing booking_node or calendar_orchestrator.
"""
import logging
from typing import Optional, List, Tuple
from langchain_core.tools import BaseTool

from .google_workspace_executor import GoogleWorkspaceExecutor

# Import tool wrapper utility
try:
    from .google_workspace_tools import create_google_workspace_read_tools
    GOOGLE_WORKSPACE_TOOLS_AVAILABLE = True
except ImportError:
    logging.warning("google_workspace_tools not available - READ tools disabled")
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
        Create Google Workspace executor with OAuth credentials.

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

        # Load Google OAuth credentials from Supabase
        try:
            print(f"[EXECUTOR_FACTORY] Loading Google OAuth credentials from Supabase...")
            google_creds = await load_google_credentials(user_id)

            if google_creds:
                print(f"[EXECUTOR_FACTORY] ✅ Google OAuth credentials found")
                print(f"[EXECUTOR_FACTORY] Creating GoogleWorkspaceExecutor...")
                logger.info(f"Google OAuth credentials found for user {user_id}")
                executor = GoogleWorkspaceExecutor(google_creds)
                print(f"[EXECUTOR_FACTORY] ✅ GoogleWorkspaceExecutor created successfully")
                return executor
            else:
                print(f"[EXECUTOR_FACTORY] ❌ No Google OAuth credentials in Supabase for user {user_id}")
                error_msg = f"No Google OAuth credentials found for user {user_id}. Please connect Google Calendar in the config app."
                if required:
                    raise ValueError(error_msg)
                logger.info(f"No Google OAuth credentials for user {user_id}")
                return None

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
