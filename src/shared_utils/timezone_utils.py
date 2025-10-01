"""
Centralized Timezone Utilities for Agent Inbox
Provides consistent timezone handling across all agents.

Usage:
    from shared_utils.timezone_utils import get_agent_timezone, get_current_context

    # Get timezone for an agent (reads from config.py or config.yaml)
    tz = get_agent_timezone('calendar_agent', config_file_type='py')

    # Get current time context in agent's timezone
    context = get_current_context(timezone_name=tz)
"""

import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Dict, Optional, Literal
from pathlib import Path


def get_global_timezone() -> str:
    """
    Get the system-wide USER_TIMEZONE from environment variables.

    Works in both local dev (loads from .env) and deployment (env vars injected by platform).

    Returns:
        str: Timezone name (e.g., 'America/Toronto')
    """
    from dotenv import load_dotenv

    # Load .env if it exists (local dev) - searches parent directories automatically
    # In deployment, this is a no-op (no .env file), env vars are injected by platform
    load_dotenv()

    return os.getenv('USER_TIMEZONE', 'America/Toronto')


def get_agent_timezone(
    agent_name: str,
    config_file_type: Literal['py', 'yaml'] = 'py',
    timezone_field: Optional[str] = None
) -> str:
    """
    Get timezone for a specific agent from its configuration file.

    Args:
        agent_name: Name of the agent directory (e.g., 'calendar_agent', 'executive-ai-assistant')
        config_file_type: Type of config file ('py' for config.py, 'yaml' for config.yaml)
        timezone_field: Optional specific field name to look for
            If None, will auto-detect common patterns:
            - CALENDAR_TIMEZONE
            - TEMPLATE_TIMEZONE
            - timezone (for YAML)

    Returns:
        str: Timezone name, or falls back to system timezone if:
            - Config file doesn't exist
            - Field is not found or empty

    Examples:
        >>> get_agent_timezone('calendar_agent')
        'Asia/Shanghai'

        >>> get_agent_timezone('executive-ai-assistant', config_file_type='yaml')
        'America/Toronto'

        >>> get_agent_timezone('_react_agent_mcp_template')
        'America/Toronto'  # Falls back to system timezone if not configured
    """
    global_tz = get_global_timezone()

    try:
        agent_dir = Path(__file__).parent.parent / agent_name

        if config_file_type == 'py':
            config_file = agent_dir / 'config.py'
            if not config_file.exists():
                return global_tz

            content = config_file.read_text()

            # Auto-detect timezone field name if not specified
            if timezone_field is None:
                # Try common patterns in order of specificity
                for pattern in ['CALENDAR_TIMEZONE', 'TEMPLATE_TIMEZONE', 'USER_TIMEZONE']:
                    if f"{pattern} = " in content:
                        timezone_field = pattern
                        break

            if timezone_field:
                # Extract value using regex
                import re
                match = re.search(rf"{timezone_field}\s*=\s*['\"]([^'\"]+)['\"]", content)
                if match:
                    tz_value = match.group(1)
                    # Return the configured timezone directly
                    if not tz_value:
                        return global_tz
                    return tz_value

            return global_tz

        elif config_file_type == 'yaml':
            import yaml

            # For executive-ai-assistant, config.yaml is in eaia/main/
            if agent_name == 'executive-ai-assistant':
                config_file = agent_dir / 'eaia' / 'main' / 'config.yaml'
            else:
                config_file = agent_dir / 'config.yaml'

            if not config_file.exists():
                return global_tz

            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f)

            # Auto-detect field name if not specified
            if timezone_field is None:
                timezone_field = 'timezone'

            tz_value = config_data.get(timezone_field)

            # Return configured timezone or fallback to system default (America/Toronto from .env)
            if not tz_value:
                return global_tz

            return tz_value

    except Exception as e:
        # Fallback to system timezone (America/Toronto from .env) on any error
        print(f"Warning: Could not read timezone for {agent_name}: {e}")
        return global_tz


def get_current_context(timezone_name: Optional[str] = None) -> Dict[str, str]:
    """
    Get current time and timezone context.
    Centralized function used by all agents for consistent time handling.

    Args:
        timezone_name: Optional timezone name. If None, uses system default (USER_TIMEZONE from .env).

    Returns:
        Dict containing:
            - current_time: ISO format datetime with timezone
            - timezone: Timezone object string repr
            - timezone_name: Name of the timezone (e.g., 'America/Toronto')
            - today: Today's date with day name
            - tomorrow: Tomorrow's date with day name
            - time_str: Human-readable time string

    Example:
        >>> ctx = get_current_context('America/Toronto')
        >>> print(ctx['today'])
        '2025-09-29 (Sunday)'
        >>> print(ctx['time_str'])
        '02:30 PM EDT'
    """
    if timezone_name is None:
        timezone_name = get_global_timezone()

    try:
        timezone_zone = ZoneInfo(timezone_name)
        current_time = datetime.now(timezone_zone)
        tomorrow = current_time + timedelta(days=1)

        return {
            "current_time": current_time.isoformat(),
            "timezone": str(timezone_zone),
            "timezone_name": timezone_name,
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
            "tomorrow": f"{tomorrow.strftime('%Y-%m-%d')} ({tomorrow.strftime('%A')})",
            "time_str": current_time.strftime('%I:%M %p UTC'),
            "error": str(e)
        }


def format_datetime_with_timezone(dt_str: str, timezone_name: Optional[str] = None) -> str:
    """
    Formats a datetime string with the specified timezone.

    Args:
        dt_str: The datetime string to format (ISO format or with Z suffix)
        timezone_name: The timezone to use. If None, uses system default (USER_TIMEZONE from .env).

    Returns:
        A formatted datetime string with the timezone abbreviation.

    Example:
        >>> format_datetime_with_timezone("2025-09-29T14:00:00Z", "America/Toronto")
        '2025-09-29 10:00 AM EDT'
    """
    if timezone_name is None:
        timezone_name = get_global_timezone()

    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        tz = ZoneInfo(timezone_name)
        dt = dt.astimezone(tz)
        return dt.strftime("%Y-%m-%d %I:%M %p %Z")
    except Exception as e:
        # Return original string if formatting fails
        return dt_str


# Convenience function for agents that need timezone in their prompts
def get_timezone_context_for_prompt(agent_name: Optional[str] = None, config_file_type: Literal['py', 'yaml'] = 'py') -> str:
    """
    Get formatted timezone context suitable for including in agent prompts.

    Args:
        agent_name: Optional agent name to get agent-specific timezone.
                   If None, uses system default (USER_TIMEZONE from .env).
        config_file_type: Type of config file for the agent

    Returns:
        Formatted string with current time and timezone context

    Example:
        >>> print(get_timezone_context_for_prompt('calendar_agent'))
        Current time: 2025-09-29 02:30 PM CST
        Timezone: Asia/Shanghai
        Today: 2025-09-29 (Sunday)
        Tomorrow: 2025-09-30 (Monday)
    """
    if agent_name:
        tz = get_agent_timezone(agent_name, config_file_type)
    else:
        tz = get_global_timezone()

    ctx = get_current_context(tz)

    return f"""Current time: {ctx['time_str']}
Timezone: {ctx['timezone_name']}
Today: {ctx['today']}
Tomorrow: {ctx['tomorrow']}"""