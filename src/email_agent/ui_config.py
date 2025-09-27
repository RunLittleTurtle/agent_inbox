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
    'name': 'Email',
    'description': 'MCP-based agent for email management and Gmail operations',
    'config_type': 'template_config',
    'config_path': 'src/email/config.py'
}

CONFIG_SECTIONS = [
    {
        'key': 'agent_identity',
        'label': 'Agent Identity',
        'description': 'Basic agent identification and branding',
        'fields': [
            {
                'key': 'agent_name',
                'label': 'Agent Name (Internal)',
                'type': 'text',
                'default': 'email',
                'description': 'Internal agent identifier (lowercase, no spaces)',
                'placeholder': 'gmail, sheets, drive',
                'required': True,
                'validation': {'pattern': '^[a-z_]+$'}
            },
            {
                'key': 'agent_display_name',
                'label': 'Display Name',
                'type': 'text',
                'default': 'Email',
                'description': 'Human-readable agent name shown in UI',
                'placeholder': 'Gmail Agent, Google Sheets, Google Drive',
                'required': True
            },
            {
                'key': 'agent_description',
                'label': 'Description',
                'type': 'textarea',
                'default': 'email management and Gmail operations',
                'description': 'Brief description of agent capabilities',
                'placeholder': 'email management, spreadsheet operations, file storage',
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
            },
            {
                'key': 'max_tokens',
                'label': 'Max Tokens',
                'type': 'number',
                'default': 2000,
                'description': 'Maximum tokens per response',
                'validation': {'min': 100, 'max': 8192}
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
                'envVar': 'PIPEDREAM_MCP_SERVER_google_gmail',
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
                'agent_name': 'email',
                'agent_display_name': 'Email',
                'agent_description': 'email management and Gmail operations'
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