"""
React Agent MCP Template UI Configuration Schema

⚠️  CRITICAL: When duplicating this template:
1. Replace ALL {PLACEHOLDER} values with actual agent details
2. Only include fields that are actually implemented in your agent
3. Update agent-inbox/src/pages/api/config/ endpoints (see MCP_AGENT_CONFIGURATION_GUIDE.md)
4. Test two-way sync in config UI at http://localhost:3004/config

This file defines the configuration interface schema for the Next.js configuration UI.
"""

CONFIG_INFO = {
    'name': 'React Agent Template',
    'description': 'Template for creating new MCP-based agents',
    'config_type': 'template_config',
    'config_path': 'src/_react_agent_mcp_template/config.py'
}

CONFIG_SECTIONS = [
    {
        'key': 'agent_identity',
        'label': 'Agent Identity',
        'description': 'Agent identification and status',
        'fields': [
            {
                'key': 'agent_display_name',
                'label': 'Display Name',
                'type': 'text',
                'default': 'Template Agent',
                'description': 'Human-readable agent name shown in UI',
                'placeholder': 'Gmail Agent, Google Sheets, Google Drive',
                'required': True
            },
            {
                'key': 'agent_description',
                'label': 'Description',
                'type': 'textarea',
                'default': 'Template for creating new MCP-based agents',
                'description': 'Brief description of agent capabilities',
                'placeholder': 'email management, spreadsheet operations, file storage',
                'required': True
            },
            {
                'key': 'agent_status',
                'label': 'Status',
                'type': 'select',
                'default': 'disabled',
                'description': 'Enable or disable this agent',
                'options': ['active', 'disabled'],
                'required': True
            },
            {
                'key': 'mcp_service',
                'label': 'MCP Service Name',
                'type': 'text',
                'default': 'template_service',
                'description': 'MCP service identifier (used in environment variable)',
                'placeholder': 'google_gmail, google_sheets, google_drive',
                'required': True,
                'validation': {'pattern': '^[a-z_]+$'},
                'note': 'This determines the environment variable: PIPEDREAM_MCP_SERVER_{service_name}'
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
                'options': [
                    'claude-sonnet-4-20250514',
                    'claude-3-5-sonnet-20241022',
                    'gpt-4o',
                    'gpt-4o-mini'
                ],
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
        'key': 'agent_configuration',
        'label': 'Agent Configuration',
        'description': 'Agent behavior and prompt settings',
        'fields': [
            {
                'key': 'agent_prompt',
                'label': 'System Prompt',
                'type': 'textarea',
                'default': 'You are a helpful AI assistant. Use the available tools to help users efficiently.',
                'description': 'Main system prompt that defines agent behavior',
                'placeholder': 'Enter the system prompt for your agent...',
                'required': True
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
                'default': 'global',
                'description': 'Your timezone - select Use Global for system default',
                'options': [
                    'global',
                    'America/New_York',
                    'America/Chicago',
                    'America/Denver',
                    'America/Los_Angeles',
                    'America/Toronto',
                    'America/Montreal',
                    'Europe/London',
                    'Europe/Paris',
                    'Europe/Berlin',
                    'Asia/Tokyo',
                    'Asia/Shanghai',
                    'Asia/Singapore',
                    'Australia/Sydney'
                ],
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
                'key': 'mcp_server_url',
                'label': 'MCP Server URL',
                'type': 'text',
                'envVar': 'PIPEDREAM_MCP_SERVER',
                'description': 'URL for the MCP server endpoint',
                'placeholder': 'https://mcp.pipedream.net/xxx/service_name',
                'required': True,
                'note': 'Environment variable name depends on your MCP service'
            }
        ]
    }
]


def get_current_config():
    """Get current configuration values from config.py template"""
    try:
        from .config import LLM_CONFIG, AGENT_NAME, AGENT_DISPLAY_NAME, AGENT_DESCRIPTION, MCP_SERVICE

        return {
            'agent_identity': {
                'agent_name': AGENT_NAME,
                'agent_display_name': AGENT_DISPLAY_NAME,
                'agent_description': AGENT_DESCRIPTION
            },
            'llm': LLM_CONFIG,
            'mcp_integration': {
                # MCP server URL comes from environment variable
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
                'model': 'claude-sonnet-4-20250514',
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