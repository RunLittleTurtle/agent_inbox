"""
Job Search Orchestrator
Clean LangGraph implementation using SimpleRAG
Following KISS principles and LangGraph best practices
"""

from typing import Dict, Any, Optional, List
from typing_extensions import TypedDict

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from .simple_rag import SimpleRAG
from .config import LLM_CONFIG
from .tools import get_job_search_tools


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
    Clean job search orchestrator using SimpleRAG and LangGraph best practices

    Workflow:
    1. Initialize with default CV (automatically indexed)
    2. User uploads job posting via tools
    3. Generate tailored cover letter via tools
    4. Support CV queries and job matching via tools
    """

    def __init__(self, llm_config: Dict[str, Any] = None):
        """Initialize orchestrator"""
        self.llm_config = llm_config or LLM_CONFIG
        self.llm = ChatOpenAI(**self.llm_config)
        self.checkpointer = MemorySaver()

        # Initialize SimpleRAG with default CV
        self.simple_rag = self._initialize_rag()

        # Get tools
        self.tools = get_job_search_tools()

        # Build workflow - React agent comes pre-compiled
        self.workflow = self._build_workflow()

    def _initialize_rag(self) -> SimpleRAG:
        """Initialize SimpleRAG with default CV"""
        try:
            import os

            # Load default CV
            docs_path = os.path.join(
                os.path.dirname(__file__),
                "docs",
                "CV - Samuel Audette_Technical_Product_Manager_AI_2025_09.md"
            )

            if os.path.exists(docs_path):
                with open(docs_path, 'r', encoding='utf-8') as f:
                    default_cv = f.read()

                # Initialize RAG and index CV
                rag = SimpleRAG(self.llm_config)
                success = rag.index_cv_content(default_cv)

                if success:
                    print("✅ SimpleRAG initialized with default CV")
                else:
                    print("⚠️ SimpleRAG initialized but CV indexing failed")

                return rag
            else:
                print("⚠️ Default CV not found, initializing empty RAG")
                return SimpleRAG(self.llm_config)

        except Exception as e:
            print(f"⚠️ RAG initialization error: {e}")
            return SimpleRAG(self.llm_config)

    def _build_workflow(self):
        """Build simple React agent workflow"""

        # Create React agent with tools - this is already a complete graph
        # Create React agent with tools
        react_agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
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
    print("✅ SimpleRAG initialized with default CV")
    print("✅ React agent configured with job search tools")
