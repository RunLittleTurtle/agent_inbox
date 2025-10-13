"""
Tool Executor Factory - Provider Selection Logic
Selects appropriate calendar executor based on available credentials.

This factory implements the Strategy pattern to abstract provider selection:
- Google Workspace API (primary): Direct Google Calendar API access
- Rube MCP (fallback): Universal MCP server with OAuth to 500+ apps

The factory makes it easy to add more providers in the future
(Microsoft Graph, Apple Calendar, etc.) without changing booking_node or calendar_orchestrator.
"""
import logging
from typing import Optional, Union, List, Tuple
from langchain_core.tools import BaseTool

from .mcp_executor import MCPToolExecutor
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
    """Factory for creating the appropriate tool executor based on credential availability"""

    @staticmethod
    async def create_executor(
        user_id: Optional[str] = None,
        mcp_tools: Optional[List[BaseTool]] = None,
        provider_preference: str = "auto"
    ) -> Tuple[Union[GoogleWorkspaceExecutor, MCPToolExecutor], List[BaseTool]]:
        """
        Create executor AND read-only tools based on credential availability.

        Priority (when provider_preference="auto"):
        1. Google Workspace API (if OAuth credentials available)
        2. Rube MCP (if MCP tools available)
        3. Raise error if neither available

        Args:
            user_id: Clerk user ID for loading credentials
            mcp_tools: List of MCP tools (for Rube MCP fallback)
            provider_preference: Provider selection strategy:
                - "auto": Try Google first, fallback to Rube MCP
                - "google_only": Only use Google Workspace API
                - "rube_only": Only use Rube MCP

        Returns:
            Tuple of (executor, read_tools):
            - executor: GoogleWorkspaceExecutor or MCPToolExecutor for WRITE operations
            - read_tools: List of READ-ONLY tools for calendar_agent node

        Raises:
            ValueError: If no executor can be created with available credentials
        """
        logger.info(f"Creating executor for user_id={user_id}, preference={provider_preference}")

        # Handle preference-based selection
        if provider_preference == "google_only":
            executor = await ExecutorFactory._create_google_executor(user_id, required=True)
            read_tools = await ExecutorFactory._get_read_tools(executor)
            return executor, read_tools

        elif provider_preference == "rube_only":
            executor = await ExecutorFactory._create_mcp_executor(mcp_tools, required=True)
            # MCP tools are handled separately in calendar_orchestrator
            return executor, []

        # Auto selection: Try Google first, fallback to Rube MCP
        elif provider_preference == "auto":
            # Try Google Workspace first
            google_executor = await ExecutorFactory._create_google_executor(user_id, required=False)
            if google_executor:
                logger.info("Using Google Workspace API executor (primary workflow)")
                read_tools = await ExecutorFactory._get_read_tools(google_executor)
                return google_executor, read_tools

            # Fallback to Rube MCP
            logger.info("Google OAuth not configured, falling back to Rube MCP")
            mcp_executor = await ExecutorFactory._create_mcp_executor(mcp_tools, required=False)
            if mcp_executor:
                logger.info("Using Rube MCP executor (fallback workflow)")
                # MCP tools are handled separately in calendar_orchestrator
                return mcp_executor, []

            # Neither available
            raise ValueError(
                "No calendar executor available. "
                "Configure Google OAuth or Rube MCP server to enable calendar operations."
            )

        else:
            raise ValueError(f"Unknown provider_preference: {provider_preference}")

    @staticmethod
    async def _create_google_executor(
        user_id: Optional[str],
        required: bool = False
    ) -> Optional[GoogleWorkspaceExecutor]:
        """
        Try to create Google Workspace executor.

        Args:
            user_id: Clerk user ID
            required: If True, raise error if credentials not available

        Returns:
            GoogleWorkspaceExecutor or None

        Raises:
            ValueError: If required=True and credentials not available
        """
        print(f"\n[EXECUTOR_FACTORY] _create_google_executor for user: {user_id}")

        if not GOOGLE_OAUTH_AVAILABLE:
            print(f"[EXECUTOR_FACTORY] ❌ Google OAuth utilities not available")
            if required:
                raise ValueError("Google OAuth utilities not available")
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
                if required:
                    raise ValueError(f"No Google OAuth credentials found for user {user_id}")
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
    async def _create_mcp_executor(
        mcp_tools: Optional[List[BaseTool]],
        required: bool = False
    ) -> Optional[MCPToolExecutor]:
        """
        Try to create Rube MCP executor.

        Args:
            mcp_tools: List of MCP tools
            required: If True, raise error if tools not available

        Returns:
            MCPToolExecutor or None

        Raises:
            ValueError: If required=True and tools not available
        """
        if not mcp_tools or len(mcp_tools) == 0:
            if required:
                raise ValueError("No MCP tools available for Rube MCP executor")
            logger.info("No MCP tools provided, skipping Rube MCP executor")
            return None

        logger.info(f"Creating Rube MCP executor with {len(mcp_tools)} tools")
        return MCPToolExecutor(mcp_tools)

    @staticmethod
    async def _get_read_tools(executor) -> List[BaseTool]:
        """
        Get READ-ONLY tools from executor for calendar_agent node.

        Args:
            executor: GoogleWorkspaceExecutor or MCPToolExecutor

        Returns:
            List of READ-ONLY LangChain tools (list-events, get-event, list-calendars)
        """
        print(f"\n[EXECUTOR_FACTORY] _get_read_tools called")
        print(f"[EXECUTOR_FACTORY] Executor type: {type(executor).__name__}")
        print(f"[EXECUTOR_FACTORY] Is GoogleWorkspaceExecutor: {isinstance(executor, GoogleWorkspaceExecutor)}")

        if isinstance(executor, GoogleWorkspaceExecutor):
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
        else:
            # For MCP executors, tools are handled separately in calendar_orchestrator
            print(f"[EXECUTOR_FACTORY] Not GoogleWorkspaceExecutor (is {type(executor).__name__})")
            return []

    @staticmethod
    async def get_provider_status(
        user_id: Optional[str] = None,
        mcp_tools: Optional[List[BaseTool]] = None
    ) -> dict:
        """
        Get status of available calendar providers.

        This is useful for UI display to show which providers are configured.

        Args:
            user_id: Clerk user ID
            mcp_tools: List of MCP tools

        Returns:
            Dict with provider availability:
            {
                'google_workspace': {'available': bool, 'reason': str},
                'rube_mcp': {'available': bool, 'reason': str},
                'recommended': str  # Which provider would be used with "auto"
            }
        """
        status = {
            'google_workspace': {'available': False, 'reason': ''},
            'rube_mcp': {'available': False, 'reason': ''},
            'recommended': None
        }

        # Check Google Workspace
        if GOOGLE_OAUTH_AVAILABLE and user_id:
            try:
                has_google = await check_google_credentials_available(user_id)
                if has_google:
                    status['google_workspace'] = {
                        'available': True,
                        'reason': 'OAuth credentials configured'
                    }
                else:
                    status['google_workspace'] = {
                        'available': False,
                        'reason': 'OAuth not configured'
                    }
            except Exception as e:
                status['google_workspace'] = {
                    'available': False,
                    'reason': f'Error: {str(e)}'
                }
        elif not GOOGLE_OAUTH_AVAILABLE:
            status['google_workspace'] = {
                'available': False,
                'reason': 'OAuth utilities not installed'
            }
        else:
            status['google_workspace'] = {
                'available': False,
                'reason': 'No user_id provided'
            }

        # Check Rube MCP
        if mcp_tools and len(mcp_tools) > 0:
            status['rube_mcp'] = {
                'available': True,
                'reason': f'{len(mcp_tools)} MCP tools loaded'
            }
        else:
            status['rube_mcp'] = {
                'available': False,
                'reason': 'MCP server not configured'
            }

        # Determine recommended provider
        if status['google_workspace']['available']:
            status['recommended'] = 'google_workspace'
        elif status['rube_mcp']['available']:
            status['recommended'] = 'rube_mcp'
        else:
            status['recommended'] = None

        return status
