"""
Job Search Agent UI Configuration Schema
Streamlined config interface focused on essential user settings
"""

CONFIG_INFO = {
    'name': 'Job Search Agent',
    'description': 'CV analysis and job application assistance',
    'config_type': 'job_config',
    'config_path': 'src/job_search_agent/config.py'
}

CONFIG_SECTIONS = [
    {
        'key': 'agent_identity',
        'label': 'Agent Information',
        'description': 'Job search agent identification',
        'fields': [
            {
                'key': 'agent_name',
                'label': 'Agent Name',
                'type': 'text',
                'default': 'job_search',
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
        'description': 'Configure the AI model for job search tasks',
        'fields': [
            {
                'key': 'model',
                'label': 'Model',
                'type': 'select',
                'default': 'claude-sonnet-4-20250514',
                'description': 'Select AI model for job search',
                'options': [
                    'claude-sonnet-4-20250514',
                    'claude-3-5-sonnet-20241022',
                    'gpt-4o'
                ],
                'required': True
            },
            {
                'key': 'temperature',
                'label': 'Temperature',
                'type': 'number',
                'default': 0,
                'description': 'Response creativity (0=focused, 1=creative)',
                'validation': {'min': 0, 'max': 1, 'step': 0.1}
            }
        ]
    },
    {
        'key': 'linkedin_settings',
        'label': 'LinkedIn Integration',
        'description': 'LinkedIn account for job searching',
        'fields': [
            {
                'key': 'linkedin_email',
                'label': 'LinkedIn Email',
                'type': 'text',
                'envVar': 'LINKEDIN_EMAIL',
                'description': 'Your LinkedIn account email',
                'placeholder': 'user@example.com'
            },
            {
                'key': 'linkedin_password',
                'label': 'LinkedIn Password',
                'type': 'password',
                'envVar': 'LINKEDIN_PASSWORD',
                'description': 'LinkedIn password (encrypted)',
                'placeholder': '••••••••'
            }
        ]
    },
    {
        'key': 'job_preferences',
        'label': 'Job Preferences',
        'description': 'Your job search preferences',
        'fields': [
            {
                'key': 'job_types',
                'label': 'Preferred Job Types',
                'type': 'select',
                'default': 'full_time',
                'description': 'Type of positions you prefer',
                'options': ['full_time', 'part_time', 'contract', 'remote']
            },
            {
                'key': 'experience_level',
                'label': 'Experience Level',
                'type': 'select',
                'default': 'mid',
                'description': 'Your experience level',
                'options': ['entry', 'mid', 'senior', 'executive']
            },
            {
                'key': 'auto_tailor',
                'label': 'Auto-Tailor Applications',
                'type': 'boolean',
                'default': True,
                'description': 'Customize CV/cover letter per job'
            }
        ]
    }
]