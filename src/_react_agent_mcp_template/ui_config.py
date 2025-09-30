"""
React Agent MCP Template UI Configuration Schema

⚠️  CRITICAL: When duplicating this template:
1. Replace ALL {PLACEHOLDER} values with actual agent details
2. Only include fields that are actually implemented in your agent
3. Update agent-inbox/src/pages/api/config/ endpoints (see MCP_AGENT_CONFIGURATION_GUIDE.md)
4. Test two-way sync in config UI at http://localhost:3004/config

This file defines the configuration interface schema for the Next.js configuration UI.
"""

# Import centralized configuration constants
from src.shared_utils import (
    STANDARD_LLM_MODEL_OPTIONS,
    STANDARD_TIMEZONE_OPTIONS,
    STANDARD_TEMPERATURE_OPTIONS,
    DEFAULT_LLM_MODEL,
    DEFAULT_TIMEZONE
)

CONFIG_INFO = {
    'name': 'React Agent Template',
    'description': 'Template for creating new MCP-based agents',
    'config_type': 'template_config',
    'config_path': 'src/_react_agent_mcp_template/ui_config.py'
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
                'default': 'template',
                'description': 'Internal agent identifier',
                'readonly': True,
                'required': True
            },
            {
                'key': 'agent_display_name',
                'label': 'Display Name',
                'type': 'text',
                'default': 'Template Agent',
                'description': 'Human-readable agent name shown in UI',
                'readonly': True,
                'required': True
            },
            {
                'key': 'agent_description',
                'label': 'Description',
                'type': 'textarea',
                'default': 'Template for creating new MCP-based agents',
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
                'description': 'Template Agent operational status',
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
                'default': DEFAULT_LLM_MODEL,
                'description': 'Primary AI model for agent tasks',
                'options': STANDARD_LLM_MODEL_OPTIONS,
                'required': True,
                'note': 'Uses global ANTHROPIC_API_KEY from environment'
            },
            {
                'key': 'temperature',
                'label': 'Temperature',
                'type': 'select',
                'options': STANDARD_TEMPERATURE_OPTIONS,
                'description': 'Response creativity (0=focused, 1=creative)'
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
                'default': DEFAULT_TIMEZONE,
                'description': 'Your timezone for accurate scheduling and communication',
                'options': STANDARD_TIMEZONE_OPTIONS,
                'required': True
            }
        ]
    },
    {
        'key': 'mcp_integration',
        'label': 'MCP Server Configuration',
        'description': 'API connection settings for external services',
        'fields': [
            {
                'key': 'mcp_env_var',
                'label': 'MCP Environment Variable',
                'type': 'text',
                'readonly': True,
                'default': '',
                'description': 'Name of the environment variable containing the MCP server URL (read-only)',
                'placeholder': 'RUBE_MCP_SERVER, COMPOSIO_MCP_SERVER_slack, PIPEDREAM_MCP_SERVER_gmail, etc.',
                'required': False,
                'note': 'This shows which environment variable is used. Configured in agent code.'
            },
            {
                'key': 'mcp_server_url',
                'label': 'MCP Server URL',
                'type': 'text',
                'description': 'The MCP server URL (editable - updates .env file)',
                'placeholder': 'https://rube.app/mcp, https://mcp.composio.dev/xxx/slack, https://mcp.pipedream.net/xxx/gmail',
                'required': False,
                'note': 'Editing this updates the URL in your .env file'
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
    """Get current configuration values from config.py template"""
    try:
        from .config import LLM_CONFIG, AGENT_NAME, AGENT_DISPLAY_NAME, AGENT_DESCRIPTION, MCP_SERVICE, TEMPLATE_TIMEZONE
        from .prompt import AGENT_SYSTEM_PROMPT, AGENT_ROLE_PROMPT, AGENT_GUIDELINES_PROMPT

        return {
            'agent_identity': {
                'agent_name': AGENT_NAME,
                'agent_display_name': AGENT_DISPLAY_NAME,
                'agent_description': AGENT_DESCRIPTION
            },
            'llm': LLM_CONFIG,
            'user_preferences': {
                'timezone': TEMPLATE_TIMEZONE
            },
            'mcp_integration': {
                # MCP server URL comes from environment variable
            },
            'prompt_templates': {
                'agent_system_prompt': AGENT_SYSTEM_PROMPT,
                'agent_role_prompt': AGENT_ROLE_PROMPT,
                'agent_guidelines_prompt': AGENT_GUIDELINES_PROMPT
            }
        }
    except ImportError:
        # Return template defaults if config doesn't exist yet
        return {
            'agent_identity': {
                'agent_name': 'template',
                'agent_display_name': 'Template Agent',
                'agent_description': 'Template for creating new MCP-based agents'
            },
            'llm': {
                'model': DEFAULT_LLM_MODEL,
                'temperature': 0.2,
                'max_tokens': 2000
            },
            'mcp_integration': {
                # MCP server URL comes from environment variable
            }
        }


def update_config_value(section_key: str, field_key: str, value):
    """Update configuration value in config.py template"""
    # TODO: Implement template config updating logic
    # This would modify the template variables in config.py
    pass