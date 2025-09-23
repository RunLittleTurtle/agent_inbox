"""
Data schemas for the agent
MOST AGENTS DON'T NEED THIS - MessagesState is usually sufficient
Only add schemas if you have domain-specific data structures
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel

# TODO: Only add schemas if you really need them
# Most React agents work fine with just MessagesState

class ToolResponse(BaseModel):
    """Standard response format for tool operations"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

# TODO: Add domain-specific schemas only if needed
# Example:
# class EmailData(BaseModel):
#     id: str
#     subject: str
#     content: str
