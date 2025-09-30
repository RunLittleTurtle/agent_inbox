"""
Centralized LLM Model and Timezone Options
Single source of truth for all agent configurations

IMPORTANT: This file loads constants from config/model_constants.json
To add new models or timezones, edit the JSON file.
Changes automatically propagate to both Python and TypeScript code.
"""

import json
from pathlib import Path

# Load constants from JSON (single source of truth)
_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "model_constants.json"

try:
    with open(_CONFIG_PATH, 'r') as f:
        _config = json.load(f)
except FileNotFoundError:
    raise FileNotFoundError(
        f"Configuration file not found at {_CONFIG_PATH}. "
        "Please ensure config/model_constants.json exists."
    )

# ============================================================================
# LLM MODEL OPTIONS
# ============================================================================
# Loaded from JSON - edit config/model_constants.json to modify

STANDARD_LLM_MODEL_OPTIONS = _config["STANDARD_LLM_MODEL_OPTIONS"]
MODEL_DESCRIPTIONS = _config["MODEL_DESCRIPTIONS"]

# ============================================================================
# TIMEZONE OPTIONS
# ============================================================================
# Loaded from JSON - edit config/model_constants.json to modify

STANDARD_TIMEZONE_OPTIONS = _config["STANDARD_TIMEZONE_OPTIONS"]

# ============================================================================
# TEMPERATURE OPTIONS
# ============================================================================
# Loaded from JSON - edit config/model_constants.json to modify

STANDARD_TEMPERATURE_OPTIONS = _config["STANDARD_TEMPERATURE_OPTIONS"]

# ============================================================================
# AGENT STATUS OPTIONS
# ============================================================================
# Loaded from JSON - edit config/model_constants.json to modify

STANDARD_AGENT_STATUS_OPTIONS = _config["STANDARD_AGENT_STATUS_OPTIONS"]

# ============================================================================
# DEFAULT VALUES
# ============================================================================
# Loaded from JSON - edit config/model_constants.json to modify
#
# USE THESE in:
# - ui_config.py 'default' fields (for dropdown defaults)
# - ui_config.py get_current_config() fallback values
# - config.py imports for FALLBACK USE ONLY (use in .get() calls, not assignments)
# - TypeScript route.ts fallback values
# - Any agent function that needs a fallback model
#
# CRITICAL: In config.py, use LITERAL VALUES for fields updated by config UI:
#   CORRECT:   LLM_CONFIG = {"model": "claude-sonnet-4-5-20250929", "temperature": 0.3}
#   WRONG:     LLM_CONFIG = {"model": DEFAULT_LLM_MODEL, "temperature": 0.3}
# The TypeScript update API uses regex to find and replace literal values.
# Constants won't match the regex patterns and will prevent UI updates from working.

DEFAULT_LLM_MODEL = _config["DEFAULT_LLM_MODEL"]
DEFAULT_TIMEZONE = _config["DEFAULT_TIMEZONE"]
DEFAULT_TEMPERATURE = _config["DEFAULT_TEMPERATURE"]
DEFAULT_STREAMING = _config["DEFAULT_STREAMING"]

# Task-specific model recommendations (can be overridden by agents)
DEFAULT_TRIAGE_MODEL = _config["DEFAULT_TRIAGE_MODEL"]
DEFAULT_DRAFT_MODEL = _config["DEFAULT_DRAFT_MODEL"]
DEFAULT_REWRITE_MODEL = _config["DEFAULT_REWRITE_MODEL"]
DEFAULT_SCHEDULING_MODEL = _config["DEFAULT_SCHEDULING_MODEL"]
DEFAULT_REFLECTION_MODEL = _config["DEFAULT_REFLECTION_MODEL"]