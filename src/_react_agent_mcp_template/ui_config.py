"""
React Agent MCP Template UI Configuration Schema
Standardized config interface for future agents based on the template
"""

CONFIG_INFO = {
    'name': '{AGENT_DISPLAY_NAME}',
    'description': 'MCP-based agent for {AGENT_DESCRIPTION}',
    'config_type': 'template_config',
    'config_path': 'src/{AGENT_NAME}/config.py'
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
                'default': '{AGENT_NAME}',
                'description': 'Internal agent identifier (lowercase, no spaces)',
                'placeholder': 'gmail, sheets, drive',
                'required': True,
                'validation': {'pattern': '^[a-z_]+$'}
            },
            {
                'key': 'agent_display_name',
                'label': 'Display Name',
                'type': 'text',
                'default': '{AGENT_DISPLAY_NAME}',
                'description': 'Human-readable agent name shown in UI',
                'placeholder': 'Gmail Agent, Google Sheets, Google Drive',
                'required': True
            },
            {
                'key': 'agent_description',
                'label': 'Description',
                'type': 'textarea',
                'default': '{AGENT_DESCRIPTION}',
                'description': 'Brief description of agent capabilities',
                'placeholder': 'email management, spreadsheet operations, file storage',
                'required': True
            },
            {
                'key': 'mcp_service',
                'label': 'MCP Service Name',
                'type': 'text',
                'default': '{MCP_SERVICE}',
                'description': 'MCP service identifier for API connections',
                'placeholder': 'google_gmail, google_sheets, google_drive',
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
                'note': 'Uses global ANTHROPIC_API_KEY from main .env'
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
                'key': 'streaming',
                'label': 'Enable Streaming',
                'type': 'boolean',
                'default': False,
                'description': 'Enable streaming responses (disable for LangGraph compatibility)'
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
        'label': 'MCP Integration',
        'description': 'Model Context Protocol server configuration',
        'fields': [
            {
                'key': 'mcp_server_url',
                'label': 'MCP Server URL',
                'type': 'text',
                'envVar': 'PIPEDREAM_MCP_SERVER_{MCP_SERVICE}',
                'description': 'URL for the MCP server endpoint',
                'placeholder': 'https://mcp.pipedream.net/xxx/service_name',
                'required': True,
                'note': 'Uses environment variable based on MCP service name'
            },
            {
                'key': 'mcp_timeout',
                'label': 'MCP Request Timeout (seconds)',
                'type': 'number',
                'default': 30,
                'description': 'Timeout for MCP server requests',
                'validation': {'min': 10, 'max': 120}
            },
            {
                'key': 'mcp_retry_attempts',
                'label': 'MCP Retry Attempts',
                'type': 'number',
                'default': 3,
                'description': 'Number of retry attempts for MCP failures',
                'validation': {'min': 1, 'max': 10}
            },
            {
                'key': 'enable_mcp_caching',
                'label': 'Enable MCP Caching',
                'type': 'boolean',
                'default': True,
                'description': 'Cache MCP responses for better performance'
            },
            {
                'key': 'mcp_cache_ttl',
                'label': 'Cache TTL (minutes)',
                'type': 'number',
                'default': 15,
                'description': 'How long to cache MCP responses',
                'validation': {'min': 1, 'max': 1440}
            }
        ]
    },
    {
        'key': 'timezone_settings',
        'label': 'Timezone & Context',
        'description': 'Time and context configuration for agent operations',
        'fields': [
            {
                'key': 'user_timezone',
                'label': 'User Timezone',
                'type': 'select',
                'envVar': 'USER_TIMEZONE',
                'default': 'America/Toronto',
                'description': 'User timezone for time-aware operations',
                'options': [
                    'America/Toronto',
                    'America/Montreal',
                    'America/New_York',
                    'America/Los_Angeles',
                    'Europe/London',
                    'Europe/Paris',
                    'Asia/Tokyo',
                    'Asia/Shanghai',
                    'Australia/Sydney'
                ],
                'note': 'Synced with global timezone setting'
            },
            {
                'key': 'enable_context_awareness',
                'label': 'Enable Context Awareness',
                'type': 'boolean',
                'default': True,
                'description': 'Include current time and date in agent context'
            },
            {
                'key': 'context_refresh_interval',
                'label': 'Context Refresh Interval (minutes)',
                'type': 'number',
                'default': 30,
                'description': 'How often to refresh time context',
                'validation': {'min': 1, 'max': 1440}
            }
        ]
    },
    {
        'key': 'behavior',
        'label': 'Agent Behavior',
        'description': 'Agent response patterns and behavior configuration',
        'fields': [
            {
                'key': 'response_style',
                'label': 'Response Style',
                'type': 'select',
                'default': 'professional',
                'description': 'Default tone and style for agent responses',
                'options': ['casual', 'professional', 'technical', 'friendly']
            },
            {
                'key': 'enable_proactive_suggestions',
                'label': 'Proactive Suggestions',
                'type': 'boolean',
                'default': True,
                'description': 'Allow agent to make proactive suggestions'
            },
            {
                'key': 'enable_error_recovery',
                'label': 'Enable Error Recovery',
                'type': 'boolean',
                'default': True,
                'description': 'Attempt to recover from API errors gracefully'
            },
            {
                'key': 'max_conversation_length',
                'label': 'Max Conversation Length',
                'type': 'number',
                'default': 20,
                'description': 'Maximum number of messages to retain in context',
                'validation': {'min': 5, 'max': 100}
            },
            {
                'key': 'enable_handoff_tools',
                'label': 'Enable Handoff Tools',
                'type': 'boolean',
                'default': False,
                'description': 'Allow agent to use handoff tools (disable for supervisor pattern)'
            }
        ]
    },
    {
        'key': 'features',
        'label': 'Features',
        'description': 'Enable/disable agent features',
        'fields': [
            {
                'key': 'enable_tool_validation',
                'label': 'Tool Validation',
                'type': 'boolean',
                'default': True,
                'description': 'Validate tool inputs before execution'
            },
            {
                'key': 'enable_response_formatting',
                'label': 'Response Formatting',
                'type': 'boolean',
                'default': True,
                'description': 'Apply consistent formatting to agent responses'
            },
            {
                'key': 'enable_batch_operations',
                'label': 'Batch Operations',
                'type': 'boolean',
                'default': False,
                'description': 'Support batch processing of multiple requests'
            },
            {
                'key': 'enable_async_processing',
                'label': 'Async Processing',
                'type': 'boolean',
                'default': True,
                'description': 'Use asynchronous processing for better performance'
            }
        ]
    },
    {
        'key': 'debugging',
        'label': 'Debugging & Monitoring',
        'description': 'Debug and monitoring configuration',
        'fields': [
            {
                'key': 'debug_mode',
                'label': 'Debug Mode',
                'type': 'boolean',
                'default': False,
                'description': 'Enable detailed debug logging'
            },
            {
                'key': 'log_tool_calls',
                'label': 'Log Tool Calls',
                'type': 'boolean',
                'default': True,
                'description': 'Log all tool calls and responses'
            },
            {
                'key': 'log_mcp_requests',
                'label': 'Log MCP Requests',
                'type': 'boolean',
                'default': False,
                'description': 'Log all MCP server requests and responses'
            },
            {
                'key': 'enable_performance_monitoring',
                'label': 'Performance Monitoring',
                'type': 'boolean',
                'default': True,
                'description': 'Track performance metrics and response times'
            },
            {
                'key': 'log_level',
                'label': 'Log Level',
                'type': 'select',
                'default': 'INFO',
                'description': 'Logging level for agent operations',
                'options': ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            }
        ]
    }
]


