"""
KISS-Compliant State for Multi-Agent System
Minimal changes to original state.py to work with prebuilt components
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence
from uuid import uuid4
from enum import Enum

from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import MessagesState, add_messages
from typing_extensions import Annotated


class AgentType(str, Enum):
    """Types d'agents disponibles"""
    CALENDAR_AGENT = "calendar_agent"
    EMAIL_AGENT = "email_agent"
    JOB_SEARCH_AGENT = "job_search_agent"
    SUPERVISOR = "supervisor"


class TaskStatus(str, Enum):
    """Status of a task"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class SimpleTask(BaseModel):
    """Simple task for basic tracking"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    agent_name: AgentType = Field(...)
    description: str = Field(...)
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    user_request: str = Field(...)
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = Field(default=None)
    result: Optional[str] = Field(default=None)

    def complete(self, result: str):
        """Mark the task as completed"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        self.result = result

    def fail(self, error: str):
        """Mark the task as failed"""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now()
        self.result = f"Error: {error}"


def add_tasks(existing: List[SimpleTask], new: List[SimpleTask]) -> List[SimpleTask]:
    """Reducer for tasks"""
    existing_map = {task.id: task for task in existing}
    for task in new:
        existing_map[task.id] = task
    return list(existing_map.values())


# KISS-Compliant State for Prebuilt Components
class WorkflowState(MessagesState):  #  MUST inherit from MessagesState
    """
    Simple state compatible with create_react_agent and langgraph_supervisor
    Only adds what's absolutely necessary beyond messages
    """

    # Temporal context (from your existing graph.py)
    current_time: str = Field(..., description="Timestamp actuel")
    timezone: str = Field(default="America/Toronto", description="Timezone")
    timezone_name: str = Field(default="America/Toronto", description="Nom du timezone")

    # Minimal task tracking - ONLY what supervisor needs to know
    current_agent: Optional[AgentType] = Field(
        default=None,
        description="Which agent is currently handling the request"
    )

    # Simple agent completion tracking - just what's needed for routing
    completed_agents: List[AgentType] = Field(
        default_factory=list,
        description="Agents that finished their current task"
    )

    # Basic task history for visibility
    tasks: List[SimpleTask] = Field(
        default_factory=list,
        description="Task history for tracking"
    )

    def add_task(self, agent_name: AgentType, description: str, user_request: str) -> SimpleTask:
        """Simple task creation"""
        task = SimpleTask(
            agent_name=agent_name,
            description=description,
            user_request=user_request
        )
        self.tasks.append(task)
        return task

    def mark_agent_completed(self, agent_name: AgentType):
        """Mark agent as completed - simple tracking"""
        if agent_name not in self.completed_agents:
            self.completed_agents.append(agent_name)
        self.current_agent = None

    def get_summary(self) -> Dict[str, Any]:
        """Simple summary for supervisor visibility"""
        total = len(self.tasks)
        completed = len([t for t in self.tasks if t.status == TaskStatus.COMPLETED])

        return {
            "total_tasks": total,
            "completed_tasks": completed,
            "success_rate": completed / total if total > 0 else 0,
            "current_agent": self.current_agent.value if self.current_agent else None,
            "completed_agents": [a.value for a in self.completed_agents]
        }


# For compatibility with existing code
GlobalWorkflowState = WorkflowState
CalendarAgentState = WorkflowState
