"""
Calendar Agent UI Configuration Schema
Streamlined config interface focused on essential user settings
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
        'description': 'Calendar agent identification',
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
                'type': 'text',
                'default': 'Active',
                'description': 'Agent operational status',
                'readonly': True
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
                'envVar': 'USER_TIMEZONE',
                'default': 'America/Toronto',
                'description': 'Your timezone for scheduling',
                'options': [
                    'America/Toronto',
                    'America/Montreal',
                    'America/New_York',
                    'America/Los_Angeles',
                    'America/Chicago',
                    'Europe/London',
                    'Europe/Paris',
                    'Asia/Tokyo'
                ]
            },
            {
                'key': 'work_hours_start',
                'label': 'Work Day Starts',
                'type': 'select',
                'default': '09:00',
                'description': 'Start of your work day',
                'options': ['07:00', '08:00', '09:00', '10:00']
            },
            {
                'key': 'work_hours_end',
                'label': 'Work Day Ends',
                'type': 'select',
                'default': '17:00',
                'description': 'End of your work day',
                'options': ['16:00', '17:00', '18:00', '19:00', '20:00']
            },
            {
                'key': 'default_meeting_duration',
                'label': 'Default Meeting Duration',
                'type': 'select',
                'default': '30',
                'description': 'Default duration for new meetings',
                'options': ['15', '30', '45', '60', '90']
            }
        ]
    }
]