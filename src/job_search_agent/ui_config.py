"""
Job Search Agent UI Configuration Schema
Standardized config interface for the job search agent
"""

CONFIG_INFO = {
    'name': 'Job Search Agent',
    'description': 'AI-powered job application assistant for CV analysis and cover letter generation',
    'config_type': 'python_config',
    'config_path': 'src/job_search_agent/config.py'
}

CONFIG_SECTIONS = [
    {
        'key': 'llm',
        'label': 'Language Model',
        'description': 'AI model configuration for job search tasks',
        'fields': [
            {
                'key': 'model',
                'label': 'Model Name',
                'type': 'select',
                'envVar': 'JOB_SEARCH_LLM_MODEL',
                'default': 'claude-sonnet-4-20250514',
                'description': 'Primary AI model for job search operations',
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
                'envVar': 'JOB_SEARCH_LLM_TEMPERATURE',
                'default': 0.0,
                'description': 'Model creativity level (0.0 = focused, 1.0 = creative)',
                'validation': {'min': 0.0, 'max': 1.0, 'step': 0.1}
            },
            {
                'key': 'max_tokens',
                'label': 'Max Tokens',
                'type': 'number',
                'envVar': 'JOB_SEARCH_LLM_MAX_TOKENS',
                'default': 2000,
                'description': 'Maximum tokens per response',
                'validation': {'min': 100, 'max': 8192}
            },
            {
                'key': 'timeout',
                'label': 'Request Timeout (seconds)',
                'type': 'number',
                'envVar': 'JOB_SEARCH_LLM_TIMEOUT',
                'default': 60,
                'description': 'API request timeout duration',
                'validation': {'min': 10, 'max': 300}
            },
            {
                'key': 'max_retries',
                'label': 'Max Retries',
                'type': 'number',
                'envVar': 'JOB_SEARCH_LLM_MAX_RETRIES',
                'default': 3,
                'description': 'Number of retry attempts on failure',
                'validation': {'min': 0, 'max': 10}
            }
        ]
    },
    {
        'key': 'storage',
        'label': 'Storage Configuration',
        'description': 'File storage and data management settings',
        'fields': [
            {
                'key': 'base_path',
                'label': 'Base Storage Path',
                'type': 'text',
                'envVar': 'JOB_SEARCH_STORAGE_PATH',
                'default': './job_search_data',
                'description': 'Root directory for agent data storage'
            },
            {
                'key': 'documents_path',
                'label': 'Documents Path',
                'type': 'text',
                'envVar': 'JOB_SEARCH_DOCUMENTS_PATH',
                'default': './job_search_data/documents',
                'description': 'Directory for CV and job posting documents'
            },
            {
                'key': 'vectors_path',
                'label': 'Vectors Path',
                'type': 'text',
                'envVar': 'JOB_SEARCH_VECTORS_PATH',
                'default': './job_search_data/vectors',
                'description': 'Directory for vector embeddings storage'
            },
            {
                'key': 'cleanup_days',
                'label': 'Cleanup Days',
                'type': 'number',
                'envVar': 'JOB_SEARCH_CLEANUP_DAYS',
                'default': 30,
                'description': 'Days to keep old files before cleanup',
                'validation': {'min': 1, 'max': 365}
            },
            {
                'key': 'max_file_size_mb',
                'label': 'Max File Size (MB)',
                'type': 'number',
                'envVar': 'JOB_SEARCH_MAX_FILE_SIZE_MB',
                'default': 10,
                'description': 'Maximum file size for uploads',
                'validation': {'min': 1, 'max': 100}
            }
        ]
    },
    {
        'key': 'processing',
        'label': 'Document Processing',
        'description': 'RAG and document analysis configuration',
        'fields': [
            {
                'key': 'chunk_size',
                'label': 'Chunk Size',
                'type': 'number',
                'envVar': 'JOB_SEARCH_CHUNK_SIZE',
                'default': 500,
                'description': 'Text chunk size for document processing',
                'validation': {'min': 100, 'max': 2000}
            },
            {
                'key': 'chunk_overlap',
                'label': 'Chunk Overlap',
                'type': 'number',
                'envVar': 'JOB_SEARCH_CHUNK_OVERLAP',
                'default': 100,
                'description': 'Overlap between document chunks',
                'validation': {'min': 0, 'max': 500}
            },
            {
                'key': 'quality_threshold',
                'label': 'Quality Threshold',
                'type': 'number',
                'envVar': 'JOB_SEARCH_QUALITY_THRESHOLD',
                'default': 8,
                'description': 'Minimum quality score (1-10)',
                'validation': {'min': 1, 'max': 10}
            },
            {
                'key': 'max_iterations',
                'label': 'Max Iterations',
                'type': 'number',
                'envVar': 'JOB_SEARCH_MAX_ITERATIONS',
                'default': 3,
                'description': 'Maximum improvement iterations',
                'validation': {'min': 1, 'max': 10}
            },
            {
                'key': 'rag_top_k',
                'label': 'RAG Top K Results',
                'type': 'number',
                'envVar': 'JOB_SEARCH_RAG_TOP_K',
                'default': 8,
                'description': 'Number of top results for RAG queries',
                'validation': {'min': 1, 'max': 20}
            },
            {
                'key': 'vector_dimensions',
                'label': 'Vector Dimensions',
                'type': 'number',
                'envVar': 'JOB_SEARCH_VECTOR_DIMENSIONS',
                'default': 384,
                'description': 'Vector embedding dimensions',
                'options': [384, 768, 1024, 1536],
                'type': 'select'
            }
        ]
    },
    {
        'key': 'user_preferences',
        'label': 'User Preferences',
        'description': 'Default settings for cover letters and applications',
        'fields': [
            {
                'key': 'cover_letter_length',
                'label': 'Default Cover Letter Length',
                'type': 'select',
                'default': 'medium',
                'description': 'Preferred cover letter length',
                'options': ['short', 'medium', 'long']
            },
            {
                'key': 'tone',
                'label': 'Default Tone',
                'type': 'select',
                'default': 'professional',
                'description': 'Default writing tone for cover letters',
                'options': ['casual', 'professional', 'enthusiastic']
            },
            {
                'key': 'format',
                'label': 'Default Format Style',
                'type': 'select',
                'default': 'traditional',
                'description': 'Default cover letter format',
                'options': ['modern', 'traditional', 'creative']
            },
            {
                'key': 'language',
                'label': 'Default Language',
                'type': 'select',
                'default': 'french',
                'description': 'Default language for cover letters',
                'options': ['english', 'french', 'bilingual']
            },
            {
                'key': 'export_format',
                'label': 'Default Export Format',
                'type': 'select',
                'default': 'markdown',
                'description': 'Default format for exporting documents',
                'options': ['markdown', 'pdf', 'docx']
            }
        ]
    },
    {
        'key': 'workflow',
        'label': 'Workflow Settings',
        'description': 'Agent behavior and workflow configuration',
        'fields': [
            {
                'key': 'enable_interrupts',
                'label': 'Enable Interrupts',
                'type': 'boolean',
                'envVar': 'JOB_SEARCH_ENABLE_INTERRUPTS',
                'default': False,
                'description': 'Allow human intervention during processing'
            },
            {
                'key': 'auto_quality_review',
                'label': 'Auto Quality Review',
                'type': 'boolean',
                'envVar': 'JOB_SEARCH_AUTO_QUALITY',
                'default': True,
                'description': 'Automatically review and improve outputs'
            },
            {
                'key': 'enable_rag_by_default',
                'label': 'Enable RAG by Default',
                'type': 'boolean',
                'envVar': 'JOB_SEARCH_ENABLE_RAG',
                'default': True,
                'description': 'Use RAG for document analysis by default'
            },
            {
                'key': 'parallel_processing',
                'label': 'Parallel Processing',
                'type': 'boolean',
                'envVar': 'JOB_SEARCH_PARALLEL',
                'default': False,
                'description': 'Enable parallel processing for better performance'
            },
            {
                'key': 'debug_mode',
                'label': 'Debug Mode',
                'type': 'boolean',
                'envVar': 'JOB_SEARCH_DEBUG',
                'default': False,
                'description': 'Enable detailed debug logging'
            }
        ]
    },
    {
        'key': 'feature_flags',
        'label': 'Features',
        'description': 'Enable/disable specific agent features',
        'fields': [
            {
                'key': 'enable_multilingual',
                'label': 'Multilingual Support',
                'type': 'boolean',
                'default': True,
                'description': 'Enable French/English language support'
            },
            {
                'key': 'enable_industry_templates',
                'label': 'Industry Templates',
                'type': 'boolean',
                'default': True,
                'description': 'Enable industry-specific cover letter templates'
            },
            {
                'key': 'enable_rag_search',
                'label': 'RAG Search',
                'type': 'boolean',
                'default': True,
                'description': 'Enable semantic search in documents'
            },
            {
                'key': 'enable_quality_scoring',
                'label': 'Quality Scoring',
                'type': 'boolean',
                'default': True,
                'description': 'Enable automatic quality assessment'
            },
            {
                'key': 'enable_export_formats',
                'label': 'Export Formats',
                'type': 'boolean',
                'default': True,
                'description': 'Enable multiple export format options'
            },
            {
                'key': 'enable_ai_feedback',
                'label': 'AI Feedback',
                'type': 'boolean',
                'default': True,
                'description': 'Enable AI-powered improvement suggestions'
            }
        ]
    }
]


def get_current_config():
    """Get current configuration values from config.py"""
    try:
        from .config import (
            LLM_CONFIG, STORAGE_CONFIG, PROCESSING_CONFIG,
            DEFAULT_USER_PREFERENCES, WORKFLOW_CONFIG, FEATURE_FLAGS
        )

        return {
            'llm': LLM_CONFIG,
            'storage': STORAGE_CONFIG,
            'processing': PROCESSING_CONFIG,
            'user_preferences': DEFAULT_USER_PREFERENCES,
            'workflow': WORKFLOW_CONFIG,
            'feature_flags': FEATURE_FLAGS
        }
    except ImportError:
        return {}


def update_config_value(section_key: str, field_key: str, value):
    """Update configuration value in config.py"""
    # TODO: Implement config file updating logic
    # This would modify the actual config.py values
    pass