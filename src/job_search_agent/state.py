"""
Job Search Agent State Management
Simple state definition for LangGraph React agent
"""
from typing import Dict, Any, List, Optional
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage


class JobSearchState(TypedDict):
    """Simple state for job search workflow"""
    messages: List[BaseMessage]

    # Job-specific data (replaces document_store)
    job_posting: Optional[str]
    job_analysis: Optional[Dict[str, Any]]
    cv_analysis: Optional[Dict[str, Any]]


def get_thread_config(thread_id: str) -> Dict[str, Any]:
    """Get thread configuration for LangGraph checkpointer"""
    return {
        "configurable": {
            "thread_id": thread_id
        }
    }
