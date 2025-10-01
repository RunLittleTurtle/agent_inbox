"""
Calendar Agent UI Configuration Schema
Optimized configuration for calendar agent settings
"""

# Import centralized configuration constants
from shared_utils import (
    STANDARD_LLM_MODEL_OPTIONS,
    STANDARD_TIMEZONE_OPTIONS,
    STANDARD_TEMPERATURE_OPTIONS,
    DEFAULT_LLM_MODEL,
    DEFAULT_TIMEZONE
)

CONFIG_INFO = {
    'name': 'Calendar Agent',
    'description': 'Google Calendar management and scheduling',
    'config_type': 'calendar_config',
    'config_path': 'src/calendar_agent/config.py'
}

CONFIG_SECTIONS = [
    {
        'key': 'agent_identity',
        'label': 'Agent Identity',
        'description': 'Calendar agent identification and status',
        'fields': [
            {
                'key': 'agent_name',
                'label': 'Agent Name',
                'type': 'text',
                'default': 'calendar',
                'description': 'Internal agent identifier',
                'readonly': True,
                'required': True
            },
            {
                'key': 'agent_display_name',
                'label': 'Display Name',
                'type': 'text',
                'default': 'Calendar Agent',
                'description': 'Human-readable agent name shown in UI',
                'readonly': True,
                'required': True
            },
            {
                'key': 'agent_description',
                'label': 'Description',
                'type': 'textarea',
                'default': 'Google Calendar management and scheduling',
                'description': 'Brief description of agent capabilities',
                'readonly': True,
                'rows': 3,
                'required': True
            },
            {
                'key': 'agent_status',
                'label': 'Agent Status',
                'type': 'select',
                'default': 'active',
                'description': 'Calendar Agent operational status',
                'options': ['active', 'disabled'],
                'required': True
            }
        ]
    },
    {
        'key': 'user_preferences',
        'label': 'User Preferences',
        'description': 'Personal calendar settings and preferences',
        'fields': [
            {
                'key': 'timezone',
                'label': 'Timezone',
                'type': 'select',
                'default': DEFAULT_TIMEZONE,
                'description': 'Your timezone for accurate scheduling and communication',
                'placeholder': 'Select timezone',
                'options': STANDARD_TIMEZONE_OPTIONS
            },
            {
                'key': 'work_hours_start',
                'label': 'Work Day Starts',
                'type': 'select',
                'default': '09:00',
                'description': 'Start of your work day',
                'options': ['07:00', '07:30', '08:00', '08:30', '09:00', '09:30', '10:00']
            },
            {
                'key': 'work_hours_end',
                'label': 'Work Day Ends',
                'type': 'select',
                'default': '17:00',
                'description': 'End of your work day',
                'options': ['16:00', '16:30', '17:00', '17:30', '18:00', '18:30', '19:00', '19:30', '20:00']
            },
            {
                'key': 'default_meeting_duration',
                'label': 'Default Meeting Duration',
                'type': 'select',
                'default': '30',
                'description': 'Default duration for new meetings (minutes)',
                'options': ['15', '30', '45', '60', '90', '120']
            }
        ]
    },
    {
        'key': 'llm',
        'label': 'Language Model',
        'description': 'AI model configuration for calendar operations',
        'fields': [
            {
                'key': 'model',
                'label': 'Model Name',
                'type': 'select',
                'default': DEFAULT_LLM_MODEL,
                'description': 'Primary AI model for calendar tasks',
                'options': STANDARD_LLM_MODEL_OPTIONS,
                'required': True
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
        'key': 'prompt_templates',
        'label': 'System Prompts',
        'description': 'Customize calendar agent behavior through system prompts',
        'card_style': 'orange',
        'fields': [
            {
                'key': 'agent_system_prompt',
                'label': 'Main System Prompt',
                'type': 'textarea',
                'description': 'Main system prompt that defines calendar agent behavior',
                'placeholder': 'You are a helpful Calendar Agent...',
                'required': True,
                'rows': 15,
                'note': 'Use {current_time}, {timezone_name}, {today}, {tomorrow} as placeholders'
            },
            {
                'key': 'agent_role_prompt',
                'label': 'Role Description',
                'type': 'textarea',
                'description': 'Define the calendar agent\'s role and capabilities',
                'rows': 6,
                'placeholder': 'CAPABILITIES (read-only)\n- Check availability...'
            },
            {
                'key': 'agent_guidelines_prompt',
                'label': 'Operational Guidelines',
                'type': 'textarea',
                'description': 'Guidelines for calendar agent behavior and responses',
                'rows': 8,
                'placeholder': 'PRINCIPLES\n- Assume ALL user times are in local timezone...'
            },
            {
                'key': 'routing_system_prompt',
                'label': 'Workflow Routing Prompt',
                'type': 'textarea',
                'description': 'Advanced: Smart routing logic for workflow decisions',
                'rows': 10,
                'placeholder': 'You are a smart calendar workflow router...'
            },
            {
                'key': 'booking_extraction_prompt',
                'label': 'Booking Extraction Prompt',
                'type': 'textarea',
                'description': 'Advanced: Template for extracting booking details from conversations',
                'rows': 12,
                'placeholder': 'Extract booking details from this request...'
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
                'default': 'PIPEDREAM_MCP_SERVER',
                'description': 'Name of the environment variable containing the MCP server URL (read-only)',
                'placeholder': 'PIPEDREAM_MCP_SERVER',
                'required': False,
                'note': 'This shows which environment variable is used. Configured in agent code.'
            },
            {
                'key': 'mcp_server_url',
                'label': 'MCP Server URL',
                'type': 'text',
                'description': 'The MCP server URL (editable - updates .env file)',
                'placeholder': 'https://mcp.pipedream.net/xxx/google_calendar',
                'required': False,
                'note': 'Editing this updates the URL in your .env file'
            }
        ]
    }
]