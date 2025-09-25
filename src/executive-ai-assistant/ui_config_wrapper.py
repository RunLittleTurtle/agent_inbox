"""
Executive AI Assistant UI Configuration Wrapper
Non-breaking wrapper that translates between existing config.yaml/config.py and UI schema
"""
import yaml
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional

CONFIG_INFO = {
    'name': 'Executive AI Assistant',
    'description': 'AI-powered email management and executive assistance',
    'config_type': 'yaml_wrapper',
    'config_path': 'src/executive-ai-assistant/eaia/main/config.yaml'
}

CONFIG_SECTIONS = [
    {
        'key': 'profile',
        'label': 'Profile Settings',
        'description': 'Personal profile and identity configuration',
        'fields': [
            {
                'key': 'email',
                'label': 'Email Address',
                'type': 'text',
                'yaml_path': 'email',
                'description': 'Primary email address for the assistant',
                'required': True,
                'note': 'Also uses global USER_GOOGLE_EMAIL from main .env'
            },
            {
                'key': 'full_name',
                'label': 'Full Name',
                'type': 'text',
                'yaml_path': 'full_name',
                'description': 'Full name for email signatures and formal communication'
            },
            {
                'key': 'name',
                'label': 'Short Name',
                'type': 'text',
                'yaml_path': 'name',
                'description': 'Preferred short name for casual communication'
            },
            {
                'key': 'background',
                'label': 'Background',
                'type': 'textarea',
                'yaml_path': 'background',
                'description': 'Professional background and context for the assistant'
            },
            {
                'key': 'timezone',
                'label': 'Timezone',
                'type': 'select',
                'yaml_path': 'timezone',
                'envVar': 'USER_TIMEZONE',
                'default': 'America/Toronto',
                'description': 'Timezone for scheduling and time references',
                'options': [
                    'America/Toronto',
                    'America/Montreal',
                    'America/New_York',
                    'America/Los_Angeles',
                    'Europe/London',
                    'Europe/Paris',
                    'Asia/Tokyo'
                ],
                'note': 'Synced with global timezone setting'
            }
        ]
    },
    {
        'key': 'email_preferences',
        'label': 'Email Preferences',
        'description': 'Email writing style and behavior preferences',
        'fields': [
            {
                'key': 'response_preferences',
                'label': 'Response Style Preferences',
                'type': 'textarea',
                'yaml_path': 'response_preferences',
                'description': 'Guidelines for email tone and style matching',
                'placeholder': 'e.g., Match sender tone, be direct and professional...'
            },
            {
                'key': 'rewrite_preferences',
                'label': 'Rewrite Preferences',
                'type': 'textarea',
                'yaml_path': 'rewrite_preferences',
                'description': 'Detailed preferences for how emails should be rewritten',
                'rows': 8
            },
            {
                'key': 'schedule_preferences',
                'label': 'Schedule Preferences',
                'type': 'textarea',
                'yaml_path': 'schedule_preferences',
                'description': 'Default scheduling preferences and meeting settings',
                'placeholder': 'e.g., Default 30-minute meetings unless specified...'
            },
            {
                'key': 'background_preferences',
                'label': 'Background Preferences',
                'type': 'textarea',
                'yaml_path': 'background_preferences',
                'description': 'Context about technical interests and engagement preferences'
            }
        ]
    },
    {
        'key': 'triage_settings',
        'label': 'Email Triage Settings',
        'description': 'Email filtering and categorization rules',
        'fields': [
            {
                'key': 'triage_no',
                'label': 'Auto-Archive Rules',
                'type': 'textarea',
                'yaml_path': 'triage_no',
                'description': 'Emails that should be automatically archived (no action needed)',
                'placeholder': '- Automated emails from services\n- Cold outreach from vendors...',
                'rows': 6
            },
            {
                'key': 'triage_notify',
                'label': 'Notification Rules',
                'type': 'textarea',
                'yaml_path': 'triage_notify',
                'description': 'Emails that require notification but no immediate response',
                'placeholder': '- Google docs shared\n- DocuSign documents...',
                'rows': 6
            },
            {
                'key': 'triage_email',
                'label': 'Response Required Rules',
                'type': 'textarea',
                'yaml_path': 'triage_email',
                'description': 'Emails that require active response from the user',
                'placeholder': '- Direct questions from clients\n- Meeting requests...',
                'rows': 8
            }
        ]
    },
    {
        'key': 'features',
        'label': 'Features',
        'description': 'Enable/disable assistant features',
        'fields': [
            {
                'key': 'memory',
                'label': 'Memory Storage',
                'type': 'boolean',
                'yaml_path': 'memory',
                'default': True,
                'description': 'Enable conversation memory and context retention'
            },
            {
                'key': 'enable_gmail_integration',
                'label': 'Gmail Integration',
                'type': 'boolean',
                'default': True,
                'description': 'Enable Gmail MCP integration',
                'note': 'Requires MCP servers configured in main .env'
            },
            {
                'key': 'enable_calendar_integration',
                'label': 'Calendar Integration',
                'type': 'boolean',
                'default': True,
                'description': 'Enable Google Calendar integration for scheduling'
            },
            {
                'key': 'enable_auto_triage',
                'label': 'Auto Triage',
                'type': 'boolean',
                'default': True,
                'description': 'Automatically categorize incoming emails'
            },
            {
                'key': 'enable_draft_generation',
                'label': 'Draft Generation',
                'type': 'boolean',
                'default': True,
                'description': 'Generate email drafts for user review'
            }
        ]
    },
    {
        'key': 'llm_settings',
        'label': 'AI Model Settings',
        'description': 'Language model configuration for email processing',
        'fields': [
            {
                'key': 'model',
                'label': 'Primary Model',
                'type': 'select',
                'default': 'claude-3-5-sonnet-20241022',
                'description': 'AI model for email analysis and generation',
                'options': [
                    'claude-3-5-sonnet-20241022',
                    'claude-sonnet-4-20250514',
                    'gpt-4o',
                    'gpt-4o-mini'
                ],
                'note': 'Uses global ANTHROPIC_API_KEY from main .env'
            },
            {
                'key': 'temperature',
                'label': 'Temperature',
                'type': 'number',
                'default': 0.1,
                'description': 'Model creativity level (0.0 = focused, 1.0 = creative)',
                'validation': {'min': 0.0, 'max': 1.0, 'step': 0.1}
            },
            {
                'key': 'max_tokens',
                'label': 'Max Tokens',
                'type': 'number',
                'default': 2000,
                'description': 'Maximum tokens per response',
                'validation': {'min': 100, 'max': 8192}
            }
        ]
    }
]


