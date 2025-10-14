"""
Google Workspace LangChain Tools - TEMPLATE
Wraps GoogleWorkspaceExecutor methods as LangChain tools for agent use.

CUSTOMIZATION REQUIRED:
1. Replace example_tool_* with your domain-specific tools
2. Update tool names, descriptions, and parameters
3. Implement tool logic by calling executor methods

LangChain Tool Patterns:
- Use @tool decorator for automatic tool creation
- Use closure pattern to inject executor into tool functions
- Return JSON strings for structured data
- Handle errors gracefully with try/except

Tool Examples:
- Calendar: list_events, get_event, search_events
- Contacts: list_contacts, get_contact, search_contacts
- Email: list_messages, get_message, send_message
- Drive: list_files, get_file, upload_file
"""
import json
import logging
from typing import List
from langchain_core.tools import BaseTool, tool

from .google_workspace_executor import GoogleWorkspaceExecutor

logger = logging.getLogger(__name__)


def create_google_workspace_tools(executor: GoogleWorkspaceExecutor) -> List[BaseTool]:
    """
    Create LangChain tools for Google Workspace integration.

    Uses closure pattern: Tools capture the executor instance at creation time,
    allowing them to call executor methods without passing executor as parameter.

    Args:
        executor: GoogleWorkspaceExecutor instance with authenticated API client

    Returns:
        List of LangChain BaseTool instances for agent use
    """
    logger.info("Creating Google Workspace tools using closure pattern")

    # ==========================================================================
    # TODO: REPLACE THESE EXAMPLE TOOLS WITH YOUR DOMAIN-SPECIFIC TOOLS
    # ==========================================================================
    #
    # EXAMPLES FOR DIFFERENT GOOGLE APIS:
    #
    # --- Google Calendar Tools ---
    # @tool
    # def list_calendar_events(
    #     calendar_id: str = "primary",
    #     max_results: int = 10
    # ) -> str:
    #     """List upcoming events from Google Calendar"""
    #     try:
    #         events = executor.list_events(calendar_id, max_results)
    #         return json.dumps(events, indent=2)
    #     except Exception as e:
    #         logger.error(f"Error listing calendar events: {e}")
    #         return f"Error: {str(e)}"
    #
    # --- Google Contacts Tools ---
    # @tool
    # def list_contacts(page_size: int = 50) -> str:
    #     """List contacts from Google Contacts"""
    #     try:
    #         contacts = executor.list_contacts(page_size)
    #         return json.dumps(contacts, indent=2)
    #     except Exception as e:
    #         logger.error(f"Error listing contacts: {e}")
    #         return f"Error: {str(e)}"
    #
    # --- Gmail Tools ---
    # @tool
    # def list_emails(query: str = "", max_results: int = 10) -> str:
    #     """List emails from Gmail inbox"""
    #     try:
    #         messages = executor.list_messages(query, max_results)
    #         return json.dumps(messages, indent=2)
    #     except Exception as e:
    #         logger.error(f"Error listing emails: {e}")
    #         return f"Error: {str(e)}"
    #
    # --- Google Drive Tools ---
    # @tool
    # def list_drive_files(page_size: int = 10) -> str:
    #     """List files from Google Drive"""
    #     try:
    #         files = executor.list_files(page_size)
    #         return json.dumps(files, indent=2)
    #     except Exception as e:
    #         logger.error(f"Error listing Drive files: {e}")
    #         return f"Error: {str(e)}"

    @tool
    def example_tool_list(max_results: int = 10) -> str:
        """
        TODO: Replace with your domain-specific list tool.

        Example: list_contacts, list_events, list_messages, list_files

        Args:
            max_results: Maximum number of items to return

        Returns:
            JSON string with list of items
        """
        try:
            # TODO: Call your executor's list method
            # results = executor.list_your_items(max_results)
            # return json.dumps(results, indent=2)
            raise NotImplementedError(
                "Replace this tool with your domain-specific implementation. "
                "See examples in comments above."
            )
        except Exception as e:
            logger.error(f"Error in example_tool_list: {e}")
            return f"Error: {str(e)}"

    @tool
    def example_tool_get(item_id: str) -> str:
        """
        TODO: Replace with your domain-specific get tool.

        Example: get_contact, get_event, get_message, get_file

        Args:
            item_id: ID of item to retrieve

        Returns:
            JSON string with item details
        """
        try:
            # TODO: Call your executor's get method
            # result = executor.get_your_item(item_id)
            # return json.dumps(result, indent=2)
            raise NotImplementedError(
                "Replace this tool with your domain-specific implementation. "
                "See examples in comments above."
            )
        except Exception as e:
            logger.error(f"Error in example_tool_get: {e}")
            return f"Error: {str(e)}"

    @tool
    def example_tool_search(query: str) -> str:
        """
        TODO: Replace with your domain-specific search tool.

        Example: search_contacts, search_events, search_messages

        Args:
            query: Search query string

        Returns:
            JSON string with matching items
        """
        try:
            # TODO: Call your executor's search method
            # results = executor.search_your_items(query)
            # return json.dumps(results, indent=2)
            raise NotImplementedError(
                "Replace this tool with your domain-specific implementation. "
                "See examples in comments above."
            )
        except Exception as e:
            logger.error(f"Error in example_tool_search: {e}")
            return f"Error: {str(e)}"

    # ==========================================================================
    # TOOL REGISTRATION
    # ==========================================================================
    # TODO: Update this list with your actual tools
    tools = [
        example_tool_list,
        example_tool_get,
        example_tool_search,
    ]

    logger.info(f"Created {len(tools)} Google Workspace tools")
    for tool_instance in tools:
        logger.info(f"   - {tool_instance.name}: {tool_instance.description}")

    return tools


# ==========================================================================
# HELPER: Create No-Tools Agent (when credentials missing)
# ==========================================================================

def create_no_tools_message() -> str:
    """
    Message to show when Google OAuth credentials are not available.
    This is displayed by a no-tools agent when user hasn't connected Google account.

    Returns:
        User-friendly message explaining how to connect Google account
    """
    return """
I don't have access to your Google account yet. To use this agent, please:

1. Go to the configuration app
2. Navigate to the Google OAuth section
3. Click "Connect Google Account"
4. Authorize the required permissions
5. Return here to use the agent

Once connected, I'll be able to access your Google data and assist you.
    """.strip()
