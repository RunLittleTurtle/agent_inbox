# LangGraph Development Guide

A comprehensive guide for building robust, scalable AI agents using LangGraph best practices. This document provides specific patterns, code examples, and debugging strategies for developing high-quality LangGraph applications.

## 1. Structure Requirements

### Mandatory Codebase Search Before Development

**ALWAYS search before creating new files or functionality:**

```python
# Search pattern workflow - NEVER skip this step
# 1. Search for existing implementations
grep -r "StateGraph" src/ --include="*.py"
grep -r "create_react_agent" src/ --include="*.py"
grep -r "class.*State" src/ --include="*.py"

# 2. Search for similar patterns
find . -name "*agent*.py" -type f
find . -name "*state*.py" -type f

# 3. Examine existing structure before creating
```

### File Organization Patterns

**Agent Structure (Single Responsibility)**
```
src/
├── agents/
│   ├── research_agent/
│   │   ├── __init__.py
│   │   ├── state.py          # Agent-specific state schema
│   │   ├── tools.py          # Agent-specific tools
│   │   ├── graph.py          # Graph construction
│   │   └── prompts.py        # Agent prompts
│   └── analysis_agent/
│       ├── __init__.py
│       ├── state.py
│       ├── tools.py
│       ├── graph.py
│       └── prompts.py
├── shared/
│   ├── state.py              # Shared state schemas
│   ├── tools.py              # Common tools
│   └── utils.py              # Utilities
└── supervisor/
    ├── __init__.py
    ├── supervisor.py         # Multi-agent coordination
    └── routing.py            # Agent routing logic
```

**State Schema Organization**
```python
# src/shared/state.py - Base state schemas
from typing import Annotated, Sequence, TypedDict, List, Optional, Dict, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class BaseAgentState(TypedDict):
    """Base state schema for all agents"""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    current_step: str
    error_count: int

class ResearchState(BaseAgentState):
    """Research agent specific state"""
    search_results: List[Dict[str, Any]]
    sources: List[str]
    confidence_score: float

# src/agents/research_agent/state.py - Agent-specific extensions
from shared.state import ResearchState
from typing import List, Optional

class ExtendedResearchState(ResearchState):
    """Extended research state with additional fields"""
    research_depth: int
    topic_focus: Optional[str]
```

### Import Conventions

**Correct Import Patterns**
```python
# Standard library first
import asyncio
import logging
from datetime import datetime
from typing import Annotated, Sequence, TypedDict, List, Optional, Dict, Any

# Third-party imports
from pydantic import BaseModel, Field

# LangChain imports (grouped)
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate

# LangGraph imports (grouped)
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import create_react_agent, ToolNode
from langgraph.checkpoint.sqlite import SqliteSaver

# Local imports (relative)
from .state import ResearchState
from .tools import research_tools
from ..shared.utils import format_response
```

**AVOID These Import Patterns**
```python
# ❌ Wildcard imports
from langgraph.graph import *

# ❌ Mixing import styles
from langgraph.graph import StateGraph, END
import langgraph.graph

# ❌ Circular imports
from agents.research_agent import research_graph  # If research_agent imports this module
```

### Module Structure Standards

**Agent Module Template**
```python
# src/agents/research_agent/__init__.py
"""Research Agent for information gathering and analysis."""

from .graph import create_research_agent
from .state import ResearchState

__all__ = ["create_research_agent", "ResearchState"]

# src/agents/research_agent/graph.py
"""Research agent graph construction."""

from typing import Dict, Any
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent

from .state import ResearchState
from .tools import research_tools
from .prompts import RESEARCH_PROMPT

def create_research_agent(model, checkpointer=None):
    """Create a research agent with proper configuration."""

    # Create the react agent
    agent = create_react_agent(
        model=model,
        tools=research_tools,
        prompt=RESEARCH_PROMPT
    )

    # Add checkpointer if provided
    if checkpointer:
        agent = agent.compile(checkpointer=checkpointer)

    return agent
```

### Export Patterns

**Clean Agent Interfaces**
```python
# src/agents/research_agent/graph.py
def create_research_agent(
    model,
    tools: Optional[List] = None,
    checkpointer = None,
    config: Optional[Dict[str, Any]] = None
) -> StateGraph:
    """
    Create a research agent with standardized interface.

    Args:
        model: Language model instance
        tools: Optional custom tools list
        checkpointer: Optional persistence layer
        config: Optional configuration dictionary

    Returns:
        Compiled StateGraph ready for invocation

    Example:
        >>> agent = create_research_agent(
        ...     model=ChatAnthropic(model="claude-3-sonnet"),
        ...     checkpointer=SqliteSaver.from_conn_string(":memory:")
        ... )
        >>> result = agent.invoke(
        ...     {"messages": [HumanMessage(content="Research AI trends")]},
        ...     {"configurable": {"thread_id": "123"}}
        ... )
    """
    # Implementation here
    pass

# Export function for external use
__all__ = ["create_research_agent"]
```

### Search-First Development Workflow

**Required Search Pattern Before Creating**
```python
# Step 1: Search for existing state schemas
# Command: grep -r "class.*State" src/ --include="*.py"

# Step 2: Search for similar functionality
# Command: grep -r "research" src/ --include="*.py" -i

# Step 3: Check for existing tools
# Command: find . -name "*tools*" -type f

# Step 4: Examine similar agents
# Command: ls -la src/agents/

# Example implementation after search:
def create_new_agent_after_search():
    """Only create after thorough search reveals no existing solution."""

    # Found existing ResearchState in shared/state.py - reuse it
    from shared.state import ResearchState

    # Found similar tools in shared/tools.py - extend them
    from shared.tools import base_search_tool

    # Extend existing pattern rather than recreate
    extended_tools = base_search_tool + [new_specific_tool]

    return create_react_agent(model, extended_tools)
```

### Structured Output Validation

**Input/Output Schema Validation**
```python
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from langchain_core.output_parsers import PydanticOutputParser

class ResearchOutput(BaseModel):
    """Structured output for research results."""

    summary: str = Field(..., description="Research summary")
    sources: List[str] = Field(..., description="Source URLs")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    key_findings: List[str] = Field(..., description="Key findings list")

    @validator('sources')
    def validate_sources(cls, v):
        if not v:
            raise ValueError("At least one source is required")
        return v

# Integration with LangGraph node
def research_node(state: ResearchState) -> Dict[str, Any]:
    """Research node with structured output validation."""

    # Create parser
    parser = PydanticOutputParser(pydantic_object=ResearchOutput)

    # Add parser instructions to prompt
    prompt_with_parser = research_prompt + parser.get_format_instructions()

    try:
        # Get LLM response
        response = model.invoke(prompt_with_parser)

        # Parse and validate
        parsed_output = parser.parse(response.content)

        return {
            "messages": [AIMessage(content=str(parsed_output))],
            "search_results": parsed_output.sources,
            "confidence_score": parsed_output.confidence
        }

    except Exception as e:
        # Handle parsing errors gracefully
        return {
            "messages": [AIMessage(content=f"Parsing error: {str(e)}")],
            "error_count": state.get("error_count", 0) + 1
        }
```

### Framework Integration Debugging Patterns

**LangGraph State Debugging**
```python
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def debug_state_changes(state_before: Dict, state_after: Dict, node_name: str):
    """Debug state changes between nodes."""

    logger.info(f"=== {node_name.upper()} NODE DEBUG ===")

    # Check message changes
    messages_before = len(state_before.get("messages", []))
    messages_after = len(state_after.get("messages", []))

    if messages_after != messages_before:
        logger.info(f"Messages: {messages_before} -> {messages_after}")

        # Log new messages
        new_messages = state_after["messages"][messages_before:]
        for i, msg in enumerate(new_messages):
            logger.info(f"New message {i}: {type(msg).__name__} - {msg.content[:100]}...")

    # Check other state changes
    for key in set(state_before.keys()) | set(state_after.keys()):
        if state_before.get(key) != state_after.get(key):
            logger.info(f"{key}: {state_before.get(key)} -> {state_after.get(key)}")

# Usage in nodes
def research_node_with_debug(state: ResearchState) -> Dict[str, Any]:
    """Research node with debugging."""

    state_before = dict(state)

    # Node logic here
    result = {
        "messages": state["messages"] + [AIMessage(content="Research complete")],
        "current_step": "analysis"
    }

    # Debug state changes
    debug_state_changes(state_before, {**state, **result}, "research")

    return result
```

**Documentation References:**
- LangGraph State Management: https://langchain-ai.github.io/langgraph/concepts/low_level/#state
- TypedDict vs Pydantic: https://langchain-ai.github.io/langgraph/concepts/low_level/#schema
- Import Best Practices: https://python.langchain.com/docs/contributing/code_style
- Structured Outputs: https://python.langchain.com/docs/how_to/structured_output

## 2. Deployment-First

### Local Development Stack Architecture

**Core Components Integration**
```python
# Local development setup with full stack integration
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.store.memory import InMemoryStore
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
import os

def setup_local_development_stack():
    """Complete local development stack setup."""

    # 1. SQLite Persistence (Primary)
    checkpointer = SqliteSaver.from_conn_string("data/checkpoints.db")

    # 2. Memory Store for cross-thread data
    store = InMemoryStore()

    # 3. Vector Store Integration
    embeddings = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"))
    vectorstore = Chroma(
        persist_directory="data/vectorstore",
        embedding_function=embeddings
    )

    # 4. Graph compilation with all components
    graph = workflow.compile(
        checkpointer=checkpointer,
        store=store,
        debug=True  # Enable debug mode for development
    )

    return graph, vectorstore, store
```

### Environment Configuration Patterns

**Bulletproof Environment Setup**
```python
# config/environment.py
import os
from pathlib import Path
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

class EnvironmentConfig:
    """Environment configuration with validation and fallbacks."""

    def __init__(self):
        self.load_environment()
        self.validate_required_vars()
        self.setup_directories()

    def load_environment(self):
        """Load environment variables with precedence order."""

        # 1. Load from .env file
        env_file = Path(".env")
        if env_file.exists():
            load_dotenv(env_file)
            logger.info("Loaded environment from .env file")

        # 2. Development vs Production detection
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.debug_mode = self.environment == "development"

        # 3. API Keys with validation
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.langsmith_api_key = os.getenv("LANGSMITH_API_KEY")

        # 4. Local development specific
        self.user_timezone = os.getenv("USER_TIMEZONE", "America/Toronto")
        self.sqlite_path = os.getenv("SQLITE_PATH", "data/checkpoints.db")
        self.vectorstore_path = os.getenv("VECTORSTORE_PATH", "data/vectorstore")

    def validate_required_vars(self):
        """Validate required environment variables."""

        required_vars = {
            "OPENAI_API_KEY": self.openai_api_key,
            "ANTHROPIC_API_KEY": self.anthropic_api_key,
        }

        missing_vars = [var for var, value in required_vars.items() if not value]

        if missing_vars:
            raise EnvironmentError(
                f"Missing required environment variables: {missing_vars}\n"
                f"Please set them in your .env file or environment"
            )

        logger.info("All required environment variables validated")

    def setup_directories(self):
        """Ensure required directories exist."""

        directories = [
            Path(self.sqlite_path).parent,
            Path(self.vectorstore_path),
            Path("logs"),
            Path("data/documents")
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

        logger.info("Required directories created/validated")

# Usage
config = EnvironmentConfig()
```

**Environment File Template (.env.example)**
```bash
# Core API Keys
OPENAI_API_KEY=sk-your_openai_key_here
ANTHROPIC_API_KEY=sk-ant-your_anthropic_key_here

# Optional: LangSmith for tracing
LANGSMITH_API_KEY=lsv2_pt_your_langsmith_key_here
LANGSMITH_TRACING=true
LANGCHAIN_PROJECT=agent-inbox-local-dev

# Local Development Configuration
ENVIRONMENT=development
USER_TIMEZONE=America/Toronto
SQLITE_PATH=data/checkpoints.db
VECTORSTORE_PATH=data/vectorstore

# MCP Server Configuration (if using external MCP servers)
PIPEDREAM_MCP_SERVER=https://your-account.m.pipedream.net/mcp

# Optional: Vector Store Configuration
EMBEDDING_MODEL=text-embedding-3-small
VECTOR_STORE_TYPE=chroma
```

### MCP Server Integration Patterns

**Documentation Server Setup**
```python
# mcp/documentation_client.py
from langchain_mcp_adapters import MCPClient
import asyncio
import logging

logger = logging.getLogger(__name__)

class DocumentationMCPClient:
    """MCP client for LangGraph documentation access."""

    def __init__(self):
        self.client = None
        self.is_initialized = False

    async def initialize(self):
        """Initialize MCP client with error handling."""

        try:
            # Use the local MCP server configuration
            self.client = MCPClient()
            await self.client.connect("uvx --from mcpdoc mcpdoc --urls 'LangGraph Python:https://langchain-ai.github.io/langgraph/llms.txt LangGraph JS:https://langchain-ai.github.io/langgraphjs/llms.txt LangChain Python:https://python.langchain.com/llms.txt LangChain JS:https://js.langchain.com/llms.txt' --transport stdio")

            self.is_initialized = True
            logger.info("MCP Documentation client initialized successfully")

            return True

        except Exception as e:
            logger.warning(f"MCP client initialization failed: {e}")
            logger.info("Continuing without MCP documentation access")
            return False

    async def search_documentation(self, query: str, source: str = "LangGraph Python") -> str:
        """Search documentation with fallback handling."""

        if not self.is_initialized:
            return f"Documentation search unavailable. Query: {query}"

        try:
            # Use MCP tools to search documentation
            tools = await self.client.list_tools()

            # Find the documentation search tool
            search_tool = next((tool for tool in tools if "fetch_docs" in tool.name), None)

            if search_tool:
                result = await self.client.call_tool(
                    search_tool.name,
                    {"source": source, "query": query}
                )
                return result.content
            else:
                return f"Documentation search tool not available for query: {query}"

        except Exception as e:
            logger.warning(f"MCP documentation search failed: {e}")
            return f"Documentation search failed for query: {query}"

# Global instance for reuse
documentation_client = DocumentationMCPClient()
```

**MCP Tool Integration in Agents**
```python
from langchain_core.tools import tool
from typing import Optional

@tool
async def search_langgraph_docs(query: str, source: str = "LangGraph Python") -> str:
    """
    Search LangGraph documentation for implementation examples and best practices.

    Args:
        query: Search query for documentation
        source: Documentation source (LangGraph Python, LangChain Python, etc.)

    Returns:
        Relevant documentation content or fallback message
    """

    # Ensure MCP client is initialized
    if not documentation_client.is_initialized:
        await documentation_client.initialize()

    # Search documentation
    result = await documentation_client.search_documentation(query, source)

    return f"Documentation search results for '{query}':\n\n{result}"

# Include in agent tools
documentation_tools = [search_langgraph_docs]
```

### Persistence Strategy Implementation

**SQLite Checkpointer Patterns**
```python
from langgraph.checkpoint.sqlite import SqliteSaver
from pathlib import Path
import sqlite3
import logging

logger = logging.getLogger(__name__)

class ProductionSqliteSaver:
    """Production-ready SQLite checkpointer with error handling."""

    @classmethod
    def create_checkpointer(cls, db_path: str = "data/checkpoints.db") -> SqliteSaver:
        """Create SQLite checkpointer with proper setup."""

        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        try:
            # Create checkpointer
            checkpointer = SqliteSaver.from_conn_string(db_path)

            # Test connection
            cls.test_connection(checkpointer)

            logger.info(f"SQLite checkpointer created successfully: {db_path}")
            return checkpointer

        except Exception as e:
            logger.error(f"Failed to create SQLite checkpointer: {e}")

            # Fallback to in-memory
            logger.info("Falling back to in-memory checkpointer")
            return SqliteSaver.from_conn_string(":memory:")

    @staticmethod
    def test_connection(checkpointer: SqliteSaver):
        """Test checkpointer connection."""

        try:
            # Simple test by creating a dummy checkpoint
            test_config = {"configurable": {"thread_id": "test_connection"}}

            # This will create tables if they don't exist
            list(checkpointer.list(test_config))

            logger.info("SQLite checkpointer connection test successful")

        except Exception as e:
            logger.error(f"SQLite checkpointer connection test failed: {e}")
            raise

# Usage in graph compilation
def create_production_graph(workflow):
    """Create graph with production-ready persistence."""

    # Create checkpointer
    checkpointer = ProductionSqliteSaver.create_checkpointer()

    # Compile graph
    graph = workflow.compile(
        checkpointer=checkpointer,
        debug=False  # Disable debug in production
    )

    return graph
```

### Vector Store Integration

**Chroma Vector Store Setup**
```python
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from typing import List, Optional
import os

class VectorStoreManager:
    """Vector store manager for document retrieval."""

    def __init__(self, persist_directory: str = "data/vectorstore"):
        self.persist_directory = persist_directory
        self.embeddings = OpenAIEmbeddings(
            api_key=os.getenv("OPENAI_API_KEY"),
            model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        )
        self.vectorstore = None
        self.initialize()

    def initialize(self):
        """Initialize vector store with error handling."""

        try:
            # Create persist directory
            Path(self.persist_directory).mkdir(parents=True, exist_ok=True)

            # Initialize Chroma
            self.vectorstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )

            logger.info(f"Vector store initialized: {self.persist_directory}")

        except Exception as e:
            logger.error(f"Vector store initialization failed: {e}")

            # Fallback to in-memory
            self.vectorstore = Chroma(embedding_function=self.embeddings)
            logger.info("Using in-memory vector store fallback")

    def add_documents(self, documents: List[Document]):
        """Add documents to vector store with error handling."""

        try:
            self.vectorstore.add_documents(documents)
            logger.info(f"Added {len(documents)} documents to vector store")

        except Exception as e:
            logger.error(f"Failed to add documents to vector store: {e}")

    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        """Search vector store with error handling."""

        try:
            results = self.vectorstore.similarity_search(query, k=k)
            logger.info(f"Vector search returned {len(results)} results for: {query[:50]}...")
            return results

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

# Integration with LangGraph tools
@tool
def search_documents(query: str, k: int = 4) -> str:
    """Search local document store for relevant information."""

    vector_manager = VectorStoreManager()
    results = vector_manager.similarity_search(query, k)

    if not results:
        return f"No relevant documents found for query: {query}"

    # Format results
    formatted_results = []
    for i, doc in enumerate(results, 1):
        content = doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
        formatted_results.append(f"Result {i}:\n{content}\n")

    return "\n".join(formatted_results)
```

### LangSmith Integration for Development

**Development Monitoring Setup**
```python
import os
from langsmith import Client
import logging

logger = logging.getLogger(__name__)

def setup_langsmith_tracing():
    """Setup LangSmith for development tracing."""

    langsmith_api_key = os.getenv("LANGSMITH_API_KEY")

    if not langsmith_api_key:
        logger.info("LangSmith API key not found, skipping tracing setup")
        return None

    try:
        # Set environment variables for automatic tracing
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "agent-inbox-local-dev")
        os.environ["LANGCHAIN_API_KEY"] = langsmith_api_key

        # Test connection
        client = Client(api_key=langsmith_api_key)

        logger.info("LangSmith tracing enabled successfully")
        return client

    except Exception as e:
        logger.warning(f"LangSmith setup failed: {e}")

        # Disable tracing on failure
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        return None

# Call during application startup
langsmith_client = setup_langsmith_tracing()
```

**Documentation References:**
- SQLite Checkpointer: https://langchain-ai.github.io/langgraph/how-tos/persistence_sqlite/
- MCP Integration: https://github.com/langchain-ai/langchain-mcp-adapters
- Vector Store Setup: https://python.langchain.com/docs/integrations/vectorstores/chroma
- Environment Configuration: https://python.langchain.com/docs/guides/development/debugging
- LangSmith Tracing: https://docs.smith.langchain.com/tracing

## 3. Core Principles

### A. Prebuilt Components

**create_react_agent - Modern Agent Construction**
```python
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from typing import Optional, List

# ✅ CORRECT: Modern create_react_agent usage (2024-2025)
@tool
def web_search(query: str) -> str:
    """Search the web for current information."""
    # Implementation here
    return f"Search results for: {query}"

@tool
def calculator(expression: str) -> str:
    """Calculate mathematical expressions."""
    try:
        result = eval(expression)  # Use safe_eval in production
        return str(result)
    except:
        return "Invalid expression"

def create_modern_research_agent(model):
    """Create research agent using modern patterns."""

    # Define tools
    tools = [web_search, calculator]

    # Define system prompt
    system_prompt = """You are a research assistant specializing in data analysis and web research.

Key capabilities:
- Search for current information using web_search tool
- Perform calculations using calculator tool
- Synthesize findings into clear summaries

Always cite sources and show your reasoning."""

    # Create agent with proper configuration
    agent = create_react_agent(
        model=model,
        tools=tools,
        prompt=system_prompt,
        # Modern configurations
        state_schema=None,  # Use default MessagesState
        checkpointer=None   # Add checkpointer externally
    )

    return agent

# ❌ AVOID: Deprecated manual graph construction for simple agents
# Don't manually build StateGraph when create_react_agent suffices
```