class ExecutiveAIConfigManager:
    """Wrapper class to manage config.yaml while providing UI schema interface"""

    def __init__(self):
        self.config_path = Path(__file__).parent / 'eaia' / 'main' / 'config.yaml'

    async def get_current_config(self) -> Dict[str, Any]:
        """Get current configuration from config.yaml"""
        try:
            if not self.config_path.exists():
                return self._get_default_config()

            def _load_yaml():
                with open(self.config_path, 'r') as f:
                    return yaml.safe_load(f)

            config_data = await asyncio.to_thread(_load_yaml)
            return self._transform_yaml_to_ui_format(config_data)

        except Exception as e:
            print(f"Error loading config: {e}")
            return self._get_default_config()

    def _transform_yaml_to_ui_format(self, yaml_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform YAML data to UI section format"""
        ui_data = {
            'profile': {
                'email': yaml_data.get('email', ''),
                'full_name': yaml_data.get('full_name', ''),
                'name': yaml_data.get('name', ''),
                'background': yaml_data.get('background', ''),
                'timezone': yaml_data.get('timezone', 'America/Toronto')
            },
            'email_preferences': {
                'response_preferences': yaml_data.get('response_preferences', ''),
                'rewrite_preferences': yaml_data.get('rewrite_preferences', ''),
                'schedule_preferences': yaml_data.get('schedule_preferences', ''),
                'background_preferences': yaml_data.get('background_preferences', '')
            },
            'triage_settings': {
                'triage_no': yaml_data.get('triage_no', ''),
                'triage_notify': yaml_data.get('triage_notify', ''),
                'triage_email': yaml_data.get('triage_email', '')
            },
            'features': {
                'memory': yaml_data.get('memory', True),
                'enable_gmail_integration': True,
                'enable_calendar_integration': True,
                'enable_auto_triage': True,
                'enable_draft_generation': True
            },
            'llm_settings': {
                'model': 'claude-3-5-sonnet-20241022',
                'temperature': 0.1,
                'max_tokens': 2000
            }
        }
        return ui_data

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration when config.yaml doesn't exist"""
        return {
            'profile': {
                'email': '',
                'full_name': '',
                'name': '',
                'background': '',
                'timezone': 'America/Toronto'
            },
            'email_preferences': {
                'response_preferences': '',
                'rewrite_preferences': '',
                'schedule_preferences': 'By default, unless specified otherwise, you should make meetings 30 minutes long.',
                'background_preferences': ''
            },
            'triage_settings': {
                'triage_no': '',
                'triage_notify': '',
                'triage_email': ''
            },
            'features': {
                'memory': True,
                'enable_gmail_integration': True,
                'enable_calendar_integration': True,
                'enable_auto_triage': True,
                'enable_draft_generation': True
            },
            'llm_settings': {
                'model': 'claude-3-5-sonnet-20241022',
                'temperature': 0.1,
                'max_tokens': 2000
            }
        }

    async def update_config_value(self, section_key: str, field_key: str, value: Any):
        """Update a configuration value in config.yaml"""
        try:
            # Load current config
            config_data = {}
            if self.config_path.exists():
                def _load_yaml():
                    with open(self.config_path, 'r') as f:
                        return yaml.safe_load(f) or {}
                config_data = await asyncio.to_thread(_load_yaml)

            # Update the value based on section and field
            yaml_path = self._get_yaml_path_for_field(section_key, field_key)
            if yaml_path:
                config_data[yaml_path] = value

            # Save back to YAML
            def _save_yaml():
                self.config_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.config_path, 'w') as f:
                    yaml.safe_dump(config_data, f, default_flow_style=False, sort_keys=False)

            await asyncio.to_thread(_save_yaml)
            return True

        except Exception as e:
            print(f"Error updating config: {e}")
            return False

    def _get_yaml_path_for_field(self, section_key: str, field_key: str) -> Optional[str]:
        """Get the YAML path for a UI field"""
        # Map UI field paths to YAML paths
        field_mapping = {
            ('profile', 'email'): 'email',
            ('profile', 'full_name'): 'full_name',
            ('profile', 'name'): 'name',
            ('profile', 'background'): 'background',
            ('profile', 'timezone'): 'timezone',
            ('email_preferences', 'response_preferences'): 'response_preferences',
            ('email_preferences', 'rewrite_preferences'): 'rewrite_preferences',
            ('email_preferences', 'schedule_preferences'): 'schedule_preferences',
            ('email_preferences', 'background_preferences'): 'background_preferences',
            ('triage_settings', 'triage_no'): 'triage_no',
            ('triage_settings', 'triage_notify'): 'triage_notify',
            ('triage_settings', 'triage_email'): 'triage_email',
            ('features', 'memory'): 'memory'
        }

        return field_mapping.get((section_key, field_key))


# Global instance for easy access
config_manager = ExecutiveAIConfigManager()


def get_current_config():
    """Get current configuration (sync wrapper)"""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If already in async context, create a new task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, config_manager.get_current_config())
                return future.result()
        else:
            return asyncio.run(config_manager.get_current_config())
    except Exception:
        return config_manager._get_default_config()


def update_config_value(section_key: str, field_key: str, value: Any):
    """Update configuration value (sync wrapper)"""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If already in async context, create a new task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(
                    asyncio.run,
                    config_manager.update_config_value(section_key, field_key, value)
                )
                return future.result()
        else:
            return asyncio.run(config_manager.update_config_value(section_key, field_key, value))
    except Exception as e:
        print(f"Error updating config: {e}")
        return False