"""
Calendar Agent UI Configuration Schema
Optimized configuration for calendar agent settings
"""

CONFIG_INFO = {
    'name': 'Calendar Agent',
    'description': 'Google Calendar management and scheduling',
    'config_type': 'calendar_config',
    'config_path': 'src/calendar_agent/config.py'
}

CONFIG_SECTIONS = [
    {
        'key': 'agent_identity',
        'label': 'Agent Information',
        'description': 'Calendar agent identification and status',
        'fields': [
            {
                'key': 'agent_name',
                'label': 'Agent Name',
                'type': 'text',
                'default': 'calendar',
                'description': 'Internal agent identifier',
                'readonly': True
            },
            {
                'key': 'agent_display_name',
                'label': 'Display Name',
                'type': 'text',
                'default': 'Calendar Agent',
                'description': 'Human-readable agent name shown in UI',
                'required': True
            },
            {
                'key': 'agent_description',
                'label': 'Description',
                'type': 'textarea',
                'default': 'Google Calendar management and scheduling',
                'description': 'Brief description of agent capabilities',
                'required': True
            },
            {
                'key': 'agent_status',
                'label': 'Status',
                'type': 'select',
                'default': 'active',
                'description': 'Enable or disable this agent',
                'options': ['active', 'disabled']
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
                'default': 'claude-sonnet-4-20250514',
                'description': 'Primary AI model for calendar tasks',
                'options': [
                    'claude-sonnet-4-20250514',
                    'claude-3-5-sonnet-20241022',
                    'gpt-4o',
                    'gpt-4o-mini'
                ],
                'required': True
            },
            {
                'key': 'temperature',
                'label': 'Temperature',
                'type': 'number',
                'default': 0.3,
                'description': 'Response creativity (0=focused, 1=creative)',
                'validation': {'min': 0.0, 'max': 1.0, 'step': 0.1}
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
    },
    {
        'key': 'user_preferences',
        'label': 'Your Preferences',
        'description': 'Personal calendar settings',
        'fields': [
            {
                'key': 'timezone',
                'label': 'Timezone',
                'type': 'select',
                'default': 'global',
                'description': 'Your timezone - select Use Global for system default',
                'placeholder': 'Select timezone',
                'options': [
                    'global',
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
        'key': 'prompt_templates',
        'label': 'System Prompts',
        'description': 'Customize calendar agent behavior through system prompts',
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
    }
]