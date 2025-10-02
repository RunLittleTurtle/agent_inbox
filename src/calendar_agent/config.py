"""
Calendar Agent Configuration
Central configuration for calendar agent settings
"""
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Dict
from dotenv import load_dotenv

# Import centralized defaults for fallback only
from shared_utils import DEFAULT_LLM_MODEL, DEFAULT_STREAMING

load_dotenv()

# Agent Identity
AGENT_NAME = "calendar"
AGENT_DISPLAY_NAME = "Calendar"
AGENT_DESCRIPTION = "Google Calendar management and scheduling"
AGENT_STATUS = "active"  # active or disabled
MCP_SERVICE = "google_calendar"

# Import prompts from prompt.py following LangGraph best practices
from .prompt import AGENT_SYSTEM_PROMPT

# MCP Environment Variable - use existing variable from .env
# The calendar agent uses the generic PIPEDREAM_MCP_SERVER variable
MCP_ENV_VAR = "PIPEDREAM_MCP_SERVER"

# LLM Configuration
# NOTE: These values are updated by the config UI. Use literal values here.
# The DEFAULT constants are imported for fallback use in code (e.g., .get() calls)
LLM_CONFIG = {
    "model": "gpt-5",
    "temperature": 0.3,
    "streaming": False
}

# MCP Server Configuration
# Uses the existing PIPEDREAM_MCP_SERVER from .env
MCP_SERVER_URL = os.getenv(MCP_ENV_VAR, '')

# User Preferences
# Agent-specific timezone setting (set via config UI)
# 'global' means use the system-wide USER_TIMEZONE from main .env
CALENDAR_TIMEZONE = 'America/Toronto'  # This will be updated by config UI

# CRITICAL: Always define USER_TIMEZONE first as a fallback
USER_TIMEZONE = os.getenv('USER_TIMEZONE', 'America/Toronto')

# Effective timezone: Use agent-specific if set, otherwise fall back to global
try:
    if CALENDAR_TIMEZONE == 'global' or not CALENDAR_TIMEZONE:
        # Use the global timezone from main .env (already set above)
        pass
    else:
        # Use the agent-specific timezone
        USER_TIMEZONE = CALENDAR_TIMEZONE
except Exception as e:
    # Fallback already set above
    pass

# Calendar Settings (editable via config UI)
WORK_HOURS_START = '09:00'
WORK_HOURS_END = '16:00'
DEFAULT_MEETING_DURATION = '30'  # minutes

def is_agent_enabled():
    """Check if the agent is enabled"""
    return AGENT_STATUS == "active"

def get_current_context() -> Dict[str, str]:
    """
    Get current time and timezone context from environment
    Centralized function used by all agents for consistent time handling
    """
    try:
        timezone_zone = ZoneInfo(USER_TIMEZONE)
        current_time = datetime.now(timezone_zone)
        tomorrow = current_time + timedelta(days=1)

        return {
            "current_time": current_time.isoformat(),
            "timezone": str(timezone_zone),
            "timezone_name": USER_TIMEZONE,
            "today": f"{current_time.strftime('%Y-%m-%d')} ({current_time.strftime('%A')})",
            "tomorrow": f"{tomorrow.strftime('%Y-%m-%d')} ({tomorrow.strftime('%A')})",
            "time_str": current_time.strftime('%I:%M %p %Z')
        }
    except Exception as e:
        # Fallback to UTC if timezone fails
        current_time = datetime.now(ZoneInfo("UTC"))
        return {
            "current_time": current_time.isoformat(),
            "timezone": "UTC",
            "timezone_name": "UTC",
            "today": f"{current_time.strftime('%Y-%m-%d')} ({current_time.strftime('%A')})",
            "tomorrow": f"{current_time.strftime('%Y-%m-%d')} ({current_time.strftime('%A')})",
            "time_str": current_time.strftime('%I:%M %p UTC')
        }

# =============================================================================
# DEFAULTS EXPORT FOR FASTAPI CONFIG BRIDGE
# =============================================================================
# This export allows FastAPI to read immutable config defaults from code
# These are agent-specific defaults, not shared across agents

DEFAULTS = {
    "llm": LLM_CONFIG,
    "calendar_settings": {
        "work_hours_start": WORK_HOURS_START,
        "work_hours_end": WORK_HOURS_END,
        "default_meeting_duration": DEFAULT_MEETING_DURATION,
        "timezone": CALENDAR_TIMEZONE,
    },
    "agent_identity": {
        "agent_name": AGENT_NAME,
        "agent_display_name": AGENT_DISPLAY_NAME,
        "agent_description": AGENT_DESCRIPTION,
        "agent_status": AGENT_STATUS,
    },
}
