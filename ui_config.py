"""
Main .env Configuration UI Schema
Defines all global environment variables for the config UI
"""

# Import centralized configuration constants
from src.shared_utils import (
    STANDARD_TIMEZONE_OPTIONS,
    DEFAULT_TIMEZONE
)

CONFIG_INFO = {
    'name': 'Global Environment',
    'description': 'Core system-wide configuration and API keys',
    'config_type': 'env_file',
    'config_path': '.env'
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
                'description': 'API key for GPT models (backup)',
                'placeholder': 'sk-proj-...'
            },
            {
                'key': 'whisper_transcription_mode',
                'label': 'Voice Transcription Mode',
                'type': 'select',
                'envVar': 'WHISPER_TRANSCRIPTION_MODE',
                'options': WHISPER_TRANSCRIPTION_OPTIONS,
                'default': 'api',
                'description': 'API: Fast cloud transcription (recommended). Browser: Downloads 450MB model once, works offline.',
                'note': 'Browser mode downloads model on first use (~1-2 min). Persists in browser cache across sessions.',
                'warning': 'If browser cache is cleared, you may need to re-download the model or switch back to API mode.'
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
                'label': 'LangSmith API Key',
                'type': 'password',
                'envVar': 'LANGSMITH_API_KEY',
                'description': 'API key for LangSmith monitoring and tracing',
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
