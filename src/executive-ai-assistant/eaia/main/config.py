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
    Fetch user configuration from Supabase agent_configs and user_secrets tables.

    Following the calendar_agent pattern:
    - Agent-specific config (models, prompts) from agent_configs table
    - User secrets (API keys, credentials) from user_secrets table
    - Google OAuth credentials are fetched via gmail.py (using utils/google_oauth_utils.py)

    Returns flattened config dict or None if fetch fails
    """
    import os
    from supabase import create_client, Client

    # Extract user_id from LangGraph config metadata
    user_id = config.get("configurable", {}).get("user_id")
    if not user_id:
        # Try alternative locations where user_id might be stored
        metadata = config.get("metadata", {})
        user_id = metadata.get("user_id") or metadata.get("clerk_user_id")

    if not user_id:
        print("  No user_id found in config - using config.yaml")
        return None

    # Initialize Supabase client
    SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_SECRET_KEY")

    if not SUPABASE_URL or not SUPABASE_KEY:
        print(f"  Supabase credentials not configured - falling back to config.yaml for user {user_id}")
        return None

    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

        # 1. Fetch agent-specific config from agent_configs table
        agent_config_result = supabase.table("agent_configs") \
            .select("config_data, prompts") \
            .eq("clerk_id", user_id) \
            .eq("agent_id", "executive_ai_assistant") \
            .maybe_single() \
            .execute()

        # 2. Fetch user secrets (API keys, timezone, etc.) from user_secrets table
        user_secrets_result = supabase.table("user_secrets") \
            .select("anthropic_api_key, openai_api_key, timezone") \
            .eq("clerk_id", user_id) \
            .maybe_single() \
            .execute()

        # 3. Load base config from config.yaml as foundation
        config_path = _ROOT.joinpath("config.yaml")

        def _load_yaml():
            with open(config_path) as stream:
                return yaml.safe_load(stream)

        base_config = await asyncio.to_thread(_load_yaml)

        # 4. Merge configurations (priority: agent_configs > user_secrets > config.yaml)
        merged_config = base_config.copy()

        # Merge user secrets (API keys, timezone)
        if user_secrets_result and user_secrets_result.data:
            secrets = user_secrets_result.data
            if secrets.get("anthropic_api_key"):
                merged_config["anthropic_api_key"] = secrets["anthropic_api_key"]
            if secrets.get("openai_api_key"):
                merged_config["openai_api_key"] = secrets["openai_api_key"]
            if secrets.get("timezone"):
                merged_config["timezone"] = secrets["timezone"]

        # Merge agent-specific config (models, prompts)
        if agent_config_result and agent_config_result.data:
            config_data = agent_config_result.data.get("config_data", {})

            # Flatten nested config structure from Supabase
            # Config is stored as: {"llm_triage": {"triage_model": "...", "triage_temperature": ...}}
            # We need to flatten to: {"triage_model": "...", "triage_temperature": ...}
            for section_key, section_values in config_data.items():
                if isinstance(section_values, dict):
                    merged_config.update(section_values)

            # Merge prompts
            prompts = agent_config_result.data.get("prompts", {})
            if prompts:
                merged_config.update(prompts)

        print(f"  Loaded config from Supabase for user {user_id}")
        print(f"    - triage_model: {merged_config.get('triage_model', 'not set')}")
        print(f"    - draft_model: {merged_config.get('draft_model', 'not set')}")
        print(f"    - has_anthropic_key: {bool(merged_config.get('anthropic_api_key'))}")
        print(f"    - has_openai_key: {bool(merged_config.get('openai_api_key'))}")

        return merged_config

    except Exception as e:
        print(f"  Error fetching from Supabase: {e}")
        import traceback
        traceback.print_exc()
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
