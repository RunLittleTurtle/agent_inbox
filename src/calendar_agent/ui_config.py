"""
Calendar Agent UI Configuration Schema
Standardized config interface for the calendar agent
"""

CONFIG_INFO = {
    'name': 'Calendar Agent',
    'description': 'AI-powered calendar management and scheduling assistant',
    'config_type': 'embedded_config',
    'config_path': 'src/calendar_agent/calendar_orchestrator.py'
}

CONFIG_SECTIONS = [
    {
        'key': 'llm',
        'label': 'Language Model',
        'description': 'AI model configuration for calendar operations',
        'fields': [
            {
                'key': 'model',
                'label': 'Model Name',
                'type': 'select',
                'default': 'claude-3-5-sonnet-20241022',
                'description': 'Primary AI model for calendar tasks',
                'options': [
                    'claude-3-5-sonnet-20241022',
                    'claude-sonnet-4-20250514',
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
                'default': 0.1,
                'description': 'Model creativity level for calendar operations',
                'validation': {'min': 0.0, 'max': 1.0, 'step': 0.1}
            },
            {
                'key': 'max_tokens',
                'label': 'Max Tokens',
                'type': 'number',
                'default': 1500,
                'description': 'Maximum tokens per response',
                'validation': {'min': 100, 'max': 4096}
            }
        ]
    },
    {
        'key': 'mcp_integration',
        'label': 'MCP Integration',
        'description': 'Model Context Protocol server configuration',
        'fields': [
            {
                'key': 'google_calendar_mcp',
                'label': 'Google Calendar MCP Server',
                'type': 'text',
                'envVar': 'PIPEDREAM_MCP_SERVER',
                'description': 'Primary Google Calendar MCP server URL',
                'placeholder': 'https://mcp.pipedream.net/xxx/google_calendar',
                'required': True,
                'note': 'Uses global MCP server from main .env'
            },
            {
                'key': 'google_workspace_mcp',
                'label': 'Google Workspace MCP Server',
                'type': 'text',
                'envVar': 'MCP_SERVER_GOOGLE_WORKSPACE',
                'default': 'http://localhost:3000/mcp',
                'description': 'Local Google Workspace MCP server',
                'note': 'Fallback MCP server for enhanced features'
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
            }
        ]
    },
    {
        'key': 'calendar_settings',
        'label': 'Calendar Settings',
        'description': 'Calendar-specific behavior and preferences',
        'fields': [
            {
                'key': 'default_meeting_duration',
                'label': 'Default Meeting Duration (minutes)',
                'type': 'select',
                'default': 30,
                'description': 'Default duration for new meetings',
                'options': [15, 30, 45, 60, 90, 120],
                'note': 'Overridden by user preferences in main config'
            },
            {
                'key': 'timezone',
                'label': 'Calendar Timezone',
                'type': 'select',
                'envVar': 'USER_TIMEZONE',
                'default': 'America/Toronto',
                'description': 'Timezone for calendar operations',
                'options': [
                    'America/Toronto',
                    'America/Montreal',
                    'America/New_York',
                    'America/Los_Angeles',
                    'Europe/London',
                    'Europe/Paris',
                    'Asia/Tokyo'
                ],
                'note': 'Uses global timezone from main .env'
            },
            {
                'key': 'booking_window_days',
                'label': 'Booking Window (days)',
                'type': 'number',
                'default': 90,
                'description': 'How far in advance bookings can be made',
                'validation': {'min': 7, 'max': 365}
            },
            {
                'key': 'min_notice_hours',
                'label': 'Minimum Notice (hours)',
                'type': 'number',
                'default': 2,
                'description': 'Minimum hours notice required for bookings',
                'validation': {'min': 0, 'max': 168}
            },
            {
                'key': 'max_events_per_day',
                'label': 'Max Events Per Day',
                'type': 'number',
                'default': 10,
                'description': 'Maximum calendar events per day',
                'validation': {'min': 1, 'max': 50}
            }
        ]
    },
    {
        'key': 'scheduling_preferences',
        'label': 'Scheduling Preferences',
        'description': 'AI scheduling behavior and constraints',
        'fields': [
            {
                'key': 'work_hours_start',
                'label': 'Work Hours Start',
                'type': 'time',
                'default': '09:00',
                'description': 'Start of work hours for scheduling'
            },
            {
                'key': 'work_hours_end',
                'label': 'Work Hours End',
                'type': 'time',
                'default': '17:00',
                'description': 'End of work hours for scheduling'
            },
            {
                'key': 'work_days',
                'label': 'Work Days',
                'type': 'multiselect',
                'default': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
                'description': 'Available days for work meetings',
                'options': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            },
            {
                'key': 'buffer_time_minutes',
                'label': 'Buffer Time (minutes)',
                'type': 'number',
                'default': 15,
                'description': 'Buffer time between meetings',
                'validation': {'min': 0, 'max': 60}
            },
            {
                'key': 'lunch_break_start',
                'label': 'Lunch Break Start',
                'type': 'time',
                'default': '12:00',
                'description': 'Lunch break start time'
            },
            {
                'key': 'lunch_break_duration',
                'label': 'Lunch Break Duration (minutes)',
                'type': 'number',
                'default': 60,
                'description': 'Duration of lunch break',
                'validation': {'min': 30, 'max': 180}
            }
        ]
    },
    {
        'key': 'features',
        'label': 'Features',
        'description': 'Enable/disable calendar agent features',
        'fields': [
            {
                'key': 'enhanced_calendar_agent',
                'label': 'Enhanced Calendar Agent',
                'type': 'boolean',
                'envVar': 'USE_ENHANCED_CALENDAR_AGENT',
                'default': True,
                'description': 'Enable enhanced calendar agent features',
                'note': 'Global setting from main .env'
            },
            {
                'key': 'enable_smart_scheduling',
                'label': 'Smart Scheduling',
                'type': 'boolean',
                'default': True,
                'description': 'AI-powered intelligent scheduling suggestions'
            },
            {
                'key': 'enable_conflict_detection',
                'label': 'Conflict Detection',
                'type': 'boolean',
                'default': True,
                'description': 'Automatic detection of scheduling conflicts'
            },
            {
                'key': 'enable_meeting_reminders',
                'label': 'Meeting Reminders',
                'type': 'boolean',
                'default': True,
                'description': 'Send automated meeting reminders'
            },
            {
                'key': 'enable_attendee_analysis',
                'label': 'Attendee Analysis',
                'type': 'boolean',
                'default': True,
                'description': 'Analyze attendee availability and preferences'
            },
            {
                'key': 'enable_location_suggestions',
                'label': 'Location Suggestions',
                'type': 'boolean',
                'default': True,
                'description': 'Suggest meeting locations based on participants'
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
                'key': 'log_mcp_requests',
                'label': 'Log MCP Requests',
                'type': 'boolean',
                'default': False,
                'description': 'Log all MCP server requests and responses'
            },
            {
                'key': 'enable_performance_metrics',
                'label': 'Performance Metrics',
                'type': 'boolean',
                'default': True,
                'description': 'Collect performance metrics for optimization'
            },
            {
                'key': 'cache_calendar_data',
                'label': 'Cache Calendar Data',
                'type': 'boolean',
                'default': True,
                'description': 'Cache calendar data to improve performance'
            },
            {
                'key': 'cache_duration_minutes',
                'label': 'Cache Duration (minutes)',
                'type': 'number',
                'default': 30,
                'description': 'How long to cache calendar data',
                'validation': {'min': 5, 'max': 1440}
            }
        ]
    }
]


def get_current_config():
    """Get current configuration values from calendar orchestrator"""
    # Since calendar agent config is embedded, return defaults
    # TODO: Extract actual values from calendar_orchestrator.py
    return {
        'llm': {
            'model': 'claude-3-5-sonnet-20241022',
            'temperature': 0.1,
            'max_tokens': 1500
        },
        'mcp_integration': {
            'mcp_timeout': 30,
            'mcp_retry_attempts': 3
        },
        'calendar_settings': {
            'default_meeting_duration': 30,
            'booking_window_days': 90,
            'min_notice_hours': 2,
            'max_events_per_day': 10
        },
        'scheduling_preferences': {
            'work_hours_start': '09:00',
            'work_hours_end': '17:00',
            'work_days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
            'buffer_time_minutes': 15,
            'lunch_break_start': '12:00',
            'lunch_break_duration': 60
        },
        'features': {
            'enable_smart_scheduling': True,
            'enable_conflict_detection': True,
            'enable_meeting_reminders': True,
            'enable_attendee_analysis': True,
            'enable_location_suggestions': True
        },
        'debugging': {
            'debug_mode': False,
            'log_mcp_requests': False,
            'enable_performance_metrics': True,
            'cache_calendar_data': True,
            'cache_duration_minutes': 30
        }
    }


def update_config_value(section_key: str, field_key: str, value):
    """Update configuration value in calendar orchestrator"""
    # TODO: Implement config updating logic for embedded config
    # This would modify the calendar_orchestrator.py file
    pass