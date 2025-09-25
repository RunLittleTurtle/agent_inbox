"""
Drive React Agent UI Configuration Schema
Standardized config interface for the Google Drive agent
"""

CONFIG_INFO = {
    'name': 'Google Drive Agent',
    'description': 'AI-powered Google Drive file management and operations',
    'config_type': 'drive_agent_config',
    'config_path': 'src/drive_react_agent/config.py'
}

CONFIG_SECTIONS = [
    {
        'key': 'agent_identity',
        'label': 'Agent Identity',
        'description': 'Google Drive agent identification',
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
                'key': 'agent_display_name',
                'label': 'Display Name',
                'type': 'text',
                'default': 'Google Drive',
                'description': 'Human-readable agent name'
            },
            {
                'key': 'agent_description',
                'label': 'Description',
                'type': 'text',
                'default': 'file management',
                'description': 'Brief description of agent capabilities'
            },
            {
                'key': 'mcp_service',
                'label': 'MCP Service',
                'type': 'text',
                'default': 'google_drive',
                'description': 'MCP service identifier'
            }
        ]
    },
    {
        'key': 'llm',
        'label': 'Language Model',
        'description': 'AI model configuration for Drive operations',
        'fields': [
            {
                'key': 'model',
                'label': 'Model Name',
                'type': 'select',
                'default': 'claude-sonnet-4-20250514',
                'description': 'Primary AI model for Drive tasks',
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
                'description': 'Enable streaming responses'
            }
        ]
    },
    {
        'key': 'drive_settings',
        'label': 'Drive Settings',
        'description': 'Google Drive specific configuration',
        'fields': [
            {
                'key': 'google_drive_mcp',
                'label': 'Google Drive MCP Server',
                'type': 'text',
                'envVar': 'PIPEDREAM_MCP_SERVER_google_drive',
                'description': 'Google Drive MCP server URL',
                'placeholder': 'https://mcp.pipedream.net/xxx/google_drive',
                'required': True,
                'note': 'Uses global Google Drive MCP from main .env'
            },
            {
                'key': 'default_folder_view',
                'label': 'Default Folder View',
                'type': 'select',
                'default': 'grid',
                'description': 'Default view mode for folder listings',
                'options': ['list', 'grid', 'detailed']
            },
            {
                'key': 'max_search_results',
                'label': 'Max Search Results',
                'type': 'number',
                'default': 50,
                'description': 'Maximum number of search results to return',
                'validation': {'min': 10, 'max': 500}
            },
            {
                'key': 'enable_version_tracking',
                'label': 'Enable Version Tracking',
                'type': 'boolean',
                'default': True,
                'description': 'Track file version history'
            },
            {
                'key': 'auto_organize_uploads',
                'label': 'Auto-organize Uploads',
                'type': 'boolean',
                'default': False,
                'description': 'Automatically organize uploaded files into folders'
            }
        ]
    },
    {
        'key': 'file_operations',
        'label': 'File Operations',
        'description': 'File handling and processing settings',
        'fields': [
            {
                'key': 'allowed_file_types',
                'label': 'Allowed File Types',
                'type': 'multiselect',
                'default': ['pdf', 'docx', 'txt', 'md', 'jpg', 'png', 'xlsx', 'pptx'],
                'description': 'File types allowed for operations',
                'options': ['pdf', 'docx', 'txt', 'md', 'jpg', 'png', 'gif', 'xlsx', 'pptx', 'csv', 'json', 'xml']
            },
            {
                'key': 'max_file_size_mb',
                'label': 'Max File Size (MB)',
                'type': 'number',
                'default': 100,
                'description': 'Maximum file size for operations',
                'validation': {'min': 1, 'max': 1000}
            },
            {
                'key': 'enable_ocr',
                'label': 'Enable OCR',
                'type': 'boolean',
                'default': True,
                'description': 'Enable OCR for image and PDF files'
            },
            {
                'key': 'enable_preview_generation',
                'label': 'Generate Previews',
                'type': 'boolean',
                'default': True,
                'description': 'Generate preview thumbnails for files'
            },
            {
                'key': 'backup_before_modification',
                'label': 'Backup Before Modification',
                'type': 'boolean',
                'default': True,
                'description': 'Create backup copies before modifying files'
            }
        ]
    },
    {
        'key': 'sharing_permissions',
        'label': 'Sharing & Permissions',
        'description': 'Default sharing and permission settings',
        'fields': [
            {
                'key': 'default_sharing_level',
                'label': 'Default Sharing Level',
                'type': 'select',
                'default': 'restricted',
                'description': 'Default sharing level for new files',
                'options': ['private', 'restricted', 'anyone_with_link', 'public']
            },
            {
                'key': 'default_permission_role',
                'label': 'Default Permission Role',
                'type': 'select',
                'default': 'viewer',
                'description': 'Default permission role for shared files',
                'options': ['viewer', 'commenter', 'editor', 'owner']
            },
            {
                'key': 'enable_link_expiration',
                'label': 'Enable Link Expiration',
                'type': 'boolean',
                'default': False,
                'description': 'Automatically set expiration dates on sharing links'
            },
            {
                'key': 'default_expiration_days',
                'label': 'Default Expiration (days)',
                'type': 'number',
                'default': 30,
                'description': 'Default expiration period for sharing links',
                'validation': {'min': 1, 'max': 365}
            }
        ]
    },
    {
        'key': 'search_indexing',
        'label': 'Search & Indexing',
        'description': 'Search functionality and content indexing',
        'fields': [
            {
                'key': 'enable_full_text_search',
                'label': 'Enable Full-text Search',
                'type': 'boolean',
                'default': True,
                'description': 'Enable searching within file contents'
            },
            {
                'key': 'index_file_contents',
                'label': 'Index File Contents',
                'type': 'boolean',
                'default': True,
                'description': 'Create searchable index of file contents'
            },
            {
                'key': 'search_timeout_seconds',
                'label': 'Search Timeout (seconds)',
                'type': 'number',
                'default': 30,
                'description': 'Maximum time to wait for search results',
                'validation': {'min': 5, 'max': 120}
            },
            {
                'key': 'enable_smart_suggestions',
                'label': 'Smart Suggestions',
                'type': 'boolean',
                'default': True,
                'description': 'Provide AI-powered file and folder suggestions'
            }
        ]
    },
    {
        'key': 'features',
        'label': 'Features',
        'description': 'Enable/disable Drive agent features',
        'fields': [
            {
                'key': 'enable_bulk_operations',
                'label': 'Bulk Operations',
                'type': 'boolean',
                'default': True,
                'description': 'Support bulk file operations'
            },
            {
                'key': 'enable_folder_management',
                'label': 'Folder Management',
                'type': 'boolean',
                'default': True,
                'description': 'Advanced folder creation and organization'
            },
            {
                'key': 'enable_duplicate_detection',
                'label': 'Duplicate Detection',
                'type': 'boolean',
                'default': True,
                'description': 'Detect and manage duplicate files'
            },
            {
                'key': 'enable_metadata_extraction',
                'label': 'Metadata Extraction',
                'type': 'boolean',
                'default': True,
                'description': 'Extract and index file metadata'
            },
            {
                'key': 'enable_collaboration_features',
                'label': 'Collaboration Features',
                'type': 'boolean',
                'default': True,
                'description': 'Advanced sharing and collaboration tools'
            },
            {
                'key': 'enable_workflow_automation',
                'label': 'Workflow Automation',
                'type': 'boolean',
                'default': False,
                'description': 'Automated file processing workflows'
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
                'key': 'log_file_operations',
                'label': 'Log File Operations',
                'type': 'boolean',
                'default': True,
                'description': 'Log all file operations and changes'
            },
            {
                'key': 'log_api_requests',
                'label': 'Log API Requests',
                'type': 'boolean',
                'default': False,
                'description': 'Log Google Drive API requests'
            },
            {
                'key': 'enable_performance_monitoring',
                'label': 'Performance Monitoring',
                'type': 'boolean',
                'default': True,
                'description': 'Track operation performance and response times'
            },
            {
                'key': 'cache_file_metadata',
                'label': 'Cache File Metadata',
                'type': 'boolean',
                'default': True,
                'description': 'Cache file metadata for faster access'
            },
            {
                'key': 'cache_duration_minutes',
                'label': 'Cache Duration (minutes)',
                'type': 'number',
                'default': 30,
                'description': 'How long to cache metadata',
                'validation': {'min': 5, 'max': 1440}
            }
        ]
    }
]


