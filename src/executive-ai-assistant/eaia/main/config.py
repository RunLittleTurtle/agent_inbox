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
    Fetch user configuration from Supabase Config API
    Returns flattened config dict or None if fetch fails
    """
    import os
    import httpx

    # Extract user_id from LangGraph config metadata
    # LangGraph Cloud passes user identity through thread metadata
    user_id = config.get("configurable", {}).get("user_id")
    if not user_id:
        # Try alternative locations where user_id might be stored
        metadata = config.get("metadata", {})
        user_id = metadata.get("user_id") or metadata.get("clerk_user_id")

    if not user_id:
        print("⚠️  No user_id found in config - skipping Supabase fetch")
        return None

    # Get Config API URL from environment or use default
    config_api_url = os.environ.get("CONFIG_API_URL", "http://localhost:8000")
    agent_id = "executive-ai-assistant"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Fetch agent-specific config
            agent_response = await client.get(
                f"{config_api_url}/api/config/values",
                params={"agent_id": agent_id, "user_id": user_id}
            )

            # Fetch global config (API keys, credentials)
            global_response = await client.get(
                f"{config_api_url}/api/config/values",
                params={"agent_id": "global", "user_id": user_id}
            )

            if agent_response.status_code != 200:
                print(f"⚠️  Config API returned {agent_response.status_code} - falling back to config.yaml")
                return None

            agent_data = agent_response.json()
            global_data = global_response.json() if global_response.status_code == 200 else {}

            print(f"✅ Fetched config from Supabase for user {user_id}")

            # Flatten nested config structure to match config.yaml format
            # Input:  { values: { section_key: { field_key: { current: value, ... } } } }
            # Output: { field_key: value, ... }
            flat_config = {}

            # First, flatten agent-specific config
            values = agent_data.get("values", {})
            for section_key, section_value in values.items():
                if isinstance(section_value, dict):
                    for field_key, field_value in section_value.items():
                        if isinstance(field_value, dict) and "current" in field_value:
                            flat_config[field_key] = field_value["current"]

            # Then, add global config (API keys from user_secrets)
            # Global config comes as flat structure, not nested
            for section_key, section_value in global_data.items():
                if section_key == "ai_models":
                    # Extract API keys
                    if isinstance(section_value, dict):
                        flat_config["anthropic_api_key"] = section_value.get("anthropic_api_key", "")
                        flat_config["openai_api_key"] = section_value.get("openai_api_key", "")
                elif section_key == "langgraph_system":
                    # Extract LangSmith key
                    if isinstance(section_value, dict):
                        flat_config["langsmith_api_key"] = section_value.get("langsmith_api_key", "")
                elif section_key == "google_workspace":
                    # Extract Google credentials
                    if isinstance(section_value, dict):
                        flat_config["google_client_id"] = section_value.get("google_client_id", "")
                        flat_config["google_client_secret"] = section_value.get("google_client_secret", "")
                        flat_config["google_refresh_token"] = section_value.get("google_refresh_token", "")

            print(f"🔍 DEBUG: Flattened config has {len(flat_config)} fields")
            print(f"🔍 DEBUG: Has API keys: anthropic={bool(flat_config.get('anthropic_api_key'))}, openai={bool(flat_config.get('openai_api_key'))}")

            return flat_config

    except Exception as e:
        print(f"⚠️  Error fetching from Supabase Config API: {e}")
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