**create_supervisor - Multi-Agent Coordination**
```python
from langgraph.prebuilt import create_supervisor
from langchain_core.messages import HumanMessage

def create_multi_agent_system():
    """Create supervisor system with specialized agents."""

    # Create specialized agents
    research_agent = create_react_agent(
        model=model,
        tools=[web_search, database_query],
        prompt="You are a research specialist. Focus on gathering accurate information."
    )

    analysis_agent = create_react_agent(
        model=model,
        tools=[calculator, data_analyzer],
        prompt="You are a data analyst. Focus on processing and analyzing information."
    )

    writing_agent = create_react_agent(
        model=model,
        tools=[document_formatter, style_checker],
        prompt="You are a writing specialist. Focus on clear communication and formatting."
    )

    # Create supervisor with clear routing instructions
    supervisor_prompt = """You are a project supervisor coordinating specialized agents.

Available agents:
- research_agent: For information gathering, web searches, database queries
- analysis_agent: For data processing, calculations, statistical analysis
- writing_agent: For document creation, formatting, and communication

Routing guidelines:
1. Start with research_agent for information gathering
2. Use analysis_agent for processing collected data
3. Use writing_agent for final output formatting
4. Allow agents to work iteratively when needed

Provide clear instructions to each agent about their specific task."""

    # Create supervisor system
    supervisor_graph = create_supervisor(
        agents=[research_agent, analysis_agent, writing_agent],
        model=model,
        prompt=supervisor_prompt,

        # Modern configurations
        supervisor_name="project_supervisor",
        output_mode="last_message",  # Return final agent output
        add_handoff_back_messages=True  # Include handoff context
    )

    return supervisor_graph.compile()

# Usage with proper thread management
config = {"configurable": {"thread_id": "project_123"}}
result = supervisor.invoke(
    {"messages": [HumanMessage(content="Research and analyze AI market trends")]},
    config
)
```

**ToolNode - Advanced Tool Integration**
```python
from langgraph.prebuilt import ToolNode
from langchain_core.messages import ToolMessage, AIMessage
from langchain_core.tools import tool
from typing import List, Dict, Any
import json
import logging

logger = logging.getLogger(__name__)

# Define tools with proper error handling
@tool
def risky_api_call(endpoint: str, data: Dict[str, Any]) -> str:
    """Make API call that might fail."""
    try:
        # Simulate API call
        if "error" in endpoint:
            raise Exception("API endpoint returned error")

        return json.dumps({"status": "success", "data": data})

    except Exception as e:
        # Log error but let ToolNode handle it
        logger.error(f"API call failed: {e}")
        raise  # Re-raise for ToolNode error handling

# ✅ CORRECT: ToolNode with comprehensive error handling
def create_resilient_tool_node():
    """Create tool node with proper error handling."""

    tools = [risky_api_call, web_search, calculator]

    # Option 1: Custom error message
    tool_node = ToolNode(
        tools,
        handle_tool_errors="I encountered an error executing the tool. Let me try a different approach or provide alternative information."
    )

    # Option 2: Custom error handling function
    def custom_error_handler(error: Exception, tool_name: str, tool_input: Dict) -> str:
        """Custom error handling logic."""

        logger.error(f"Tool {tool_name} failed with input {tool_input}: {error}")

        # Different handling based on tool type
        if tool_name == "risky_api_call":
            return f"API service is temporarily unavailable. Error: {str(error)}"
        elif tool_name == "web_search":
            return f"Web search failed. Please try rephrasing your query. Error: {str(error)}"
        else:
            return f"Tool execution failed: {str(error)}"

    advanced_tool_node = ToolNode(tools, handle_tool_errors=custom_error_handler)

    return advanced_tool_node

# Integration with custom state tracking
def tool_node_with_tracking(state):
    """Tool node with execution tracking."""

    # Execute tools
    tool_node = create_resilient_tool_node()
    result = tool_node(state)

    # Add tracking information
    if "tool_executions" not in state:
        state["tool_executions"] = []

    # Track successful/failed executions
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls"):
        for tool_call in last_message.tool_calls:
            state["tool_executions"].append({
                "tool_name": tool_call["name"],
                "timestamp": datetime.now().isoformat(),
                "success": "error" not in result.get("messages", [])[-1].content.lower()
            })

    return result
```

**Built-in Reducers and Custom Reducers**
```python
from typing import Annotated, Sequence, List, Dict, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from operator import add

# ✅ CORRECT: Using built-in add_messages reducer
class ModernAgentState(TypedDict):
    """Modern state schema with proper reducers."""

    # Messages with automatic appending
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # Lists with automatic concatenation
    search_results: Annotated[List[Dict], add]

    # Simple values (no reducer - will overwrite)
    current_step: str
    confidence_score: float

# Custom reducers for complex data
def merge_research_data(current: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """Custom reducer for merging research data."""

    if not current:
        return new

    # Merge dictionaries with preference for newer data
    merged = current.copy()

    for key, value in new.items():
        if key == "sources":
            # Combine and deduplicate sources
            existing_sources = set(merged.get("sources", []))
            new_sources = set(value) if isinstance(value, list) else {value}
            merged["sources"] = list(existing_sources | new_sources)

        elif key == "confidence_scores":
            # Average confidence scores
            existing = merged.get("confidence_scores", [])
            merged["confidence_scores"] = existing + ([value] if isinstance(value, (int, float)) else value)

        else:
            # Default: newer overwrites older
            merged[key] = value

    return merged

class AdvancedResearchState(TypedDict):
    """Advanced state with custom reducer."""

    messages: Annotated[Sequence[BaseMessage], add_messages]
    research_data: Annotated[Dict[str, Any], merge_research_data]
    step_count: int  # Simple counter, no reducer

# Usage in nodes
def research_node(state: AdvancedResearchState) -> Dict[str, Any]:
    """Research node demonstrating reducer usage."""

    # This will be merged with existing research_data
    new_research = {
        "sources": ["https://example.com/article1"],
        "confidence_scores": [0.85],
        "last_updated": datetime.now().isoformat()
    }

    return {
        "messages": [AIMessage(content="Research completed")],
        "research_data": new_research,  # Will be merged, not overwritten
        "step_count": state.get("step_count", 0) + 1  # Will overwrite
    }
```

### B. Model Preferences

**Anthropic Claude - Optimal Use Cases**
```python
from langchain_anthropic import ChatAnthropic
import os

# ✅ RECOMMENDED: Claude Sonnet 4 for complex reasoning
def create_claude_agent_for_analysis():
    """Claude excels at analysis, reasoning, and complex tasks."""

    model = ChatAnthropic(
        model="claude-sonnet-4-20250514",  # Latest model
        temperature=0.1,  # Low for consistency
        max_tokens=4096,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),

        # Claude-specific optimizations
        extra_headers={
            "anthropic-beta": "computer-use-2024-10-22"  # Enable latest features
        }
    )

    # Claude is excellent for:
    prompt = """You are an expert analyst with strong reasoning capabilities.

Strengths to leverage:
- Complex multi-step reasoning
- Detailed analysis and critique
- Careful instruction following
- Nuanced understanding of context
- Strong ethical reasoning

Focus on thorough analysis and provide detailed explanations of your reasoning."""

    return create_react_agent(model, tools, prompt)

# Use Claude for:
# - Complex analysis tasks
# - Multi-step reasoning
# - Code review and refactoring
# - Detailed research and synthesis
# - Tasks requiring careful instruction following
```

**OpenAI GPT-4 - Optimal Use Cases**
```python
from langchain_openai import ChatOpenAI

# ✅ RECOMMENDED: GPT-4o for tool use and real-time tasks
def create_gpt4_agent_for_tools():
    """GPT-4 excels at tool use and real-time interactions."""

    model = ChatOpenAI(
        model="gpt-4o",  # Best for tool use
        temperature=0.0,  # Deterministic for tool calls
        max_tokens=2048,
        openai_api_key=os.getenv("OPENAI_API_KEY"),

        # GPT-4 optimizations
        model_kwargs={
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0
        }
    )

    # GPT-4 is excellent for:
    prompt = """You are a capable assistant optimized for tool use and real-time tasks.

Strengths to leverage:
- Excellent tool calling accuracy
- Fast response times
- Good general knowledge
- Reliable structured output
- Strong web search integration

Focus on efficient tool usage and quick, accurate responses."""

    return create_react_agent(model, tools, prompt)

# Use GPT-4 for:
# - Heavy tool usage scenarios
# - Real-time interactions
# - Web search and data retrieval
# - Structured output generation
# - General assistant tasks
```

**Model Selection Decision Matrix**
```python
from enum import Enum
from typing import List, Dict, Any

class TaskType(Enum):
    ANALYSIS = "analysis"
    TOOL_HEAVY = "tool_heavy"
    CREATIVE = "creative"
    CODE_REVIEW = "code_review"
    REAL_TIME = "real_time"
    RESEARCH = "research"

def select_optimal_model(task_type: TaskType, requirements: Dict[str, Any]) -> str:
    """Select optimal model based on task characteristics."""

    # Decision matrix based on 2024-2025 performance data
    model_recommendations = {
        TaskType.ANALYSIS: "claude-sonnet-4-20250514",      # Best reasoning
        TaskType.TOOL_HEAVY: "gpt-4o",                      # Best tool calling
        TaskType.CREATIVE: "claude-sonnet-4-20250514",      # Best creativity
        TaskType.CODE_REVIEW: "claude-sonnet-4-20250514",   # Best code analysis
        TaskType.REAL_TIME: "gpt-4o",                       # Fastest response
        TaskType.RESEARCH: "claude-sonnet-4-20250514"       # Best synthesis
    }

    base_model = model_recommendations[task_type]

    # Adjust based on specific requirements
    if requirements.get("cost_sensitive", False):
        if base_model.startswith("claude-sonnet-4"):
            return "claude-haiku-3-20240307"  # Cost-effective alternative
        elif base_model.startswith("gpt-4o"):
            return "gpt-4o-mini"  # Cost-effective alternative

    if requirements.get("max_tokens", 0) > 8192:
        # Prefer Claude for long context
        return "claude-sonnet-4-20250514"

    return base_model

# Usage example
def create_task_optimized_agent(task_type: TaskType, requirements: Dict[str, Any]):
    """Create agent with optimal model for task."""

    model_name = select_optimal_model(task_type, requirements)

    if model_name.startswith("claude"):
        model = ChatAnthropic(model=model_name, **claude_config)
    else:
        model = ChatOpenAI(model=model_name, **openai_config)

    return create_react_agent(model, tools, task_specific_prompt)
```

**Streaming Configuration**
```python
from langchain_core.callbacks import StreamingStdOutCallbackHandler
from typing import AsyncIterator, Dict, Any

# ✅ CORRECT: Proper streaming setup
class AgentStreamingHandler:
    """Handle streaming responses from agents."""

    def __init__(self):
        self.current_response = ""
        self.callbacks = []

    async def stream_response(self, graph, input_data, config) -> AsyncIterator[str]:
        """Stream agent responses with proper error handling."""

        try:
            # Stream with proper configuration
            async for chunk in graph.astream(input_data, config, stream_mode="values"):

                # Extract new content from messages
                if "messages" in chunk:
                    last_message = chunk["messages"][-1]

                    if hasattr(last_message, "content"):
                        new_content = last_message.content

                        # Yield only new content
                        if new_content != self.current_response:
                            delta = new_content[len(self.current_response):]
                            self.current_response = new_content
                            yield delta

        except Exception as e:
            yield f"Streaming error: {str(e)}"

# Integration with agent
def create_streaming_agent():
    """Create agent optimized for streaming."""

    model = ChatOpenAI(
        model="gpt-4o",
        temperature=0.3,
        streaming=True,  # Enable streaming
        callbacks=[StreamingStdOutCallbackHandler()]  # Optional: console output
    )

    return create_react_agent(model, tools, prompt)

# Usage
async def run_streaming_session():
    """Run streaming agent session."""

    agent = create_streaming_agent()
    handler = AgentStreamingHandler()

    config = {"configurable": {"thread_id": "stream_session_1"}}
    input_data = {"messages": [HumanMessage(content="Explain quantum computing")]}

    print("Agent response:")
    async for chunk in handler.stream_response(agent, input_data, config):
        print(chunk, end="", flush=True)

    print("\nResponse complete.")
```

### C. Message & State Management

**TypedDict vs Pydantic Decision Matrix**
```python
from typing import TypedDict, Annotated, Sequence, List, Optional
from pydantic import BaseModel, Field, validator
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

# ✅ RECOMMENDED: TypedDict for performance-critical applications
class HighPerformanceState(TypedDict):
    """Use TypedDict when performance is critical and validation is optional."""

    messages: Annotated[Sequence[BaseMessage], add_messages]
    step_count: int
    processing_time: float
    results: List[dict]  # Type hint for IDE support

# Benefits of TypedDict:
# - Faster execution (no validation overhead)
# - Less memory usage
# - Better compatibility with LangGraph
# - Simpler debugging

# ✅ USE WHEN: Performance is critical, team has good typing discipline

# ✅ RECOMMENDED: Pydantic when data validation is critical
class ValidatedState(BaseModel):
    """Use Pydantic when data integrity is critical."""

    messages: Annotated[Sequence[BaseMessage], add_messages] = Field(default_factory=list)
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Must be between 0 and 1")
    source_urls: List[str] = Field(..., min_items=1, description="At least one source required")
    timestamp: Optional[str] = Field(None, description="ISO format timestamp")

    @validator('source_urls')
    def validate_urls(cls, v):
        """Validate URL format."""
        import re
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        for url in v:
            if not url_pattern.match(url):
                raise ValueError(f"Invalid URL: {url}")
        return v

# Benefits of Pydantic:
# - Runtime validation catches errors early
# - Better error messages
# - Automatic serialization/deserialization
# - Rich type validation

# ✅ USE WHEN: Data integrity is critical, external data sources, complex validation

# Decision helper function
def choose_state_schema(requirements: Dict[str, bool]) -> str:
    """Help choose between TypedDict and Pydantic."""

    if requirements.get("runtime_validation_critical", False):
        return "Pydantic"

    if requirements.get("external_data_sources", False):
        return "Pydantic"

    if requirements.get("performance_critical", False):
        return "TypedDict"

    if requirements.get("simple_internal_state", False):
        return "TypedDict"

    # Default recommendation
    return "TypedDict"  # LangGraph default
```

**Message Handling Best Practices**
```python
from langchain_core.messages import (
    BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
)
from typing import List, Sequence, Annotated
from langgraph.graph.message import add_messages
import logging

logger = logging.getLogger(__name__)

class ConversationManager:
    """Manage message flows and conversation state."""

    @staticmethod
    def create_system_message(role_description: str, capabilities: List[str]) -> SystemMessage:
        """Create structured system message."""

        capability_list = "\n".join([f"- {cap}" for cap in capabilities])

        content = f"""You are {role_description}.

Your capabilities:
{capability_list}

Always be helpful, accurate, and explain your reasoning when asked."""

        return SystemMessage(content=content)

    @staticmethod
    def add_conversation_context(
        messages: Sequence[BaseMessage],
        context: str,
        max_history: int = 10
    ) -> List[BaseMessage]:
        """Add context while managing conversation history."""

        # Convert to list for manipulation
        message_list = list(messages)

        # Limit history to prevent context overflow
        if len(message_list) > max_history:
            # Keep system message + recent history
            system_messages = [msg for msg in message_list if isinstance(msg, SystemMessage)]
            recent_messages = message_list[-(max_history-len(system_messages)):]
            message_list = system_messages + recent_messages

        # Add context as system message if needed
        if context and not any(context in msg.content for msg in message_list if isinstance(msg, SystemMessage)):
            context_message = SystemMessage(content=f"Additional context: {context}")
            message_list.insert(-1 if message_list else 0, context_message)

        return message_list

    @staticmethod
    def filter_messages_by_type(
        messages: Sequence[BaseMessage],
        include_types: List[str] = None,
        exclude_types: List[str] = None
    ) -> List[BaseMessage]:
        """Filter messages by type for specific processing."""

        if include_types is None and exclude_types is None:
            return list(messages)

        filtered = []
        for msg in messages:
            msg_type = type(msg).__name__.replace("Message", "").lower()

            if include_types and msg_type not in [t.lower() for t in include_types]:
                continue

            if exclude_types and msg_type in [t.lower() for t in exclude_types]:
                continue

            filtered.append(msg)

        return filtered

# ✅ CORRECT: Proper message handling in nodes
def conversation_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Node with proper message handling."""

    messages = state["messages"]

    # Add conversation context
    manager = ConversationManager()
    contextual_messages = manager.add_conversation_context(
        messages,
        context=state.get("current_context", ""),
        max_history=15
    )

    # Process with model
    response = model.invoke(contextual_messages)

    # Return with proper reducer usage
    return {
        "messages": [response],  # add_messages reducer will append
        "last_interaction": datetime.now().isoformat()
    }
```

**State Persistence and Thread Management**
```python
from langgraph.checkpoint.sqlite import SqliteSaver
from typing import Dict, Any, Optional
import uuid
from datetime import datetime, timedelta

class ThreadManager:
    """Manage conversation threads and persistence."""

    def __init__(self, checkpointer: SqliteSaver):
        self.checkpointer = checkpointer

    def create_thread(self, user_id: str, session_type: str = "general") -> str:
        """Create new conversation thread."""

        thread_id = f"{session_type}_{user_id}_{uuid.uuid4().hex[:8]}"

        # Initialize thread with metadata
        config = {
            "configurable": {
                "thread_id": thread_id,
                "user_id": user_id,
                "session_type": session_type,
                "created_at": datetime.now().isoformat()
            }
        }

        return thread_id, config

    def list_user_threads(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """List conversation threads for a user."""

        try:
            # Get all threads (checkpointer doesn't have direct user filtering)
            threads = []

            # This is a simplified approach - in production you'd need better filtering
            for thread_data in self.checkpointer.list({}):
                config = thread_data.config
                if config.get("configurable", {}).get("user_id") == user_id:
                    threads.append({
                        "thread_id": config["configurable"]["thread_id"],
                        "session_type": config["configurable"].get("session_type", "general"),
                        "created_at": config["configurable"].get("created_at"),
                        "last_checkpoint": thread_data.checkpoint
                    })

            # Sort by creation time and limit
            threads.sort(key=lambda x: x["created_at"], reverse=True)
            return threads[:limit]

        except Exception as e:
            logger.error(f"Failed to list threads for user {user_id}: {e}")
            return []

    def cleanup_old_threads(self, days_old: int = 30) -> int:
        """Clean up old conversation threads."""

        cutoff_date = datetime.now() - timedelta(days=days_old)
        cleaned_count = 0

        try:
            # Note: This is simplified - production would need better cleanup methods
            logger.info(f"Cleanup would remove threads older than {cutoff_date}")
            # Implementation would depend on checkpointer capabilities

        except Exception as e:
            logger.error(f"Thread cleanup failed: {e}")

        return cleaned_count

# Memory patterns for cross-thread data sharing
class UserMemoryManager:
    """Manage persistent user data across threads."""

    def __init__(self, store):
        self.store = store

    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences across all threads."""

        try:
            namespace = ["user_preferences", user_id]
            prefs = self.store.get(namespace, "preferences")
            return prefs.value if prefs else {}

        except Exception as e:
            logger.error(f"Failed to get user preferences for {user_id}: {e}")
            return {}

    def update_user_preference(self, user_id: str, key: str, value: Any):
        """Update user preference."""

        try:
            namespace = ["user_preferences", user_id]
            current_prefs = self.get_user_preferences(user_id)
            current_prefs[key] = value

            self.store.put(namespace, "preferences", current_prefs)
            logger.info(f"Updated preference {key} for user {user_id}")

        except Exception as e:
            logger.error(f"Failed to update preference for {user_id}: {e}")

    def get_conversation_summary(self, thread_id: str) -> Optional[str]:
        """Get conversation summary for context in new threads."""

        try:
            namespace = ["conversation_summaries", thread_id]
            summary = self.store.get(namespace, "summary")
            return summary.value if summary else None

        except Exception as e:
            logger.error(f"Failed to get conversation summary for {thread_id}: {e}")
            return None

# Usage in graph construction
def create_persistent_agent_system():
    """Create agent system with proper persistence."""

    # Setup persistence components
    checkpointer = SqliteSaver.from_conn_string("data/conversations.db")
    store = InMemoryStore()  # Use RedisStore for production

    # Create managers
    thread_manager = ThreadManager(checkpointer)
    memory_manager = UserMemoryManager(store)

    # Compile graph with persistence
    graph = workflow.compile(
        checkpointer=checkpointer,
        store=store
    )

    return graph, thread_manager, memory_manager
```

