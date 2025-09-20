"""
Pydantic schemas for email validation and composition
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field, validator
import re


class EmailRecipient(BaseModel):
    """Validate email recipient"""
    email: EmailStr
    name: Optional[str] = None


class EmailContent(BaseModel):
    """Validate email content structure"""
    subject: str = Field(..., min_length=1, max_length=500, description="Email subject line")
    body: str = Field(..., min_length=1, description="Email body content")

    @validator('subject')
    def validate_subject(cls, v):
        if not v.strip():
            raise ValueError("Subject cannot be empty or whitespace only")
        return v.strip()

    @validator('body')
    def validate_body(cls, v):
        if not v.strip():
            raise ValueError("Body cannot be empty or whitespace only")
        return v.strip()


class EmailDraft(BaseModel):
    """Validate email draft before creation"""
    to: List[EmailStr] = Field(..., min_items=1, description="Recipient email addresses")
    subject: str = Field(..., min_length=1, max_length=500, description="Email subject")
    body: str = Field(..., min_length=1, description="Email body content")
    cc: Optional[List[EmailStr]] = Field(default=None, description="CC recipients")
    bcc: Optional[List[EmailStr]] = Field(default=None, description="BCC recipients")

    @validator('to', 'cc', 'bcc')
    def validate_email_lists(cls, v):
        if v is not None and len(v) == 0:
            return None
        return v

    @validator('subject')
    def validate_subject(cls, v):
        if not v.strip():
            raise ValueError("Subject cannot be empty")
        # Check for spam-like patterns
        spam_patterns = [r'\b(FREE|URGENT|ACT NOW)\b', r'!!!+', r'\$\$\$+']
        for pattern in spam_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError(f"Subject contains potentially spam-like content: {v}")
        return v.strip()

    def format_for_display(self) -> str:
        """Format email draft for human-readable display"""
        display = f"""
📧 **EMAIL READY FOR SENDING**

**To:** {', '.join(self.to)}
**CC:** {', '.join(self.cc) if self.cc else 'None'}
**BCC:** {', '.join(self.bcc) if self.bcc else 'None'}
**Subject:** {self.subject}

**Email Body:**
----------------------------------------
{self.body}
----------------------------------------
"""
        return display


class EmailCompositionRequest(BaseModel):
    """Request schema for email composition"""
    recipient: str = Field(..., description="Who is receiving this email")
    purpose: str = Field(..., description="Purpose/goal of the email")
    context: Optional[str] = Field(default=None, description="Additional context or background")
    tone: Optional[str] = Field(default="professional", description="Desired tone (professional, friendly, formal, etc.)")
    key_points: Optional[List[str]] = Field(default=None, description="Key points to include")
    call_to_action: Optional[str] = Field(default=None, description="Specific action requested from recipient")
    sender_name: str = Field(default="Samuel", description="Name of the sender")


class ComposedEmail(BaseModel):
    """Response schema for composed email"""
    subject: str = Field(..., description="Generated subject line")
    body: str = Field(..., description="Generated email body")
    reasoning: str = Field(..., description="Brief explanation of composition choices")
    tone_used: str = Field(..., description="Actual tone applied")


class HumanReviewRequest(BaseModel):
    """Schema for human review interrupt"""
    action: str = Field(..., description="Action being requested (e.g., 'send_email', 'create_draft')")
    email_data: Optional[EmailDraft] = Field(default=None, description="Email data to be reviewed")
    raw_args: Dict[str, Any] = Field(default_factory=dict, description="Raw tool arguments")
    reasoning: Optional[str] = Field(default=None, description="Why this email is being sent")

    def to_interrupt_format(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Convert to interrupt format for Agent Inbox UI"""
        description = "Please review this action"

        if self.email_data:
            description = self.email_data.format_for_display()
            description += "\nPlease review this email carefully before sending.\n"
            description += "Click 'Accept' to send immediately, 'Edit' to modify, or 'Reject' to cancel."
        elif self.action == "gmail-delete-email":
            email_id = self.raw_args.get('id', 'Unknown')
            description = f"""
⚠️ **WARNING: DELETE EMAIL**

Email ID: {email_id}

This action will permanently delete the email.
Please confirm this deletion.
"""

        return {
            "action_request": {
                "action": self.action,
                "args": self.raw_args,
                "email_preview": self.email_data.dict() if self.email_data else None
            },
            "config": config,
            "description": description
        }


class InterruptResponse(BaseModel):
    """Schema for interrupt response validation"""
    type: str = Field(..., description="Response type: 'accept', 'edit', 'response', or 'reject'")
    args: Optional[Dict[str, Any]] = Field(default=None, description="Additional arguments based on type")

    @validator('type')
    def validate_type(cls, v):
        valid_types = ['accept', 'edit', 'response', 'reject']
        if v not in valid_types:
            raise ValueError(f"Invalid response type. Must be one of: {valid_types}")
        return v


class EmailTracker(BaseModel):
    """Track email content across tool calls"""
    last_composed: Optional[ComposedEmail] = None
    last_draft: Optional[EmailDraft] = None
    draft_map: Dict[str, EmailDraft] = Field(default_factory=dict)

    def store_composed(self, email: ComposedEmail):
        """Store the last composed email"""
        self.last_composed = email

    def store_draft(self, draft_id: str, draft: EmailDraft):
        """Store a draft by ID"""
        self.last_draft = draft
        self.draft_map[draft_id] = draft

    def get_draft(self, draft_id: Optional[str] = None) -> Optional[EmailDraft]:
        """Get a draft by ID or the last draft"""
        if draft_id and draft_id in self.draft_map:
            return self.draft_map[draft_id]
        return self.last_draft

    def compose_to_draft(self) -> Optional[EmailDraft]:
        """Convert last composed email to draft format"""
        if not self.last_composed:
            return None

        # Parse recipient from composed email (this is simplified, might need enhancement)
        return EmailDraft(
            to=["recipient@example.com"],  # This would need to be extracted properly
            subject=self.last_composed.subject,
            body=self.last_composed.body,
            cc=None,
            bcc=None
        )