def get_current_config():
    """Get current configuration values from config.py template"""
    try:
        from .config import LLM_CONFIG, AGENT_NAME, AGENT_DISPLAY_NAME, AGENT_DESCRIPTION, MCP_SERVICE, get_current_context

        # Get current context for timezone info
        context = get_current_context()

        return {
            'agent_identity': {
                'agent_name': AGENT_NAME,
                'agent_display_name': AGENT_DISPLAY_NAME,
                'agent_description': AGENT_DESCRIPTION,
                'mcp_service': MCP_SERVICE
            },
            'llm': LLM_CONFIG,
            'mcp_integration': {
                'mcp_timeout': 30,
                'mcp_retry_attempts': 3,
                'enable_mcp_caching': True,
                'mcp_cache_ttl': 15
            },
            'timezone_settings': {
                'user_timezone': context.get('timezone_name', 'America/Toronto'),
                'enable_context_awareness': True,
                'context_refresh_interval': 30
            },
            'behavior': {
                'response_style': 'professional',
                'enable_proactive_suggestions': True,
                'enable_error_recovery': True,
                'max_conversation_length': 20,
                'enable_handoff_tools': False
            },
            'features': {
                'enable_tool_validation': True,
                'enable_response_formatting': True,
                'enable_batch_operations': False,
                'enable_async_processing': True
            },
            'debugging': {
                'debug_mode': False,
                'log_tool_calls': True,
                'log_mcp_requests': False,
                'enable_performance_monitoring': True,
                'log_level': 'INFO'
            }
        }
    except ImportError:
        # Return template defaults if config doesn't exist yet
        return {
            'agent_identity': {
                'agent_name': '{AGENT_NAME}',
                'agent_display_name': '{AGENT_DISPLAY_NAME}',
                'agent_description': '{AGENT_DESCRIPTION}',
                'mcp_service': '{MCP_SERVICE}'
            },
            'llm': {
                'model': 'claude-sonnet-4-20250514',
                'temperature': 0.2,
                'streaming': False,
                'max_tokens': 2000
            },
            'mcp_integration': {
                'mcp_timeout': 30,
                'mcp_retry_attempts': 3,
                'enable_mcp_caching': True,
                'mcp_cache_ttl': 15
            },
            'timezone_settings': {
                'user_timezone': 'America/Toronto',
                'enable_context_awareness': True,
                'context_refresh_interval': 30
            },
            'behavior': {
                'response_style': 'professional',
                'enable_proactive_suggestions': True,
                'enable_error_recovery': True,
                'max_conversation_length': 20,
                'enable_handoff_tools': False
            },
            'features': {
                'enable_tool_validation': True,
                'enable_response_formatting': True,
                'enable_batch_operations': False,
                'enable_async_processing': True
            },
            'debugging': {
                'debug_mode': False,
                'log_tool_calls': True,
                'log_mcp_requests': False,
                'enable_performance_monitoring': True,
                'log_level': 'INFO'
            }
        }


def update_config_value(section_key: str, field_key: str, value):
    """Update configuration value in config.py template"""
    # TODO: Implement template config updating logic
    # This would modify the template variables in config.py
    pass