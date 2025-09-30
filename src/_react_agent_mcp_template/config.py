"""
Agent configuration - centralized settings

🔥 CRITICAL: Replace ALL placeholder values below for configuration UI to work:
- {AGENT_NAME} → actual agent name (e.g., "gmail", "sheets", "drive")
- {AGENT_DISPLAY_NAME} → display name (e.g., "Gmail", "Google Sheets")
- {AGENT_DESCRIPTION} → description (e.g., "email management", "spreadsheet operations")
- {MCP_SERVICE} → MCP service name (e.g., "google_gmail", "google_sheets")

Also update agent-inbox/src/pages/api/config/ endpoints when duplicating.
See ../../MCP_AGENT_CONFIGURATION_GUIDE.md for complete instructions.
"""

import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Dict
from dotenv import load_dotenv

load_dotenv()

# TODO: Configure for your agent
AGENT_NAME = "{AGENT_NAME}"  # e.g., "gmail", "sheets", "drive" - DO NOT CHANGE (internal identifier)
AGENT_DISPLAY_NAME = "{AGENT_DISPLAY_NAME}"  # e.g., "Gmail", "Google Sheets", "Google Drive"
AGENT_DESCRIPTION = "{AGENT_DESCRIPTION}"  # e.g., "email management", "spreadsheet operations"
AGENT_STATUS = "disabled"  # active or disabled

# Import prompts from prompt.py following LangGraph best practices
from .prompt import AGENT_SYSTEM_PROMPT

# MCP Configuration
# ARCHITECTURE NOTE:
#   1. This config.py reads the MCP URL from the main .env file using os.getenv()
#   2. The UI config (ui_config.py) reads from THIS file, not from .env
#   3. Prompts (prompt.py) also read from THIS file, not from .env
#   This ensures proper separation: .env → config.py → UI/prompts
#
# Specify the exact environment variable name that contains your MCP server URL
# This is flexible - works with any MCP provider (Rube, Composio, Pipedream, custom, etc.)
# Examples:
#   - Rube: "RUBE_MCP_SERVER" (universal)
#   - Composio: "COMPOSIO_MCP_SERVER_google_classroom"
#   - Pipedream: "PIPEDREAM_MCP_SERVER_google_gmail"
#   - Custom: "MY_CUSTOM_MCP_SERVER"
MCP_ENV_VAR = "{MCP_PROVIDER}_MCP_SERVER_{SERVICE_NAME}"  # e.g., "RUBE_MCP_SERVER", "COMPOSIO_MCP_SERVER_slack"

# MCP Server URL - reads from the specified environment variable in main .env
# Will be empty if the environment variable doesn't exist or template is unconfigured
MCP_SERVER_URL = os.getenv(MCP_ENV_VAR, '') if not any(placeholder in MCP_ENV_VAR for placeholder in ["{MCP_ENV_VAR}", "{MCP_PROVIDER}", "{SERVICE_NAME}"]) else ''

# Timezone Configuration
# 'global' means use the system-wide USER_TIMEZONE from main .env
TEMPLATE_TIMEZONE = 'America/Toronto'  # This will be updated by config UI

# Effective timezone: Use agent-specific if set, otherwise fall back to global
if TEMPLATE_TIMEZONE == 'global' or not TEMPLATE_TIMEZONE:
    # Use the global timezone from main .env
    USER_TIMEZONE = os.getenv('USER_TIMEZONE', 'America/Toronto')
else:
    # Use the agent-specific timezone
    USER_TIMEZONE = TEMPLATE_TIMEZONE

LLM_CONFIG = {
    "model": "gpt-5",
    "temperature": 0.1,
    "streaming": False,  # Disable streaming for LangGraph compatibility
    "api_key": os.getenv("ANTHROPIC_API_KEY")
}


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

def is_agent_enabled():
    """Check if the agent is enabled"""
    return AGENT_STATUS == "active"
