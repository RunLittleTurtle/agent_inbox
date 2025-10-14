"""
Agent State Schema - TEMPLATE
Defines state management for Google OAuth agent using Pydantic v2.

CUSTOMIZATION REQUIRED:
1. Add domain-specific state fields (replace example_items, example_query)
2. Update reducers if you need custom merge logic
3. Keep MessagesState as base for LangGraph compatibility

LangGraph 2025 Best Practices:
- Inherit from MessagesState for message history
- Use Annotated for custom reducers
- Use Pydantic BaseModel for structured data
- Keep state minimal - only essential fields

State Examples:
- Calendar: current_events, booking_draft, calendar_preferences
- Contacts: current_contacts, contact_search_query, selected_contact
- Email: current_emails, email_draft, selected_labels
- Drive: current_files, upload_queue, folder_path
"""
from typing import Annotated, List, Dict, Optional, Any
from pydantic import BaseModel, Field
from langgraph.graph import MessagesState


# ==========================================================================
# CUSTOM REDUCERS (for merging state updates)
# ==========================================================================

def merge_dict_lists(left: Optional[List[Dict]], right: Optional[List[Dict]]) -> List[Dict]:
    """
    Merge two lists of dictionaries by 'id' field.
    This is useful for maintaining lists of items from Google APIs.

    Logic:
    - If right is empty/None, return left unchanged
    - Otherwise, merge right into left by ID
    - Items in right replace items in left with same ID
    - New items in right are appended

    Args:
        left: Existing list of dicts
        right: New list of dicts to merge

    Returns:
        Merged list with updated items
    """
    if not right:
        return left if left else []

    if not left:
        return right

    # Build lookup by ID
    merged = {item.get('id'): item for item in left}

    # Update/add items from right
    for item in right:
        item_id = item.get('id')
        if item_id:
            merged[item_id] = item

    return list(merged.values())


def append_if_new(left: Optional[List[str]], right: Optional[List[str]]) -> List[str]:
    """
    Append items from right to left, avoiding duplicates.

    Args:
        left: Existing list
        right: New items to append

    Returns:
        Combined list without duplicates
    """
    if not right:
        return left if left else []

    if not left:
        return right

    # Convert to set for deduplication, preserve order
    seen = set(left)
    result = list(left)

    for item in right:
        if item not in seen:
            result.append(item)
            seen.add(item)

    return result


# ==========================================================================
# STATE SCHEMA
# ==========================================================================

class GoogleAuthAgentState(MessagesState):
    """
    Generic Google OAuth agent state.

    Inherits from MessagesState to get:
    - messages: List[BaseMessage] - conversation history (auto-managed by LangGraph)

    Add domain-specific fields below.
    """

    # User identification (required for OAuth)
    user_id: str = Field(
        default="",
        description="Clerk user ID for loading Google OAuth credentials"
    )

    # ==========================================================================
    # TODO: ADD DOMAIN-SPECIFIC FIELDS HERE
    # ==========================================================================
    #
    # EXAMPLES FOR DIFFERENT DOMAINS:
    #
    # --- Calendar Agent ---
    # current_events: Annotated[List[Dict], merge_dict_lists] = Field(
    #     default_factory=list,
    #     description="List of calendar events currently being discussed"
    # )
    # booking_draft: Optional[Dict] = Field(
    #     default=None,
    #     description="Draft event for booking approval workflow"
    # )
    #
    # --- Contacts Agent ---
    # current_contacts: Annotated[List[Dict], merge_dict_lists] = Field(
    #     default_factory=list,
    #     description="List of contacts currently being discussed"
    # )
    # contact_search_query: Optional[str] = Field(
    #     default=None,
    #     description="Current search query for contacts"
    # )
    # selected_contact: Optional[Dict] = Field(
    #     default=None,
    #     description="Currently selected contact for detailed view"
    # )
    #
    # --- Email Agent ---
    # current_emails: Annotated[List[Dict], merge_dict_lists] = Field(
    #     default_factory=list,
    #     description="List of emails currently being discussed"
    # )
    # email_draft: Optional[Dict] = Field(
    #     default=None,
    #     description="Draft email for send approval workflow"
    # )
    # selected_labels: Annotated[List[str], append_if_new] = Field(
    #     default_factory=list,
    #     description="Gmail labels to filter by"
    # )
    #
    # --- Drive Agent ---
    # current_files: Annotated[List[Dict], merge_dict_lists] = Field(
    #     default_factory=list,
    #     description="List of Drive files currently being discussed"
    # )
    # current_folder_id: Optional[str] = Field(
    #     default=None,
    #     description="Current folder being browsed"
    # )

    # TEMPLATE: Generic placeholder fields (REPLACE with your domain-specific fields)
    example_items: Annotated[List[Dict], merge_dict_lists] = Field(
        default_factory=list,
        description="TODO: Replace with your domain-specific list (e.g., contacts, events, emails)"
    )

    example_query: Optional[str] = Field(
        default=None,
        description="TODO: Replace with your domain-specific query field"
    )

    example_selected_item: Optional[Dict] = Field(
        default=None,
        description="TODO: Replace with your domain-specific selected item"
    )

    # ==========================================================================
    # OPTIONAL: Human-in-the-loop fields (only if your agent needs approval workflows)
    # ==========================================================================
    # approval_required: bool = Field(
    #     default=False,
    #     description="Whether current operation requires human approval"
    # )
    #
    # approval_granted: bool = Field(
    #     default=False,
    #     description="Whether human has approved the operation"
    # )


# ==========================================================================
# OPTIONAL: Additional Pydantic Models for Structured Data
# ==========================================================================
# Use these for validating structured inputs/outputs from LLM or tools

# Example: Contact schema for Contacts Agent
# class Contact(BaseModel):
#     id: str
#     name: str
#     email: Optional[str] = None
#     phone: Optional[str] = None
#
# Example: Event schema for Calendar Agent
# class CalendarEvent(BaseModel):
#     id: str
#     title: str
#     start_time: str
#     end_time: str
#     description: Optional[str] = None
#
# Example: Email schema for Email Agent
# class EmailMessage(BaseModel):
#     id: str
#     subject: str
#     sender: str
#     snippet: str
#     labels: List[str] = []

class ExampleItem(BaseModel):
    """
    TODO: Replace with your domain-specific data model.

    Example: Contact, CalendarEvent, EmailMessage, DriveFile
    """
    id: str = Field(description="Unique identifier")
    name: str = Field(description="Display name")
    description: Optional[str] = Field(default=None, description="Additional details")

    # TODO: Add domain-specific fields
    # email: Optional[str] = None
    # phone: Optional[str] = None
    # start_time: Optional[str] = None
    # end_time: Optional[str] = None
