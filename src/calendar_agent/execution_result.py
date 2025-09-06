"""
Execution Result Management for Calendar Operations
Single source of truth for MCP tool execution results and state management.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field
from uuid import uuid4


class ExecutionStatus(str, Enum):
    """Status of MCP tool execution"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MCPToolResult(BaseModel):
    """Structured result from a single MCP tool execution"""
    tool_name: str = Field(..., description="Name of the MCP tool")
    status: ExecutionStatus = Field(..., description="Execution status")
    raw_result: Any = Field(..., description="Raw result from MCP tool")
    success: bool = Field(..., description="Whether the operation succeeded")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    api_restrictions: List[str] = Field(default_factory=list, description="API restrictions encountered")
    data_returned: Optional[Dict[str, Any]] = Field(default=None, description="Structured data from result")
    execution_time: float = Field(default=0.0, description="Time taken in seconds")

    def is_successful(self) -> bool:
        """Check if execution was successful"""
        return self.status in [ExecutionStatus.SUCCESS, ExecutionStatus.PARTIAL_SUCCESS]

    def get_error_details(self) -> str:
        """Get detailed error information"""
        if self.error_message:
            return self.error_message
        if not self.success:
            return f"Tool {self.tool_name} failed: {str(self.raw_result)}"
        return "No error"


class BookingExecutionResult(BaseModel):
    """Complete result of a booking operation (may involve multiple MCP tools)"""
    execution_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique execution ID")
    booking_title: str = Field(..., description="Title of the booking")
    user_request: str = Field(..., description="Original user request")
    overall_status: ExecutionStatus = Field(..., description="Overall execution status")

    # MCP tool results
    tool_results: List[MCPToolResult] = Field(default_factory=list, description="Results from all MCP tools")

    # Metadata
    started_at: datetime = Field(default_factory=datetime.now, description="When execution started")
    completed_at: Optional[datetime] = Field(default=None, description="When execution completed")

    # Result analysis
    successful_operations: List[str] = Field(default_factory=list, description="Successfully completed operations")
    failed_operations: List[str] = Field(default_factory=list, description="Failed operations")
    api_restrictions_encountered: List[str] = Field(default_factory=list, description="API restrictions found")

    # User-facing messages
    success_message: str = Field(default="", description="Message for successful operations")
    error_message: str = Field(default="", description="Message for errors")
    info_message: str = Field(default="", description="Additional information for user")

    def add_tool_result(self, result: MCPToolResult):
        """Add a tool result and update overall status"""
        self.tool_results.append(result)

        if result.is_successful():
            self.successful_operations.append(f"{result.tool_name}: Success")
        else:
            self.failed_operations.append(f"{result.tool_name}: {result.get_error_details()}")

        # Collect API restrictions
        self.api_restrictions_encountered.extend(result.api_restrictions)

        # Update overall status
        self._update_overall_status()

    def _update_overall_status(self):
        """Update overall status based on tool results"""
        if not self.tool_results:
            self.overall_status = ExecutionStatus.PENDING
            return

        successful = [r for r in self.tool_results if r.is_successful()]
        failed = [r for r in self.tool_results if not r.is_successful()]

        if len(successful) == len(self.tool_results):
            self.overall_status = ExecutionStatus.SUCCESS
        elif len(successful) > 0:
            self.overall_status = ExecutionStatus.PARTIAL_SUCCESS
        else:
            self.overall_status = ExecutionStatus.FAILED

    def complete_execution(self):
        """Mark execution as completed and generate user messages"""
        self.completed_at = datetime.now()
        self._generate_user_messages()

    def _generate_user_messages(self):
        """Generate appropriate user-facing messages based on results"""
        if self.overall_status == ExecutionStatus.SUCCESS:
            self.success_message = f"✅ {self.booking_title} completed successfully!"
            if self.api_restrictions_encountered:
                self.info_message = "ℹ️ " + "; ".join(set(self.api_restrictions_encountered))

        elif self.overall_status == ExecutionStatus.PARTIAL_SUCCESS:
            self.success_message = f"⚠️ {self.booking_title} partially completed"
            self.error_message = "Some operations failed: " + "; ".join(self.failed_operations)
            if self.api_restrictions_encountered:
                self.info_message = "ℹ️ " + "; ".join(set(self.api_restrictions_encountered))

        else:
            self.error_message = f"❌ {self.booking_title} failed: " + "; ".join(self.failed_operations)

    def get_supervisor_message(self) -> str:
        """Get the complete message to send to supervisor"""
        parts = []

        if self.success_message:
            parts.append(self.success_message)

        if self.error_message:
            parts.append(self.error_message)

        if self.info_message:
            parts.append(self.info_message)

        # Add operation details
        if self.successful_operations:
            parts.append("📋 Successful operations:")
            for op in self.successful_operations:
                parts.append(f"  • {op}")

        if self.failed_operations:
            parts.append("❌ Failed operations:")
            for op in self.failed_operations:
                parts.append(f"  • {op}")

        return "\n".join(parts)

    def get_task_result_summary(self) -> str:
        """Get summary for task tracking"""
        if self.overall_status == ExecutionStatus.SUCCESS:
            return f"Successfully completed: {self.booking_title}"
        elif self.overall_status == ExecutionStatus.PARTIAL_SUCCESS:
            return f"Partially completed: {self.booking_title} - {len(self.failed_operations)} operations failed"
        else:
            return f"Failed: {self.booking_title} - {self.get_primary_error()}"

    def get_primary_error(self) -> str:
        """Get the primary error message"""
        if self.failed_operations:
            return self.failed_operations[0]
        return "Unknown error"
