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
AGENT_NAME = "email"  # e.g., "gmail", "sheets", "drive"
AGENT_DISPLAY_NAME = "Email"  # e.g., "Gmail", "Google Sheets", "Google Drive"
AGENT_DESCRIPTION = "email management and Gmail operations"  # e.g., "email management", "spreadsheet operations"
MCP_SERVICE = "google_gmail"  # e.g., "google_gmail", "google_sheets", "google_drive"

# MCP Environment Variable
MCP_ENV_VAR = f"PIPEDREAM_MCP_SERVER_{MCP_SERVICE}"

# Timezone configuration from environment
USER_TIMEZONE = os.getenv("USER_TIMEZONE", "America/Toronto")

LLM_CONFIG = {
    "model": "claude-sonnet-4-20250514",
    "temperature": 0.3,
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
