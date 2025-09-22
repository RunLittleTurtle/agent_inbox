import os
import asyncio
import yaml
from pathlib import Path

_ROOT = Path(__file__).absolute().parent


async def get_config(config: dict):
    # This loads things either ALL from configurable, or
    # all from the config.yaml
    # This is done intentionally to enforce an "all or nothing" configuration
    if "email" in config["configurable"]:
        return config["configurable"]
    else:
        # Use asyncio.to_thread to move blocking YAML loading to a separate thread
        config_path = _ROOT.joinpath("config.yaml")

        def _load_yaml():
            with open(config_path) as stream:
                return yaml.safe_load(stream)

        return await asyncio.to_thread(_load_yaml)

LLM_CONFIG = {
    "model": "claude-sonnet-4-20250514",
    "temperature": 0.2,
    "api_key": os.getenv("ANTHROPIC_API_KEY")
}
