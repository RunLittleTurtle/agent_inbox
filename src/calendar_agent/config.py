"""
Calendar Agent Configuration
Central configuration for calendar agent settings
"""
import os

# Agent Identity
AGENT_NAME = "calendar"
AGENT_DISPLAY_NAME = "Calendar"
AGENT_DESCRIPTION = "Google Calendar management and scheduling"
AGENT_STATUS = "active"  # active or disabled
MCP_SERVICE = "google_calendar"

# LLM Configuration
LLM_CONFIG = {
    "model": "claude-sonnet-4-20250514",
    "temperature": 0.3,
    "streaming": False
}

# MCP Server Configuration
# Uses global PIPEDREAM_MCP_SERVER from .env
MCP_SERVER_URL = os.getenv('PIPEDREAM_MCP_SERVER', '')

# User Preferences
# Agent-specific timezone setting (set via config UI)
# 'global' means use the system-wide USER_TIMEZONE from main .env
CALENDAR_TIMEZONE = 'global'  # This will be updated by config UI

# Effective timezone: Use agent-specific if set, otherwise fall back to global
if CALENDAR_TIMEZONE == 'global' or not CALENDAR_TIMEZONE:
    # Use the global timezone from main .env
    USER_TIMEZONE = os.getenv('USER_TIMEZONE', 'America/Toronto')
else:
    # Use the agent-specific timezone
    USER_TIMEZONE = CALENDAR_TIMEZONE

# Calendar Settings (editable via config UI)
WORK_HOURS_START = '09:00'
WORK_HOURS_END = '16:00'
DEFAULT_MEETING_DURATION = '30'  # minutes

def is_agent_enabled():
    """Check if the agent is enabled"""
    return AGENT_STATUS == "active"
