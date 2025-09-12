"""
Global State pour le multi-agent system
Intégration native avec LangGraph en gardant le principe KISS
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence
from uuid import uuid4
from enum import Enum

from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, MessagesState, START, END, add_messages
from typing_extensions import Annotated


class AgentType(str, Enum):
    """Types d'agents disponibles"""
    CALENDAR_AGENT = "calendar_agent"
    EMAIL_AGENT = "email_agent"
    JOB_SEARCH_AGENT = "job_search_agent"
    SUPERVISOR = "supervisor"


class TaskStatus(str, Enum):
    """Statut d'une tâche"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class SimpleTask(BaseModel):
    """Tâche simple pour le tracking basique"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    agent_name: AgentType = Field(...)
    description: str = Field(...)
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    user_request: str = Field(...)
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = Field(default=None)
    result: Optional[str] = Field(default=None)

    def complete(self, result: str):
        """Marquer la tâche comme complétée"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        self.result = result

    def fail(self, error: str):
        """Marquer la tâche comme échouée"""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now()
        self.result = f"Error: {error}"


def add_tasks(existing: List[SimpleTask], new: List[SimpleTask]) -> List[SimpleTask]:
    """Reducer pour les tâches"""
    existing_map = {task.id: task for task in existing}
    for task in new:
        existing_map[task.id] = task
    return list(existing_map.values())


# États additionnels pour les agents spécialisés
class RoutingDecision(BaseModel):
    """Décision de routage pour les agents"""
    agent: AgentType = Field(...)
    reason: str = Field(...)

class BookingContext(BaseModel):
    """Contexte pour les réservations calendar"""
    event_type: str = Field(...)
    duration: Optional[int] = Field(default=None)
    attendees: List[str] = Field(default_factory=list)

# State compatible avec graph.py existant - utilise la structure simple de BaseModel
class WorkflowState(BaseModel):
    """
    State global compatible avec graph.py existant
    Structure simple pour assurer la compatibilité
    """

    # Messages - compatible avec graph.py existant (List[BaseMessage])
    messages: List[BaseMessage] = Field(
        default_factory=list,
        description="Message history"
    )

    # Contexte temporel (exactement comme dans graph.py existant)
    current_time: str = Field(..., description="Timestamp actuel")
    timezone: str = Field(default="America/Toronto", description="Timezone")
    timezone_name: str = Field(default="America/Toronto", description="Nom du timezone")

    # Tracking simple des tâches
    tasks: List[SimpleTask] = Field(
        default_factory=list,
        description="Tâches avec tracking basique"
    )

    # Compteurs simples
    agent_call_count: Dict[AgentType, int] = Field(
        default_factory=dict,
        description="Nombre d'appels par agent"
    )

    # États spécialisés pour les agents
    routing_decision: Optional[RoutingDecision] = Field(
        default=None,
        description="Dernière décision de routage"
    )

    booking_context: Optional[BookingContext] = Field(
        default=None,
        description="Contexte de réservation pour calendar agent"
    )

    def add_task(self, agent_name: AgentType, description: str, user_request: str) -> SimpleTask:
        """Ajouter une nouvelle tâche"""
        task = SimpleTask(
            agent_name=agent_name,
            description=description,
            user_request=user_request
        )
        self.tasks.append(task)

        # Incrémenter le compteur d'appels
        self.agent_call_count[agent_name] = self.agent_call_count.get(agent_name, 0) + 1

        return task

    def get_task_summary(self) -> Dict[str, Any]:
        """Résumé simple des tâches"""
        total = len(self.tasks)
        completed = len([t for t in self.tasks if t.status == TaskStatus.COMPLETED])
        failed = len([t for t in self.tasks if t.status == TaskStatus.FAILED])

        return {
            "total_tasks": total,
            "completed_tasks": completed,
            "failed_tasks": failed,
            "success_rate": completed / total if total > 0 else 0,
            "agent_calls": dict(self.agent_call_count)
        }

# State avec support LangGraph natif pour les nouveaux graphes
class GlobalWorkflowState(BaseModel):
    """
    State avancé avec reducers LangGraph natifs
    Pour les nouveaux graphes qui veulent utiliser les patterns LangGraph
    """

    # Messages avec reducer LangGraph natif
    messages: Annotated[Sequence[BaseMessage], add_messages] = Field(
        default_factory=list,
        description="Message history avec reducer automatique"
    )

    # Contexte temporel
    current_time: str = Field(..., description="Timestamp actuel")
    timezone: str = Field(default="America/Toronto", description="Timezone")
    timezone_name: str = Field(default="America/Toronto", description="Nom du timezone")

    # Tracking avec reducer natif
    tasks: Annotated[List[SimpleTask], add_tasks] = Field(
        default_factory=list,
        description="Tâches avec reducer automatique"
    )

    # Compteurs simples
    agent_call_count: Dict[AgentType, int] = Field(
        default_factory=dict,
        description="Nombre d'appels par agent"
    )

    # États spécialisés
    routing_decision: Optional[RoutingDecision] = Field(default=None)
    booking_context: Optional[BookingContext] = Field(default=None)

    def add_task(self, agent_name: AgentType, description: str, user_request: str) -> SimpleTask:
        """Ajouter une nouvelle tâche"""
        task = SimpleTask(
            agent_name=agent_name,
            description=description,
            user_request=user_request
        )
        # Le reducer add_tasks s'occupe de l'ajout
        self.tasks = add_tasks(self.tasks, [task])

        self.agent_call_count[agent_name] = self.agent_call_count.get(agent_name, 0) + 1
        return task

# États spécialisés pour compatibility avec calendar_orchestrator
CalendarAgentState = GlobalWorkflowState
