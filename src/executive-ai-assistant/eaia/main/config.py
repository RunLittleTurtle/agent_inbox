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


async def get_config(config: dict):
    # This loads things either ALL from configurable, or
    # all from the config.yaml
    # This is done intentionally to enforce an "all or nothing" configuration
    if "email" in config["configurable"]:
        config_data = config["configurable"]
    else:
        # Use asyncio.to_thread to move blocking YAML loading to a separate thread
        config_path = _ROOT.joinpath("config.yaml")

        def _load_yaml():
            with open(config_path) as stream:
                return yaml.safe_load(stream)

        config_data = await asyncio.to_thread(_load_yaml)

    # CRITICAL: Resolve template variables before returning
    # This ensures modules get "bill" instead of "{name}"
    return _resolve_templates(config_data)
