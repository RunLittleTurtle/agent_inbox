"""
Executive AI Assistant Config Defaults
⚠️ IMPORTANT: These are FALLBACK values only
⚠️ Actual runtime values loaded from config.yaml via eaia/main/config.py

This file exists to:
1. Fix broken ui_config.py imports (lines 413-414)
2. Provide DEFAULTS export for FastAPI config bridge
3. Serve as static reference for code-defined defaults

DO NOT MODIFY eaia/main/config.py - that handles runtime YAML loading
"""

# Agent Identity (read-only in UI)
AGENT_NAME = "executive-ai-assistant"
AGENT_DISPLAY_NAME = "Executive AI Assistant"
AGENT_DESCRIPTION = "AI-powered executive assistant for email management, scheduling, and task automation"
MCP_SERVICE = "google_workspace"

# Per-Node LLM Model Defaults
# These match the fallback values in each node file:
# - triage.py line 55
# - draft_response.py line 100
# - rewrite.py line 36
# - find_meeting_time.py line 73
# - reflection_graphs.py line 69
LLM_CONFIG = {
    "triage_model": "claude-3-5-haiku-20241022",
    "triage_temperature": 0.1,
    "draft_model": "claude-sonnet-4-20250514",
    "draft_temperature": 0.3,
    "rewrite_model": "claude-sonnet-4-20250514",
    "rewrite_temperature": 0.3,
    "scheduling_model": "gpt-4o",
    "scheduling_temperature": 0.1,
    "reflection_model": "claude-sonnet-4-20250514",
    "reflection_temperature": 0.3,
}

# Timezone default (from config.yaml)
DEFAULT_TIMEZONE = "America/Toronto"

# =============================================================================
# DEFAULTS EXPORT FOR FASTAPI CONFIG BRIDGE
# =============================================================================
# This export allows FastAPI to read immutable config defaults from code
# These are agent-specific defaults, not shared across agents

DEFAULTS = {
    "llm": LLM_CONFIG,
    "agent_identity": {
        "agent_name": AGENT_NAME,
        "agent_display_name": AGENT_DISPLAY_NAME,
        "agent_description": AGENT_DESCRIPTION,
        "mcp_service": MCP_SERVICE,
    },
    "timezone": DEFAULT_TIMEZONE,
}