**Documentation References:**
- create_react_agent: https://langchain-ai.github.io/langgraph/how-tos/create-react-agent/
- create_supervisor: https://langchain-ai.github.io/langgraph/tutorials/multi_agent/agent_supervisor/
- ToolNode Configuration: https://langchain-ai.github.io/langgraph/how-tos/tool-calling/
- Message Reducers: https://langchain-ai.github.io/langgraph/concepts/low_level/#reducers
- Model Selection: https://python.langchain.com/docs/integrations/chat/
- Streaming: https://langchain-ai.github.io/langgraph/how-tos/streaming/
- State Management: https://langchain-ai.github.io/langgraph/concepts/low_level/#state
- Thread Management: https://langchain-ai.github.io/langgraph/how-tos/persistence/

## 4. Tool Usage

### A. Streaming

**Real-time Updates with Stream Modes**
```python
from typing import AsyncIterator, Dict, Any, List
from langgraph.graph import StateGraph
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

class StreamingManager:
    """Manage different types of streaming for LangGraph agents."""

    @staticmethod
    async def stream_values(graph, input_data: Dict, config: Dict) -> AsyncIterator[Dict[str, Any]]:
        """Stream complete state values after each node execution."""

        try:
            async for chunk in graph.astream(input_data, config, stream_mode="values"):
                yield chunk

        except Exception as e:
            logger.error(f"Values streaming failed: {e}")
            yield {"error": f"Streaming failed: {str(e)}"}

    @staticmethod
    async def stream_updates(graph, input_data: Dict, config: Dict) -> AsyncIterator[Dict[str, Any]]:
        """Stream only state updates/changes from each node."""

        try:
            async for chunk in graph.astream(input_data, config, stream_mode="updates"):
                # Each chunk contains node_name -> state_updates
                for node_name, updates in chunk.items():
                    yield {
                        "node": node_name,
                        "updates": updates,
                        "timestamp": datetime.now().isoformat()
                    }

        except Exception as e:
            logger.error(f"Updates streaming failed: {e}")
            yield {"error": f"Update streaming failed: {str(e)}"}

    @staticmethod
    async def stream_messages_only(graph, input_data: Dict, config: Dict) -> AsyncIterator[str]:
        """Stream only new message content for user display."""

        current_message_count = len(input_data.get("messages", []))

        try:
            async for chunk in graph.astream(input_data, config, stream_mode="values"):

                messages = chunk.get("messages", [])

                # Yield only new messages
                if len(messages) > current_message_count:
                    new_messages = messages[current_message_count:]
                    current_message_count = len(messages)

                    for msg in new_messages:
                        if hasattr(msg, 'content') and msg.content:
                            yield msg.content

        except Exception as e:
            logger.error(f"Message streaming failed: {e}")
            yield f"Streaming error: {str(e)}"

# ✅ CORRECT: Progress indicators during long operations
class ProgressTracker:
    """Track and stream progress for long-running operations."""

    def __init__(self):
        self.current_step = 0
        self.total_steps = 0
        self.step_descriptions = {}

    def initialize(self, total_steps: int, step_descriptions: Dict[int, str]):
        """Initialize progress tracking."""
        self.total_steps = total_steps
        self.step_descriptions = step_descriptions
        self.current_step = 0

    async def stream_with_progress(
        self,
        graph,
        input_data: Dict,
        config: Dict,
        progress_callback=None
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream with progress indicators."""

        try:
            async for chunk in graph.astream(input_data, config, stream_mode="updates"):

                for node_name, updates in chunk.items():
                    # Update progress
                    self.current_step += 1
                    progress_percent = (self.current_step / self.total_steps) * 100

                    # Create progress update
                    progress_update = {
                        "type": "progress",
                        "current_step": self.current_step,
                        "total_steps": self.total_steps,
                        "progress_percent": progress_percent,
                        "current_operation": self.step_descriptions.get(
                            self.current_step,
                            f"Processing {node_name}"
                        ),
                        "node_updates": updates
                    }

                    # Call progress callback if provided
                    if progress_callback:
                        await progress_callback(progress_update)

                    yield progress_update

        except Exception as e:
            yield {
                "type": "error",
                "message": f"Progress streaming failed: {str(e)}",
                "current_step": self.current_step
            }

# Usage example with progress tracking
async def run_research_with_progress():
    """Run research agent with progress indicators."""

    # Setup progress tracking
    tracker = ProgressTracker()
    tracker.initialize(
        total_steps=4,
        step_descriptions={
            1: "Searching for information...",
            2: "Analyzing search results...",
            3: "Synthesizing findings...",
            4: "Generating final report..."
        }
    )

    # Progress callback function
    async def progress_callback(update):
        print(f"Progress: {update['progress_percent']:.1f}% - {update['current_operation']}")

    # Stream with progress
    config = {"configurable": {"thread_id": "research_001"}}
    input_data = {"messages": [HumanMessage(content="Research AI market trends")]}

    async for update in tracker.stream_with_progress(
        research_agent, input_data, config, progress_callback
    ):
        if update["type"] == "progress":
            # Handle progress updates
            print(f"Step {update['current_step']}/{update['total_steps']} complete")
        elif update["type"] == "error":
            print(f"Error: {update['message']}")
```

**Error Streaming Patterns**
```python
class ErrorStreamingHandler:
    """Handle errors during streaming operations."""

    @staticmethod
    async def stream_with_error_recovery(
        graph,
        input_data: Dict,
        config: Dict,
        max_retries: int = 3
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream with automatic error recovery."""

        retry_count = 0

        while retry_count <= max_retries:
            try:
                async for chunk in graph.astream(input_data, config, stream_mode="values"):
                    yield {
                        "type": "success",
                        "data": chunk,
                        "retry_count": retry_count
                    }

                # If we get here, streaming completed successfully
                return

            except Exception as e:
                retry_count += 1

                error_update = {
                    "type": "error",
                    "message": str(e),
                    "retry_count": retry_count,
                    "max_retries": max_retries,
                    "will_retry": retry_count <= max_retries
                }

                yield error_update

                if retry_count <= max_retries:
                    # Wait before retry with exponential backoff
                    wait_time = 2 ** retry_count
                    await asyncio.sleep(wait_time)

                    yield {
                        "type": "retry",
                        "message": f"Retrying in {wait_time} seconds... (attempt {retry_count})",
                        "retry_count": retry_count
                    }
                else:
                    yield {
                        "type": "failure",
                        "message": "Maximum retries exceeded",
                        "final_error": str(e)
                    }
                    return

# Real-time streaming with WebSocket integration
class WebSocketStreamer:
    """Stream LangGraph responses over WebSocket."""

    def __init__(self, websocket):
        self.websocket = websocket
        self.is_connected = True

    async def stream_to_websocket(self, graph, input_data: Dict, config: Dict):
        """Stream agent responses to WebSocket client."""

        try:
            await self.websocket.send(json.dumps({
                "type": "stream_start",
                "message": "Starting agent execution..."
            }))

            async for chunk in graph.astream(input_data, config, stream_mode="values"):

                if not self.is_connected:
                    break

                # Extract messages for streaming
                messages = chunk.get("messages", [])
                if messages:
                    last_message = messages[-1]

                    if hasattr(last_message, 'content'):
                        await self.websocket.send(json.dumps({
                            "type": "message_chunk",
                            "content": last_message.content,
                            "message_type": type(last_message).__name__
                        }))

            await self.websocket.send(json.dumps({
                "type": "stream_complete",
                "message": "Agent execution completed"
            }))

        except Exception as e:
            await self.websocket.send(json.dumps({
                "type": "stream_error",
                "message": str(e)
            }))

        finally:
            self.is_connected = False
```

### B. Interrupts

**Human-in-the-Loop Configuration**
```python
from langgraph.graph import StateGraph, END, START
from typing import Dict, Any, List, Optional

class HumanInteractionManager:
    """Manage human-in-the-loop interactions."""

    def create_interactive_workflow(self, nodes: Dict[str, callable]) -> StateGraph:
        """Create workflow with strategic interrupt points."""

        workflow = StateGraph(InteractiveState)

        # Add nodes
        for name, node_func in nodes.items():
            workflow.add_node(name, node_func)

        # Add edges with interrupt points before critical decisions
        workflow.add_edge(START, "research")
        workflow.add_edge("research", "human_review")  # Interrupt before human review
        workflow.add_edge("human_review", "analysis")
        workflow.add_edge("analysis", "human_approval")  # Interrupt before final approval
        workflow.add_edge("human_approval", END)

        # Compile with interrupt points
        return workflow.compile(
            checkpointer=checkpointer,
            interrupt_before=["human_review", "human_approval"]  # Pause here for human input
        )

    def add_human_feedback_node(self, state: InteractiveState) -> Dict[str, Any]:
        """Node for collecting human feedback."""

        # This node waits for human input
        pending_review = state.get("pending_human_review", {})

        if not pending_review:
            # Set up review request
            return {
                "pending_human_review": {
                    "request_type": "feedback",
                    "data": state.get("research_results", {}),
                    "timestamp": datetime.now().isoformat()
                },
                "messages": [AIMessage(content="Waiting for human review...")]
            }

        # If we have human feedback, process it
        human_feedback = state.get("human_feedback")
        if human_feedback:
            return {
                "messages": [HumanMessage(content=human_feedback)],
                "review_complete": True,
                "pending_human_review": {}  # Clear pending review
            }

        # Still waiting
        return {"messages": [AIMessage(content="Still waiting for human input...")]}

# ✅ CORRECT: Resume patterns after interruption
class InterruptionHandler:
    """Handle workflow interruptions and resumptions."""

    def __init__(self, graph):
        self.graph = graph

    async def run_until_interrupt(
        self,
        input_data: Dict,
        config: Dict
    ) -> Dict[str, Any]:
        """Run workflow until it hits an interrupt point."""

        try:
            # This will run until interrupt
            result = await self.graph.ainvoke(input_data, config)
            return {
                "status": "completed",
                "result": result,
                "interrupted": False
            }

        except InterruptedError:
            # Expected interruption
            return {
                "status": "interrupted",
                "interrupted": True,
                "message": "Workflow paused for human input"
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "interrupted": False
            }

    async def resume_after_input(
        self,
        config: Dict,
        human_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Resume workflow after human input."""

        try:
            # Add human input to state if provided
            if human_input:
                # Update state with human input
                current_state = await self.graph.aget_state(config)
                updated_state = current_state.values.copy()
                updated_state.update(human_input)

                # Resume with updated state
                result = await self.graph.ainvoke(updated_state, config)
            else:
                # Resume without changes (just continue from checkpoint)
                result = await self.graph.ainvoke(None, config)

            return {
                "status": "completed",
                "result": result
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

# Usage example with interrupt handling
async def interactive_research_session():
    """Run interactive research session with human input."""

    # Create interactive workflow
    manager = HumanInteractionManager()
    workflow = manager.create_interactive_workflow({
        "research": research_node,
        "human_review": manager.add_human_feedback_node,
        "analysis": analysis_node,
        "human_approval": approval_node
    })

    handler = InterruptionHandler(workflow)

    # Start workflow
    config = {"configurable": {"thread_id": "interactive_001"}}
    input_data = {"messages": [HumanMessage(content="Research quantum computing applications")]}

    # Run until first interrupt
    result = await handler.run_until_interrupt(input_data, config)

    if result["interrupted"]:
        print("Workflow paused for human review")

        # Simulate getting human input
        human_feedback = input("Please provide your feedback: ")

        # Resume with human input
        resume_result = await handler.resume_after_input(
            config,
            {"human_feedback": human_feedback}
        )

        print(f"Final result: {resume_result}")
```

**User Input Collection Patterns**
```python
from typing import Union, List, Dict
from enum import Enum

class InputType(Enum):
    TEXT = "text"
    CHOICE = "choice"
    RATING = "rating"
    APPROVAL = "approval"

class UserInputCollector:
    """Collect different types of user input during workflow execution."""

    @staticmethod
    def create_input_request(
        input_type: InputType,
        prompt: str,
        options: Optional[List[str]] = None,
        validation_rules: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Create standardized input request."""

        request = {
            "type": input_type.value,
            "prompt": prompt,
            "timestamp": datetime.now().isoformat(),
            "validation_rules": validation_rules or {}
        }

        if input_type == InputType.CHOICE and options:
            request["options"] = options

        return request

    @staticmethod
    def validate_user_input(
        input_value: Any,
        input_type: InputType,
        validation_rules: Dict = None
    ) -> Dict[str, Any]:
        """Validate user input against rules."""

        validation_rules = validation_rules or {}

        try:
            if input_type == InputType.TEXT:
                if validation_rules.get("min_length") and len(input_value) < validation_rules["min_length"]:
                    return {"valid": False, "error": f"Input too short (minimum {validation_rules['min_length']} characters)"}

                if validation_rules.get("max_length") and len(input_value) > validation_rules["max_length"]:
                    return {"valid": False, "error": f"Input too long (maximum {validation_rules['max_length']} characters)"}

            elif input_type == InputType.CHOICE:
                options = validation_rules.get("options", [])
                if options and input_value not in options:
                    return {"valid": False, "error": f"Invalid choice. Options: {', '.join(options)}"}

            elif input_type == InputType.RATING:
                min_rating = validation_rules.get("min", 1)
                max_rating = validation_rules.get("max", 5)

                try:
                    rating = float(input_value)
                    if rating < min_rating or rating > max_rating:
                        return {"valid": False, "error": f"Rating must be between {min_rating} and {max_rating}"}
                except ValueError:
                    return {"valid": False, "error": "Rating must be a number"}

            elif input_type == InputType.APPROVAL:
                if str(input_value).lower() not in ["yes", "no", "y", "n", "true", "false"]:
                    return {"valid": False, "error": "Please respond with yes/no"}

            return {"valid": True, "validated_value": input_value}

        except Exception as e:
            return {"valid": False, "error": f"Validation error: {str(e)}"}

# Integration with workflow nodes
def interactive_approval_node(state: InteractiveState) -> Dict[str, Any]:
    """Node that requests user approval before proceeding."""

    collector = UserInputCollector()

    # Check if we already have user input
    if state.get("user_approval_response"):
        # Process the approval
        response = state["user_approval_response"]

        if response.lower() in ["yes", "y", "true"]:
            return {
                "messages": [AIMessage(content="Approval received. Proceeding...")],
                "approval_granted": True
            }
        else:
            return {
                "messages": [AIMessage(content="Request denied. Stopping workflow.")],
                "approval_granted": False
            }

    # Create approval request
    approval_request = collector.create_input_request(
        InputType.APPROVAL,
        "Do you approve the proposed analysis approach?",
        validation_rules={"required": True}
    )

    return {
        "messages": [AIMessage(content="Requesting user approval...")],
        "pending_user_input": approval_request,
        "waiting_for_approval": True
    }
```

### C. Validation

**Input Validation Strategies**
```python
from pydantic import BaseModel, Field, validator
from typing import Any, Dict, List, Optional, Union
import re
from datetime import datetime

class InputValidator:
    """Comprehensive input validation for LangGraph nodes."""

    @staticmethod
    def validate_message_input(messages: List[Any]) -> Dict[str, Any]:
        """Validate message input structure."""

        if not isinstance(messages, list):
            return {"valid": False, "error": "Messages must be a list"}

        if not messages:
            return {"valid": False, "error": "Messages list cannot be empty"}

        # Check message types
        valid_message_types = ["HumanMessage", "AIMessage", "SystemMessage", "ToolMessage"]

        for i, msg in enumerate(messages):
            msg_type = type(msg).__name__
            if msg_type not in valid_message_types:
                return {
                    "valid": False,
                    "error": f"Invalid message type at index {i}: {msg_type}"
                }

            if not hasattr(msg, 'content') or not msg.content:
                return {
                    "valid": False,
                    "error": f"Message at index {i} has no content"
                }

        return {"valid": True, "message_count": len(messages)}

    @staticmethod
    def validate_search_query(query: str) -> Dict[str, Any]:
        """Validate search query input."""

        if not isinstance(query, str):
            return {"valid": False, "error": "Query must be a string"}

        if not query.strip():
            return {"valid": False, "error": "Query cannot be empty"}

        if len(query) < 3:
            return {"valid": False, "error": "Query too short (minimum 3 characters)"}

        if len(query) > 500:
            return {"valid": False, "error": "Query too long (maximum 500 characters)"}

        # Check for suspicious patterns
        suspicious_patterns = [
            r'<script.*?>.*?</script>',  # Script injection
            r'javascript:',              # JavaScript URLs
            r'data:.*base64',           # Base64 data URLs
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return {"valid": False, "error": "Query contains suspicious content"}

        return {"valid": True, "cleaned_query": query.strip()}

# Runtime validation schemas
class ResearchRequestSchema(BaseModel):
    """Schema for validating research requests."""

    query: str = Field(..., min_length=3, max_length=500)
    source_types: List[str] = Field(default=["web", "academic"], description="Types of sources to search")
    max_results: int = Field(default=10, ge=1, le=50, description="Maximum number of results")
    language: str = Field(default="en", regex=r"^[a-z]{2}$", description="Language code")
    urgency: str = Field(default="normal", regex=r"^(low|normal|high|critical)$")

    @validator('source_types')
    def validate_source_types(cls, v):
        valid_sources = {"web", "academic", "news", "books", "patents"}
        for source in v:
            if source not in valid_sources:
                raise ValueError(f"Invalid source type: {source}")
        return v

    @validator('query')
    def validate_query_content(cls, v):
        # Additional custom validation
        if any(word in v.lower() for word in ["hack", "exploit", "attack"]):
            raise ValueError("Query contains prohibited terms")
        return v

def validate_node_input(validation_schema: BaseModel):
    """Decorator for validating node inputs."""

    def decorator(node_func):
        async def wrapper(state: Dict[str, Any]) -> Dict[str, Any]:
            try:
                # Extract input data based on schema
                input_data = {}
                for field_name, field_info in validation_schema.__fields__.items():
                    if field_name in state:
                        input_data[field_name] = state[field_name]

                # Validate input
                validated_data = validation_schema(**input_data)

                # Add validated data to state
                state_with_validation = state.copy()
                state_with_validation.update(validated_data.dict())

                # Call original node function
                return await node_func(state_with_validation)

            except ValueError as e:
                # Return validation error
                return {
                    "messages": [AIMessage(content=f"Input validation failed: {str(e)}")],
                    "validation_error": str(e),
                    "node_skipped": True
                }

        return wrapper
    return decorator

# Usage with validation decorator
@validate_node_input(ResearchRequestSchema)
async def validated_research_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Research node with automatic input validation."""

    # Input is guaranteed to be valid here
    query = state["query"]
    max_results = state["max_results"]
    source_types = state["source_types"]

    # Perform research with validated inputs
    results = await perform_research(query, max_results, source_types)

    return {
        "messages": [AIMessage(content=f"Research completed for: {query}")],
        "research_results": results
    }
```

**State Validation Patterns**
```python
class StateValidator:
    """Validate state consistency across node transitions."""

    @staticmethod
    def validate_state_transition(
        before_state: Dict[str, Any],
        after_state: Dict[str, Any],
        expected_changes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate that state changes match expectations."""

        validation_results = {"valid": True, "errors": [], "warnings": []}

        # Check required changes
        for key, expected_value in expected_changes.items():
            if key not in after_state:
                validation_results["errors"].append(f"Required key '{key}' missing from state")
                validation_results["valid"] = False
            elif expected_value != "any" and after_state[key] != expected_value:
                validation_results["warnings"].append(
                    f"Key '{key}' has unexpected value: {after_state[key]} (expected: {expected_value})"
                )

        # Check for unexpected removals
        for key in before_state:
            if key not in after_state:
                validation_results["warnings"].append(f"Key '{key}' was removed from state")

        # Check message integrity
        before_messages = before_state.get("messages", [])
        after_messages = after_state.get("messages", [])

        if len(after_messages) < len(before_messages):
            validation_results["errors"].append("Messages were lost during node execution")
            validation_results["valid"] = False

        return validation_results

    @staticmethod
    def create_state_validator(expected_schema: Dict[str, type]):
        """Create validator function for state schema."""

        def validator(state: Dict[str, Any]) -> Dict[str, Any]:
            validation_results = {"valid": True, "errors": []}

            for key, expected_type in expected_schema.items():
                if key not in state:
                    validation_results["errors"].append(f"Required key '{key}' missing")
                    validation_results["valid"] = False
                elif not isinstance(state[key], expected_type):
                    validation_results["errors"].append(
                        f"Key '{key}' has wrong type: {type(state[key])} (expected: {expected_type})"
                    )
                    validation_results["valid"] = False

            return validation_results

        return validator

# Validation middleware for nodes
def with_state_validation(expected_schema: Dict[str, type]):
    """Decorator to add state validation to nodes."""

    validator = StateValidator.create_state_validator(expected_schema)

    def decorator(node_func):
        async def wrapper(state: Dict[str, Any]) -> Dict[str, Any]:

            # Validate input state
            input_validation = validator(state)

            if not input_validation["valid"]:
                return {
                    "messages": [AIMessage(content=f"State validation failed: {input_validation['errors']}")],
                    "validation_errors": input_validation["errors"],
                    "node_skipped": True
                }

            # Execute node
            before_state = state.copy()
            result = await node_func(state)
            after_state = {**state, **result}

            # Validate output state
            output_validation = validator(after_state)

            if not output_validation["valid"]:
                logger.warning(f"Node {node_func.__name__} produced invalid state: {output_validation['errors']}")

            return result

        return wrapper
    return decorator
```

