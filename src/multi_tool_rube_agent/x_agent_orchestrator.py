"""
React Agent Orchestrator with MCP Integration
Uses centralized config from config.py
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any

from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv

from utils.llm_utils import get_llm
from .tools import get_agent_simple_tools
from .prompt import AGENT_SYSTEM_PROMPT
from .config import LLM_CONFIG, AGENT_NAME, get_current_context

load_dotenv()


class AgentOrchestrator:
    """Simple React Agent with MCP tools"""

    def __init__(self, llm_config: Dict[str, Any] = None):
        self.llm_config = llm_config or LLM_CONFIG

        # Extract model and temperature
        model_name = self.llm_config.get("model", "claude-sonnet-4-20250514")
        temperature = self.llm_config.get("temperature", 0.3)

        # Validate API key based on model provider
        if model_name.startswith('claude') or model_name.startswith('opus'):
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not found for Claude model")
        else:  # OpenAI models
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found for OpenAI model")

        # Use centralized get_llm function for cross-provider support
        self.llm = get_llm(model_name, temperature=temperature)
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


def create_multi_tool_rube_agent():
    """
    REQUIRED function for supervisor integration
    MUST match pattern: create_{agent}_agent()
    """
    return create_default_orchestrator()


if __name__ == "__main__":
    """Test the orchestrator"""
    try:
        workflow = create_default_orchestrator()
        print(f"✅ {AGENT_NAME} Agent Created Successfully")
    except Exception as e:
        print(f"❌ Error: {e}")
