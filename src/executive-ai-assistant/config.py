"""
Executive AI Assistant Config Defaults
 IMPORTANT: These are FALLBACK values only
 Actual runtime values loaded from config.yaml via eaia/main/config.py

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
    "draft_model": "gpt-5",
    "draft_temperature": 1,  # Reasoning models like gpt-5 use temperature 1 only
    "rewrite_model": "claude-sonnet-4-5-20250929",
    "rewrite_temperature": 0.3,
    "scheduling_model": "gpt-4o",
    "scheduling_temperature": 0.1,
    "reflection_model": "claude-sonnet-4-5-20250929",
    "reflection_temperature": 0.3,
}

# Timezone default (from config.yaml)
DEFAULT_TIMEZONE = "America/Toronto"

# =============================================================================
# LAZY-LOADING HELPER FOR TRIAGE PROMPTS
# =============================================================================

def _load_config_yaml():
    """
    Load configuration from config.yaml
    Returns dict with all user-editable fields
    """
    import yaml
    from pathlib import Path

    try:
        config_path = Path(__file__).parent / "eaia" / "main" / "config.yaml"
        with open(config_path) as stream:
            return yaml.safe_load(stream)
    except Exception as e:
        print(f"  Warning: Could not load config.yaml: {e}")
        return {}

def _load_triage_prompts_from_config_yaml():
    """
    Load triage prompts from config.yaml
    These are the SAFE prompts that reflection loop never modifies
    """
    config_data = _load_config_yaml()
    return {
        "triage_no": config_data.get("triage_no", ""),
        "triage_notify": config_data.get("triage_notify", ""),
        "triage_email": config_data.get("triage_email", ""),
    }

def _load_user_preferences_from_config_yaml():
    """Load user profile and preference fields from config.yaml (combined for UI)"""
    config_data = _load_config_yaml()
    return {
        # User profile fields
        "email": config_data.get("email", ""),
        "name": config_data.get("name", ""),
        "full_name": config_data.get("full_name", ""),
        "background": config_data.get("background", ""),
        "timezone": config_data.get("timezone", "America/Toronto"),
        # User preference fields
        "background_preferences": config_data.get("background_preferences", ""),
        "response_preferences": config_data.get("response_preferences", ""),
        "schedule_preferences": config_data.get("schedule_preferences", ""),
        "rewrite_preferences": config_data.get("rewrite_preferences", ""),
    }

def _load_agent_settings_from_config_yaml():
    """Load agent settings from config.yaml"""
    config_data = _load_config_yaml()
    return {
        "memory": config_data.get("memory", True),
    }

# =============================================================================
# DEFAULTS EXPORT FOR FASTAPI CONFIG BRIDGE
# =============================================================================
# This export allows FastAPI to read immutable config defaults from code
# These are agent-specific defaults, not shared across agents
# IMPORTANT: Section keys must match CONFIG_SECTIONS keys in ui_config.py

# Load all config sections at module load time
_TRIAGE_PROMPTS = _load_triage_prompts_from_config_yaml()
_USER_PREFERENCES = _load_user_preferences_from_config_yaml()
_AGENT_SETTINGS = _load_agent_settings_from_config_yaml()

DEFAULTS = {
    # Split LLM config to match ui_config.py sections
    "llm_triage": {
        "triage_model": LLM_CONFIG["triage_model"],
        "triage_temperature": LLM_CONFIG["triage_temperature"],
    },
    "llm_draft": {
        "draft_model": LLM_CONFIG["draft_model"],
        "draft_temperature": LLM_CONFIG["draft_temperature"],
    },
    "llm_rewrite": {
        "rewrite_model": LLM_CONFIG["rewrite_model"],
        "rewrite_temperature": LLM_CONFIG["rewrite_temperature"],
    },
    "llm_scheduling": {
        "scheduling_model": LLM_CONFIG["scheduling_model"],
        "scheduling_temperature": LLM_CONFIG["scheduling_temperature"],
    },
    "llm_reflection": {
        "reflection_model": LLM_CONFIG["reflection_model"],
        "reflection_temperature": LLM_CONFIG["reflection_temperature"],
    },
    "agent_identity": {
        "agent_name": AGENT_NAME,
        "agent_display_name": AGENT_DISPLAY_NAME,
        "agent_description": AGENT_DESCRIPTION,
        "mcp_service": MCP_SERVICE,
    },
    # Triage prompts section (SAFE - never modified by reflection loop)
    "triage_prompts": _TRIAGE_PROMPTS,
    # User preferences section (profile + preferences combined to match ui_config.py)
    "user_preferences": _USER_PREFERENCES,
    # Agent settings section (feature flags)
    "agent_settings": _AGENT_SETTINGS,
}