**Tool Output Validation**
```python
from langchain_core.tools import tool
from typing import Any, Dict, List, Union
import json

class ToolOutputValidator:
    """Validate and sanitize tool outputs."""

    @staticmethod
    def validate_json_output(output: str) -> Dict[str, Any]:
        """Validate and parse JSON tool output."""

        try:
            # Try to parse JSON
            parsed = json.loads(output)

            return {
                "valid": True,
                "parsed_output": parsed,
                "output_type": type(parsed).__name__
            }

        except json.JSONDecodeError as e:
            return {
                "valid": False,
                "error": f"Invalid JSON: {str(e)}",
                "raw_output": output[:200] + "..." if len(output) > 200 else output
            }

    @staticmethod
    def sanitize_text_output(output: str, max_length: int = 5000) -> str:
        """Sanitize text output from tools."""

        if not isinstance(output, str):
            output = str(output)

        # Truncate if too long
        if len(output) > max_length:
            output = output[:max_length] + "... [truncated]"

        # Remove potentially dangerous content
        dangerous_patterns = [
            r'<script.*?>.*?</script>',
            r'javascript:',
            r'data:.*base64',
        ]

        for pattern in dangerous_patterns:
            output = re.sub(pattern, '[REMOVED]', output, flags=re.IGNORECASE | re.DOTALL)

        return output

# Enhanced tool with output validation
@tool
def validated_web_search(query: str) -> str:
    """Web search tool with output validation."""

    # Input validation
    input_validator = InputValidator()
    validation_result = input_validator.validate_search_query(query)

    if not validation_result["valid"]:
        return f"Search failed: {validation_result['error']}"

    try:
        # Perform actual search (mock implementation)
        raw_results = perform_web_search(validation_result["cleaned_query"])

        # Validate and sanitize output
        output_validator = ToolOutputValidator()

        if isinstance(raw_results, dict):
            # Validate JSON structure
            json_validation = output_validator.validate_json_output(json.dumps(raw_results))

            if json_validation["valid"]:
                # Additional structure validation
                if "results" in raw_results and isinstance(raw_results["results"], list):
                    # Sanitize each result
                    sanitized_results = []
                    for result in raw_results["results"]:
                        if isinstance(result, dict) and "content" in result:
                            result["content"] = output_validator.sanitize_text_output(result["content"])
                        sanitized_results.append(result)

                    raw_results["results"] = sanitized_results

                return json.dumps(raw_results)
            else:
                return f"Search completed but output format invalid: {json_validation['error']}"

        else:
            # Text output
            sanitized_output = output_validator.sanitize_text_output(str(raw_results))
            return sanitized_output

    except Exception as e:
        logger.error(f"Web search failed: {e}")
        return f"Search failed due to error: {str(e)}"

# Tool validation middleware
def with_output_validation(output_schema: Optional[BaseModel] = None):
    """Decorator to add output validation to tools."""

    def decorator(tool_func):
        def wrapper(*args, **kwargs):
            try:
                # Execute tool
                result = tool_func(*args, **kwargs)

                # Validate output if schema provided
                if output_schema:
                    try:
                        validated_result = output_schema(**result if isinstance(result, dict) else {"output": result})
                        return validated_result.dict() if hasattr(validated_result, 'dict') else validated_result
                    except ValueError as e:
                        return f"Tool output validation failed: {str(e)}"

                # Basic sanitization for string outputs
                if isinstance(result, str):
                    validator = ToolOutputValidator()
                    return validator.sanitize_text_output(result)

                return result

            except Exception as e:
                logger.error(f"Tool {tool_func.__name__} failed: {e}")
                return f"Tool execution failed: {str(e)}"

        return wrapper
    return decorator
```

### D. Error Management

**Graceful Degradation Patterns**
```python
from typing import List, Dict, Any, Optional, Callable
import asyncio
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class GracefulDegradationManager:
    """Manage graceful degradation when components fail."""

    def __init__(self):
        self.fallback_handlers = {}
        self.service_health = {}

    def register_fallback(self, service_name: str, fallback_handler: Callable):
        """Register fallback handler for a service."""
        self.fallback_handlers[service_name] = fallback_handler

    def check_service_health(self, service_name: str) -> bool:
        """Check if service is healthy."""
        health_info = self.service_health.get(service_name, {})

        # Consider service unhealthy if it failed recently
        if health_info.get("consecutive_failures", 0) > 3:
            last_failure = health_info.get("last_failure")
            if last_failure:
                time_since_failure = datetime.now() - datetime.fromisoformat(last_failure)
                if time_since_failure < timedelta(minutes=5):  # Circuit breaker
                    return False

        return True

    def record_service_result(self, service_name: str, success: bool, error: str = None):
        """Record service execution result."""

        if service_name not in self.service_health:
            self.service_health[service_name] = {
                "consecutive_failures": 0,
                "total_calls": 0,
                "success_count": 0
            }

        health_info = self.service_health[service_name]
        health_info["total_calls"] += 1

        if success:
            health_info["consecutive_failures"] = 0
            health_info["success_count"] += 1
        else:
            health_info["consecutive_failures"] += 1
            health_info["last_failure"] = datetime.now().isoformat()
            health_info["last_error"] = error

    async def execute_with_fallback(
        self,
        service_name: str,
        primary_func: Callable,
        *args, **kwargs
    ) -> Dict[str, Any]:
        """Execute function with fallback on failure."""

        # Check if service is healthy
        if not self.check_service_health(service_name):
            logger.warning(f"Service {service_name} is unhealthy, using fallback")
            if service_name in self.fallback_handlers:
                return await self.fallback_handlers[service_name](*args, **kwargs)
            else:
                return {"error": f"Service {service_name} unavailable and no fallback configured"}

        try:
            # Try primary function
            result = await primary_func(*args, **kwargs)
            self.record_service_result(service_name, success=True)

            return {
                "success": True,
                "result": result,
                "source": "primary"
            }

        except Exception as e:
            logger.error(f"Primary service {service_name} failed: {e}")
            self.record_service_result(service_name, success=False, error=str(e))

            # Try fallback
            if service_name in self.fallback_handlers:
                try:
                    fallback_result = await self.fallback_handlers[service_name](*args, **kwargs)

                    return {
                        "success": True,
                        "result": fallback_result,
                        "source": "fallback",
                        "primary_error": str(e)
                    }

                except Exception as fallback_error:
                    logger.error(f"Fallback for {service_name} also failed: {fallback_error}")

                    return {
                        "success": False,
                        "error": str(e),
                        "fallback_error": str(fallback_error)
                    }
            else:
                return {
                    "success": False,
                    "error": str(e),
                    "message": "No fallback available"
                }

# Example: Web search with fallback to cached results
class WebSearchWithFallback:
    """Web search with graceful degradation."""

    def __init__(self):
        self.degradation_manager = GracefulDegradationManager()
        self.cache = {}  # Simple cache for demo

        # Register fallback handler
        self.degradation_manager.register_fallback(
            "web_search",
            self.cached_search_fallback
        )

    async def search(self, query: str) -> Dict[str, Any]:
        """Main search method with fallback."""

        return await self.degradation_manager.execute_with_fallback(
            "web_search",
            self.primary_web_search,
            query
        )

    async def primary_web_search(self, query: str) -> List[Dict[str, Any]]:
        """Primary web search implementation."""

        # Simulate potential failure
        import random
        if random.random() < 0.3:  # 30% chance of failure
            raise Exception("Web search API unavailable")

        # Mock search results
        results = [
            {"title": f"Result for {query}", "url": f"https://example.com/{query}"}
        ]

        # Cache results
        self.cache[query] = {
            "results": results,
            "timestamp": datetime.now().isoformat()
        }

        return results

    async def cached_search_fallback(self, query: str) -> List[Dict[str, Any]]:
        """Fallback to cached results."""

        cached_result = self.cache.get(query)

        if cached_result:
            # Check if cache is not too old (e.g., 1 hour)
            cached_time = datetime.fromisoformat(cached_result["timestamp"])
            if datetime.now() - cached_time < timedelta(hours=1):
                logger.info(f"Using cached results for query: {query}")
                return cached_result["results"]

        # If no cache, return limited results
        logger.warning(f"No fresh cache for query: {query}, returning limited results")
        return [
            {
                "title": f"Cached/Limited result for: {query}",
                "url": "https://example.com",
                "note": "This is a fallback result due to service unavailability"
            }
        ]
```

**Retry Logic with Exponential Backoff**
```python
import asyncio
import random
from typing import Callable, Any, Optional, Dict

class RetryManager:
    """Manage retry logic with exponential backoff and jitter."""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number."""

        # Exponential backoff
        delay = self.base_delay * (self.exponential_base ** attempt)

        # Cap at max delay
        delay = min(delay, self.max_delay)

        # Add jitter to prevent thundering herd
        if self.jitter:
            delay *= (0.5 + random.random() * 0.5)  # 50-100% of calculated delay

        return delay

    async def retry_with_backoff(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute function with retry and exponential backoff."""

        last_exception = None

        for attempt in range(self.max_attempts):
            try:
                result = await func(*args, **kwargs)

                return {
                    "success": True,
                    "result": result,
                    "attempts": attempt + 1
                }

            except Exception as e:
                last_exception = e
                logger.warning(f"Attempt {attempt + 1} failed: {e}")

                # Don't delay after the last attempt
                if attempt < self.max_attempts - 1:
                    delay = self.calculate_delay(attempt)
                    logger.info(f"Retrying in {delay:.2f} seconds...")
                    await asyncio.sleep(delay)

        # All attempts failed
        return {
            "success": False,
            "error": str(last_exception),
            "attempts": self.max_attempts
        }

    def should_retry(self, exception: Exception) -> bool:
        """Determine if an exception should trigger a retry."""

        # Don't retry on certain types of errors
        non_retryable_errors = [
            ValueError,  # Bad input
            KeyError,    # Missing data
            TypeError,   # Wrong type
        ]

        if type(exception) in non_retryable_errors:
            return False

        # Retry on network/service errors
        retryable_patterns = [
            "timeout",
            "connection",
            "service unavailable",
            "rate limit"
        ]

        error_message = str(exception).lower()
        return any(pattern in error_message for pattern in retryable_patterns)

# Circuit breaker pattern
class CircuitBreaker:
    """Circuit breaker to prevent cascading failures."""

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def _can_attempt(self) -> bool:
        """Check if we can attempt the operation."""

        if self.state == "CLOSED":
            return True

        if self.state == "OPEN":
            # Check if timeout has passed
            if self.last_failure_time:
                time_since_failure = datetime.now() - self.last_failure_time
                if time_since_failure.total_seconds() > self.timeout:
                    self.state = "HALF_OPEN"
                    return True
            return False

        if self.state == "HALF_OPEN":
            return True

        return False

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function through circuit breaker."""

        if not self._can_attempt():
            raise Exception(f"Circuit breaker is OPEN. Service unavailable.")

        try:
            result = await func(*args, **kwargs)

            # Success - reset circuit breaker
            self.failure_count = 0
            self.state = "CLOSED"

            return result

        except self.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.now()

            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                logger.warning(f"Circuit breaker opened after {self.failure_count} failures")

            raise e

# Integration with LangGraph nodes
class ResilientNodeExecutor:
    """Execute nodes with comprehensive error handling."""

    def __init__(self):
        self.retry_manager = RetryManager(max_attempts=3, base_delay=1.0)
        self.circuit_breakers = {}

    def get_circuit_breaker(self, node_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for node."""

        if node_name not in self.circuit_breakers:
            self.circuit_breakers[node_name] = CircuitBreaker(
                failure_threshold=3,
                timeout=30.0
            )

        return self.circuit_breakers[node_name]

    async def execute_node_with_resilience(
        self,
        node_func: Callable,
        node_name: str,
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute node with full resilience patterns."""

        circuit_breaker = self.get_circuit_breaker(node_name)

        async def wrapped_execution():
            return await circuit_breaker.call(node_func, state)

        # Execute with retry logic
        result = await self.retry_manager.retry_with_backoff(wrapped_execution)

        if not result["success"]:
            # Node failed completely, return safe fallback
            return {
                "messages": [AIMessage(content=f"Node {node_name} failed: {result['error']}")],
                "node_error": result["error"],
                "attempts": result["attempts"],
                "fallback_used": True
            }

        return result["result"]

# Usage in node definition
resilient_executor = ResilientNodeExecutor()

async def resilient_research_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Research node with full error resilience."""

    async def core_research_logic(state):
        # Your actual research logic here
        query = state.get("query", "")

        # Simulate potential failure
        if random.random() < 0.4:  # 40% chance of failure
            raise Exception("Research service temporarily unavailable")

        return {
            "messages": [AIMessage(content=f"Research completed for: {query}")],
            "research_results": [{"title": "Sample result"}]
        }

    return await resilient_executor.execute_node_with_resilience(
        core_research_logic,
        "research_node",
        state
    )
```

**Documentation References:**
- Streaming Modes: https://langchain-ai.github.io/langgraph/how-tos/streaming/
- Human-in-the-Loop: https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/
- Input Validation: https://python.langchain.com/docs/how_to/structured_output
- Error Handling: https://langchain-ai.github.io/langgraph/how-tos/tool-calling-errors/
- Circuit Breaker Pattern: https://python.langchain.com/docs/guides/development/debugging
- Retry Strategies: https://python.langchain.com/docs/how_to/retry/

## 5. Best Practices

### Graph Construction Patterns

**Node Definition Best Practices**
```python
from typing import Dict, Any, Optional, List
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
import logging

logger = logging.getLogger(__name__)

# ✅ CORRECT: Single responsibility nodes
def research_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Single-purpose node for research operations.

    Responsibilities:
    - Extract query from state
    - Perform search operation
    - Return structured results

    Does NOT handle:
    - Analysis (separate node)
    - Formatting (separate node)
    - Decision making (separate node)
    """

    query = state.get("query", "")

    if not query:
        return {
            "messages": [AIMessage(content="No query provided for research")],
            "research_error": "missing_query"
        }

    try:
        # Single focused operation
        results = perform_research(query)

        return {
            "messages": [AIMessage(content=f"Research completed: {len(results)} results found")],
            "research_results": results,
            "research_status": "completed"
        }

    except Exception as e:
        logger.error(f"Research failed: {e}")
        return {
            "messages": [AIMessage(content=f"Research failed: {str(e)}")],
            "research_error": str(e),
            "research_status": "failed"
        }

# ❌ AVOID: Multi-responsibility nodes
def bad_research_and_analysis_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    BAD: Node doing too many things
    - Research (should be separate)
    - Analysis (should be separate)
    - Formatting (should be separate)
    - Decision making (should be separate)
    """
    # Don't do this - too many responsibilities in one node
    pass

# ✅ CORRECT: Proper state updates with clear contracts
def analysis_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analysis node with clear input/output contract.

    Input requirements:
    - research_results: List[Dict] - Results to analyze

    Output guarantees:
    - analysis_summary: str - Summary of analysis
    - key_insights: List[str] - Key insights found
    - confidence_score: float - Confidence in analysis
    """

    research_results = state.get("research_results", [])

    if not research_results:
        return {
            "messages": [AIMessage(content="No research results to analyze")],
            "analysis_summary": "No data available for analysis",
            "key_insights": [],
            "confidence_score": 0.0
        }

    # Perform focused analysis
    summary = analyze_results(research_results)
    insights = extract_insights(research_results)
    confidence = calculate_confidence(research_results, summary)

    return {
        "messages": [AIMessage(content=f"Analysis complete with {len(insights)} insights")],
        "analysis_summary": summary,
        "key_insights": insights,
        "confidence_score": confidence
    }

# Helper functions for clean node implementation
def validate_node_inputs(state: Dict[str, Any], required_keys: List[str]) -> Optional[str]:
    """Validate required inputs for a node."""
    missing_keys = [key for key in required_keys if key not in state or not state[key]]
    return f"Missing required inputs: {missing_keys}" if missing_keys else None

def create_error_response(error_message: str, error_type: str = "general") -> Dict[str, Any]:
    """Create standardized error response."""
    return {
        "messages": [AIMessage(content=f"Error: {error_message}")],
        "error_type": error_type,
        "error_message": error_message,
        "node_status": "failed"
    }
```

**Edge Management and Routing Logic**
```python
from langgraph.graph import StateGraph, END, START

# ✅ CORRECT: Clear routing logic with proper conditions
def create_research_workflow():
    """Create workflow with clean edge management."""

    workflow = StateGraph(ResearchState)

    # Add nodes
    workflow.add_node("research", research_node)
    workflow.add_node("validation", validation_node)
    workflow.add_node("analysis", analysis_node)
    workflow.add_node("synthesis", synthesis_node)
    workflow.add_node("error_handler", error_handling_node)

    # Set entry point
    workflow.add_edge(START, "research")

    # ✅ CORRECT: Conditional edges with clear logic
    workflow.add_conditional_edges(
        "research",
        research_router,
        {
            "success": "validation",
            "error": "error_handler",
            "retry": "research"  # Allow retries
        }
    )

    workflow.add_conditional_edges(
        "validation",
        validation_router,
        {
            "valid": "analysis",
            "invalid": "error_handler",
            "needs_more_data": "research"
        }
    )

    # Simple edges for linear flow
    workflow.add_edge("analysis", "synthesis")
    workflow.add_edge("synthesis", END)
    workflow.add_edge("error_handler", END)

    return workflow

def research_router(state: Dict[str, Any]) -> str:
    """Router function with clear decision logic."""

    # Check for errors first
    if state.get("research_error"):
        error_type = state.get("research_error")

        # Decide whether to retry or handle as error
        if error_type in ["rate_limit", "timeout", "temporary_failure"]:
            retry_count = state.get("retry_count", 0)
            if retry_count < 3:
                return "retry"

        return "error"

    # Check for successful results
    research_results = state.get("research_results", [])
    if research_results and len(research_results) > 0:
        return "success"

    # No results but no error - handle as error
    return "error"

def validation_router(state: Dict[str, Any]) -> str:
    """Validation routing with clear criteria."""

    research_results = state.get("research_results", [])

    if not research_results:
        return "invalid"

    # Check quality thresholds
    quality_score = calculate_result_quality(research_results)

    if quality_score < 0.3:
        return "needs_more_data"
    elif quality_score < 0.6:
        return "invalid"
    else:
        return "valid"

# ❌ AVOID: Complex routing logic
def bad_complex_router(state: Dict[str, Any]) -> str:
    """BAD: Overly complex routing logic that's hard to debug."""

    # Don't do this - too complex, hard to test and debug
    if state.get("research_results") and len(state["research_results"]) > 5:
        if state.get("confidence_score", 0) > 0.8:
            if state.get("user_requirements", {}).get("depth") == "detailed":
                if not state.get("analysis_complete"):
                    return "deep_analysis"
                else:
                    return "synthesis" if state.get("quality_check") else "validation"
    # ... more nested conditions
```

**Graph Composition Patterns**
```python
from typing import Dict, Callable

class WorkflowBuilder:
    """Builder pattern for composing complex workflows."""

    def __init__(self, state_schema):
        self.workflow = StateGraph(state_schema)
        self.nodes = {}
        self.routers = {}

    def add_processing_stage(
        self,
        stage_name: str,
        nodes: Dict[str, Callable],
        routing_logic: Optional[Callable] = None
    ):
        """Add a processing stage with multiple nodes."""

        stage_nodes = {}

        for node_name, node_func in nodes.items():
            full_node_name = f"{stage_name}_{node_name}"
            self.workflow.add_node(full_node_name, node_func)
            stage_nodes[node_name] = full_node_name

        # Store for later connection
        self.nodes[stage_name] = stage_nodes
        if routing_logic:
            self.routers[stage_name] = routing_logic

        return self

    def connect_stages(self, from_stage: str, to_stage: str, routing_key: str = None):
        """Connect processing stages."""

        if routing_key and from_stage in self.routers:
            # Use conditional edges
            self.workflow.add_conditional_edges(
                list(self.nodes[from_stage].values())[-1],  # Last node of stage
                self.routers[from_stage],
                {routing_key: list(self.nodes[to_stage].values())[0]}  # First node of next stage
            )
        else:
            # Use simple edges
            self.workflow.add_edge(
                list(self.nodes[from_stage].values())[-1],
                list(self.nodes[to_stage].values())[0]
            )

        return self

    def build(self, checkpointer=None):
        """Build the final workflow."""
        return self.workflow.compile(checkpointer=checkpointer)

# Usage example
def create_complex_research_workflow():
    """Create complex workflow using builder pattern."""

    builder = WorkflowBuilder(ComplexResearchState)

    # Add data collection stage
    builder.add_processing_stage(
        "collection",
        {
            "web_search": web_search_node,
            "database_query": database_query_node,
            "api_fetch": api_fetch_node
        },
        collection_router
    )

    # Add processing stage
    builder.add_processing_stage(
        "processing",
        {
            "clean": data_cleaning_node,
            "validate": validation_node,
            "enrich": enrichment_node
        },
        processing_router
    )

    # Add analysis stage
    builder.add_processing_stage(
        "analysis",
        {
            "statistical": statistical_analysis_node,
            "semantic": semantic_analysis_node,
            "trend": trend_analysis_node
        }
    )

    # Connect stages
    builder.connect_stages("collection", "processing", "success")
    builder.connect_stages("processing", "analysis", "validated")

    return builder.build()
```

