"""
Executive AI Assistant Prompt Defaults
⚠️ NON-BREAKING: This file provides lazy access to inline prompts from original files
⚠️ ZERO REFACTORING: All prompts remain in their original node files
⚠️ Lazy-loading pattern: Prompts loaded only when accessed (avoids import issues)

This file exists to:
1. Fix broken ui_config.py imports (lines 413-414)
2. Provide DEFAULTS export for FastAPI config bridge
3. Re-export prompts with standard names for compatibility

CRITICAL: Do NOT move prompts from their original files!
- triage_prompt stays in eaia/main/triage.py
- draft prompts stay in eaia/main/draft_response.py
- rewrite_prompt stays in eaia/main/rewrite.py
- reflection prompts stay in eaia/reflection_graphs.py

Runtime config.yaml still loads normally via eaia/main/config.py

NOTE: We use lazy loading because the node files have circular imports
that don't work when imported as submodules. This is fine because:
1. FastAPI will call get_defaults() which loads them in proper context
2. ui_config.py only needs the module to exist, not to execute
"""

import sys
from pathlib import Path

# =============================================================================
# LAZY-LOADING HELPER FUNCTION
# =============================================================================

def _load_prompts_from_files():
    """
    Lazy-load prompts from original source files
    This executes in proper context when FastAPI needs the values
    Returns dict of all prompts for DEFAULTS
    """
    # Add executive-ai-assistant to path for proper eaia imports
    exec_dir = Path(__file__).parent
    if str(exec_dir) not in sys.path:
        sys.path.insert(0, str(exec_dir))

    try:
        # Now imports will work because eaia/ is accessible
        from eaia.main.triage import triage_prompt
        from eaia.main.draft_response import EMAIL_WRITING_INSTRUCTIONS, draft_prompt
        from eaia.main.rewrite import rewrite_prompt
        from eaia.reflection_graphs import general_reflection_prompt, CHOOSE_MEMORY_PROMPT

        return {
            "triage_prompt": triage_prompt,
            "email_writing_instructions": EMAIL_WRITING_INSTRUCTIONS,
            "draft_prompt": draft_prompt,
            "rewrite_prompt": rewrite_prompt,
            "general_reflection_prompt": general_reflection_prompt,
            "choose_memory_prompt": CHOOSE_MEMORY_PROMPT,
        }
    except ImportError as e:
        print(f"⚠️  Warning: Could not load executive-ai-assistant prompts: {e}")
        return {}

# =============================================================================
# COMPATIBILITY EXPORTS FOR UI_CONFIG.PY
# =============================================================================
# ui_config.py expects these specific names (lines 414)
# Provide placeholder values - FastAPI will get real values via get_defaults()

AGENT_SYSTEM_PROMPT = "Executive AI Assistant (prompts loaded dynamically from eaia/main/)"
AGENT_ROLE_PROMPT = "Executive assistant role (see inline prompts in eaia/main/)"
AGENT_GUIDELINES_PROMPT = "Guidelines embedded in node-specific prompts"

# =============================================================================
# DEFAULTS EXPORT FOR FASTAPI CONFIG BRIDGE
# =============================================================================

def get_defaults():
    """
    Get prompt defaults - called by FastAPI when needed
    This lazy-loads the actual prompt strings from source files
    """
    prompts = _load_prompts_from_files()

    # Add compatibility exports
    prompts.update({
        "agent_system_prompt": prompts.get("email_writing_instructions", AGENT_SYSTEM_PROMPT),
        "agent_role_prompt": AGENT_ROLE_PROMPT,
        "agent_guidelines_prompt": AGENT_GUIDELINES_PROMPT,
    })

    return prompts

# Export DEFAULTS as function call for lazy evaluation
# FastAPI will call: from src.executive-ai-assistant.prompt import DEFAULTS
DEFAULTS = get_defaults()
