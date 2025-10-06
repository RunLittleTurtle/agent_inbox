"""
Main .env Configuration UI Schema
Defines all global environment variables for the config UI
"""

# Import centralized configuration constants
from shared_utils import (
    STANDARD_TIMEZONE_OPTIONS,
    DEFAULT_TIMEZONE
)

CONFIG_INFO = {
    'name': 'Global Environment',
    'description': 'Core system-wide configuration and API keys',
    'config_type': 'env_file',
    'config_path': 'src/ui_config.py'
}

CONFIG_SECTIONS = [
    {
        'key': 'user_preferences',
        'label': 'User Preferences',
        'description': 'Personal settings and preferences',
        'fields': [
            {
                'key': 'user_timezone',
                'label': 'Timezone',
                'type': 'select',
                'envVar': 'USER_TIMEZONE',
                'default': DEFAULT_TIMEZONE,
                'description': 'User timezone for llms context',
                'options': STANDARD_TIMEZONE_OPTIONS,
                'required': True
            }
        ]
    },
    {
        'key': 'ai_models',
        'label': 'AI Model APIs',
        'description': 'API keys for AI language models',
        'fields': [
            {
                'key': 'anthropic_api_key',
                'label': 'Anthropic API Key',
                'type': 'password',
                'envVar': 'ANTHROPIC_API_KEY',
                'description': 'API key for Claude models (primary)',
                'required': True,
                'placeholder': 'sk-ant-api03-...'
            },
            {
                'key': 'openai_api_key',
                'label': 'OpenAI API Key',
                'type': 'password',
                'envVar': 'OPENAI_API_KEY',
                'description': 'API key for GPT models and voice transcription',
                'placeholder': 'sk-proj-...'
            }
        ]
    },
    {
        'key': 'langgraph_system',
        'label': 'LangGraph System',
        'description': 'Core LangGraph and monitoring configuration',
        'fields': [
            {
                'key': 'langsmith_api_key',
                'label': 'LangSmith API Key (Developer Only)',
                'type': 'password',
                'envVar': 'LANGSMITH_API_KEY',
                'description': 'API key for LangSmith monitoring and tracing (for admin/developer use)',
                'placeholder': 'lsv2_pt_...'
            },
            {
                'key': 'langchain_project',
                'label': 'LangChain Project Name',
                'type': 'text',
                'envVar': 'LANGCHAIN_PROJECT',
                'default': 'ambient-email-agent',
                'readonly': True,
                'description': 'Project name for LangSmith organization (read-only - changing this can break things)'
            }
        ]
    },
    {
        'key': 'langfuse_system',
        'label': 'LangFuse (User Tracing)',
        'description': 'Per-user trace visibility and analytics - users see only their own traces',
        'fields': [
            {
                'key': 'langfuse_public_key',
                'label': 'LangFuse Public Key',
                'type': 'text',
                'envVar': 'LANGFUSE_PUBLIC_KEY',
                'description': 'Public API key for LangFuse tracing (safe to expose)',
                'placeholder': 'pk-lf-...',
                'note': 'Get from LangFuse dashboard: Settings → API Keys'
            },
            {
                'key': 'langfuse_secret_key',
                'label': 'LangFuse Secret Key',
                'type': 'password',
                'envVar': 'LANGFUSE_SECRET_KEY',
                'description': 'Secret API key for LangFuse tracing (keep secure)',
                'placeholder': 'sk-lf-...',
                'note': 'Keep this secret - stored encrypted in database'
            },
            {
                'key': 'langfuse_host',
                'label': 'LangFuse Host URL',
                'type': 'text',
                'envVar': 'LANGFUSE_HOST',
                'default': 'https://cloud.langfuse.com',
                'description': 'LangFuse server URL (cloud or self-hosted)',
                'placeholder': 'https://cloud.langfuse.com',
                'note': 'Use https://cloud.langfuse.com for cloud, or your Railway URL for self-hosted'
            }
        ]
    },
    {
        'key': 'google_workspace',
        'label': 'Google Workspace OAuth (Admin)',
        'description': 'Global OAuth credentials - configure once, all users authenticate through these credentials',
        'fields': [
            {
                'key': 'google_client_id',
                'label': 'Google Client ID',
                'type': 'text',
                'envVar': 'GOOGLE_CLIENT_ID',
                'description': 'OAuth 2.0 client ID from your Google Cloud project',
                'placeholder': 'xxx.apps.googleusercontent.com',
                'required': True,
                'note': 'From Google Cloud Console → APIs & Services → Credentials'
            },
            {
                'key': 'google_client_secret',
                'label': 'Google Client Secret',
                'type': 'password',
                'envVar': 'GOOGLE_CLIENT_SECRET',
                'description': 'OAuth 2.0 client secret from your Google Cloud project',
                'placeholder': 'GOCSPX-...',
                'required': True,
                'note': 'Keep this secret - only visible to administrators'
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
        'key': 'langgraph_deployment',
        'label': 'LangGraph Deployment URLs',
        'description': 'Production deployment URLs for Agent Inbox integration',
        'fields': [
            {
                'key': 'agent_inbox_deployment_url',
                'label': 'Agent Inbox Deployment URL',
                'type': 'text',
                'envVar': 'AGENT_INBOX_DEPLOYMENT_URL',
                'default': 'https://multi-agent-app-1d1e061875eb5640a47e3bb201edb076.us.langgraph.app',
                'readonly': True,
                'description': 'LangGraph deployment URL for agent inbox (read-only)',
                'placeholder': 'https://multi-agent-app-xxx.us.langgraph.app',
                'required': True,
                'note': 'This URL is auto-populated in Agent Inbox UI for default inboxes'
            },
            {
                'key': 'executive_deployment_url',
                'label': 'Executive AI Deployment URL',
                'type': 'text',
                'envVar': 'EXECUTIVE_DEPLOYMENT_URL',
                'default': 'https://multi-agent-app-1d1e061875eb5640a47e3bb201edb076.us.langgraph.app',
                'readonly': True,
                'description': 'LangGraph deployment URL for executive assistant (read-only)',
                'placeholder': 'https://multi-agent-app-xxx.us.langgraph.app',
                'required': True,
                'note': 'This URL is auto-populated in Agent Inbox UI for default inboxes'
            }
        ]
    }
]


def get_env_value(env_var: str):
    """Get current value from .env file"""
    import os
    from dotenv import load_dotenv
    load_dotenv()
    return os.getenv(env_var, '')


def update_env_value(env_var: str, value: str):
    """Update value in .env file"""
    import os
    from pathlib import Path

    env_path = Path('.env')
    if not env_path.exists():
        env_path.touch()

    # Read current .env content
    lines = []
    if env_path.exists():
        with open(env_path, 'r') as f:
            lines = f.readlines()

    # Find and update or add the variable
    updated = False
    for i, line in enumerate(lines):
        if line.strip().startswith(f'{env_var}='):
            lines[i] = f'{env_var}={value}\n'
            updated = True
            break

    if not updated:
        lines.append(f'{env_var}={value}\n')

    # Write back to .env
    with open(env_path, 'w') as f:
        f.writelines(lines)


def get_current_config():
    """Get current configuration values from .env"""
    config_data = {}
    for section in CONFIG_SECTIONS:
        section_data = {}
        for field in section['fields']:
            if 'envVar' in field:
                section_data[field['key']] = get_env_value(field['envVar'])
        config_data[section['key']] = section_data
    return config_data
