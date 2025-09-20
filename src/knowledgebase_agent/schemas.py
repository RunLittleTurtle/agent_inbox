"""
Schemas for Google Drive operations validation
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator


class DrivePermission(BaseModel):
    """Drive permission schema"""
    role: str = Field(description="Permission role (owner, writer, reader, etc.)")
    type: str = Field(description="Permission type (user, group, domain, anyone)")
    email: Optional[str] = Field(None, description="Email address for user/group permissions")
    domain: Optional[str] = Field(None, description="Domain for domain permissions")

    @validator('role')
    def validate_role(cls, v):
        valid_roles = ['owner', 'organizer', 'fileOrganizer', 'writer', 'commenter', 'reader']
        if v not in valid_roles:
            raise ValueError(f'Role must be one of: {valid_roles}')
        return v

    @validator('type')
    def validate_type(cls, v):
        valid_types = ['user', 'group', 'domain', 'anyone']
        if v not in valid_types:
            raise ValueError(f'Type must be one of: {valid_types}')
        return v


class DriveDraft(BaseModel):
    """Drive operation schema for validation"""
    file_id: Optional[str] = Field(None, description="File ID")
    drive_id: Optional[str] = Field(None, description="Shared drive ID")
    permission: Optional[DrivePermission] = Field(None, description="Permission settings")
    name: Optional[str] = Field(None, description="File or folder name")
    description: Optional[str] = Field(None, description="Description")

    @validator('file_id')
    def validate_file_id(cls, v):
        if v and len(v.strip()) == 0:
            raise ValueError('file_id cannot be empty')
        return v


class HumanReviewRequest(BaseModel):
    """Human review request schema"""
    action: str = Field(description="Action being requested")
    args: Dict[str, Any] = Field(description="Action arguments")
    description: str = Field(description="Human-readable description")


class InterruptResponse(BaseModel):
    """Interrupt response schema"""
    type: str = Field(description="Response type (accept, edit, response)")
    args: Optional[Dict[str, Any]] = Field(None, description="Response arguments")
