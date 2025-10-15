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
        'key': 'google_workspace',
        'label': 'Google Workspace Integration',
        'description': 'Connect your Google account to enable Gmail, Calendar, and other Google services',
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
        'key': 'langgraph_system',
        'label': 'LangGraph System',
        'description': 'Core LangGraph and monitoring configuration',
        'fields': [
            {
                'key': 'langsmith_api_key',
                'label': 'LangSmith API Key (Developer Only)',
                'type': 'password',
                'envVar': 'LANGSMITH_API_KEY',
                'readonly': True,
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