### State Design Best Practices

**Minimal State Design Principles**
```python
from typing import TypedDict, Annotated, Sequence, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

# ✅ CORRECT: Minimal, focused state
class FocusedResearchState(TypedDict):
    """Minimal state with only essential data."""

    # Core conversation
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # Essential workflow state
    current_stage: str  # track progress
    query: str         # current research query

    # Results (use reducers for accumulation)
    results: Annotated[List[Dict[str, Any]], add_list_reducer]

    # Minimal metadata
    confidence_score: float
    error_message: Optional[str]

# ❌ AVOID: Bloated state with everything
class BlogatedState(TypedDict):
    """BAD: Too much state data."""

    messages: Annotated[Sequence[BaseMessage], add_messages]

    # Too much metadata
    user_id: str
    session_id: str
    start_time: str
    last_activity: str
    user_preferences: Dict[str, Any]
    session_metadata: Dict[str, Any]

    # Redundant data
    original_query: str
    processed_query: str
    query_embeddings: List[float]
    query_analysis: Dict[str, Any]

    # Everything gets stored
    raw_search_results: List[Dict]
    processed_search_results: List[Dict]
    filtered_search_results: List[Dict]
    ranked_search_results: List[Dict]

    # Debug data (shouldn't be in production state)
    debug_info: Dict[str, Any]
    timing_data: Dict[str, float]
    api_responses: List[Dict]

# ✅ CORRECT: Proper data normalization
def add_list_reducer(current: List[Dict], new: List[Dict]) -> List[Dict]:
    """Reducer that prevents duplicates and maintains order."""

    if not current:
        return new

    # Create lookup for existing items
    existing_ids = {item.get("id") for item in current if item.get("id")}

    # Add only new items
    filtered_new = [item for item in new if item.get("id") not in existing_ids]

    return current + filtered_new

class NormalizedState(TypedDict):
    """Properly normalized state design."""

    messages: Annotated[Sequence[BaseMessage], add_messages]

    # IDs instead of full objects
    current_query_id: str
    active_result_ids: List[str]

    # Normalized data stores
    queries: Dict[str, Dict[str, Any]]      # id -> query data
    results: Dict[str, Dict[str, Any]]      # id -> result data

    # Working state
    workflow_step: str
    processing_flags: Dict[str, bool]

# State utility functions
class StateManager:
    """Utility functions for state management."""

    @staticmethod
    def add_query(state: NormalizedState, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add query to normalized state."""

        query_id = query_data.get("id") or str(uuid.uuid4())

        return {
            "current_query_id": query_id,
            "queries": {**state.get("queries", {}), query_id: query_data}
        }

    @staticmethod
    def add_results(state: NormalizedState, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Add results to normalized state."""

        result_updates = {}
        result_ids = []

        for result in results:
            result_id = result.get("id") or str(uuid.uuid4())
            result_updates[result_id] = result
            result_ids.append(result_id)

        existing_results = state.get("results", {})
        active_ids = state.get("active_result_ids", [])

        return {
            "results": {**existing_results, **result_updates},
            "active_result_ids": active_ids + result_ids
        }

    @staticmethod
    def cleanup_state(state: NormalizedState, max_results: int = 50) -> Dict[str, Any]:
        """Clean up state to prevent bloat."""

        active_ids = state.get("active_result_ids", [])

        if len(active_ids) > max_results:
            # Keep only the most recent results
            keep_ids = active_ids[-max_results:]

            # Filter results
            all_results = state.get("results", {})
            filtered_results = {id: data for id, data in all_results.items() if id in keep_ids}

            return {
                "results": filtered_results,
                "active_result_ids": keep_ids
            }

        return {}
```

### Agent Composition Strategies

**Single vs Multi-Agent Decision Framework**
```python
from enum import Enum
from typing import List, Dict, Any

class TaskComplexity(Enum):
    SIMPLE = "simple"           # Single operation, linear flow
    MODERATE = "moderate"       # Multiple steps, some branching
    COMPLEX = "complex"         # Multiple domains, parallel processing
    ENTERPRISE = "enterprise"   # Multiple teams, governance, compliance

class AgentArchitectureDecision:
    """Framework for deciding on agent architecture."""

    @staticmethod
    def recommend_architecture(
        task_complexity: TaskComplexity,
        domain_count: int,
        parallel_processing: bool,
        team_size: int,
        expertise_separation: bool
    ) -> Dict[str, Any]:
        """Recommend agent architecture based on requirements."""

        if task_complexity == TaskComplexity.SIMPLE and domain_count == 1:
            return {
                "architecture": "single_agent",
                "pattern": "create_react_agent",
                "reasoning": "Simple, single-domain task best handled by single agent"
            }

        if task_complexity == TaskComplexity.MODERATE and domain_count <= 2:
            return {
                "architecture": "single_agent_with_specialized_tools",
                "pattern": "create_react_agent_with_tool_groups",
                "reasoning": "Moderate complexity can be handled with tool specialization"
            }

        if domain_count > 2 or expertise_separation:
            return {
                "architecture": "multi_agent_specialist",
                "pattern": "create_supervisor_with_specialists",
                "reasoning": "Multiple domains require specialized agents"
            }

        if parallel_processing or team_size > 5:
            return {
                "architecture": "multi_agent_parallel",
                "pattern": "create_supervisor_with_parallel_execution",
                "reasoning": "Parallel processing benefits from multiple agents"
            }

        return {
            "architecture": "single_agent",
            "pattern": "create_react_agent",
            "reasoning": "Default to simplest architecture"
        }

# ✅ CORRECT: Single agent with good tool organization
def create_specialized_single_agent():
    """Single agent with well-organized tools."""

    # Group tools by domain
    research_tools = [web_search, academic_search, database_query]
    analysis_tools = [statistical_analysis, text_analysis, data_visualization]
    output_tools = [document_generator, chart_creator, report_formatter]

    all_tools = research_tools + analysis_tools + output_tools

    prompt = """You are a research analyst with access to comprehensive tools.

    Tool Categories:
    - Research: web_search, academic_search, database_query
    - Analysis: statistical_analysis, text_analysis, data_visualization
    - Output: document_generator, chart_creator, report_formatter

    Workflow approach:
    1. Use research tools to gather information
    2. Use analysis tools to process findings
    3. Use output tools to present results

    Always explain your tool selection and reasoning."""

    return create_react_agent(
        model=model,
        tools=all_tools,
        prompt=prompt
    )

# ✅ CORRECT: Multi-agent with clear specialization
def create_specialized_multi_agent_system():
    """Multi-agent system with clear domain separation."""

    # Research specialist
    research_agent = create_react_agent(
        model=claude_model,  # Use Claude for complex research
        tools=[web_search, academic_search, database_query],
        prompt="""You are a research specialist. Focus on:
        - Finding comprehensive, accurate information
        - Evaluating source credibility
        - Synthesizing findings from multiple sources
        Always provide source citations and confidence levels."""
    )

    # Analysis specialist
    analysis_agent = create_react_agent(
        model=gpt4_model,  # Use GPT-4 for tool-heavy analysis
        tools=[statistical_analysis, text_analysis, data_processing],
        prompt="""You are a data analyst. Focus on:
        - Processing and analyzing data
        - Identifying patterns and trends
        - Statistical validation of findings
        Always provide confidence intervals and methodology."""
    )

    # Communication specialist
    communication_agent = create_react_agent(
        model=claude_model,  # Use Claude for communication
        tools=[document_generator, visualization_tools, presentation_tools],
        prompt="""You are a communication specialist. Focus on:
        - Clear, compelling presentation of findings
        - Appropriate visualization selection
        - Audience-appropriate language and format
        Always prioritize clarity and actionable insights."""
    )

    # Supervisor with clear delegation
    supervisor_prompt = """You coordinate specialist agents for research projects.

    Agent Capabilities:
    - research_agent: Information gathering, source validation, synthesis
    - analysis_agent: Data processing, statistical analysis, pattern identification
    - communication_agent: Report writing, visualization, presentation

    Delegation Strategy:
    1. Start with research_agent for information gathering
    2. Pass findings to analysis_agent for processing
    3. Have communication_agent create final deliverables
    4. Allow iteration between agents as needed

    Always specify clear, focused tasks for each agent."""

    return create_supervisor(
        agents=[research_agent, analysis_agent, communication_agent],
        model=supervisor_model,
        prompt=supervisor_prompt
    )

# Agent communication patterns
class AgentCommunication:
    """Patterns for agent-to-agent communication."""

    @staticmethod
    def create_handoff_message(
        from_agent: str,
        to_agent: str,
        task_description: str,
        context_data: Dict[str, Any],
        success_criteria: List[str]
    ) -> Dict[str, Any]:
        """Create structured handoff between agents."""

        return {
            "type": "agent_handoff",
            "from_agent": from_agent,
            "to_agent": to_agent,
            "task": task_description,
            "context": context_data,
            "success_criteria": success_criteria,
            "timestamp": datetime.now().isoformat()
        }

    @staticmethod
    def create_collaboration_request(
        requesting_agent: str,
        target_agent: str,
        collaboration_type: str,  # "review", "validate", "enhance"
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Request collaboration between agents."""

        return {
            "type": "collaboration_request",
            "requesting_agent": requesting_agent,
            "target_agent": target_agent,
            "collaboration_type": collaboration_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
```

### Testing Strategies

**Node Unit Testing Patterns**
```python
import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any

class TestResearchNode:
    """Unit tests for research node."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_state = {
            "messages": [HumanMessage(content="Test query")],
            "query": "test research query",
            "current_stage": "research"
        }

    def test_research_node_success(self):
        """Test successful research operation."""

        # Mock the research function
        mock_results = [{"title": "Test Result", "url": "https://example.com"}]

        with patch('path.to.perform_research', return_value=mock_results):
            result = research_node(self.mock_state)

        # Verify results
        assert "research_results" in result
        assert result["research_status"] == "completed"
        assert len(result["messages"]) > 0
        assert isinstance(result["messages"][0], AIMessage)

    def test_research_node_missing_query(self):
        """Test node behavior with missing query."""

        state_without_query = {
            "messages": [HumanMessage(content="Test")],
            "current_stage": "research"
            # No query field
        }

        result = research_node(state_without_query)

        assert "research_error" in result
        assert result["research_error"] == "missing_query"
        assert "research_results" not in result

    def test_research_node_exception_handling(self):
        """Test node error handling."""

        with patch('path.to.perform_research', side_effect=Exception("API Error")):
            result = research_node(self.mock_state)

        assert "research_error" in result
        assert result["research_status"] == "failed"
        assert "API Error" in result["research_error"]

    @pytest.mark.parametrize("query,expected_status", [
        ("", "failed"),
        ("valid query", "completed"),
        ("a" * 1000, "completed"),  # Long query
    ])
    def test_research_node_various_inputs(self, query, expected_status):
        """Test node with various input scenarios."""

        test_state = {**self.mock_state, "query": query}

        with patch('path.to.perform_research', return_value=[]):
            result = research_node(test_state)

        if expected_status == "completed":
            assert result.get("research_status") == expected_status
        else:
            assert result.get("research_error") is not None

# Integration testing for complete workflows
class TestWorkflowIntegration:
    """Integration tests for complete workflows."""

    def setup_method(self):
        """Set up test workflow."""
        self.workflow = create_research_workflow()
        self.test_config = {"configurable": {"thread_id": "test_thread"}}

    async def test_complete_workflow_success(self):
        """Test complete workflow execution."""

        input_data = {
            "messages": [HumanMessage(content="Research AI trends")],
            "query": "AI trends 2024"
        }

        # Mock all external dependencies
        with patch('path.to.perform_research') as mock_research, \
             patch('path.to.analyze_results') as mock_analysis:

            mock_research.return_value = [{"title": "AI Trend", "content": "Test content"}]
            mock_analysis.return_value = "Test analysis"

            result = await self.workflow.ainvoke(input_data, self.test_config)

        # Verify final state
        assert "analysis_summary" in result
        assert "confidence_score" in result
        assert len(result["messages"]) > 1

    async def test_workflow_error_recovery(self):
        """Test workflow error handling and recovery."""

        input_data = {
            "messages": [HumanMessage(content="Research with error")],
            "query": "test query"
        }

        # Mock research to fail, but analysis to succeed
        with patch('path.to.perform_research', side_effect=Exception("Research failed")):

            result = await self.workflow.ainvoke(input_data, self.test_config)

        # Should have error handling
        assert "error" in str(result).lower()

    async def test_workflow_routing(self):
        """Test conditional routing in workflow."""

        # Test data that should trigger different routes
        test_cases = [
            {"query": "good query", "expected_path": ["research", "validation", "analysis"]},
            {"query": "", "expected_path": ["research", "error_handler"]},
        ]

        for case in test_cases:
            input_data = {
                "messages": [HumanMessage(content="Test")],
                "query": case["query"]
            }

            # Track execution path
            execution_path = []

            # Mock nodes to track execution
            def track_execution(node_name):
                def wrapper(state):
                    execution_path.append(node_name)
                    return {"messages": [AIMessage(content=f"{node_name} executed")]}
                return wrapper

            # This would require more sophisticated mocking in practice
            # For illustration purposes only

# Mock patterns for external dependencies
class MockPatterns:
    """Common mock patterns for testing."""

    @staticmethod
    def mock_llm_response(content: str = "Test response"):
        """Mock LLM response."""
        mock_message = Mock()
        mock_message.content = content
        return mock_message

    @staticmethod
    def mock_tool_execution(return_value: Any = "Tool result"):
        """Mock tool execution."""
        return Mock(return_value=return_value)

    @staticmethod
    def mock_api_call(status_code: int = 200, json_data: Dict = None):
        """Mock API call."""
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.json.return_value = json_data or {"status": "success"}
        return mock_response

# Fixture for common test data
@pytest.fixture
def sample_research_state():
    """Sample state for testing."""
    return {
        "messages": [
            HumanMessage(content="Research machine learning trends"),
            AIMessage(content="I'll help you research ML trends")
        ],
        "query": "machine learning trends 2024",
        "current_stage": "research",
        "research_results": [],
        "confidence_score": 0.0
    }

@pytest.fixture
def mock_checkpointer():
    """Mock checkpointer for testing."""
    checkpointer = Mock()
    checkpointer.get.return_value = None
    checkpointer.put.return_value = None
    return checkpointer
```

### Performance Optimization

**Memory and Computational Efficiency**
```python
import asyncio
import psutil
import time
from typing import AsyncGenerator
from functools import wraps

class PerformanceOptimizer:
    """Performance optimization utilities for LangGraph."""

    @staticmethod
    def monitor_memory_usage(func):
        """Decorator to monitor memory usage of nodes."""

        @wraps(func)
        async def wrapper(state: Dict[str, Any]) -> Dict[str, Any]:

            # Measure memory before
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024  # MB

            start_time = time.time()

            try:
                result = await func(state)

                # Measure memory after
                memory_after = process.memory_info().rss / 1024 / 1024  # MB
                execution_time = time.time() - start_time

                # Add performance metrics to result
                result["performance_metrics"] = {
                    "memory_used_mb": memory_after - memory_before,
                    "execution_time_seconds": execution_time,
                    "peak_memory_mb": memory_after
                }

                # Log if memory usage is high
                if memory_after - memory_before > 100:  # More than 100MB
                    logger.warning(f"Node {func.__name__} used {memory_after - memory_before:.2f}MB memory")

                return result

            except Exception as e:
                logger.error(f"Node {func.__name__} failed after {time.time() - start_time:.2f}s: {e}")
                raise

        return wrapper

    @staticmethod
    def optimize_state_size(state: Dict[str, Any], max_size_mb: float = 10.0) -> Dict[str, Any]:
        """Optimize state size by removing or compressing large data."""

        import sys
        import json

        # Calculate current state size
        state_size = sys.getsizeof(json.dumps(state, default=str)) / 1024 / 1024

        if state_size < max_size_mb:
            return {}  # No optimization needed

        optimizations = {}

        # Compress large text fields
        for key, value in state.items():
            if isinstance(value, str) and len(value) > 10000:
                # Truncate very long strings
                optimizations[key] = value[:10000] + "... [truncated]"

            elif isinstance(value, list) and len(value) > 100:
                # Limit list sizes
                optimizations[key] = value[:100]
                optimizations[f"{key}_truncated_count"] = len(value) - 100

        return optimizations

# Caching strategies
class StateCache:
    """Intelligent caching for expensive operations."""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.cache = {}
        self.timestamps = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        """Get cached value if still valid."""

        if key not in self.cache:
            return None

        # Check TTL
        if time.time() - self.timestamps[key] > self.ttl_seconds:
            self.remove(key)
            return None

        return self.cache[key]

    def put(self, key: str, value: Any):
        """Cache value with TTL."""

        # Evict oldest if at capacity
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.timestamps.keys(), key=lambda k: self.timestamps[k])
            self.remove(oldest_key)

        self.cache[key] = value
        self.timestamps[key] = time.time()

    def remove(self, key: str):
        """Remove cached value."""
        self.cache.pop(key, None)
        self.timestamps.pop(key, None)

    def clear(self):
        """Clear all cached values."""
        self.cache.clear()
        self.timestamps.clear()

# Global cache instance
global_cache = StateCache()

def with_caching(cache_key_func: Callable[[Dict[str, Any]], str]):
    """Decorator to add caching to node operations."""

    def decorator(node_func):
        @wraps(node_func)
        async def wrapper(state: Dict[str, Any]) -> Dict[str, Any]:

            # Generate cache key
            cache_key = cache_key_func(state)

            # Try to get from cache
            cached_result = global_cache.get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for node {node_func.__name__}")
                return cached_result

            # Execute function
            result = await node_func(state)

            # Cache result
            global_cache.put(cache_key, result)

            return result

        return wrapper
    return decorator

# Usage example with caching
def research_cache_key(state: Dict[str, Any]) -> str:
    """Generate cache key for research operations."""
    query = state.get("query", "")
    return f"research:{hash(query)}"

@with_caching(research_cache_key)
@monitor_memory_usage
async def optimized_research_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Research node with performance optimizations."""

    query = state.get("query", "")

    # Optimize state before processing
    optimizer = PerformanceOptimizer()
    state_optimizations = optimizer.optimize_state_size(state)

    # Apply optimizations
    optimized_state = {**state, **state_optimizations}

    # Perform research with async processing
    results = await perform_async_research(query)

    return {
        "messages": [AIMessage(content=f"Research completed: {len(results)} results")],
        "research_results": results,
        "state_optimized": len(state_optimizations) > 0
    }

# Async/await best practices
class AsyncOptimizations:
    """Best practices for async operations in LangGraph."""

    @staticmethod
    async def parallel_tool_execution(tools: List[Callable], inputs: List[Any]) -> List[Any]:
        """Execute multiple tools in parallel."""

        tasks = [tool(input_data) for tool, input_data in zip(tools, inputs)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Tool {i} failed: {result}")
                processed_results.append({"error": str(result)})
            else:
                processed_results.append(result)

        return processed_results

    @staticmethod
    async def batched_processing(
        items: List[Any],
        batch_size: int,
        processor: Callable
    ) -> AsyncGenerator[List[Any], None]:
        """Process items in batches to manage memory."""

        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]

            # Process batch
            batch_results = await processor(batch)

            yield batch_results

            # Small delay to allow other operations
            await asyncio.sleep(0.01)

    @staticmethod
    async def timeout_protection(
        coro: Callable,
        timeout_seconds: float = 30.0
    ) -> Dict[str, Any]:
        """Protect operations with timeout."""

        try:
            result = await asyncio.wait_for(coro, timeout=timeout_seconds)
            return {"success": True, "result": result}

        except asyncio.TimeoutError:
            logger.error(f"Operation timed out after {timeout_seconds} seconds")
            return {"success": False, "error": "Operation timed out"}

        except Exception as e:
            logger.error(f"Operation failed: {e}")
            return {"success": False, "error": str(e)}

# Example of optimized node using all patterns
@monitor_memory_usage
async def high_performance_analysis_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Analysis node optimized for performance."""

    research_results = state.get("research_results", [])

    if not research_results:
        return {"messages": [AIMessage(content="No data to analyze")]}

    async_ops = AsyncOptimizations()

    # Process in batches to manage memory
    analysis_results = []

    async for batch_result in async_ops.batched_processing(
        research_results,
        batch_size=10,
        processor=analyze_batch
    ):
        analysis_results.extend(batch_result)

    # Parallel processing for different analysis types
    analysis_tasks = [
        statistical_analysis(analysis_results),
        semantic_analysis(analysis_results),
        trend_analysis(analysis_results)
    ]

    analysis_types = await async_ops.parallel_tool_execution(
        analysis_tasks,
        [analysis_results] * 3
    )

    return {
        "messages": [AIMessage(content="Comprehensive analysis completed")],
        "statistical_analysis": analysis_types[0],
        "semantic_analysis": analysis_types[1],
        "trend_analysis": analysis_types[2],
        "total_items_analyzed": len(analysis_results)
    }
```

