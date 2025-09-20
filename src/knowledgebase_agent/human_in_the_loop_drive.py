"""
Human-in-the-loop wrapper for Google Drive tools
Implementation based on LangGraph documentation patterns
"""
from typing import Callable, Dict, Any, List, Optional
from langchain_core.tools import BaseTool, tool as create_tool
from langchain_core.runnables import RunnableConfig
from langgraph.types import interrupt
from langgraph.prebuilt.interrupt import HumanInterruptConfig, HumanInterrupt

# Import schemas - adjust path based on your directory structure
try:
    from .schemas import DriveDraft, HumanReviewRequest, InterruptResponse
except ImportError:
    # Fallback if schemas not available
    print("Warning: Drive schemas not found, validation will be limited")
    DriveDraft = None
    HumanReviewRequest = None
    InterruptResponse = None


def add_human_in_the_loop(
    tool: Callable | BaseTool,
    *,
    interrupt_config: HumanInterruptConfig = None,
    require_approval: bool = True,
) -> BaseTool:
    """
    Wrap a tool to support human-in-the-loop review.

    Args:
        tool: The tool to wrap
        interrupt_config: Configuration for the interrupt
        require_approval: Whether to require human approval before execution
    """
    if not isinstance(tool, BaseTool):
        tool = create_tool(tool)

    if interrupt_config is None:
        interrupt_config = {
            "allow_accept": True,
            "allow_edit": True,
            "allow_respond": True,
        }

    @create_tool(
        tool.name,
        description=f"{tool.description} (with human approval)",
        args_schema=tool.args_schema
    )
    def call_tool_with_interrupt(config: RunnableConfig, **tool_input):
        """Execute tool with human-in-the-loop approval"""

        # Validate drive data if this is a critical drive tool
        critical_tools = [
            'Delete File', 'Delete Shared Drive', 'Delete Comment',
            'Move File to Trash', 'Remove Access Proposals', 'Remove Comment',
            'Update Shared Drive', 'Share File or Folder', 'Update File'
        ]

        if tool.name in critical_tools:
            try:
                # Basic validation for drive operations
                if tool.name in ['Delete File', 'Move File to Trash'] and 'file_id' in tool_input:
                    if not tool_input.get('file_id'):
                        return f"❌ Drive validation failed: file_id is required"

                if tool.name == 'Share File or Folder' and DriveDraft:
                    # Only validate if schemas are available
                    drive_draft = DriveDraft(**tool_input)
                    print(f"✓ Drive validation passed for {tool.name}")

            except Exception as e:
                return f"❌ Drive validation failed: {str(e)}"

        if not require_approval:
            # Skip approval for certain tools or contexts
            return tool.invoke(tool_input, config)

        # Create human review request
        request: HumanInterrupt = {
            "action_request": {
                "action": tool.name,
                "args": tool_input
            },
            "config": interrupt_config,
            "description": f"Please review the {tool.name} action before execution"
        }

        # Request human approval
        response = interrupt([request])[0]

        # Process human response
        if response["type"] == "accept":
            # Execute tool as requested
            tool_response = tool.invoke(tool_input, config)

        elif response["type"] == "edit":
            # Use edited arguments
            updated_args = response["args"]["args"]

            # Re-validate edited drive data
            if tool.name in critical_tools:
                try:
                    if tool.name in ['Delete File', 'Move File to Trash'] and 'file_id' in updated_args:
                        if not updated_args.get('file_id'):
                            return f"❌ Edited drive validation failed: file_id is required"

                    if tool.name == 'Share File or Folder' and DriveDraft:
                        drive_draft = DriveDraft(**updated_args)
                        print(f"✓ Edited drive validation passed for {tool.name}")

                except Exception as e:
                    return f"❌ Edited drive validation failed: {str(e)}"

            tool_response = tool.invoke(updated_args, config)

        elif response["type"] == "response":
            # Return user feedback instead of executing tool
            user_feedback = response["args"]
            tool_response = f"Human feedback: {user_feedback}"

        else:
            raise ValueError(f"Unsupported interrupt response type: {response['type']}")

        return tool_response

    return call_tool_with_interrupt


def create_drive_approval_tools(tools: List[BaseTool]) -> List[BaseTool]:
    """
    Wrap Google Drive tools with human-in-the-loop approval.

    Args:
        tools: List of Google Drive tools to wrap

    Returns:
        List of wrapped tools with human approval
    """
    wrapped_tools = []

    # Tools that require human approval (critical/destructive operations)
    approval_required_tools = [
        'Delete File',
        'Delete Shared Drive',
        'Delete Comment',
        'Move File to Trash',
        'Remove Access Proposals',
        'Remove Comment',
        'Update Shared Drive',
        'Share File or Folder',
        'Update File'
    ]

    # Tools that don't require approval (read-only or safe operations)
    no_approval_tools = [
        'List Files',
        'Get File By Id',
        'Get Folder ID on a Path',
        'Get Shared Drive',
        'List Access Proposals',
        'List Comments',
        'Search for Shared Drives',
        'Find File',
        'Find Folder',
        'Find Forms',
        'Find Spreadsheets',
        'Download File'
    ]

    for tool in tools:
        if tool.name in approval_required_tools:
            # Wrap with human approval
            wrapped_tool = add_human_in_the_loop(
                tool,
                interrupt_config={
                    "allow_accept": True,
                    "allow_edit": True,
                    "allow_respond": True,
                },
                require_approval=True
            )
            wrapped_tools.append(wrapped_tool)

        elif tool.name in no_approval_tools:
            # No approval needed for read-only tools
            wrapped_tools.append(tool)

        else:
            # Default: add approval for unknown tools to be safe
            wrapped_tool = add_human_in_the_loop(tool, require_approval=True)
            wrapped_tools.append(wrapped_tool)

    return wrapped_tools


def validate_drive_before_action(drive_data: Dict[str, Any], action_type: str) -> bool:
    """
    Validate Google Drive data before executing action

    Args:
        drive_data: Drive operation data to validate
        action_type: Type of drive action being performed

    Returns:
        True if valid, raises ValueError if invalid
    """
    try:
        # Validate using Pydantic model for sharing operations (if available)
        if action_type in ['Share File or Folder'] and DriveDraft:
            drive_draft = DriveDraft(**drive_data)

        # Additional business logic validation
        if action_type in ['Delete File', 'Move File to Trash']:
            if not drive_data.get('file_id'):
                raise ValueError("file_id is required for file operations")

        if action_type == 'Share File or Folder':
            if not drive_data.get('permission'):
                raise ValueError("permission data is required for sharing")

            # Check permission type is valid
            valid_roles = ['owner', 'organizer', 'fileOrganizer', 'writer', 'commenter', 'reader']
            permission = drive_data.get('permission', {})
            if permission.get('role') not in valid_roles:
                raise ValueError(f"Invalid permission role. Must be one of: {valid_roles}")

        if action_type == 'Update File':
            if not drive_data.get('file_id'):
                raise ValueError("file_id is required for file updates")

        if action_type in ['Delete Shared Drive', 'Update Shared Drive']:
            if not drive_data.get('drive_id'):
                raise ValueError("drive_id is required for shared drive operations")

        return True

    except Exception as e:
        raise ValueError(f"Drive validation failed: {str(e)}")
