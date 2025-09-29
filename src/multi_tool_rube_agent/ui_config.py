"""
React Agent MCP Template UI Configuration Schema

⚠️  CRITICAL: When duplicating this template:
1. Replace ALL {PLACEHOLDER} values with actual agent details
2. Only include fields that are actually implemented in your agent
3. Update agent-inbox/src/pages/api/config/ endpoints (see MCP_AGENT_CONFIGURATION_GUIDE.md)
4. Test two-way sync in config UI at http://localhost:3004/config

This file defines the configuration interface schema for the Next.js configuration UI.
"""

# STANDARD OPTIONS LISTS
# These are Python placeholders that get replaced by TypeScript at runtime
# The ACTUAL master list is defined in: config-app/src/app/api/config/agents/route.ts
# That TypeScript file replaces these variable names with the actual arrays when parsing
STANDARD_LLM_MODEL_OPTIONS = []
STANDARD_TIMEZONE_OPTIONS = []

CONFIG_INFO = {
    'name': 'Multi-Tool Rube Agent',
    'description': 'Universal agent with access to 500+ apps through Rube MCP server',
    'config_type': 'agent_config',
    'config_path': 'src/multi_tool_rube_agent/ui_config.py'
}

CONFIG_SECTIONS = [
    {
        'key': 'agent_identity',
        'label': 'Agent Identity',
        'description': 'Agent identification and status',
        'fields': [
            {
                'key': 'agent_name',
                'label': 'Agent Name',
                'type': 'text',
                'default': 'multi_tool_rube',
                'description': 'Internal agent identifier',
                'readonly': True,
                'required': True
            },
            {
                'key': 'agent_display_name',
                'label': 'Display Name',
                'type': 'text',
                'default': 'Multi-Tool Rube Agent',
                'description': 'Human-readable agent name shown in UI',
                'readonly': True,
                'required': True
            },
            {
                'key': 'agent_description',
                'label': 'Description',
                'type': 'textarea',
                'default': 'Universal agent with access to 500+ apps through Rube MCP server',
                'description': 'Brief description of agent capabilities',
                'readonly': True,
                'rows': 3,
                'required': True
            },
            {
                'key': 'agent_status',
                'label': 'Agent Status',
                'type': 'select',
                'default': 'disabled',
                'description': 'Multi-Tool Rube Agent operational status',
                'options': ['active', 'disabled'],
                'required': True
            }
        ]
    },
    {
        'key': 'llm',
        'label': 'Language Model',
        'description': 'AI model configuration for agent operations',
        'fields': [
            {
                'key': 'model',
                'label': 'Model Name',
                'type': 'select',
                'default': 'claude-sonnet-4-20250514',
                'description': 'Primary AI model for agent tasks',
                'options': STANDARD_LLM_MODEL_OPTIONS,
                'required': True,
                'note': 'Uses global ANTHROPIC_API_KEY from environment'
            },
            {
                'key': 'temperature',
                'label': 'Temperature',
                'type': 'number',
                'default': 0.2,
                'description': 'Model creativity level (0.0 = focused, 1.0 = creative)',
                'validation': {'min': 0.0, 'max': 1.0, 'step': 0.1}
            }
        ]
    },
    {
        'key': 'user_preferences',
        'label': 'User Preferences',
        'description': 'Personal settings and preferences',
        'fields': [
            {
                'key': 'timezone',
                'label': 'Timezone',
                'type': 'select',
                'default': 'America/Toronto',
                'description': 'Your timezone for accurate scheduling and communication',
                'options': STANDARD_TIMEZONE_OPTIONS,
                'required': True
            }
        ]
    },
    {
        'key': 'mcp_integration',
        'label': 'Rube MCP Server Configuration',
        'description': 'Universal MCP server providing access to 500+ applications',
        'fields': [
            {
                'key': 'mcp_env_var',
                'label': 'Rube Environment Variable',
                'type': 'text',
                'readonly': True,
                'default': 'RUBE_MCP_SERVER',
                'description': 'Environment variable for Rube MCP server URL (read-only)',
                'placeholder': 'RUBE_MCP_SERVER',
                'required': False,
                'note': 'Rube uses a single unified MCP server for all 500+ applications'
            },
            {
                'key': 'mcp_server_url',
                'label': 'Rube MCP Server URL',
                'type': 'text',
                'description': 'The Rube MCP server URL (editable - updates .env file)',
                'placeholder': 'https://rube.app/mcp',
                'default': 'https://rube.app/mcp',
                'required': True,
                'note': 'Rube provides unified access to 500+ apps through OAuth 2.1'
            }
        ]
    },
    {
        'key': 'prompt_templates',
        'label': 'System Prompts',
        'description': 'Customize agent behavior through system prompts',
        'card_style': 'orange',
        'fields': [
            {
                'key': 'agent_system_prompt',
                'label': 'System Prompt',
                'type': 'textarea',
                'description': 'Main system prompt that defines agent behavior',
                'placeholder': 'Enter the complete system prompt...',
                'required': True,
                'rows': 15
            }
        ]
    }
]


def get_current_config():
    """Get current configuration values from config.py"""
    try:
        from .config import LLM_CONFIG, AGENT_NAME, AGENT_DISPLAY_NAME, AGENT_DESCRIPTION, MCP_ENV_VAR, MCP_SERVER_URL
        from .prompt import AGENT_SYSTEM_PROMPT

        return {
            'agent_identity': {
                'agent_name': AGENT_NAME,
                'agent_display_name': AGENT_DISPLAY_NAME,
                'agent_description': AGENT_DESCRIPTION
            },
            'llm': LLM_CONFIG,
            'mcp_integration': {
                'mcp_env_var': MCP_ENV_VAR,
                'mcp_server_url': MCP_SERVER_URL
            },
            'prompt_templates': {
                'agent_system_prompt': AGENT_SYSTEM_PROMPT
            }
        }
    except ImportError:
        # Return defaults if config doesn't exist yet
        return {
            'agent_identity': {
                'agent_name': 'multi_tool_rube',
                'agent_display_name': 'Multi-Tool Rube Agent',
                'agent_description': 'Universal agent with access to 500+ apps through Rube MCP server'
            },
            'llm': {
                'model': 'claude-sonnet-4-20250514',
                'temperature': 0.2,
                'max_tokens': 2000
            },
            'mcp_integration': {
                'mcp_env_var': 'RUBE_MCP_SERVER',
                'mcp_server_url': 'https://rube.app/mcp'
            }
        }


def update_config_value(section_key: str, field_key: str, value):
    """Update configuration value in config.py template"""
    # TODO: Implement template config updating logic
    # This would modify the template variables in config.py
    pass