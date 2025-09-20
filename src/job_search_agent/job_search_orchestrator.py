"""
Job Search Orchestrator
Clean LangGraph implementation using simple_rag.py
Following KISS principles and LangGraph best practices
"""

from typing import Dict, Any, Optional, List
from typing_extensions import TypedDict

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain_anthropic import ChatAnthropic

from .simple_rag import SimpleRAG
from .config import LLM_CONFIG
from .tools import get_job_search_tools
from .prompt import REACT_AGENT_SYSTEM_PROMPT


# =============================================================================
# STATE DEFINITION
# =============================================================================

class JobSearchState(TypedDict):
    """Simple state for job search workflow"""
    messages: List[BaseMessage]


# =============================================================================
# MAIN ORCHESTRATOR
# =============================================================================

class JobSearchOrchestrator:
    """
    Clean job search orchestrator using simple_rag.py

    Note: tools.py manages its own SimpleRAG instance with default CV.
    This orchestrator just provides the React agent framework.
    """

    def __init__(self, llm_config: Dict[str, Any] = None):
        """Initialize orchestrator"""
        self.llm_config = llm_config or LLM_CONFIG
        self.llm = ChatAnthropic(**self.llm_config)
        self.checkpointer = MemorySaver()

        # Get tools (tools.py manages its own SimpleRAG instance)
        self.tools = get_job_search_tools()

        # Build workflow - React agent comes pre-compiled
        self.workflow = self._build_workflow()

    def _build_workflow(self):
        """Build simple React agent workflow"""

        # Create React agent with tools and anti-hallucination prompt
        react_agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=REACT_AGENT_SYSTEM_PROMPT,
            name="job_search_agent"
        )

        return react_agent


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_job_search_orchestrator(llm_config: Dict[str, Any] = None):
    """
    Factory function to create job search orchestrator

    Args:
        llm_config: Optional LLM configuration

    Returns:
        React agent workflow ready for execution
    """
    orchestrator = JobSearchOrchestrator(llm_config)
    return orchestrator.workflow


def create_default_orchestrator():
    """
    Create orchestrator with default configuration

    Returns:
        React agent workflow ready for execution
    """
    orchestrator = JobSearchOrchestrator(LLM_CONFIG)
    return orchestrator.workflow


# =============================================================================
# MAIN INTERFACE FOR GRAPH.PY
# =============================================================================

def create_job_search_agent():
    """
    Main entry point for graph.py
    Returns React agent ready for LangGraph Studio
    """
    return create_default_orchestrator()


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    """Example usage of the orchestrator"""

    # Create orchestrator
    workflow = create_default_orchestrator()

    print("🚀 Job Search Orchestrator Created Successfully")
    print("✅ Ready for LangGraph Studio")
    print("✅ Tools use dedicated simple_rag.py for CV operations")
    print("✅ React agent configured with job search tools")
