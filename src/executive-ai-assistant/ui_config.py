"""
Executive AI Assistant UI Configuration Wrapper
Non-breaking wrapper that translates between existing config.yaml/config.py and UI schema
"""
"""
React Agent MCP Template UI Configuration Schema

⚠️  CRITICAL: When duplicating this template:
1. Replace ALL {PLACEHOLDER} values with actual agent details
2. Only include fields that are actually implemented in your agent
3. Update agent-inbox/src/pages/api/config/ endpoints (see MCP_AGENT_CONFIGURATION_GUIDE.md)
4. Test two-way sync in config UI at http://localhost:3004/config

This file defines the configuration interface schema for the Next.js configuration UI.
"""

# STANDARD OPTIONS LISTS
# These are Python placeholders that get replaced by TypeScript at runtime
# The ACTUAL master list is defined in: config-app/src/app/api/config/agents/route.ts
# That TypeScript file replaces these variable names with the actual arrays when parsing
STANDARD_LLM_MODEL_OPTIONS = []
STANDARD_TIMEZONE_OPTIONS = []

CONFIG_INFO = {
    'name': 'Executive AI Assistant',
    'description': 'AI-powered executive assistant for email management, scheduling, and task automation',
    'config_type': 'executive_config',
    'config_path': 'src/executive-ai-assistant/ui_config.py'
}