**Documentation References:**
- Graph Construction: https://langchain-ai.github.io/langgraph/concepts/low_level/#graphs
- State Design: https://langchain-ai.github.io/langgraph/concepts/low_level/#state
- Agent Composition: https://langchain-ai.github.io/langgraph/tutorials/multi_agent/agent_supervisor/
- Testing LangGraph: https://langchain-ai.github.io/langgraph/how-tos/testing/
- Performance: https://langchain-ai.github.io/langgraph/concepts/persistence/#performance
- Async Patterns: https://python.langchain.com/docs/guides/development/debugging

## 6. Coding Standards

### Type Safety and Modern Python Typing

**LangGraph-Specific Type Annotations**
```python
from typing import (
    TypedDict, Annotated, Sequence, List, Dict, Any, Optional,
    Union, Callable, Protocol, Generic, TypeVar, Literal, get_type_hints
)
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field, validator
from abc import ABC, abstractmethod
import inspect

# ✅ CORRECT: Comprehensive type annotations for state
class ResearchState(TypedDict):
    """Research workflow state with complete type safety."""

    # Core messaging with reducer
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # Required fields with specific types
    query: str
    current_stage: Literal["research", "analysis", "synthesis", "complete"]

    # Optional fields with proper defaults
    research_results: Optional[List[Dict[str, Any]]]
    analysis_summary: Optional[str]
    confidence_score: Optional[float]
    error_message: Optional[str]

    # Complex nested structures
    metadata: Optional[Dict[str, Union[str, int, float, bool, List[str]]]]
    processing_flags: Optional[Dict[Literal["validated", "processed", "reviewed"], bool]]

# Generic types for reusable components
T = TypeVar('T')
StateType = TypeVar('StateType', bound=Dict[str, Any])

class NodeFunction(Protocol[StateType]):
    """Protocol for type-safe node functions."""

    def __call__(self, state: StateType) -> Dict[str, Any]:
        """Node function signature."""
        ...

class AsyncNodeFunction(Protocol[StateType]):
    """Protocol for async node functions."""

    async def __call__(self, state: StateType) -> Dict[str, Any]:
        """Async node function signature."""
        ...

# ✅ CORRECT: Generic workflow builder with type safety
class TypeSafeWorkflowBuilder(Generic[StateType]):
    """Type-safe workflow builder with generic state."""

    def __init__(self, state_type: type[StateType]):
        self.state_type = state_type
        self.nodes: Dict[str, Union[NodeFunction[StateType], AsyncNodeFunction[StateType]]] = {}
        self.routers: Dict[str, Callable[[StateType], str]] = {}

    def add_node(
        self,
        name: str,
        func: Union[NodeFunction[StateType], AsyncNodeFunction[StateType]]
    ) -> 'TypeSafeWorkflowBuilder[StateType]':
        """Add a type-safe node."""

        # Validate function signature at build time
        sig = inspect.signature(func)
        params = list(sig.parameters.values())

        if len(params) != 1:
            raise TypeError(f"Node function {name} must have exactly one parameter")

        # Store node
        self.nodes[name] = func
        return self

    def add_router(
        self,
        name: str,
        router_func: Callable[[StateType], str]
    ) -> 'TypeSafeWorkflowBuilder[StateType]':
        """Add a type-safe router function."""
        self.routers[name] = router_func
        return self

# Type-safe node decorators
def typed_node(state_type: type[StateType]):
    """Decorator for type-safe node creation."""

    def decorator(func: Callable[[StateType], Dict[str, Any]]):

        # Validate function signature
        sig = inspect.signature(func)
        params = list(sig.parameters.values())

        if len(params) != 1:
            raise TypeError("Node function must have exactly one parameter")

        # Add runtime type checking
        def wrapper(state: StateType) -> Dict[str, Any]:
            # Validate input state structure
            if not isinstance(state, dict):
                raise TypeError(f"State must be a dictionary, got {type(state)}")

            # Check required fields for TypedDict
            if hasattr(state_type, '__required_keys__'):
                missing_keys = state_type.__required_keys__ - set(state.keys())
                if missing_keys:
                    raise ValueError(f"Missing required state keys: {missing_keys}")

            result = func(state)

            # Validate output
            if not isinstance(result, dict):
                raise TypeError(f"Node function must return dict, got {type(result)}")

            return result

        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        wrapper.__annotations__ = func.__annotations__

        return wrapper

    return decorator

# Usage example with complete type safety
@typed_node(ResearchState)
def research_node(state: ResearchState) -> Dict[str, Any]:
    """Type-safe research node with complete annotations."""

    query: str = state["query"]
    current_stage: str = state["current_stage"]

    # Type-safe result construction
    result: Dict[str, Any] = {
        "messages": [AIMessage(content=f"Research completed for: {query}")],
        "research_results": [{"title": "Sample", "url": "https://example.com"}],
        "current_stage": "analysis"
    }

    return result

# Runtime type validation utilities
class TypeValidator:
    """Runtime type validation for complex structures."""

    @staticmethod
    def validate_message_sequence(messages: Any) -> Sequence[BaseMessage]:
        """Validate message sequence type."""

        if not isinstance(messages, (list, tuple)):
            raise TypeError(f"Messages must be a sequence, got {type(messages)}")

        validated_messages = []
        for i, msg in enumerate(messages):
            if not isinstance(msg, BaseMessage):
                raise TypeError(f"Message {i} must be BaseMessage, got {type(msg)}")
            validated_messages.append(msg)

        return validated_messages

    @staticmethod
    def validate_state_schema(state: Dict[str, Any], schema: type) -> bool:
        """Validate state against TypedDict schema."""

        if not isinstance(state, dict):
            return False

        # Get type hints
        hints = get_type_hints(schema)

        # Check required keys (simplified - production would be more complex)
        if hasattr(schema, '__required_keys__'):
            missing_keys = schema.__required_keys__ - set(state.keys())
            if missing_keys:
                raise ValueError(f"Missing required keys: {missing_keys}")

        # Validate types (basic validation)
        for key, expected_type in hints.items():
            if key in state:
                value = state[key]
                # Basic type checking (production would handle complex types)
                if hasattr(expected_type, '__origin__'):
                    # Handle generic types like List[str], Dict[str, Any]
                    continue
                elif not isinstance(value, expected_type):
                    raise TypeError(f"Key '{key}' should be {expected_type}, got {type(value)}")

        return True
```

### Comprehensive Error Handling Standards

**Exception Hierarchies and Recovery Patterns**
```python
from typing import Optional, Type, Dict, Any, List
from enum import Enum
import logging
import traceback
from datetime import datetime

# ✅ CORRECT: Custom exception hierarchy for LangGraph applications
class LangGraphError(Exception):
    """Base exception for all LangGraph-related errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        recoverable: bool = True
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        self.recoverable = recoverable
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/serialization."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "context": self.context,
            "recoverable": self.recoverable,
            "timestamp": self.timestamp
        }

class StateValidationError(LangGraphError):
    """State validation failed."""

    def __init__(self, message: str, invalid_keys: List[str], state_context: Dict[str, Any]):
        super().__init__(
            message,
            error_code="STATE_VALIDATION_FAILED",
            context={"invalid_keys": invalid_keys, "state_keys": list(state_context.keys())},
            recoverable=False
        )

class NodeExecutionError(LangGraphError):
    """Node execution failed."""

    def __init__(self, node_name: str, original_error: Exception, state_context: Dict[str, Any]):
        super().__init__(
            f"Node '{node_name}' execution failed: {str(original_error)}",
            error_code="NODE_EXECUTION_FAILED",
            context={
                "node_name": node_name,
                "original_error_type": type(original_error).__name__,
                "state_size": len(state_context)
            },
            recoverable=True
        )
        self.original_error = original_error

class ToolExecutionError(LangGraphError):
    """Tool execution failed."""

    def __init__(self, tool_name: str, error_details: str, input_data: Dict[str, Any]):
        super().__init__(
            f"Tool '{tool_name}' failed: {error_details}",
            error_code="TOOL_EXECUTION_FAILED",
            context={
                "tool_name": tool_name,
                "input_data": input_data,
                "error_details": error_details
            },
            recoverable=True
        )

class ExternalServiceError(LangGraphError):
    """External service unavailable or failed."""

    def __init__(self, service_name: str, status_code: Optional[int] = None, details: str = ""):
        super().__init__(
            f"External service '{service_name}' failed",
            error_code="EXTERNAL_SERVICE_FAILED",
            context={
                "service_name": service_name,
                "status_code": status_code,
                "details": details
            },
            recoverable=True
        )

# Error handling decorators
class ErrorHandlingLevel(Enum):
    STRICT = "strict"        # Fail fast, no recovery
    GRACEFUL = "graceful"    # Try recovery, fallback on failure
    RESILIENT = "resilient"  # Multiple recovery attempts

def handle_errors(
    level: ErrorHandlingLevel = ErrorHandlingLevel.GRACEFUL,
    fallback_response: Optional[Dict[str, Any]] = None,
    log_errors: bool = True
):
    """Comprehensive error handling decorator for node functions."""

    def decorator(func: Callable):

        @wraps(func)
        async def wrapper(state: Dict[str, Any]) -> Dict[str, Any]:

            node_name = func.__name__
            logger = logging.getLogger(f"node.{node_name}")

            try:
                # Validate state before execution
                if not isinstance(state, dict):
                    raise StateValidationError(
                        "State must be a dictionary",
                        invalid_keys=["__root__"],
                        state_context={}
                    )

                # Execute function
                result = await func(state)

                # Validate result
                if not isinstance(result, dict):
                    raise NodeExecutionError(
                        node_name,
                        TypeError(f"Node must return dict, got {type(result)}"),
                        state
                    )

                return result

            except LangGraphError as e:
                # Handle custom exceptions
                if log_errors:
                    logger.error(f"LangGraph error in {node_name}: {e.to_dict()}")

                if level == ErrorHandlingLevel.STRICT or not e.recoverable:
                    raise e

                # Graceful handling
                error_response = {
                    "messages": [AIMessage(content=f"Error in {node_name}: {e.message}")],
                    "error": e.to_dict(),
                    "node_failed": node_name
                }

                if fallback_response:
                    error_response.update(fallback_response)

                return error_response

            except Exception as e:
                # Handle unexpected exceptions
                wrapped_error = NodeExecutionError(node_name, e, state)

                if log_errors:
                    logger.error(f"Unexpected error in {node_name}: {wrapped_error.to_dict()}")
                    logger.error(f"Traceback: {traceback.format_exc()}")

                if level == ErrorHandlingLevel.STRICT:
                    raise wrapped_error

                # Create error response
                error_response = {
                    "messages": [AIMessage(content=f"Unexpected error in {node_name}: {str(e)}")],
                    "error": wrapped_error.to_dict(),
                    "node_failed": node_name
                }

                if fallback_response:
                    error_response.update(fallback_response)

                return error_response

        return wrapper
    return decorator

# Usage with comprehensive error handling
@handle_errors(
    level=ErrorHandlingLevel.GRACEFUL,
    fallback_response={"research_status": "failed", "retry_suggested": True}
)
async def resilient_research_node(state: ResearchState) -> Dict[str, Any]:
    """Research node with comprehensive error handling."""

    query = state.get("query")
    if not query:
        raise StateValidationError(
            "Query is required for research",
            invalid_keys=["query"],
            state_context=state
        )

    try:
        # Attempt external API call
        results = await external_research_api(query)

        return {
            "messages": [AIMessage(content=f"Research completed: {len(results)} results")],
            "research_results": results,
            "research_status": "completed"
        }

    except Exception as e:
        # Convert to domain-specific error
        raise ToolExecutionError("external_research_api", str(e), {"query": query})

# Error recovery strategies
class ErrorRecovery:
    """Error recovery strategies for LangGraph workflows."""

    @staticmethod
    def create_recovery_node(error_types: List[Type[LangGraphError]]):
        """Create a recovery node for specific error types."""

        def recovery_node(state: Dict[str, Any]) -> Dict[str, Any]:
            """Recovery node that handles specific errors."""

            error_info = state.get("error", {})
            error_type = error_info.get("error_type")

            if error_type == "ToolExecutionError":
                # Attempt alternative tools or cached results
                return {
                    "messages": [AIMessage(content="Attempting recovery with alternative approach...")],
                    "recovery_attempted": True,
                    "recovery_method": "alternative_tool"
                }

            elif error_type == "ExternalServiceError":
                # Use fallback service or cached data
                return {
                    "messages": [AIMessage(content="External service unavailable, using fallback...")],
                    "recovery_attempted": True,
                    "recovery_method": "fallback_service"
                }

            else:
                # Generic recovery
                return {
                    "messages": [AIMessage(content="Attempting generic error recovery...")],
                    "recovery_attempted": True,
                    "recovery_method": "generic"
                }

        return recovery_node

    @staticmethod
    def should_retry(error: LangGraphError, attempt_count: int, max_attempts: int = 3) -> bool:
        """Determine if error should trigger a retry."""

        if attempt_count >= max_attempts:
            return False

        # Don't retry validation errors
        if isinstance(error, StateValidationError):
            return False

        # Retry external service errors
        if isinstance(error, (ExternalServiceError, ToolExecutionError)):
            return True

        # Check if error is marked as recoverable
        return error.recoverable
```

### Code Organization and Architecture

**Clean Separation and Dependency Injection**
```python
from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable, Dict, Any, List
from dataclasses import dataclass
import logging

# ✅ CORRECT: Interface-based design with protocols
@runtime_checkable
class ResearchService(Protocol):
    """Protocol for research services."""

    async def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Perform research search."""
        ...

    def get_service_name(self) -> str:
        """Get service name."""
        ...

@runtime_checkable
class AnalysisService(Protocol):
    """Protocol for analysis services."""

    async def analyze(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform data analysis."""
        ...

    def get_capabilities(self) -> List[str]:
        """Get analysis capabilities."""
        ...

# Concrete implementations
class WebResearchService:
    """Web-based research service implementation."""

    def __init__(self, api_key: str, rate_limit: int = 100):
        self.api_key = api_key
        self.rate_limit = rate_limit
        self.logger = logging.getLogger(self.__class__.__name__)

    async def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Perform web search."""
        self.logger.info(f"Searching web for: {query}")

        # Implementation would call actual web API
        return [
            {"title": f"Result for {query}", "url": "https://example.com"}
        ]

    def get_service_name(self) -> str:
        return "WebResearchService"

class DatabaseResearchService:
    """Database-based research service."""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.logger = logging.getLogger(self.__class__.__name__)

    async def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search internal database."""
        self.logger.info(f"Searching database for: {query}")

        # Implementation would query database
        return [
            {"title": f"DB Result for {query}", "source": "internal_db"}
        ]

    def get_service_name(self) -> str:
        return "DatabaseResearchService"

# Dependency injection container
@dataclass
class ServiceContainer:
    """Service container for dependency injection."""

    research_service: ResearchService
    analysis_service: AnalysisService
    logger: logging.Logger

    @classmethod
    def create_default(cls) -> 'ServiceContainer':
        """Create container with default services."""

        return cls(
            research_service=WebResearchService(api_key="default_key"),
            analysis_service=StatisticalAnalysisService(),
            logger=logging.getLogger("default")
        )

    @classmethod
    def create_for_testing(cls) -> 'ServiceContainer':
        """Create container with test services."""

        return cls(
            research_service=MockResearchService(),
            analysis_service=MockAnalysisService(),
            logger=logging.getLogger("test")
        )

# Clean node factory with dependency injection
class NodeFactory:
    """Factory for creating nodes with injected dependencies."""

    def __init__(self, container: ServiceContainer):
        self.container = container

    def create_research_node(self) -> Callable:
        """Create research node with injected services."""

        @handle_errors(ErrorHandlingLevel.GRACEFUL)
        async def research_node(state: Dict[str, Any]) -> Dict[str, Any]:
            """Research node with clean dependencies."""

            query = state.get("query", "")
            max_results = state.get("max_results", 10)

            # Use injected service
            results = await self.container.research_service.search(query, max_results)

            self.container.logger.info(
                f"Research completed using {self.container.research_service.get_service_name()}"
            )

            return {
                "messages": [AIMessage(content=f"Found {len(results)} results")],
                "research_results": results,
                "service_used": self.container.research_service.get_service_name()
            }

        return research_node

    def create_analysis_node(self) -> Callable:
        """Create analysis node with injected services."""

        @handle_errors(ErrorHandlingLevel.GRACEFUL)
        async def analysis_node(state: Dict[str, Any]) -> Dict[str, Any]:
            """Analysis node with clean dependencies."""

            research_results = state.get("research_results", [])

            if not research_results:
                return {
                    "messages": [AIMessage(content="No data to analyze")],
                    "analysis_summary": "No data available"
                }

            # Use injected service
            analysis = await self.container.analysis_service.analyze(research_results)

            return {
                "messages": [AIMessage(content="Analysis completed")],
                "analysis_results": analysis,
                "analysis_capabilities": self.container.analysis_service.get_capabilities()
            }

        return analysis_node

# Clean workflow assembly
class WorkflowAssembler:
    """Assembles complete workflows with clean architecture."""

    def __init__(self, node_factory: NodeFactory):
        self.node_factory = node_factory
        self.logger = logging.getLogger(self.__class__.__name__)

    def create_research_workflow(self, checkpointer=None) -> StateGraph:
        """Create research workflow with clean architecture."""

        # Create nodes with dependency injection
        research_node = self.node_factory.create_research_node()
        analysis_node = self.node_factory.create_analysis_node()

        # Build workflow
        workflow = StateGraph(ResearchState)

        # Add nodes
        workflow.add_node("research", research_node)
        workflow.add_node("analysis", analysis_node)
        workflow.add_node("synthesis", self.create_synthesis_node())

        # Define flow
        workflow.add_edge(START, "research")
        workflow.add_edge("research", "analysis")
        workflow.add_edge("analysis", "synthesis")
        workflow.add_edge("synthesis", END)

        # Compile and return
        compiled = workflow.compile(checkpointer=checkpointer)

        self.logger.info("Research workflow created successfully")
        return compiled

    def create_synthesis_node(self) -> Callable:
        """Create synthesis node."""

        @handle_errors(ErrorHandlingLevel.GRACEFUL)
        async def synthesis_node(state: Dict[str, Any]) -> Dict[str, Any]:
            """Synthesize research and analysis results."""

            research_results = state.get("research_results", [])
            analysis_results = state.get("analysis_results", {})

            # Perform synthesis
            summary = f"Synthesized {len(research_results)} research results with analysis"

            return {
                "messages": [AIMessage(content=summary)],
                "final_summary": summary,
                "synthesis_complete": True
            }

        return synthesis_node

# Usage with clean architecture
def create_production_workflow():
    """Create production workflow with proper architecture."""

    # Create service container
    container = ServiceContainer.create_default()

    # Create node factory
    node_factory = NodeFactory(container)

    # Create workflow assembler
    assembler = WorkflowAssembler(node_factory)

    # Create checkpointer
    checkpointer = SqliteSaver.from_conn_string("production.db")

    # Assemble workflow
    return assembler.create_research_workflow(checkpointer)
```

### Documentation Standards

