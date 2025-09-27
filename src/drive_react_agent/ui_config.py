"""
Google Drive Agent UI Configuration Schema
Streamlined config interface focused on essential user settings
"""

CONFIG_INFO = {
    'name': 'Google Drive Agent',
    'description': 'Google Drive file management and operations',
    'config_type': 'drive_config',
    'config_path': 'src/drive_react_agent/config.py'
}

CONFIG_SECTIONS = [
    {
        'key': 'agent_identity',
        'label': 'Agent Information',
        'description': 'Drive agent identification',
        'fields': [
            {
                'key': 'agent_name',
                'label': 'Agent Name',
                'type': 'text',
                'default': 'drive',
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
        'description': 'Configure the AI model for Drive operations',
        'fields': [
            {
                'key': 'model',
                'label': 'Model',
                'type': 'select',
                'default': 'claude-sonnet-4-20250514',
                'description': 'Select AI model for Drive tasks',
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
                'default': 0.2,
                'description': 'Response creativity (0=focused, 1=creative)',
                'validation': {'min': 0, 'max': 1, 'step': 0.1}
            }
        ]
    },
    {
        'key': 'mcp_connection',
        'label': 'MCP Server',
        'description': 'Google Drive API connection',
        'fields': [
            {
                'key': 'drive_mcp_url',
                'label': 'Drive MCP URL',
                'type': 'text',
                'envVar': 'PIPEDREAM_MCP_SERVER_google_drive',
                'description': 'Google Drive MCP server endpoint',
                'placeholder': 'https://mcp.pipedream.net/xxx/google_drive',
                'required': True
            }
        ]
    },
    {
        'key': 'file_preferences',
        'label': 'File Management',
        'description': 'Default file handling settings',
        'fields': [
            {
                'key': 'default_view',
                'label': 'Default View',
                'type': 'select',
                'default': 'list',
                'description': 'Default folder view mode',
                'options': ['list', 'grid']
            },
            {
                'key': 'max_file_size_mb',
                'label': 'Max Upload Size (MB)',
                'type': 'select',
                'default': '100',
                'description': 'Maximum file upload size',
                'options': ['10', '50', '100', '500', '1000']
            },
            {
                'key': 'auto_backup',
                'label': 'Auto Backup',
                'type': 'boolean',
                'default': True,
                'description': 'Backup files before modification'
            }
        ]
    },
    {
        'key': 'sharing_defaults',
        'label': 'Sharing Settings',
        'description': 'Default file sharing preferences',
        'fields': [
            {
                'key': 'default_permission',
                'label': 'Default Permission',
                'type': 'select',
                'default': 'viewer',
                'description': 'Default permission for shared files',
                'options': ['viewer', 'commenter', 'editor']
            },
            {
                'key': 'link_sharing',
                'label': 'Link Sharing',
                'type': 'select',
                'default': 'restricted',
                'description': 'Default link sharing setting',
                'options': ['restricted', 'anyone_with_link']
            }
        ]
    }
]