CONFIG_SECTIONS = [
    {
        'key': 'user_preferences',
        'label': 'User Preferences',
        'description': 'Personal information, background, and scheduling preferences',
        'fields': [
            {
                'key': 'name',
                'label': 'First Name',
                'type': 'text',
                'description': 'Your first name (used in casual communications)',
                'placeholder': 'Samuel',
                'required': True
            },
            {
                'key': 'full_name',
                'label': 'Full Name',
                'type': 'text',
                'description': 'Your complete name (used in formal communications)',
                'placeholder': 'Samuel Audette',
                'required': True
            },
            {
                'key': 'email',
                'label': 'Email Address',
                'type': 'text',
                'description': 'The email address this assistant manages',
                'placeholder': 'info@800m.ca',
                'required': True
            },
            {
                'key': 'background',
                'label': 'Background Information',
                'type': 'textarea',
                'description': 'Brief background about yourself (helps the assistant provide context-aware responses)',
                'placeholder': 'Samuel is a software developer and entrepreneur working on AI agent systems...',
                'rows': 4,
                'required': True
            },
            {
                'key': 'timezone',
                'label': 'Timezone',
                'type': 'select',
                'default': 'America/Toronto',
                'description': 'Your timezone for accurate scheduling and communication',
                'options': STANDARD_TIMEZONE_OPTIONS,
                'required': True
            },
            {
                'key': 'schedule_preferences',
                'label': 'Scheduling Preferences',
                'type': 'textarea',
                'description': 'Default preferences for meeting scheduling (duration, timing, etc.)',
                'placeholder': 'By default, unless specified otherwise, you should make meetings 30 minutes long.',
                'rows': 3,
                'required': False
            }
        ]
    },
    {
        'key': 'llm_triage',
        'label': 'Email Triage Model',
        'description': 'AI model for categorizing incoming emails (ignore/notify/respond). This runs first and makes the mark-as-read decision. Runs most frequently - consider a fast, cheap model.',
        'fields': [
            {
                'key': 'triage_model',
                'label': 'Triage Model',
                'type': 'select',
                'default': 'claude-3-5-haiku-20241022',
                'description': 'Model for email categorization. Haiku (fast, cheap) works well for this simple task. Sonnet-4 (balanced), GPT-4o (balanced), GPT-5 (expensive), o3 (reasoning, very expensive), Opus-4 (highest quality, most expensive)',
                'options': STANDARD_LLM_MODEL_OPTIONS,
                'required': True
            },
            {
                'key': 'triage_temperature',
                'label': 'Temperature',
                'type': 'number',
                'default': 0.1,
                'description': 'Model creativity (0.0 = very focused for consistent categorization)',
                'validation': {'min': 0.0, 'max': 1.0, 'step': 0.1}
            }
        ]
    },
    {
        'key': 'llm_draft',
        'label': 'Email Drafting Model',
        'description': 'AI model for writing initial email responses. This needs good reasoning and writing quality - consider a balanced or high-quality model.',
        'fields': [
            {
                'key': 'draft_model',
                'label': 'Draft Model',
                'type': 'select',
                'default': 'claude-sonnet-4-20250514',
                'description': 'Model for drafting email responses. Sonnet-4 (balanced, good price) recommended. Haiku (fast, cheap), GPT-4o (balanced), GPT-5 (expensive), o3 (reasoning, very expensive), Opus-4 (highest quality, most expensive)',
                'options': STANDARD_LLM_MODEL_OPTIONS,
                'required': True
            },
            {
                'key': 'draft_temperature',
                'label': 'Temperature',
                'type': 'number',
                'default': 0.2,
                'description': 'Model creativity (0.2 = balanced for professional emails)',
                'validation': {'min': 0.0, 'max': 1.0, 'step': 0.1}
            }
        ]
    },
    {
        'key': 'llm_rewrite',
        'label': 'Email Rewriting Model',
        'description': 'AI model for rewriting drafts to match your personal tone and style. This needs excellent style understanding - consider a high-quality model.',
        'fields': [
            {
                'key': 'rewrite_model',
                'label': 'Rewrite Model',
                'type': 'select',
                'default': 'claude-sonnet-4-20250514',
                'description': 'Model for rewriting emails to match your style. Opus-4 (highest quality) best for tone matching. Sonnet-4 (balanced), Haiku (fast, cheap), GPT-4o (balanced), GPT-5 (expensive), o3 (reasoning, very expensive)',
                'options': STANDARD_LLM_MODEL_OPTIONS,
                'required': True
            },
            {
                'key': 'rewrite_temperature',
                'label': 'Temperature',
                'type': 'number',
                'default': 0.3,
                'description': 'Model creativity (0.3 = more creative for natural tone adaptation)',
                'validation': {'min': 0.0, 'max': 1.0, 'step': 0.1}
            }
        ]
    },
    {
        'key': 'llm_scheduling',
        'label': 'Meeting Scheduling Model',
        'description': 'AI model for finding meeting times and calendar management. This needs calendar reasoning - consider a reasoning-focused model.',
        'fields': [
            {
                'key': 'scheduling_model',
                'label': 'Scheduling Model',
                'type': 'select',
                'default': 'gpt-4o',
                'description': 'Model for calendar analysis and meeting scheduling. GPT-4o (balanced) or o3 (reasoning, expensive) work well. Sonnet-4 (balanced), Haiku (fast, cheap), GPT-5 (expensive), Opus-4 (highest quality, most expensive)',
                'options': STANDARD_LLM_MODEL_OPTIONS,
                'required': True
            },
            {
                'key': 'scheduling_temperature',
                'label': 'Temperature',
                'type': 'number',
                'default': 0.1,
                'description': 'Model creativity (0.1 = focused for accurate calendar analysis)',
                'validation': {'min': 0.0, 'max': 1.0, 'step': 0.1}
            }
        ]
    },
    {
        'key': 'llm_reflection',
        'label': 'Email Reflection Model',
        'description': 'AI model for analyzing and reflecting on email quality before sending. This needs strong analytical capabilities - consider a reasoning-focused model.',
        'fields': [
            {
                'key': 'reflection_model',
                'label': 'Reflection Model',
                'type': 'select',
                'default': 'claude-sonnet-4-20250514',
                'description': 'Model for analyzing email drafts and providing quality feedback. o3 (reasoning, expensive) best for analysis. Opus-4 (highest quality, most expensive), Sonnet-4 (balanced), GPT-5 (expensive), GPT-4o (balanced), Haiku (fast, cheap)',
                'options': STANDARD_LLM_MODEL_OPTIONS,
                'required': True
            },
            {
                'key': 'reflection_temperature',
                'label': 'Temperature',
                'type': 'number',
                'default': 0.1,
                'description': 'Model creativity (0.1 = analytical and focused for email quality assessment)',
                'validation': {'min': 0.0, 'max': 1.0, 'step': 0.1}
            }
        ]
    },
    {
        'key': 'email_preferences',
        'label': 'Email Communication Preferences',
        'description': 'Configure how the assistant rewrites your draft emails to match your personal style',
        'card_style': 'orange',
        'fields': [
            {
                'key': 'rewrite_preferences',
                'label': 'Email Rewriting Style',
                'type': 'textarea',
                'description': 'Specify how the assistant should rewrite and improve your draft emails. These preferences ensure your writing style is consistent and professional.',
                'placeholder': '{name} has preferences for how his emails should be written:\n- Match the recipient\'s communication style and formality\n- Be concise and actionable in all communications\n- Use clear subject lines that reflect the email content\n- End emails with clear next steps or expectations\n- Maintain a professional yet approachable tone\n- Keep responses focused and avoid unnecessary details',
                'rows': 12,
                'required': False,
                'note': 'Applied when the assistant reviews and improves your draft emails before sending.'
            }
        ]
    },
    {
        'key': 'triage_prompts',
        'label': 'Triage Decision Prompts',
        'description': 'AI-powered email classification rules. These prompts control the RespondTo tool behavior you see in LangSmith traces.',
        'card_style': 'orange',
        'fields': [
            {
                'key': 'triage_no',
                'label': 'Ignore Rules - RespondTo tool (response=no)',
                'type': 'textarea',
                'description': 'CONTROLS MARK-AS-READ: When RespondTo tool returns response=no, the email is marked as read and ignored. Define criteria for emails that should be automatically filtered. Be specific to avoid dismissing important emails.',
                'placeholder': '- Automated emails from services that are spam\n- Cold outreach from vendors trying to sell products or services\n- Newsletter subscriptions and marketing emails\n- Automated calendar invitations',
                'rows': 12,
                'required': False,
                'note': 'Emails matching these criteria will be silently filtered. Be specific to avoid missing important communications.',
                'card_style': 'orange'
            },
            {
                'key': 'triage_notify',
                'label': 'Notify Rules - RespondTo tool (response=notify)',
                'type': 'textarea',
                'description': 'When RespondTo tool returns response=notify, you will be informed but email is marked as read. Define criteria for emails that need awareness but no response.',
                'placeholder': '- Google docs that were shared with you\n- DocuSign documents that need to be signed\n- Technical questions about AI development\n- Meeting requests that require attention but not immediate response',
                'rows': 12,
                'required': False,
                'note': 'These emails will appear in your notifications for awareness but won\'t be marked as urgent.',
                'card_style': 'orange'
            },
            {
                'key': 'triage_email',
                'label': 'Response Rules - RespondTo tool (response=email)',
                'type': 'textarea',
                'description': 'When RespondTo tool returns response=email, a draft is created and email stays unread. Define criteria for emails that require your direct response and AI-assisted drafting.',
                'placeholder': '- Emails from clients or collaborators that explicitly ask you a question\n- Emails from clients where someone scheduled a meeting and you haven\'t responded\n- Direct emails from lawyers or legal matters\n- Technical collaboration requests about your AI projects',
                'rows': 15,
                'required': False,
                'note': 'High-priority emails that need your attention and potentially AI-assisted response drafting.',
                'card_style': 'orange'
            }
        ]
    },
    {
        'key': 'ai_models',
        'label': 'AI Model APIs',
        'description': 'API keys for AI language models',
        'fields': [
            {
                'key': 'anthropic_api_key',
                'label': 'Anthropic API Key',
                'type': 'password',
                'description': 'API key for Claude models (primary)',
                'required': True,
                'placeholder': 'sk-ant-api03-...'
            },
            {
                'key': 'openai_api_key',
                'label': 'OpenAI API Key',
                'type': 'password',
                'description': 'API key for GPT models (backup)',
                'placeholder': 'sk-proj-...'
            }
        ]
    },
    {
        'key': 'langgraph_system',
        'label': 'LangGraph System',
        'description': 'Core LangGraph and monitoring configuration',
        'fields': [
            {
                'key': 'langsmith_api_key',
                'label': 'LangSmith API Key',
                'type': 'password',
                'description': 'API key for LangSmith monitoring and tracing',
                'placeholder': 'lsv2_pt_...'
            },
            {
                'key': 'langchain_project',
                'label': 'LangChain Project Name',
                'type': 'text',
                'default': 'ambient-email-agent',
                'readonly': True,
                'description': 'Project name for LangSmith organization (read-only - changing this can break things)'
            }
        ]
    },
    {
        'key': 'google_workspace',
        'label': 'Google Workspace Integration',
        'description': 'OAuth credentials for Gmail, Calendar, and Google services integration',
        'fields': [
            {
                'key': 'google_client_id',
                'label': 'Google Client ID',
                'type': 'text',
                'description': 'OAuth 2.0 client ID for Google services',
                'placeholder': '443821363207-e017ea00dg7kt4g6tn3uqa54ctp18uf2.apps.googleusercontent.com',
                'required': True,
                'note': 'From Google Cloud Console OAuth 2.0 client credentials'
            },
            {
                'key': 'google_client_secret',
                'label': 'Google Client Secret',
                'type': 'password',
                'description': 'OAuth 2.0 client secret for Google services',
                'placeholder': 'GOCSPX-...',
                'required': True,
                'note': 'Keep this secret secure'
            },
            {
                'key': 'gmail_refresh_token',
                'label': 'Gmail Refresh Token',
                'type': 'password',
                'description': 'OAuth 2.0 refresh token for Gmail access',
                'placeholder': '1//05q29uIyfXcBKCgYIARA...',
                'required': True,
                'note': 'Generated during initial OAuth setup - allows persistent Gmail access'
            },
            {
                'key': 'user_google_email',
                'label': 'User Google Email',
                'type': 'text',
                'description': 'Google account email address for this assistant',
                'placeholder': 'info@800m.ca',
                'required': True,
                'note': 'Must match the Gmail account used for OAuth setup'
            }
        ]
    },
    {
        'key': 'agent_identity',
        'label': 'Agent Identity',
        'description': 'Agent identification and operational status',
        'fields': [
            {
                'key': 'agent_name',
                'label': 'Agent Name',
                'type': 'text',
                'default': 'executive-ai-assistant',
                'readonly': True,
                'description': 'Internal agent identifier',
                'required': True
            },
            {
                'key': 'agent_display_name',
                'label': 'Display Name',
                'type': 'text',
                'default': 'Executive AI Assistant',
                'readonly': True,
                'description': 'Human-readable agent name',
                'required': True
            },
            {
                'key': 'agent_description',
                'label': 'Description',
                'type': 'textarea',
                'default': 'AI-powered executive assistant for email management, scheduling, and task automation',
                'readonly': True,
                'description': 'Agent capabilities and purpose',
                'rows': 3,
                'required': True
            },
            {
                'key': 'agent_status',
                'label': 'Agent Status',
                'type': 'select',
                'default': 'active',
                'description': 'Executive AI Assistant operational status',
                'options': ['active', 'disabled'],
                'required': True
            }
        ]
    }
]


