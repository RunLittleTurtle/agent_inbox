"""
Google OAuth Agent Orchestrator - TEMPLATE
Main agent workflow using LangGraph 2025 patterns.

CUSTOMIZATION REQUIRED:
1. Replace {DOMAIN} placeholders with your agent name
2. Update class/function names (GoogleAuthAgent → YourAgent)
3. Customize state management (if using custom state beyond MessagesState)
4. Add conditional routing if you need human-in-the-loop or multi-step workflows

LangGraph 2025 Best Practices:
- Use create_react_agent for simple tool-calling agents
- Only build custom StateGraph when you need conditional routing
- Export compiled graph as 'app' for deployment
- Keep architecture simple (KISS principle)
"""
import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from langchain_core.messages import BaseMessage, SystemMessage
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, MessagesState, START, END

from shared_utils import DEFAULT_LLM_MODEL
from .config import LLM_CONFIG, USER_TIMEZONE, get_current_context
from .prompt import (
    get_formatted_prompt_with_context,
    get_no_tools_prompt
)
from .state import GoogleAuthAgentState
from .executor_factory import ExecutorFactory

# Configure logging
logger = logging.getLogger(__name__)


class GoogleAuthAgent:
    """
    Generic Google OAuth Agent using create_react_agent pattern.

    Architecture:
    - OAuth: Fetch credentials from Supabase (user_secrets table)
    - Tools: Google Workspace API tools via executor
    - Agent: create_react_agent with tools (LangGraph 2025 prebuilt)
    - State: MessagesState (simple) or GoogleAuthAgentState (if custom fields needed)

    Usage:
    ```python
    # Create and initialize agent
    agent = GoogleAuthAgent(user_id="user_123")
    await agent.initialize()

    # Get compiled graph
    graph = await agent.get_agent()

    # Invoke agent
    result = await graph.ainvoke({
        "messages": [HumanMessage(content="List my items")]
    })
    ```
    """

    def __init__(
        self,
        model: Optional[ChatAnthropic] = None,
        user_id: Optional[str] = None
    ):
        """
        Initialize Google OAuth agent.

        Args:
            model: LLM model for agent reasoning (optional)
            user_id: Clerk user ID for loading Google OAuth credentials
        """
        self.logger = logging.getLogger(__name__)
        self.user_id = user_id
        self.timezone = USER_TIMEZONE

        # Use centralized get_llm for cross-provider support
        if model:
            self.model = model
        else:
            from utils.llm_utils import get_llm
            model_name = LLM_CONFIG.get("model", DEFAULT_LLM_MODEL)
            temperature = LLM_CONFIG.get("temperature", 0.1)
            self.model = get_llm(model_name, temperature=temperature)

        # Agent components (initialized async)
        self.executor = None
        self.tools = []
        self.agent_graph = None
        self._initialized = False

        self.logger.info(f"[GoogleAuthAgent] Created for user_id={user_id}")

    async def initialize(self):
        """
        Initialize Google Workspace executor and tools.
        Must be called before using the agent.

        Note:
            Gracefully handles missing Google OAuth credentials by creating
            a no-tools agent that guides users to connect Google account.
        """
        if self._initialized:
            return

        self.logger.info(f"[GoogleAuthAgent] Initializing Google Workspace integration...")

        try:
            # Create Google Workspace executor and tools
            # Returns (None, []) if credentials missing - no exception raised
            self.executor, self.tools = await ExecutorFactory.create_executor(self.user_id)

            if self.executor is None:
                self.logger.warning(
                    f"[GoogleAuthAgent] No Google OAuth credentials found for user {self.user_id}. "
                    "Agent will run in no-tools mode and guide user to connect Google account."
                )
            else:
                self.logger.info(f"[GoogleAuthAgent] Google Workspace executor created successfully")

            self.logger.info(f"[GoogleAuthAgent] Loaded {len(self.tools)} Google Workspace tools")
            for tool in self.tools:
                self.logger.info(f"[GoogleAuthAgent]    - {tool.name}")

            self._initialized = True
            self.logger.info(f"[GoogleAuthAgent] Initialization complete")

        except Exception as e:
            self.logger.error(f"[GoogleAuthAgent] Initialization failed: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _get_agent_prompt(self) -> str:
        """
        Get agent system prompt with dynamic context.
        Loads user-edited prompt from Supabase if available.

        Returns:
            Formatted system prompt with current time/date context
        """
        # Get current time context using centralized function
        context = get_current_context()

        # Try loading user-edited prompt from Supabase
        if self.user_id:
            try:
                from utils.config_utils import get_agent_config_from_supabase
                # TODO: Replace "google_auth_agent" with your agent name
                agent_config = get_agent_config_from_supabase(self.user_id, "google_auth_agent")

                # Get user-edited system prompt
                prompt_templates = agent_config.get("prompt_templates", {})
                user_prompt = prompt_templates.get("agent_system_prompt")

                if user_prompt:
                    self.logger.info("[GoogleAuthAgent] Using user-edited prompt from Supabase")
                    # Format with dynamic context
                    return user_prompt.format(
                        current_time=context['current_time'],
                        timezone_name=context['timezone_name'],
                        today=context['today'],
                        tomorrow=context['tomorrow'],
                        time_str=context['time_str']
                    )
                else:
                    self.logger.info("[GoogleAuthAgent] No user-edited prompt found, using default")
            except Exception as e:
                self.logger.warning(f"[GoogleAuthAgent] Could not load user prompt from Supabase: {e}")

        # Fallback to default prompt from prompt.py
        # TODO: Pass your domain name and service name
        return get_formatted_prompt_with_context(
            timezone_name=context['timezone_name'],
            current_time_iso=context['current_time'],
            today_str=context['today'],
            tomorrow_str=context['tomorrow'],
            time_str=context['time_str'],
            domain="{DOMAIN}",  # TODO: Replace with your domain (e.g., "contacts")
            service_name="{SERVICE_NAME}"  # TODO: Replace with service (e.g., "Contacts")
        )

    async def get_agent(self):
        """
        Get the compiled agent graph.

        LangGraph 2025 Pattern:
        - Simple agents: Use create_react_agent (returns compiled graph directly)
        - Complex agents: Build custom StateGraph with conditional routing

        Returns:
            Compiled LangGraph agent ready for invocation
        """
        if not self._initialized:
            await self.initialize()

        if self.agent_graph:
            return self.agent_graph

        # Get agent prompt (with user edits if available)
        agent_prompt = self._get_agent_prompt()

        # ==========================================================================
        # SIMPLE PATTERN: create_react_agent (recommended for most agents)
        # ==========================================================================
        # This is the LangGraph 2025 recommended approach for tool-calling agents
        # Use this if you DON'T need:
        # - Human-in-the-loop approval workflows
        # - Conditional routing based on agent decisions
        # - Multi-step orchestration with separate nodes

        if not self.tools:
            # No tools available - create agent that explains limitations
            self.logger.warning("[GoogleAuthAgent] No tools available - creating no-tools agent")
            no_tools_prompt = get_no_tools_prompt(domain="{DOMAIN}")  # TODO: Replace {DOMAIN}
            agent = create_react_agent(
                model=self.model,
                tools=[],
                prompt=no_tools_prompt
            )
        else:
            # Tools available - create standard react agent
            self.logger.info(f"[GoogleAuthAgent] Creating agent with {len(self.tools)} tools")
            agent = create_react_agent(
                model=self.model,
                tools=self.tools,
                prompt=agent_prompt
            )

        # create_react_agent returns a compiled graph - ready to use!
        self.agent_graph = agent
        self.logger.info("[GoogleAuthAgent] Agent graph compiled successfully")

        return self.agent_graph

        # ==========================================================================
        # ADVANCED PATTERN: Custom StateGraph (only if you need complex routing)
        # ==========================================================================
        # Uncomment and customize this section if you need:
        # - Human-in-the-loop approval (before sending emails, booking events, etc.)
        # - Conditional routing (route to different nodes based on agent output)
        # - Multi-step workflows (plan → execute → review)
        #
        # Example: Email agent that requires approval before sending
        """
        # Create base agent
        agent = create_react_agent(
            model=self.model,
            tools=self.tools,
            prompt=agent_prompt
        )

        # Build custom graph with approval node
        workflow = StateGraph(GoogleAuthAgentState)  # Use custom state if needed

        # Add nodes
        workflow.add_node("agent", agent)
        workflow.add_node("approval", self._approval_node)  # Implement approval logic

        # Define routing logic
        def should_route_to_approval(state: GoogleAuthAgentState) -> str:
            # Check if agent mentioned needing approval
            messages = state.get("messages", [])
            if not messages:
                return END

            last_message = messages[-1]
            content = str(getattr(last_message, 'content', ''))

            if "requires approval" in content.lower():
                return "approval"
            return END

        # Define edges
        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges(
            "agent",
            should_route_to_approval,
            {
                "approval": "approval",
                END: END
            }
        )
        workflow.add_edge("approval", END)

        # Compile and return
        self.agent_graph = workflow.compile()
        return self.agent_graph
        """


# ==========================================================================
# Factory function for supervisor integration
# ==========================================================================

async def create_google_auth_agent(
    model: ChatAnthropic,
    user_id: str,
    agent_config: Optional[Dict[str, Any]] = None
) -> Any:
    """
    Factory function to create and initialize Google OAuth agent.
    Used by supervisor's agent node wrapper.

    Args:
        model: LLM model configured with user settings
        user_id: Clerk user ID for Google OAuth credential loading
        agent_config: Optional agent configuration from Supabase

    Returns:
        Compiled agent graph ready for invocation
    """
    logger.info(f"[create_google_auth_agent] Creating agent for user_id={user_id}")

    # Create agent instance
    agent = GoogleAuthAgent(model=model, user_id=user_id)

    # Initialize (loads Google credentials and tools)
    await agent.initialize()

    # Get compiled graph
    agent_graph = await agent.get_agent()

    logger.info(f"[create_google_auth_agent] Agent ready for user_id={user_id}")
    return agent_graph


# ==========================================================================
# Export for LangGraph deployment
# ==========================================================================
# TODO: Only uncomment if this agent is standalone (not part of supervisor)
# If this agent is called by a supervisor, export is not needed here

# from langgraph.graph import END
# graph = create_react_agent(
#     model=ChatAnthropic(model="claude-3-5-sonnet-20241022"),
#     tools=[],  # Will be loaded dynamically based on user_id
#     prompt=get_formatted_prompt_with_context(
#         timezone_name="UTC",
#         current_time_iso="",
#         today_str="",
#         tomorrow_str="",
#         domain="{DOMAIN}",
#         service_name="{SERVICE_NAME}"
#     )
# )
# app = graph  # Required for LangGraph deployment