**Comprehensive Documentation Patterns**
```python
from typing import Dict, Any, List, Optional, Union, TypeVar
from langchain_core.messages import BaseMessage
import json

class DocumentedWorkflow:
    """
    Research workflow with comprehensive documentation standards.

    This workflow orchestrates a multi-stage research process including:
    1. Initial query processing and validation
    2. Multi-source research execution
    3. Data analysis and insight extraction
    4. Result synthesis and presentation

    Architecture:
        - Uses clean dependency injection for services
        - Implements comprehensive error handling
        - Provides full type safety with TypedDict state
        - Supports checkpointing for long-running operations

    State Schema:
        ResearchState: Core state with messages, query, results, and metadata

    Key Nodes:
        - research_node: Executes research queries across multiple services
        - analysis_node: Performs statistical and semantic analysis
        - synthesis_node: Creates final summary and recommendations

    Error Handling:
        - Custom exception hierarchy for domain-specific errors
        - Graceful degradation with fallback responses
        - Comprehensive logging and monitoring integration

    Performance Considerations:
        - Async execution for I/O bound operations
        - Batched processing for large datasets
        - Intelligent caching for repeated queries

    Security:
        - Input validation and sanitization
        - API key management through environment variables
        - Safe execution of user-provided queries

    Examples:
        Basic usage:
        ```python
        workflow = create_research_workflow()
        config = {"configurable": {"thread_id": "research_001"}}

        result = await workflow.ainvoke({
            "messages": [HumanMessage(content="Research AI trends")],
            "query": "artificial intelligence trends 2024",
            "current_stage": "research"
        }, config)
        ```

        With custom services:
        ```python
        container = ServiceContainer(
            research_service=CustomResearchService(),
            analysis_service=CustomAnalysisService(),
            logger=custom_logger
        )

        workflow = WorkflowAssembler(NodeFactory(container)).create_research_workflow()
        ```

    See Also:
        - ResearchState: State schema documentation
        - NodeFactory: Dependency injection patterns
        - ServiceContainer: Service management

    Version: 2.0.0
    Author: AI Research Team
    Last Updated: 2024-12-20
    """

    def __init__(self, container: ServiceContainer):
        """
        Initialize documented workflow.

        Args:
            container: Dependency injection container with required services
                      Must include ResearchService and AnalysisService implementations

        Raises:
            ValueError: If container is missing required services
            TypeError: If services don't implement required protocols

        Example:
            ```python
            container = ServiceContainer.create_default()
            workflow = DocumentedWorkflow(container)
            ```
        """
        self.container = container
        self.logger = container.logger
        self._validate_container()

    def _validate_container(self) -> None:
        """
        Validate service container has required services.

        Raises:
            ValueError: If required services are missing
            TypeError: If services don't implement required protocols
        """
        if not isinstance(self.container.research_service, ResearchService):
            raise TypeError("research_service must implement ResearchService protocol")

        if not isinstance(self.container.analysis_service, AnalysisService):
            raise TypeError("analysis_service must implement AnalysisService protocol")

def research_node(state: ResearchState) -> Dict[str, Any]:
    """
    Execute research query across configured services.

    This node performs the core research operation by:
    1. Validating the input query for safety and completeness
    2. Executing search across all configured research services
    3. Aggregating and deduplicating results from multiple sources
    4. Applying quality filters and relevance scoring
    5. Returning structured results for downstream processing

    State Requirements:
        - query (str): Research query string, non-empty, max 500 characters
        - current_stage (str): Must be "research" to execute
        - max_results (int, optional): Maximum results to return, default 10

    State Updates:
        - research_results: List of research results with metadata
        - research_status: Completion status ("completed", "partial", "failed")
        - current_stage: Updated to "analysis" on success
        - service_metadata: Information about services used

    Error Handling:
        - StateValidationError: Invalid or missing required state fields
        - ToolExecutionError: Research service failures with fallback info
        - ExternalServiceError: External API failures with retry suggestions

    Performance Notes:
        - Executes research services in parallel for faster response
        - Implements intelligent caching for repeated queries
        - Uses batched processing for large result sets

    Security Considerations:
        - Validates query for injection attacks and suspicious patterns
        - Sanitizes all user inputs before processing
        - Logs all research queries for audit purposes

    Args:
        state: Current workflow state conforming to ResearchState schema

    Returns:
        Dict containing updated state fields:
        - messages: Updated conversation with research status
        - research_results: List of research findings with metadata
        - research_status: Status indicator for downstream nodes
        - current_stage: Next workflow stage

    Raises:
        StateValidationError: If required state fields are invalid
        ToolExecutionError: If research execution fails

    Examples:
        Successful execution:
        ```python
        state = {
            "messages": [HumanMessage(content="Research request")],
            "query": "machine learning applications",
            "current_stage": "research"
        }

        result = research_node(state)
        # Returns: {
        #     "messages": [...],
        #     "research_results": [{"title": "...", "url": "..."}],
        #     "research_status": "completed",
        #     "current_stage": "analysis"
        # }
        ```

        Error handling:
        ```python
        invalid_state = {"current_stage": "research"}  # Missing query

        try:
            result = research_node(invalid_state)
        except StateValidationError as e:
            print(f"Validation failed: {e.message}")
        ```

    See Also:
        - analysis_node: Next node in the workflow
        - ResearchService: Service protocol for research implementations
        - ToolExecutionError: Error handling for tool failures

    Version: 2.1.0
    Last Updated: 2024-12-20
    """
    # Implementation would go here
    pass

# Graph documentation generator
class GraphDocumentationGenerator:
    """Generate comprehensive documentation for LangGraph workflows."""

    @staticmethod
    def document_graph_structure(workflow: StateGraph) -> str:
        """
        Generate markdown documentation for graph structure.

        Args:
            workflow: Compiled LangGraph workflow

        Returns:
            Markdown documentation string
        """

        doc_lines = [
            "# Workflow Documentation\n",
            "## Graph Structure\n",
            "```mermaid",
            "graph TD"
        ]

        # This would analyze the actual graph structure
        # For illustration purposes only
        doc_lines.extend([
            "    START --> research",
            "    research --> analysis",
            "    analysis --> synthesis",
            "    synthesis --> END",
            "```\n",
            "## Node Descriptions\n"
        ])

        # Add node documentation
        doc_lines.extend([
            "### research_node",
            "Executes multi-source research queries with validation and error handling.\n",
            "### analysis_node",
            "Performs statistical and semantic analysis of research results.\n",
            "### synthesis_node",
            "Creates final summary and actionable recommendations.\n"
        ])

        return "\n".join(doc_lines)

    @staticmethod
    def generate_api_docs(workflow_class: type) -> Dict[str, Any]:
        """Generate API documentation in JSON format."""

        import inspect

        methods = []
        for name, method in inspect.getmembers(workflow_class, inspect.ismethod):
            if not name.startswith('_'):
                doc = inspect.getdoc(method) or "No documentation available"
                sig = str(inspect.signature(method))

                methods.append({
                    "name": name,
                    "signature": sig,
                    "documentation": doc,
                    "parameters": list(inspect.signature(method).parameters.keys())
                })

        return {
            "class_name": workflow_class.__name__,
            "documentation": inspect.getdoc(workflow_class),
            "methods": methods,
            "generated_at": datetime.now().isoformat()
        }
```

### Security Best Practices

**Safe Execution and API Key Management**
```python
import os
import re
import hashlib
import secrets
from typing import Dict, Any, Optional, List, Set
from cryptography.fernet import Fernet
from langchain_core.messages import BaseMessage
import logging

class SecurityManager:
    """Comprehensive security management for LangGraph applications."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._load_security_config()
        self._initialize_encryption()

    def _load_security_config(self):
        """Load security configuration from environment."""
        self.max_query_length = int(os.getenv("MAX_QUERY_LENGTH", "1000"))
        self.max_state_size_mb = float(os.getenv("MAX_STATE_SIZE_MB", "10.0"))
        self.allowed_domains = set(os.getenv("ALLOWED_DOMAINS", "").split(","))
        self.blocked_patterns = [
            r'<script.*?>.*?</script>',  # XSS
            r'javascript:',              # JavaScript injection
            r'data:.*base64',           # Data URLs
            r'\\x[0-9a-fA-F]{2}',       # Hex encoding
            r'eval\s*\(',               # Code evaluation
            r'exec\s*\(',               # Code execution
        ]

    def _initialize_encryption(self):
        """Initialize encryption for sensitive data."""
        encryption_key = os.getenv("ENCRYPTION_KEY")
        if not encryption_key:
            # Generate a new key if none exists (development only)
            encryption_key = Fernet.generate_key().decode()
            self.logger.warning("Generated new encryption key - store this securely!")

        self.cipher_suite = Fernet(encryption_key.encode())

    def validate_input(self, user_input: str, input_type: str = "query") -> Dict[str, Any]:
        """
        Comprehensive input validation and sanitization.

        Args:
            user_input: Raw user input to validate
            input_type: Type of input (query, message, etc.)

        Returns:
            Validation result with cleaned input or error details
        """

        validation_result = {
            "valid": True,
            "cleaned_input": user_input,
            "warnings": [],
            "blocked_patterns": []
        }

        # Length validation
        if len(user_input) > self.max_query_length:
            validation_result["valid"] = False
            validation_result["error"] = f"Input too long: {len(user_input)} > {self.max_query_length}"
            return validation_result

        # Empty input check
        if not user_input.strip():
            validation_result["valid"] = False
            validation_result["error"] = "Input cannot be empty"
            return validation_result

        # Pattern matching for suspicious content
        for pattern in self.blocked_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                validation_result["blocked_patterns"].append(pattern)
                validation_result["valid"] = False

        if validation_result["blocked_patterns"]:
            validation_result["error"] = f"Input contains blocked patterns: {validation_result['blocked_patterns']}"
            return validation_result

        # SQL injection detection (basic)
        sql_patterns = [
            r"union\s+select",
            r"drop\s+table",
            r"delete\s+from",
            r"insert\s+into",
            r"update\s+.*set",
            r"or\s+1\s*=\s*1",
            r"and\s+1\s*=\s*1"
        ]

        for pattern in sql_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                validation_result["warnings"].append(f"Potential SQL injection pattern: {pattern}")

        # URL validation if input contains URLs
        urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', user_input)
        for url in urls:
            if not self._is_url_safe(url):
                validation_result["valid"] = False
                validation_result["error"] = f"Unsafe URL detected: {url}"
                return validation_result

        # Basic HTML sanitization
        validation_result["cleaned_input"] = self._sanitize_html(user_input)

        return validation_result

    def _is_url_safe(self, url: str) -> bool:
        """Check if URL is from allowed domains."""

        if not self.allowed_domains or "*" in self.allowed_domains:
            return True

        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Check against allowed domains
            for allowed in self.allowed_domains:
                if allowed.lower() in domain:
                    return True

            return False

        except Exception:
            return False

    def _sanitize_html(self, text: str) -> str:
        """Basic HTML sanitization."""

        # Remove script tags
        text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)

        # Remove potentially dangerous attributes
        text = re.sub(r'\son\w+\s*=', ' ', text, flags=re.IGNORECASE)

        # Remove javascript: URLs
        text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)

        return text

    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data like API keys."""
        return self.cipher_suite.encrypt(data.encode()).decode()

    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        return self.cipher_suite.decrypt(encrypted_data.encode()).decode()

class APIKeyManager:
    """Secure API key management."""

    def __init__(self, security_manager: SecurityManager):
        self.security_manager = security_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        self._api_keys: Dict[str, str] = {}
        self._load_api_keys()

    def _load_api_keys(self):
        """Load API keys from secure environment variables."""

        api_key_patterns = [
            ("OPENAI_API_KEY", "openai"),
            ("ANTHROPIC_API_KEY", "anthropic"),
            ("LANGSMITH_API_KEY", "langsmith"),
            ("CUSTOM_RESEARCH_API_KEY", "research_service")
        ]

        for env_var, service_name in api_key_patterns:
            api_key = os.getenv(env_var)
            if api_key:
                # Validate key format
                if self._validate_api_key_format(api_key, service_name):
                    self._api_keys[service_name] = api_key
                    self.logger.info(f"Loaded API key for {service_name}")
                else:
                    self.logger.warning(f"Invalid API key format for {service_name}")
            else:
                self.logger.info(f"No API key found for {service_name}")

    def _validate_api_key_format(self, api_key: str, service: str) -> bool:
        """Validate API key format for different services."""

        patterns = {
            "openai": r"^sk-[A-Za-z0-9]{48}$",
            "anthropic": r"^sk-ant-[A-Za-z0-9\-_]{90,}$",
            "langsmith": r"^lsv2_pt_[A-Za-z0-9\-_]{32,}$"
        }

        if service in patterns:
            return bool(re.match(patterns[service], api_key))

        # Generic validation for unknown services
        return len(api_key) >= 20 and api_key.isascii()

    def get_api_key(self, service: str) -> Optional[str]:
        """Get API key for service with security logging."""

        if service not in self._api_keys:
            self.logger.warning(f"API key requested for unknown service: {service}")
            return None

        # Log key access (without exposing the key)
        key_hash = hashlib.sha256(self._api_keys[service].encode()).hexdigest()[:8]
        self.logger.debug(f"API key accessed for {service} (hash: {key_hash})")

        return self._api_keys[service]

    def rotate_api_key(self, service: str, new_key: str):
        """Rotate API key with validation."""

        if not self._validate_api_key_format(new_key, service):
            raise ValueError(f"Invalid API key format for {service}")

        old_key_hash = hashlib.sha256(self._api_keys.get(service, "").encode()).hexdigest()[:8]
        new_key_hash = hashlib.sha256(new_key.encode()).hexdigest()[:8]

        self._api_keys[service] = new_key
        self.logger.info(f"API key rotated for {service} (old: {old_key_hash}, new: {new_key_hash})")

# Secure node execution patterns
def secure_node_execution(security_manager: SecurityManager):
    """Decorator for secure node execution."""

    def decorator(node_func):
        @wraps(node_func)
        async def wrapper(state: Dict[str, Any]) -> Dict[str, Any]:

            # Validate state size
            state_size = len(str(state)) / 1024 / 1024  # MB
            if state_size > security_manager.max_state_size_mb:
                raise SecurityError(f"State too large: {state_size:.2f}MB > {security_manager.max_state_size_mb}MB")

            # Validate any user inputs in state
            if "query" in state:
                validation = security_manager.validate_input(state["query"], "query")
                if not validation["valid"]:
                    raise SecurityError(f"Input validation failed: {validation['error']}")

                # Use cleaned input
                state = {**state, "query": validation["cleaned_input"]}

            # Execute node with security context
            try:
                result = await node_func(state)

                # Validate output
                if isinstance(result, dict) and "messages" in result:
                    # Sanitize any message content
                    sanitized_messages = []
                    for msg in result["messages"]:
                        if hasattr(msg, "content"):
                            sanitized_content = security_manager._sanitize_html(msg.content)
                            msg.content = sanitized_content
                        sanitized_messages.append(msg)

                    result["messages"] = sanitized_messages

                return result

            except Exception as e:
                security_manager.logger.error(f"Security error in node {node_func.__name__}: {e}")
                raise

        return wrapper
    return decorator

# Usage with secure execution
security_manager = SecurityManager()
api_key_manager = APIKeyManager(security_manager)

