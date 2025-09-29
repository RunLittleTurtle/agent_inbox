"""
Shared Configuration Constants
Standardized values used across all agent configurations
"""

# Standardized LLM Model Options
# Based on Executive AI Assistant's comprehensive model list
STANDARD_LLM_MODEL_OPTIONS = [
    'claude-sonnet-4-20250514',      # Balanced performance and cost
    'claude-3-5-haiku-20241022',     # Fast, cost-effective for simple tasks
    'gpt-5',                         # Advanced capabilities, expensive
    'gpt-4o',                        # Balanced performance, good reasoning
    'o3',                            # Specialized reasoning, very expensive
    'claude-opus-4-1-20250805'       # Highest quality, most expensive
]

# Model descriptions for consistent tooltips/help text
MODEL_DESCRIPTIONS = {
    'claude-sonnet-4-20250514': 'Balanced performance and cost',
    'claude-3-5-haiku-20241022': 'Fast, cost-effective for simple tasks',
    'gpt-5': 'Advanced capabilities, expensive',
    'gpt-4o': 'Balanced performance, good reasoning',
    'o3': 'Specialized reasoning, very expensive',
    'claude-opus-4-1-20250805': 'Highest quality, most expensive'
}

# Default model selection
DEFAULT_LLM_MODEL = 'claude-sonnet-4-20250514'