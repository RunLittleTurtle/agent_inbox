"""
React Agent Orchestrator with MCP Integration
Uses centralized config from config.py
"""

import os
from typing import Dict, Any

from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv

from .tools import get_agent_simple_tools
from .prompt import AGENT_SYSTEM_PROMPT
from .config import LLM_CONFIG, AGENT_NAME, get_current_context

load_dotenv()


class AgentOrchestrator:
    """Simple React Agent with MCP tools"""

    def __init__(self, llm_config: Dict[str, Any] = None):
        self.llm_config = llm_config or LLM_CONFIG

        # Validate API key
        api_key = self.llm_config.get("api_key") or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found")

        self.llm_config = {**self.llm_config, "api_key": api_key}
        self.llm = ChatAnthropic(**self.llm_config)
        self.tools = get_agent_simple_tools()
        self.workflow = self._build_workflow()

    def _build_workflow(self):
        """Build React agent"""
        context = get_current_context()

        enhanced_prompt = f"""{AGENT_SYSTEM_PROMPT}

**CURRENT CONTEXT:**
- Now: {context['current_time']}
- Timezone: {context['timezone_name']}
- Today: {context['today']}
- Current Time: {context['time_str']}

Use available tools efficiently and provide clear feedback."""

        return create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=enhanced_prompt,
            name=f"{AGENT_NAME}_agent"
        )


def create_default_orchestrator():
    """Create orchestrator with default config"""
    orchestrator = AgentOrchestrator(LLM_CONFIG)
    return orchestrator.workflow


# Google Drive agent creation function for supervisor integration
def create_drive_agent():
    """
    REQUIRED function for supervisor integration
    Function name must match pattern: create_drive_agent()
    """
    return create_default_orchestrator()


if __name__ == "__main__":
    """Test the orchestrator"""
    try:
        workflow = create_default_orchestrator()
        print(f"✅ {AGENT_NAME} Agent Created Successfully")
    except Exception as e:
        print(f"❌ Error: {e}")
