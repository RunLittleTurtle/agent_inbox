"""
Calendar Agent - Google Workspace Only (Simplified)
Uses create_react_agent prebuilt with Google Calendar API integration.

Following LangGraph 2025 best practices:
- Prebuilt create_react_agent for agent logic
- Google Workspace API via ExecutorFactory
- User-editable prompts from Supabase
- Human-in-the-loop via booking_node with interrupt()
- Simple, maintainable architecture (KISS principle)
"""
import os
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from langchain_core.messages import BaseMessage
from langchain_core.tools import BaseTool
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, MessagesState, START, END

from shared_utils import DEFAULT_LLM_MODEL
from .prompt import get_formatted_prompt_with_context, get_no_tools_prompt
from .executor_factory import ExecutorFactory
from .booking_node import BookingNode

# Configure logging
logger = logging.getLogger(__name__)


class CalendarAgent:
    """
    Simplified Calendar Agent using Google Workspace API only.

    Architecture:
    - READ operations: Google Workspace API via create_react_agent tools
    - WRITE operations: booking_node with human-in-the-loop approval
    - Prompts: User-editable from Supabase config
    - State: MessagesState (simple, standard)
    """

    def __init__(
        self,
        model: Optional[ChatAnthropic] = None,
        user_id: Optional[str] = None
    ):
        """
        Initialize calendar agent with Google Workspace integration.

        Args:
            model: LLM model for agent reasoning
            user_id: Clerk user ID for loading user-specific config
        """
        from .config import LLM_CONFIG, USER_TIMEZONE

        # Setup logging
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

        self.logger.info(f"[CalendarAgent] Created for user_id={user_id}")

    async def initialize(self):
        """
        Initialize Google Workspace executor and tools.
        Must be called before using the agent.
        """
        if self._initialized:
            return

        self.logger.info(f"[CalendarAgent] Initializing Google Workspace integration...")

        try:
            # Create Google Workspace executor and READ tools
            self.executor, self.tools = await ExecutorFactory.create_executor(self.user_id)

            self.logger.info(f"[CalendarAgent] ✅ Loaded {len(self.tools)} Google Workspace READ tools")
            for tool in self.tools:
                self.logger.info(f"[CalendarAgent]    - {tool.name}")

            # Create booking node for WRITE operations
            self.booking_node_instance = BookingNode(
                executor=self.executor,
                model=self.model
            )

            self._initialized = True
            self.logger.info(f"[CalendarAgent] ✅ Initialization complete")

        except Exception as e:
            self.logger.error(f"[CalendarAgent] ❌ Initialization failed: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _get_agent_prompt(self) -> str:
        """
        Get agent system prompt with dynamic context.
        Loads user-edited prompt from Supabase if available.
        """
        # Get current time context
        try:
            timezone_zone = ZoneInfo(self.timezone)
            current_time = datetime.now(timezone_zone)
            tomorrow = current_time + timedelta(days=1)

            current_time_iso = current_time.isoformat()
            today_str = f"{current_time.strftime('%Y-%m-%d')} ({current_time.strftime('%A')})"
            tomorrow_str = f"{tomorrow.strftime('%Y-%m-%d')} ({tomorrow.strftime('%A')})"
        except Exception as e:
            self.logger.error(f"[CalendarAgent] Error getting timezone context: {e}")
            # Fallback to UTC
            current_time = datetime.now(ZoneInfo("UTC"))
            tomorrow = current_time + timedelta(days=1)
            current_time_iso = current_time.isoformat()
            today_str = current_time.strftime('%Y-%m-%d')
            tomorrow_str = tomorrow.strftime('%Y-%m-%d')

        # Try loading user-edited prompt from Supabase
        if self.user_id:
            try:
                from utils.config_utils import get_agent_config_from_supabase
                agent_config = get_agent_config_from_supabase(self.user_id, "calendar_agent")

                # Get user-edited system prompt
                prompt_templates = agent_config.get("prompt_templates", {})
                user_prompt = prompt_templates.get("agent_system_prompt")

                if user_prompt:
                    self.logger.info("[CalendarAgent] ✅ Using user-edited prompt from Supabase")
                    # Format with dynamic context
                    return user_prompt.format(
                        current_time=current_time_iso,
                        timezone_name=self.timezone,
                        today=today_str,
                        tomorrow=tomorrow_str
                    )
                else:
                    self.logger.info("[CalendarAgent] No user-edited prompt found, using default")
            except Exception as e:
                self.logger.warning(f"[CalendarAgent] Could not load user prompt from Supabase: {e}")

        # Fallback to default prompt from prompt.py
        return get_formatted_prompt_with_context(
            timezone_name=self.timezone,
            current_time_iso=current_time_iso,
            today_str=today_str,
            tomorrow_str=tomorrow_str
        )

    async def get_agent(self):
        """
        Get the compiled calendar agent graph.

        Returns:
            Compiled LangGraph agent ready for invocation
        """
        if not self._initialized:
            await self.initialize()

        if self.agent_graph:
            return self.agent_graph

        # Get agent prompt (with user edits if available)
        agent_prompt = self._get_agent_prompt()

        # Create agent based on tool availability
        if not self.tools:
            self.logger.warning("[CalendarAgent] ⚠️  No tools available - creating no-tools agent")
            # Agent with no tools - just explain limitations
            no_tools_prompt = get_no_tools_prompt()
            agent = create_react_agent(
                model=self.model,
                tools=[],
                prompt=no_tools_prompt
            )
        else:
            # Agent with Google READ tools + booking node for WRITEs
            self.logger.info(f"[CalendarAgent] Creating agent with {len(self.tools)} tools")
            agent = create_react_agent(
                model=self.model,
                tools=self.tools,
                prompt=agent_prompt
            )

        # Build graph with booking node for write operations
        workflow = StateGraph(MessagesState)

        # Add calendar agent node (handles READ operations)
        workflow.add_node("calendar_agent", agent)

        # Add booking node (handles WRITE operations with human approval)
        workflow.add_node("booking_approval", self.booking_node_instance.booking_approval_node)

        # Routing logic
        def should_route_to_booking(state: MessagesState) -> str:
            """Route to booking node if agent mentions booking approval needed"""
            messages = state.get("messages", [])
            if not messages:
                return END

            last_message = messages[-1]
            content = getattr(last_message, 'content', '')

            # Check if agent explicitly mentioned booking approval
            booking_keywords = [
                "booking approval",
                "approval workflow",
                "requires approval",
                "requires booking approval"
            ]

            if any(keyword in content.lower() for keyword in booking_keywords):
                self.logger.info("[CalendarAgent] Routing to booking_approval node")
                return "booking_approval"

            return END

        # Define edges
        workflow.add_edge(START, "calendar_agent")
        workflow.add_conditional_edges(
            "calendar_agent",
            should_route_to_booking,
            {
                "booking_approval": "booking_approval",
                END: END
            }
        )
        workflow.add_edge("booking_approval", END)

        # Compile graph
        self.agent_graph = workflow.compile()
        self.logger.info("[CalendarAgent] ✅ Agent graph compiled successfully")

        return self.agent_graph


# ============================================================================
# Factory function for supervisor integration
# ============================================================================

async def create_calendar_agent(
    model: ChatAnthropic,
    user_id: str,
    agent_config: Optional[Dict[str, Any]] = None
) -> Any:
    """
    Factory function to create and initialize calendar agent.
    Used by supervisor's calendar_agent_node wrapper.

    Args:
        model: LLM model configured with user settings
        user_id: Clerk user ID for Google OAuth credential loading
        agent_config: Optional agent configuration from Supabase

    Returns:
        Compiled calendar agent graph ready for invocation
    """
    logger.info(f"[create_calendar_agent] Creating agent for user_id={user_id}")

    # Create agent instance
    calendar_agent = CalendarAgent(model=model, user_id=user_id)

    # Initialize (loads Google credentials and tools)
    await calendar_agent.initialize()

    # Get compiled graph
    agent_graph = await calendar_agent.get_agent()

    logger.info(f"[create_calendar_agent] ✅ Agent ready for user_id={user_id}")
    return agent_graph