def get_current_config():
    """Get current configuration values from config.py template"""
    try:
        from .config import LLM_CONFIG, AGENT_NAME, AGENT_DISPLAY_NAME, AGENT_DESCRIPTION, MCP_SERVICE
        from .prompt import AGENT_SYSTEM_PROMPT, AGENT_ROLE_PROMPT, AGENT_GUIDELINES_PROMPT

        return {
            'agent_identity': {
                'agent_name': AGENT_NAME,
                'agent_display_name': AGENT_DISPLAY_NAME,
                'agent_description': AGENT_DESCRIPTION
            },
            'llm': LLM_CONFIG,
            'mcp_integration': {
                # MCP server URL comes from environment variable
            },
            'prompt_templates': {
                'agent_system_prompt': AGENT_SYSTEM_PROMPT,
                'agent_role_prompt': AGENT_ROLE_PROMPT,
                'agent_guidelines_prompt': AGENT_GUIDELINES_PROMPT
            }
        }
    except ImportError:
        # Return template defaults if config doesn't exist yet
        return {
            'agent_identity': {
                'agent_name': 'template',
                'agent_display_name': 'Template Agent',
                'agent_description': 'Template for creating new MCP-based agents'
            },
            'llm': {
                'model': 'claude-sonnet-4-20250514',
                'temperature': 0.2,
                'max_tokens': 2000
            },
            'mcp_integration': {
                # MCP server URL comes from environment variable
            }
        }


def update_config_value(section_key: str, field_key: str, value):
    """Update configuration value in config.py template"""
    # TODO: Implement template config updating logic
    # This would modify the template variables in config.py
    pass
