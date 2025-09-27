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
        'label': 'AI Model Settings',
        'description': 'Configure the AI model for calendar operations',
        'fields': [
            {
                'key': 'model',
                'label': 'Model',
                'type': 'select',
                'default': 'claude-3-5-sonnet-20241022',
                'description': 'Select AI model for calendar tasks',
                'options': [
                    'claude-3-5-sonnet-20241022',
                    'claude-sonnet-4-20250514',
                    'gpt-4o'
                ],
                'required': True
            },
            {
                'key': 'temperature',
                'label': 'Temperature',
                'type': 'number',
                'default': 0.1,
                'description': 'Response creativity (0=focused, 1=creative)',
                'validation': {'min': 0, 'max': 1, 'step': 0.1}
            }
        ]
    },
    {
        'key': 'mcp_connection',
        'label': 'MCP Server',
        'description': 'Google Calendar API connection',
        'fields': [
            {
                'key': 'calendar_mcp_url',
                'label': 'Calendar MCP URL',
                'type': 'text',
                'envVar': 'PIPEDREAM_MCP_SERVER',
                'description': 'Google Calendar MCP server endpoint',
                'placeholder': 'https://mcp.pipedream.net/xxx/google_calendar',
                'required': True
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
    }
]