def get_current_config():
    """Get current configuration values from Drive agent config"""
    try:
        from .config import LLM_CONFIG, AGENT_NAME, AGENT_DISPLAY_NAME, AGENT_DESCRIPTION, MCP_SERVICE

        return {
            'agent_identity': {
                'agent_name': AGENT_NAME,
                'agent_display_name': AGENT_DISPLAY_NAME,
                'agent_description': AGENT_DESCRIPTION,
                'mcp_service': MCP_SERVICE
            },
            'llm': LLM_CONFIG,
            'drive_settings': {
                'default_folder_view': 'grid',
                'max_search_results': 50,
                'enable_version_tracking': True,
                'auto_organize_uploads': False
            },
            'file_operations': {
                'allowed_file_types': ['pdf', 'docx', 'txt', 'md', 'jpg', 'png', 'xlsx', 'pptx'],
                'max_file_size_mb': 100,
                'enable_ocr': True,
                'enable_preview_generation': True,
                'backup_before_modification': True
            },
            'sharing_permissions': {
                'default_sharing_level': 'restricted',
                'default_permission_role': 'viewer',
                'enable_link_expiration': False,
                'default_expiration_days': 30
            },
            'search_indexing': {
                'enable_full_text_search': True,
                'index_file_contents': True,
                'search_timeout_seconds': 30,
                'enable_smart_suggestions': True
            },
            'features': {
                'enable_bulk_operations': True,
                'enable_folder_management': True,
                'enable_duplicate_detection': True,
                'enable_metadata_extraction': True,
                'enable_collaboration_features': True,
                'enable_workflow_automation': False
            },
            'debugging': {
                'debug_mode': False,
                'log_file_operations': True,
                'log_api_requests': False,
                'enable_performance_monitoring': True,
                'cache_file_metadata': True,
                'cache_duration_minutes': 30
            }
        }
    except ImportError:
        # Return defaults if config doesn't exist
        return {}


def update_config_value(section_key: str, field_key: str, value):
    """Update configuration value in Drive agent config.py"""
    # TODO: Implement config file updating logic
    pass