@secure_node_execution(security_manager)
async def secure_research_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Research node with comprehensive security."""

    query = state["query"]  # Already validated by decorator

    # Get API key securely
    api_key = api_key_manager.get_api_key("research_service")
    if not api_key:
        raise SecurityError("Research service API key not available")

    # Perform secure research
    results = await secure_research_api(query, api_key)

    return {
        "messages": [AIMessage(content=f"Secure research completed: {len(results)} results")],
        "research_results": results,
        "security_validated": True
    }
```

**Documentation References:**
- Type Hints: https://docs.python.org/3/library/typing.html
- Error Handling: https://python.langchain.com/docs/guides/development/debugging
- Security: https://python.langchain.com/docs/security
- Code Organization: https://python.langchain.com/docs/contributing/code_style
- Documentation: https://python.langchain.com/docs/contributing/documentation
- LangGraph Types: https://langchain-ai.github.io/langgraph/concepts/low_level/#schema

## 7. Common Pitfalls

### Critical Anti-Patterns to Avoid

**State Overwrite Mistakes**
```python
from typing import TypedDict, List, Dict, Any, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

# ❌ CRITICAL ERROR: Using regular types without reducers
class BrokenState(TypedDict):
    """BAD: No reducers - will overwrite messages and lose data."""

    messages: List[BaseMessage]  # Will overwrite previous messages!
    results: List[Dict[str, Any]]  # Will lose previous results!
    data: Dict[str, Any]  # Will lose previous data!

def broken_node(state: BrokenState) -> Dict[str, Any]:
    """BAD: This will overwrite all previous messages."""

    return {
        "messages": [AIMessage(content="New message")],  # OVERWRITES all previous!
        "results": [{"new": "result"}]  # OVERWRITES all previous!
    }

# ✅ CORRECT: Using proper reducers to accumulate data
class CorrectState(TypedDict):
    """GOOD: Uses reducers to accumulate data properly."""

    messages: Annotated[Sequence[BaseMessage], add_messages]  # Accumulates messages
    results: Annotated[List[Dict[str, Any]], add_list]  # Accumulates results
    current_value: str  # Single values can overwrite (by design)

def add_list(current: List[Any], new: List[Any]) -> List[Any]:
    """Custom reducer to accumulate list items."""
    return current + new

def correct_node(state: CorrectState) -> Dict[str, Any]:
    """GOOD: This will append to existing messages and results."""

    return {
        "messages": [AIMessage(content="New message")],  # APPENDS to existing
        "results": [{"new": "result"}]  # APPENDS to existing
        # current_value: can be omitted to keep existing, or set to overwrite
    }

# Common state overwrite debugging
def debug_state_changes(before: Dict, after: Dict, node_name: str):
    """Debug helper to identify state overwrites."""

    print(f"\n=== {node_name} State Changes ===")

    for key in set(before.keys()) | set(after.keys()):
        before_val = before.get(key, "<missing>")
        after_val = after.get(key, "<missing>")

        if key == "messages":
            before_count = len(before_val) if isinstance(before_val, (list, tuple)) else "?"
            after_count = len(after_val) if isinstance(after_val, (list, tuple)) else "?"

            if after_count < before_count:
                print(f"🚨 CRITICAL: {key} count decreased! {before_count} -> {after_count}")
            elif after_count == before_count:
                print(f"⚠️  WARNING: {key} count unchanged: {after_count}")
            else:
                print(f"✅ {key} count increased: {before_count} -> {after_count}")

        elif before_val != after_val:
            print(f"Changed {key}: {str(before_val)[:50]}... -> {str(after_val)[:50]}...")
```

**Monolithic Agent Anti-Patterns**
```python
# ❌ CRITICAL ERROR: Monolithic agent doing everything
class MonolithicBadAgent:
    """BAD: Single agent trying to handle multiple complex domains."""

    def __init__(self):
        # Too many responsibilities in one agent
        self.research_tools = [web_search, academic_search, database_query]
        self.analysis_tools = [statistical_analysis, text_analysis, trend_analysis]
        self.calendar_tools = [create_event, check_availability, send_invites]
        self.email_tools = [send_email, read_email, organize_inbox]
        self.document_tools = [create_doc, edit_doc, export_pdf]
        self.data_viz_tools = [create_chart, generate_graph, make_dashboard]

        # Overly complex prompt trying to handle everything
        self.prompt = """You are a super-agent that can:
        - Do research across multiple sources
        - Perform complex statistical analysis
        - Manage calendars and scheduling
        - Handle email communications
        - Create and edit documents
        - Generate data visualizations
        - And much more...

        Choose the right tools for any task."""  # Too vague!

        # All tools in one massive list
        all_tools = (self.research_tools + self.analysis_tools +
                    self.calendar_tools + self.email_tools +
                    self.document_tools + self.data_viz_tools)

        # Single agent with too many tools
        self.agent = create_react_agent(
            model=model,
            tools=all_tools,  # 50+ tools! Confusing for the LLM
            prompt=self.prompt
        )

    # Single method handling all types of requests
    def handle_request(self, request: str) -> str:
        """BAD: One method trying to route everything."""

        # Complex routing logic that's hard to maintain
        if "research" in request.lower() or "find" in request.lower():
            # Should be separate agent
            return self._do_research(request)
        elif "calendar" in request.lower() or "schedule" in request.lower():
            # Should be separate agent
            return self._manage_calendar(request)
        elif "email" in request.lower():
            # Should be separate agent
            return self._handle_email(request)
        # ... many more elif statements
        else:
            return "I can help with research, calendars, email, and more!"

# ✅ CORRECT: Specialized agents with clear boundaries
class SpecializedResearchAgent:
    """GOOD: Single responsibility - only research."""

    def __init__(self):
        # Focused tools for research only
        self.tools = [web_search, academic_search, database_query]

        # Clear, focused prompt
        self.prompt = """You are a research specialist.

        Your expertise:
        - Finding accurate, up-to-date information
        - Evaluating source credibility
        - Synthesizing findings from multiple sources

        Always:
        - Cite your sources
        - Indicate confidence levels
        - Suggest follow-up research if needed"""

        self.agent = create_react_agent(
            model=claude_model,  # Claude good for research
            tools=self.tools,
            prompt=self.prompt
        )

    def research(self, query: str, max_sources: int = 5) -> Dict[str, Any]:
        """Single, focused method for research."""
        return self.agent.invoke({
            "messages": [HumanMessage(content=query)],
            "max_sources": max_sources
        })

class SpecializedCalendarAgent:
    """GOOD: Single responsibility - only calendar management."""

    def __init__(self):
        # Focused tools for calendar only
        self.tools = [create_event, check_availability, send_invites]

        # Clear, focused prompt
        self.prompt = """You are a calendar management specialist.

        Your expertise:
        - Creating and managing calendar events
        - Checking availability and scheduling
        - Sending appropriate invitations

        Always:
        - Confirm details before creating events
        - Check for conflicts
        - Use appropriate time zones"""

        self.agent = create_react_agent(
            model=gpt4_model,  # GPT-4 good for tool use
            tools=self.tools,
            prompt=self.prompt
        )

# ✅ CORRECT: Supervisor coordinating specialized agents
def create_well_architected_system():
    """GOOD: Supervisor coordinating focused specialists."""

    research_agent = SpecializedResearchAgent().agent
    calendar_agent = SpecializedCalendarAgent().agent
    analysis_agent = SpecializedAnalysisAgent().agent

    supervisor_prompt = """You coordinate specialized agents:

    - research_agent: Information gathering and source validation
    - calendar_agent: Scheduling and calendar management
    - analysis_agent: Data processing and insights

    Routing guidelines:
    1. Identify the primary domain of each request
    2. Route to the most appropriate specialist
    3. Allow agents to collaborate when needed
    4. Provide clear, specific instructions to each agent

    Keep routing simple and clear."""

    return create_supervisor(
        agents=[research_agent, calendar_agent, analysis_agent],
        model=supervisor_model,
        prompt=supervisor_prompt
    )
```

**Poor Error Handling Patterns**
```python
# ❌ CRITICAL ERROR: No error handling or graceful degradation
def broken_research_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """BAD: No error handling - will crash on any failure."""

    query = state["query"]  # Will crash if missing

    # No error handling for external API
    results = external_api_call(query)  # Will crash if API is down

    # No validation of results
    processed_results = process_results(results)  # Will crash if results malformed

    return {
        "messages": [AIMessage(content=f"Found {len(processed_results)} results")],
        "research_results": processed_results
    }

# ❌ BAD: Silent failures that hide problems
def silently_broken_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """BAD: Hides errors instead of handling them properly."""

    try:
        query = state.get("query", "")
        results = external_api_call(query)
        return {"research_results": results}

    except Exception:
        # BAD: Silently returns empty results
        return {"research_results": []}  # User has no idea what went wrong!

# ✅ CORRECT: Comprehensive error handling with graceful degradation
def resilient_research_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """GOOD: Comprehensive error handling with user feedback."""

    # Input validation
    query = state.get("query", "").strip()
    if not query:
        return {
            "messages": [AIMessage(content="I need a search query to help you research.")],
            "research_error": "missing_query",
            "suggested_action": "Please provide a search query"
        }

    # Primary attempt with error handling
    try:
        results = external_api_call(query)

        if not results:
            return {
                "messages": [AIMessage(content=f"No results found for '{query}'. Try rephrasing your query.")],
                "research_results": [],
                "suggested_action": "try_different_query"
            }

        return {
            "messages": [AIMessage(content=f"Found {len(results)} results for '{query}'")],
            "research_results": results,
            "research_status": "completed"
        }

    except APIRateLimitError as e:
        return {
            "messages": [AIMessage(content="Research service is temporarily busy. Please try again in a moment.")],
            "research_error": "rate_limited",
            "retry_after": e.retry_after,
            "suggested_action": "retry_later"
        }

    except APIServiceError as e:
        # Try fallback source
        try:
            fallback_results = fallback_research_service(query)
            return {
                "messages": [AIMessage(content=f"Primary research service unavailable. Found {len(fallback_results)} results using backup source.")],
                "research_results": fallback_results,
                "research_status": "completed_with_fallback"
            }

        except Exception:
            return {
                "messages": [AIMessage(content="Research services are temporarily unavailable. Please try again later.")],
                "research_error": "all_services_down",
                "suggested_action": "try_again_later"
            }

    except Exception as e:
        logger.error(f"Unexpected error in research: {e}")
        return {
            "messages": [AIMessage(content=f"Encountered an unexpected issue while researching '{query}'. Please try again.")],
            "research_error": "unexpected_error",
            "error_details": str(e),
            "suggested_action": "retry_or_contact_support"
        }
```

### LangGraph-Specific Pitfalls

**Incorrect Interrupt Usage**
```python
# ❌ WRONG: Misusing interrupts and human-in-the-loop
def broken_interrupt_workflow():
    """BAD: Incorrect interrupt usage patterns."""

    workflow = StateGraph(State)

    # BAD: Interrupting at wrong places
    workflow.add_node("automatic_task", automatic_node)
    workflow.add_node("simple_processing", processing_node)

    # BAD: Interrupting every single node
    compiled = workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["automatic_task", "simple_processing"]  # Unnecessary interrupts!
    )

    return compiled

def broken_human_input_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """BAD: Blocking node that waits forever."""

    # BAD: Infinite blocking wait
    while True:
        user_input = input("Please provide input: ")  # Will hang in production!
        if user_input:
            break

    return {"user_input": user_input}

# ✅ CORRECT: Strategic interrupt usage
def correct_interrupt_workflow():
    """GOOD: Interrupts only where human judgment is critical."""

    workflow = StateGraph(State)

    # Regular automated nodes
    workflow.add_node("research", research_node)
    workflow.add_node("analysis", analysis_node)

    # Critical decision points that benefit from human input
    workflow.add_node("final_review", review_node)
    workflow.add_node("approval_required", approval_node)

    # Only interrupt before critical human decisions
    compiled = workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["final_review", "approval_required"]  # Strategic interrupts
    )

    return compiled

def correct_human_input_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """GOOD: Non-blocking human input collection."""

    # Check if we already have human input
    if "human_feedback" in state:
        feedback = state["human_feedback"]

        return {
            "messages": [HumanMessage(content=feedback)],
            "review_complete": True,
            "feedback_processed": True
        }

    # Set up request for human input (non-blocking)
    return {
        "messages": [AIMessage(content="Waiting for your review and feedback...")],
        "awaiting_human_input": True,
        "input_request": {
            "type": "review_feedback",
            "prompt": "Please review the analysis and provide feedback",
            "options": ["approve", "request_changes", "reject"]
        }
    }
```

**Wrong State Update Patterns**
```python
# ❌ WRONG: State mutation and incorrect updates
def broken_state_updates():
    """BAD: Multiple state update anti-patterns."""

    # BAD: Mutating state directly
    def bad_node1(state: Dict[str, Any]) -> Dict[str, Any]:
        """BAD: Mutating input state."""
        state["messages"].append(AIMessage(content="New message"))  # Mutates input!
        state["counter"] += 1  # Mutates input!
        return state  # Returns mutated input

    # BAD: Returning non-dict values
    def bad_node2(state: Dict[str, Any]) -> str:  # Should return Dict!
        return "This is wrong"  # LangGraph expects Dict

    # BAD: Inconsistent state updates
    def bad_node3(state: Dict[str, Any]) -> Dict[str, Any]:
        if some_condition():
            return {"messages": [AIMessage(content="A")], "status": "done"}
        else:
            return {"different_field": "value"}  # Inconsistent structure!

    # BAD: Overwriting critical state
    def bad_node4(state: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "messages": [AIMessage(content="New message")],  # Overwrites all messages!
            # Missing other important state fields
        }

# ✅ CORRECT: Proper state update patterns
def correct_state_updates():
    """GOOD: Proper state update patterns."""

    # GOOD: Immutable state updates
    def good_node1(state: Dict[str, Any]) -> Dict[str, Any]:
        """GOOD: Returns new state without mutating input."""

        # Don't mutate input state
        current_messages = list(state.get("messages", []))  # Copy
        current_counter = state.get("counter", 0)

        # Return new state updates
        return {
            "messages": [AIMessage(content="New message")],  # Reducer will append
            "counter": current_counter + 1  # New value
        }

    # GOOD: Always return Dict
    def good_node2(state: Dict[str, Any]) -> Dict[str, Any]:
        """GOOD: Always returns Dict with state updates."""

        result_text = process_data(state)

        return {
            "messages": [AIMessage(content=result_text)],
            "processing_complete": True
        }

    # GOOD: Consistent state structure
    def good_node3(state: Dict[str, Any]) -> Dict[str, Any]:
        """GOOD: Consistent state updates regardless of conditions."""

        if some_condition():
            message = "Condition A result"
            status = "completed_a"
        else:
            message = "Condition B result"
            status = "completed_b"

        # Always return same structure
        return {
            "messages": [AIMessage(content=message)],
            "status": status,
            "node_completed": True
        }

    # GOOD: Preserve important state
    def good_node4(state: Dict[str, Any]) -> Dict[str, Any]:
        """GOOD: Only update what needs to change."""

        return {
            "messages": [AIMessage(content="New message")],  # Adds to existing
            "last_update": datetime.now().isoformat(),  # Updates timestamp
            # Other state fields preserved automatically
        }
```

**Type Assumption Errors**
```python
# ❌ WRONG: Type assumption mistakes
def broken_type_assumptions():
    """BAD: Making incorrect assumptions about types."""

    def bad_node1(state: Dict[str, Any]) -> Dict[str, Any]:
        """BAD: Assuming types without validation."""

        # BAD: Assumes messages is always a list
        message_count = len(state["messages"])  # Crashes if missing or wrong type

        # BAD: Assumes specific message types
        last_message = state["messages"][-1]
        user_query = last_message.content  # Crashes if no content attribute

        return {"count": message_count, "query": user_query}

    def bad_node2(state: Dict[str, Any]) -> Dict[str, Any]:
        """BAD: Wrong assumptions about optional fields."""

        # BAD: Assumes field is always present
        results = state["research_results"]  # Crashes if missing

        # BAD: Assumes specific structure
        first_result = results[0]  # Crashes if empty
        title = first_result["title"]  # Crashes if no title

        return {"summary": f"Found: {title}"}

# ✅ CORRECT: Proper type checking and validation
def correct_type_handling():
    """GOOD: Proper type validation and safe access."""

    def good_node1(state: Dict[str, Any]) -> Dict[str, Any]:
        """GOOD: Safe type handling with validation."""

        # Safe access with defaults
        messages = state.get("messages", [])

        # Validate type
        if not isinstance(messages, (list, tuple)):
            return {
                "messages": [AIMessage(content="Error: Invalid message format")],
                "error": "invalid_message_type"
            }

        message_count = len(messages)

        # Safe access to last message
        if messages and hasattr(messages[-1], 'content'):
            user_query = messages[-1].content
        else:
            user_query = "No query found"

        return {
            "messages": [AIMessage(content=f"Processed {message_count} messages")],
            "message_count": message_count,
            "last_query": user_query
        }

    def good_node2(state: Dict[str, Any]) -> Dict[str, Any]:
        """GOOD: Safe access to optional nested data."""

        results = state.get("research_results", [])

        if not results or not isinstance(results, list):
            return {
                "messages": [AIMessage(content="No research results to summarize")],
                "summary": "No data available"
            }

        # Safe access to first result
        if results:
            first_result = results[0]
            if isinstance(first_result, dict):
                title = first_result.get("title", "Untitled result")
            else:
                title = "Invalid result format"
        else:
            title = "No results"

        return {
            "messages": [AIMessage(content=f"Summary: {title}")],
            "result_count": len(results),
            "summary": f"Found: {title}"
        }
```

### Codebase-Specific Issues

**Outdated State Patterns (Based on Current src/state.py)**
```python
# ❌ CURRENT ISSUE: Mixed state patterns in your codebase
# From src/state.py - this shows the inconsistency:

# You have both simple and complex state classes:
class WorkflowState(BaseModel):  # Uses Pydantic
    messages: List[BaseMessage] = Field(default_factory=list)  # No reducer!
    # ... other fields

class GlobalWorkflowState(BaseModel):  # Also Pydantic
    messages: Annotated[Sequence[BaseMessage], add_messages] = Field(default_factory=list)  # Has reducer
    # ... other fields

# ❌ PROBLEMS with current approach:
def problematic_current_patterns():
    """Issues in current codebase that need fixing."""

    # 1. Inconsistent state types
    # Some use BaseModel (Pydantic), others use TypedDict
    # This creates confusion and performance inconsistencies

    # 2. Mixed reducer usage
    # WorkflowState has no reducers (messages will be overwritten!)
    # GlobalWorkflowState has reducers (messages will accumulate)

    # 3. Complex inheritance
    # CalendarAgentState = GlobalWorkflowState  # Alias creates confusion

    # 4. Mixing concerns
    # State classes contain business logic and validation
    # Should be separate from state schema

# ✅ RECOMMENDED: Consistent, modern state patterns
class ModernUnifiedState(TypedDict):
    """GOOD: Unified, consistent state schema."""

    # Core messaging with reducer
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # Essential workflow tracking
    current_agent: Literal["supervisor", "calendar", "email", "research"]
    workflow_stage: Literal["routing", "processing", "completing"]

    # Agent-specific data (normalized)
    active_tasks: Annotated[List[Dict[str, Any]], add_list]
    completed_tasks: Annotated[List[Dict[str, Any]], add_list]

    # Simple values (no reducers needed)
    error_count: int
    last_updated: str

# Separate business logic from state
class WorkflowManager:
    """GOOD: Business logic separated from state schema."""

    @staticmethod
    def create_task(agent_name: str, description: str) -> Dict[str, Any]:
        """Create a task object."""
        return {
            "id": str(uuid.uuid4()),
            "agent": agent_name,
            "description": description,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }

    @staticmethod
    def update_workflow_stage(current_stage: str, agent: str) -> str:
        """Determine next workflow stage."""

        stage_transitions = {
            ("routing", "supervisor"): "processing",
            ("processing", "calendar"): "completing",
            ("processing", "email"): "completing",
            ("processing", "research"): "completing",
            ("completing", "supervisor"): "routing"  # For follow-up tasks
        }

        return stage_transitions.get((current_stage, agent), current_stage)
```

**Mixed Paradigm Issues**
```python
# ❌ CURRENT ISSUE: Your agents use different paradigms

# calendar_agent uses complex custom implementation:
class CalendarAgentWithMCP:  # Complex custom class
    def __init__(self, model):
        self.model = model
        # Complex MCP integration
        # Custom error handling
        # Lots of custom logic

    async def get_agent(self):
        # Returns complex custom agent
        pass

# While other agents use simple create_react_agent:
def create_simple_agent():
    return create_react_agent(model, tools, prompt)  # Simple, modern

# ❌ PROBLEMS:
def mixed_paradigm_issues():
    """Issues with mixing different agent paradigms."""

    # 1. Inconsistent interfaces
    # calendar_agent.get_agent() vs direct agent usage

    # 2. Different error handling approaches
    # Custom try/catch vs built-in LangGraph error handling

    # 3. Varying complexity levels
    # Some agents simple, others overly complex

    # 4. Maintenance burden
    # Different patterns require different debugging approaches

# ✅ RECOMMENDED: Unified modern paradigm
class UnifiedAgentFactory:
    """GOOD: Consistent agent creation patterns."""

    def __init__(self, container: ServiceContainer):
        self.container = container

    def create_calendar_agent(self) -> Any:
        """Modern calendar agent using standard patterns."""

        tools = [
            self._create_calendar_tool(),
            self._create_availability_tool(),
            self._create_scheduling_tool()
        ]

        prompt = """You are a calendar management specialist.

        Your capabilities:
        - Create and manage calendar events
        - Check availability and resolve conflicts
        - Send appropriate invitations and notifications

        Always confirm details before creating events."""

        return create_react_agent(
            model=self.container.gpt4_model,  # Good for tool use
            tools=tools,
            prompt=prompt
        )

    def create_research_agent(self) -> Any:
        """Research agent using same modern pattern."""

        tools = [
            self.container.web_search_tool,
            self.container.academic_search_tool,
            self.container.database_tool
        ]

        prompt = """You are a research specialist.

        Your capabilities:
        - Find accurate, current information
        - Evaluate source credibility
        - Synthesize findings from multiple sources

        Always cite sources and indicate confidence levels."""

        return create_react_agent(
            model=self.container.claude_model,  # Good for research
            tools=tools,
            prompt=prompt
        )

    def create_supervisor_system(self):
        """Unified supervisor using standard patterns."""

        agents = [
            self.create_calendar_agent(),
            self.create_research_agent(),
            # Add other agents with same pattern
        ]

        return create_supervisor(
            agents=agents,
            model=self.container.supervisor_model,
            prompt="""You coordinate specialized agents for user requests.

            Route requests to appropriate specialists:
            - Calendar/scheduling → calendar agent
            - Research/information → research agent

            Provide clear, specific instructions to each agent."""
        )
```

**Poor Separation of Concerns**
```python
# ❌ CURRENT ISSUE: Business logic mixed with graph construction

# Current pattern mixes concerns:
def current_mixed_concerns():
    """Current pattern that mixes multiple responsibilities."""

    # Graph construction mixed with business logic
    def create_graph():  # From your current code
        # Validation logic
        validate_environment()

        # Agent creation
        calendar_agent = await create_calendar_agent()

        # Error handling
        try:
            supervisor_model = ChatOpenAI(...)
        except Exception as e:
            logger.error(f"Failed to create model: {e}")

        # Graph building
        workflow = create_supervisor(agents, model, prompt)

        # Compilation
        return workflow.compile()

# ✅ RECOMMENDED: Clean separation of concerns
class ConfigurationManager:
    """GOOD: Handles configuration and validation."""

    def validate_environment(self) -> bool:
        """Validate environment configuration."""
        # Pure validation logic
        pass

    def load_model_configs(self) -> Dict[str, Any]:
        """Load model configurations."""
        # Pure configuration logic
        pass

class AgentFactory:
    """GOOD: Handles agent creation."""

    def create_calendar_agent(self) -> Any:
        """Create calendar agent."""
        # Pure agent creation logic
        pass

class WorkflowBuilder:
    """GOOD: Handles graph construction."""

    def build_supervisor_workflow(self, agents: List, model: Any) -> Any:
        """Build supervisor workflow."""
        # Pure graph construction logic
        pass

class ApplicationAssembler:
    """GOOD: Coordinates all components."""

    def create_application(self) -> Any:
        """Assemble complete application."""

        # Clean separation of concerns
        config_manager = ConfigurationManager()
        agent_factory = AgentFactory()
        workflow_builder = WorkflowBuilder()

        # Validate environment
        if not config_manager.validate_environment():
            raise EnvironmentError("Invalid configuration")

        # Create agents
        agents = [
            agent_factory.create_calendar_agent(),
            agent_factory.create_research_agent()
        ]

        # Load models
        models = config_manager.load_model_configs()

        # Build workflow
        return workflow_builder.build_supervisor_workflow(agents, models['supervisor'])
```

### Migration Strategy for Your Codebase

**Step-by-Step Modernization Plan**
```python
# Phase 1: Unify State Management
def phase1_state_modernization():
    """Modernize state.py to use consistent patterns."""

    # 1. Replace mixed state classes with unified TypedDict approach
    # 2. Add proper reducers to all state schemas
    # 3. Remove Pydantic BaseModel usage for state (keep for validation)
    # 4. Normalize data structures

    # Before: Multiple inconsistent state classes
    # After: Single, consistent ModernUnifiedState

# Phase 2: Refactor Monolithic Agents
def phase2_agent_decomposition():
    """Break down complex agents into focused specialists."""

    # 1. Analyze calendar_agent complex implementation
    # 2. Extract core calendar operations into focused tools
    # 3. Replace complex custom agent with create_react_agent
    # 4. Repeat for job_search_agent

    # Before: Complex custom agent implementations
    # After: Simple, focused create_react_agent usage

# Phase 3: Standardize Error Handling
def phase3_error_standardization():
    """Implement consistent error handling across all agents."""

    # 1. Add comprehensive error handling decorators
    # 2. Implement graceful fallback patterns
    # 3. Add proper logging and monitoring
    # 4. Create recovery nodes for common failure scenarios

    # Before: Inconsistent error handling
    # After: Comprehensive, consistent error management

# Phase 4: Clean Architecture Implementation
def phase4_architecture_cleanup():
    """Implement clean architecture with proper separation."""

    # 1. Separate configuration from business logic
    # 2. Implement dependency injection patterns
    # 3. Create clear interfaces for all services
    # 4. Add comprehensive testing

    # Before: Mixed concerns and responsibilities
    # After: Clean, testable, maintainable architecture
```

**Documentation References:**
- LangGraph Concepts: https://langchain-ai.github.io/langgraph/concepts/low_level/
- State Management: https://langchain-ai.github.io/langgraph/concepts/low_level/#state
- Agent Creation: https://langchain-ai.github.io/langgraph/how-tos/create-react-agent/
- Error Handling: https://langchain-ai.github.io/langgraph/how-tos/tool-calling-errors/
- Multi-Agent Systems: https://langchain-ai.github.io/langgraph/tutorials/multi_agent/agent_supervisor/
- Testing: https://langchain-ai.github.io/langgraph/how-tos/testing/
- Performance: https://langchain-ai.github.io/langgraph/concepts/persistence/#performance

---

# Conclusion

This comprehensive CLAUDE.md file provides detailed guidance for building high-quality LangGraph applications. Use the MCP documentation server to access up-to-date LangGraph documentation and examples as needed.

For implementation questions or advanced patterns, consult the official LangGraph documentation at https://langchain-ai.github.io/langgraph/
