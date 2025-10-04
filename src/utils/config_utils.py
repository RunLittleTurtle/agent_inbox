"""
Utility functions for loading user and agent-specific configuration from Supabase.

This module provides runtime config loading for agents. It's separate from config_api/main.py:
- config_api/main.py: UI ↔ Supabase (editing config, merging with defaults for display)
- config_utils.py: Agents ↔ Supabase (loading config at runtime)

Both query Supabase but serve different purposes - not duplication!
"""
import os
import sys
import io
import logging
from typing import Dict, Any, Optional
from supabase import create_client, Client

# Ensure UTF-8 encoding for stdout/stderr before any logging
# This prevents UnicodeEncodeError when Supabase returns URLs with Unicode characters
def _ensure_utf8_encoding():
    """Ensure stdout/stderr use UTF-8 encoding."""
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass  # Already configured or not supported

_ensure_utf8_encoding()

logger = logging.getLogger(__name__)


def _sanitize_dict_encoding(d: Dict[str, Any]) -> None:
    """Recursively ensure all strings in dict are properly UTF-8 encoded.

    This modifies the dict in-place to handle any encoding issues from Supabase.
    Particularly important for MCP URLs which may contain Unicode characters.

    Args:
        d: Dictionary to sanitize (modified in-place)
    """
    for key, value in d.items():
        if isinstance(value, dict):
            _sanitize_dict_encoding(value)
        elif isinstance(value, str):
            # Ensure string is valid UTF-8 by encoding/decoding
            try:
                # Most strings will already be fine, but this ensures consistency
                d[key] = value.encode('utf-8', errors='replace').decode('utf-8')
            except Exception:
                # If something goes wrong, keep original value
                pass


def get_supabase_client() -> Client:
    """
    Get Supabase client with service role key.

    Returns:
        Supabase client instance

    Raises:
        ValueError: If Supabase credentials are missing
    """
    supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SECRET_KEY")

    if not supabase_url or not supabase_key:
        raise ValueError(
            "Missing Supabase credentials. Set NEXT_PUBLIC_SUPABASE_URL and "
            "SUPABASE_SECRET_KEY in .env"
        )

    return create_client(supabase_url, supabase_key)


def get_agent_config_from_supabase(
    user_id: str,
    agent_id: str
) -> Dict[str, Any]:
    """
    Load agent-specific configuration from Supabase agent_configs table.

    This is used by agents at runtime to load user-specific configuration.
    Returns the raw config_data for the agent to use directly.

    Args:
        user_id: Clerk user ID
        agent_id: Agent identifier (e.g., "calendar_agent", "multi_tool_rube_agent")

    Returns:
        Dict with agent-specific config, or empty dict if not found

    Example:
        >>> config = get_agent_config_from_supabase("user_123", "calendar_agent")
        >>> mcp_url = config.get("mcp_integration", {}).get("mcp_server_url")
        >>> if mcp_url:
        ...     # Use user's custom MCP URL
        ... else:
        ...     # Fallback to .env for local dev
    """
    try:
        supabase = get_supabase_client()

        result = supabase.table("agent_configs")\
            .select("config_data")\
            .eq("clerk_id", user_id)\
            .eq("agent_id", agent_id)\
            .maybe_single()\
            .execute()

        if result.data and result.data.get("config_data"):
            config_data = result.data["config_data"]

            # Ensure all string values are properly decoded as UTF-8
            # This prevents issues if Supabase returns MCP URLs with Unicode characters
            if isinstance(config_data, dict):
                _sanitize_dict_encoding(config_data)

            logger.info(f" Loaded config for {agent_id}, user {user_id}")
            return config_data
        else:
            logger.info(f"  No config found for {agent_id}, user {user_id} - will use defaults")
            return {}

    except ValueError as e:
        # Missing Supabase credentials - expected in local dev without Supabase
        logger.warning(f"  Supabase not configured: {e}")
        logger.info(f"  Falling back to .env defaults for {agent_id}")
        return {}
    except Exception as e:
        logger.error(f" Error loading config for {agent_id}: {e}")
        return {}


def get_user_secrets_from_supabase(user_id: str) -> Dict[str, Any]:
    """
    Load global user secrets from Supabase user_secrets table.

    This loads API keys, timezone, and preferences that apply to ALL agents.
    Note: graph.py already handles API keys via config.configurable - this is
    provided for completeness if other parts of the system need direct access.

    Args:
        user_id: Clerk user ID

    Returns:
        Dict with user secrets (API keys, timezone, preferences)

    Example:
        >>> secrets = get_user_secrets_from_supabase("user_123")
        >>> timezone = secrets.get("timezone", "America/Toronto")
        >>> preferred_model = secrets.get("preferred_model", "claude-3-5-sonnet-20241022")
    """
    try:
        supabase = get_supabase_client()

        result = supabase.table("user_secrets")\
            .select("*")\
            .eq("clerk_id", user_id)\
            .maybe_single()\
            .execute()

        if result.data:
            logger.info(f" Loaded user secrets for user {user_id}")
            return result.data
        else:
            logger.info(f"  No user secrets found for {user_id} - will use defaults")
            return {}

    except ValueError as e:
        # Missing Supabase credentials - expected in local dev without Supabase
        logger.warning(f"  Supabase not configured: {e}")
        return {}
    except Exception as e:
        logger.error(f" Error loading user secrets: {e}")
        return {}
