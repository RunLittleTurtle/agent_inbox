import asyncio
import yaml
from pathlib import Path

_ROOT = Path(__file__).absolute().parent


def _resolve_templates(config_data: dict) -> dict:
    """
    Resolve template variables like {name}, {full_name} in config values
    This ensures modules receive fully resolved config instead of raw templates
    """
    if not isinstance(config_data, dict):
        return config_data

    # Extract values for template substitution
    template_values = {
        'name': config_data.get('name', ''),
        'full_name': config_data.get('full_name', ''),
        'email': config_data.get('email', ''),
        'background': config_data.get('background', ''),
    }

    # Create a copy to avoid mutating the original
    resolved_config = config_data.copy()

    # Fields that may contain templates
    template_fields = [
        'background', 'background_preferences', 'rewrite_preferences',
        'response_preferences', 'triage_no', 'triage_notify', 'triage_email'
    ]

    for field in template_fields:
        if field in resolved_config and isinstance(resolved_config[field], str):
            try:
                # Resolve template variables
                resolved_config[field] = resolved_config[field].format(**template_values)
            except (KeyError, ValueError):
                # If template resolution fails, keep original value
                pass

    return resolved_config


async def _fetch_from_supabase(config: dict) -> dict | None:
    """
    Fetch user configuration from Supabase (SIMPLIFIED - NO CONFIG_API).

    Following the calendar_agent pattern:
    - Google OAuth credentials are fetched via gmail.py (using utils/google_oauth_utils.py)
    - Agent-specific config comes from config.yaml (checked into repo)
    - This function is kept minimal for future Supabase config table integration

    Returns flattened config dict or None if fetch fails
    """
    import os

    # Extract user_id from LangGraph config metadata
    user_id = config.get("configurable", {}).get("user_id")
    if not user_id:
        # Try alternative locations where user_id might be stored
        metadata = config.get("metadata", {})
        user_id = metadata.get("user_id") or metadata.get("clerk_user_id")

    if not user_id:
        print("  No user_id found in config - using config.yaml")
        return None

    # NOTE: Google OAuth credentials are handled by eaia/gmail.py via load_google_credentials()
    # This function is simplified to focus on agent-specific config only

    try:
        # Future: Fetch agent-specific config from Supabase config table
        # For now, we use config.yaml (checked into repo)
        print(f"  Using config.yaml for user {user_id} (Supabase config table not yet implemented)")
        return None

    except Exception as e:
        print(f"  Error fetching from Supabase: {e}")
        return None


async def get_config(config: dict):
    # This loads things either ALL from configurable, or
    # fetches from Supabase (production), or falls back to config.yaml (dev/local)
    # This is done intentionally to enforce an "all or nothing" configuration
    if "email" in config["configurable"]:
        config_data = config["configurable"]
    else:
        # Try to fetch from Supabase Config API first (for LangGraph Cloud deployment)
        config_data = await _fetch_from_supabase(config)

        if config_data is None:
            # Fallback to config.yaml for local development
            # Use asyncio.to_thread to move blocking YAML loading to a separate thread
            config_path = _ROOT.joinpath("config.yaml")

            def _load_yaml():
                with open(config_path) as stream:
                    return yaml.safe_load(stream)

            config_data = await asyncio.to_thread(_load_yaml)

    # CRITICAL: Resolve template variables before returning
    # This ensures modules get "bill" instead of "{name}"
    return _resolve_templates(config_data)
