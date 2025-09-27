"""
Main .env Configuration UI Schema
Defines all global environment variables for the config UI
"""

CONFIG_INFO = {
    'name': 'Global Environment',
    'description': 'Core system-wide configuration and API keys',
    'config_type': 'env_file',
    'config_path': '.env'
}

CONFIG_SECTIONS = [
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
            }
        ]
    },
    {
        'key': 'langgraph_system',
        'label': 'LangGraph System',
        'description': 'Core LangGraph and monitoring configuration',
        'fields': [
            {
                'key': 'agent_inbox_graph_id',
                'label': 'Agent Inbox Graph ID',
                'type': 'text',
                'envVar': 'AGENT_INBOX_GRAPH_ID',
                'default': 'agent',
                'description': 'Main graph identifier for agent system'
            },
            {
                'key': 'langgraph_deployment_url',
                'label': 'LangGraph Deployment URL',
                'type': 'text',
                'envVar': 'LANGGRAPH_DEPLOYMENT_URL',
                'default': 'http://localhost:2024',
                'description': 'LangGraph server deployment endpoint'
            },
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
                'description': 'Project name for LangSmith organization'
            }
        ]
    },
    {
        'key': 'google_workspace',
        'label': 'Google Workspace',
        'description': 'Google OAuth and service integration',
        'fields': [
            {
                'key': 'google_oauth_credentials',
                'label': 'Google OAuth Credentials Path',
                'type': 'text',
                'envVar': 'GOOGLE_OAUTH_CREDENTIALS',
                'description': 'Path to Google OAuth JSON credentials file',
                'placeholder': '/path/to/client_secret_xxx.json'
            },
            {
                'key': 'google_client_id',
                'label': 'Google Client ID',
                'type': 'password',
                'envVar': 'GOOGLE_CLIENT_ID',
                'description': 'OAuth 2.0 client ID for Google services',
                'placeholder': 'xxxxx-xxx.apps.googleusercontent.com'
            },
            {
                'key': 'google_client_secret',
                'label': 'Google Client Secret',
                'type': 'password',
                'envVar': 'GOOGLE_CLIENT_SECRET',
                'description': 'OAuth 2.0 client secret for Google services',
                'placeholder': 'GOCSPX-...'
            },
            {
                'key': 'user_google_email',
                'label': 'User Google Email',
                'type': 'text',
                'envVar': 'USER_GOOGLE_EMAIL',
                'description': 'Primary Google account email address',
                'placeholder': 'user@example.com'
            },
            {
                'key': 'gmail_refresh_token',
                'label': 'Gmail Refresh Token',
                'type': 'password',
                'envVar': 'GMAIL_REFRESH_TOKEN',
                'description': 'OAuth refresh token for Gmail access',
                'placeholder': '1//05...'
            },
            {
                'key': 'user_timezone',
                'label': 'User Timezone',
                'type': 'select',
                'envVar': 'USER_TIMEZONE',
                'default': 'America/Toronto',
                'description': 'User timezone for calendar and scheduling',
                'options': [
                    'America/Toronto',
                    'America/Montreal',
                    'America/New_York',
                    'America/Los_Angeles',
                    'America/Chicago',
                    'Europe/London',
                    'Europe/Paris',
                    'Europe/Berlin',
                    'Asia/Tokyo',
                    'Asia/Shanghai',
                    'Australia/Sydney'
                ]
            }
        ]
    },
    {
        'key': 'mcp_servers',
        'label': 'MCP Servers',
        'description': 'Model Context Protocol server endpoints',
        'fields': [
            {
                'key': 'pipedream_google_calendar',
                'label': 'Pipedream Google Calendar MCP',
                'type': 'text',
                'envVar': 'PIPEDREAM_MCP_SERVER',
                'description': 'URL for Google Calendar MCP server',
                'placeholder': 'https://mcp.pipedream.net/xxx/google_calendar'
            },
            {
                'key': 'pipedream_google_gmail',
                'label': 'Pipedream Gmail MCP',
                'type': 'text',
                'envVar': 'PIPEDREAM_MCP_SERVER_google_gmail',
                'description': 'URL for Gmail MCP server',
                'placeholder': 'https://mcp.pipedream.net/xxx/gmail'
            },
            {
                'key': 'pipedream_google_drive',
                'label': 'Pipedream Google Drive MCP',
                'type': 'text',
                'envVar': 'PIPEDREAM_MCP_SERVER_google_drive',
                'description': 'URL for Google Drive MCP server',
                'placeholder': 'https://mcp.pipedream.net/xxx/google_drive'
            },
            {
                'key': 'pipedream_google_sheets',
                'label': 'Pipedream Google Sheets MCP',
                'type': 'text',
                'envVar': 'PIPEDREAM_MCP_SERVER_google_sheets',
                'description': 'URL for Google Sheets MCP server',
                'placeholder': 'https://mcp.pipedream.net/xxx/google_sheets'
            },
            {
                'key': 'pipedream_google_docs',
                'label': 'Pipedream Google Docs MCP',
                'type': 'text',
                'envVar': 'PIPEDREAM_MCP_SERVER_google_docs',
                'description': 'URL for Google Docs MCP server',
                'placeholder': 'https://mcp.pipedream.net/xxx/google_docs'
            },
            {
                'key': 'mcp_server_google_workspace',
                'label': 'Local Google Workspace MCP',
                'type': 'text',
                'envVar': 'MCP_SERVER_GOOGLE_WORKSPACE',
                'default': 'http://localhost:3000/mcp',
                'description': 'Local Google Workspace MCP server URL',
                'readonly': True
            }
        ]
    },
    {
        'key': 'system_settings',
        'label': 'System Settings',
        'description': 'Environment and logging configuration',
        'fields': [
            {
                'key': 'environment',
                'label': 'Environment',
                'type': 'select',
                'envVar': 'ENVIRONMENT',
                'default': 'development',
                'description': 'Current environment mode',
                'options': ['development', 'staging', 'production'],
                'readonly': True
            },
            {
                'key': 'log_level',
                'label': 'Log Level',
                'type': 'select',
                'envVar': 'LOG_LEVEL',
                'default': 'INFO',
                'description': 'System logging level',
                'options': ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                'readonly': True
            },
            {
                'key': 'force_langgraph_api',
                'label': 'Force LangGraph API',
                'type': 'boolean',
                'envVar': 'FORCE_LANGGRAPH_API',
                'default': True,
                'description': 'Force use of LangGraph API mode',
                'readonly': True
            },
            {
                'key': 'use_enhanced_calendar_agent',
                'label': 'Use Enhanced Calendar Agent',
                'type': 'boolean',
                'envVar': 'USE_ENHANCED_CALENDAR_AGENT',
                'default': True,
                'description': 'Enable the enhanced calendar agent features'
            }
        ]
    },
    {
        'key': 'third_party_apis',
        'label': 'Third-Party APIs',
        'description': 'Additional service integrations',
        'fields': [
            {
                'key': 'linkedin_email',
                'label': 'LinkedIn Email',
                'type': 'text',
                'envVar': 'LINKEDIN_EMAIL',
                'description': 'LinkedIn account email for job search features',
                'placeholder': 'user@example.com'
            },
            {
                'key': 'linkedin_password',
                'label': 'LinkedIn Password',
                'type': 'password',
                'envVar': 'LINKEDIN_PASSWORD',
                'description': 'LinkedIn account password (encrypted storage)',
                'warning': 'Stored securely for job search automation'
            },
            {
                'key': 'supabase_url',
                'label': 'Supabase URL',
                'type': 'text',
                'envVar': 'NEXT_PUBLIC_SUPABASE_URL',
                'description': 'Supabase project URL for data storage',
                'placeholder': 'https://xxx.supabase.co'
            },
            {
                'key': 'supabase_anon_key',
                'label': 'Supabase Anonymous Key',
                'type': 'password',
                'envVar': 'NEXT_PUBLIC_SUPABASE_ANON_KEY',
                'description': 'Supabase anonymous access key',
                'placeholder': 'eyJhbGciOiJIUzI1NiIs...'
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