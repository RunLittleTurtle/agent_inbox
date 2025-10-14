"""
Agent Configuration - TEMPLATE
Generic Google OAuth agent configuration.

CUSTOMIZATION REQUIRED:
1. Replace {DOMAIN} with your agent domain (e.g., 'contacts', 'email', 'drive')
2. Update GOOGLE_OAUTH_SCOPES with your required scopes
3. Optionally customize LLM settings
"""
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ==============================================================================
# LLM CONFIGURATION
# ==============================================================================
# TODO: Replace {DOMAIN} with your agent name (e.g., CONTACTS_LLM_MODEL)
DEFAULT_LLM_MODEL = "claude-3-5-sonnet-20241022"

LLM_CONFIG = {
    "model": os.getenv("{DOMAIN}_LLM_MODEL", DEFAULT_LLM_MODEL),
    "temperature": float(os.getenv("{DOMAIN}_LLM_TEMPERATURE", "0.1")),
    "max_tokens": int(os.getenv("{DOMAIN}_LLM_MAX_TOKENS", "4096")),
}

# ==============================================================================
# TIMEZONE CONFIGURATION
# ==============================================================================
# Agent-specific timezone setting (can be overridden in UI config)
TEMPLATE_TIMEZONE = 'America/Toronto'  # This will be updated by config UI

# Effective timezone: Use agent-specific if set, otherwise fall back to global
if TEMPLATE_TIMEZONE == 'global' or not TEMPLATE_TIMEZONE:
    # Use the global timezone from main .env
    USER_TIMEZONE = os.getenv('USER_TIMEZONE', 'America/Toronto')
else:
    # Use the agent-specific timezone
    USER_TIMEZONE = TEMPLATE_TIMEZONE

# ==============================================================================
# GOOGLE OAUTH CONFIGURATION
# ==============================================================================
# TODO: Update these scopes based on your Google API requirements
# See: https://developers.google.com/identity/protocols/oauth2/scopes

# EXAMPLE SCOPES FOR DIFFERENT GOOGLE APIS:
#
# Google Calendar:
#   - "https://www.googleapis.com/auth/calendar"
#   - "https://www.googleapis.com/auth/calendar.events"
#
# Google Contacts:
#   - "https://www.googleapis.com/auth/contacts.readonly"
#   - "https://www.googleapis.com/auth/contacts"
#
# Gmail:
#   - "https://www.googleapis.com/auth/gmail.readonly"
#   - "https://www.googleapis.com/auth/gmail.modify"
#   - "https://www.googleapis.com/auth/gmail.send"
#
# Google Drive:
#   - "https://www.googleapis.com/auth/drive.readonly"
#   - "https://www.googleapis.com/auth/drive.file"
#
# Google Classroom:
#   - "https://www.googleapis.com/auth/classroom.courses.readonly"
#   - "https://www.googleapis.com/auth/classroom.rosters.readonly"

GOOGLE_OAUTH_SCOPES = [
    # TODO: Add your required scopes here
    "https://www.googleapis.com/auth/REPLACE_WITH_YOUR_SCOPE",
]

# ==============================================================================
# AGENT BEHAVIOR CONFIGURATION
# ==============================================================================
# TODO: Customize these based on your agent's needs
AGENT_CONFIG = {
    "agent_name": "{DOMAIN}_agent",
    "description": "Generic Google OAuth agent template",
    "max_iterations": 10,
    "enable_human_in_loop": False,  # Set True if you need approval workflows
}

# ==============================================================================
# GOOGLE API CONFIGURATION
# ==============================================================================
# These credentials are loaded from environment variables (shared across all users)
# User-specific refresh_tokens are stored in Supabase user_secrets table
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    import logging
    logging.warning(
        "GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET not set in environment. "
        "Google OAuth authentication will not work."
    )


# ==============================================================================
# TIMEZONE CONTEXT FUNCTION (CRITICAL!)
# ==============================================================================

def get_current_context() -> Dict[str, str]:
    """
    Get current time and timezone context from environment.

    CRITICAL: This function provides timezone context that MUST be included
    in the first system message so the agent ALWAYS knows current date/time.

    Used by:
    - agent_orchestrator.py: Inject context into system prompt
    - booking_node.py (if applicable): Get current time for operations

    Returns:
        Dict with timezone context:
        - current_time: ISO formatted datetime
        - timezone: ZoneInfo string representation
        - timezone_name: Timezone name (e.g., "America/Toronto")
        - today: Formatted date with day name
        - tomorrow: Formatted date with day name
        - time_str: Human-readable time string
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
        import logging
        logging.error(f"Error getting timezone context: {e}. Falling back to UTC.")
        current_time = datetime.now(ZoneInfo("UTC"))
        tomorrow = current_time + timedelta(days=1)
        return {
            "current_time": current_time.isoformat(),
            "timezone": "UTC",
            "timezone_name": "UTC",
            "today": f"{current_time.strftime('%Y-%m-%d')} ({current_time.strftime('%A')})",
            "tomorrow": f"{tomorrow.strftime('%Y-%m-%d')} ({tomorrow.strftime('%A')})",
            "time_str": current_time.strftime('%I:%M %p UTC')
        }


def is_agent_enabled():
    """Check if the agent is enabled"""
    return AGENT_CONFIG.get("agent_status", "disabled") == "active"


# =============================================================================
# DEFAULTS EXPORT FOR FASTAPI CONFIG BRIDGE
# =============================================================================
# This export allows FastAPI to read immutable config defaults from code
# These are agent-specific defaults (template placeholders will be replaced)

DEFAULTS = {
    "llm": LLM_CONFIG,
    "agent_identity": {
        "agent_name": AGENT_CONFIG.get("agent_name", "{DOMAIN}_agent"),
        "agent_display_name": "{Domain} Agent",  # TODO: Replace with your agent display name
        "agent_description": AGENT_CONFIG.get("description", "Generic Google OAuth agent template"),
    },
    "user_preferences": {
        "timezone": TEMPLATE_TIMEZONE,
        "effective_timezone": USER_TIMEZONE,
    },
    "google_integration": {
        "google_oauth_scopes": GOOGLE_OAUTH_SCOPES,
        "enable_human_in_loop": AGENT_CONFIG.get("enable_human_in_loop", False),
    },
}
