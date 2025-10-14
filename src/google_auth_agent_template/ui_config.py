"""
UI Configuration Schema - TEMPLATE
Defines configuration UI structure for config-app integration.

CUSTOMIZATION REQUIRED:
1. Replace {DOMAIN} with your agent domain
2. Update field descriptions and examples
3. Add domain-specific configuration sections
4. Customize default values

This schema is used by the config-app UI to:
- Generate configuration forms
- Validate user inputs
- Store agent-specific settings in Supabase
"""
from typing import Dict, Any, List

# TODO: Replace {DOMAIN} with your agent name (e.g., "contacts", "email", "calendar")
AGENT_NAME = "{DOMAIN}_agent"
AGENT_DISPLAY_NAME = "{Domain} Agent"  # TODO: Capitalize first letter


def get_ui_config() -> Dict[str, Any]:
    """
    Get UI configuration schema for this agent.

    Returns:
        Dict defining configuration sections, fields, and validation rules
    """
    return {
        "agent_name": AGENT_NAME,
        "agent_display_name": AGENT_DISPLAY_NAME,
        "agent_description": f"Manage your Google {AGENT_DISPLAY_NAME} with AI assistance",
        "sections": [
            # ==================================================================
            # SECTION 1: Agent Identity (mostly cosmetic)
            # ==================================================================
            {
                "section_id": "identity",
                "section_title": "Agent Identity",
                "section_description": "Basic agent information and branding",
                "fields": [
                    {
                        "field_id": "agent_name",
                        "field_type": "text",
                        "label": "Agent Name",
                        "description": f"Display name for this agent",
                        "default_value": AGENT_DISPLAY_NAME,
                        "required": True,
                        "placeholder": f"{AGENT_DISPLAY_NAME}",
                    },
                    {
                        "field_id": "agent_description",
                        "field_type": "textarea",
                        "label": "Agent Description",
                        "description": "Brief description of what this agent does",
                        "default_value": f"AI assistant for managing Google {AGENT_DISPLAY_NAME}",
                        "required": False,
                        "placeholder": "Enter agent description...",
                    },
                ]
            },

            # ==================================================================
            # SECTION 2: User Preferences
            # ==================================================================
            {
                "section_id": "user_preferences",
                "section_title": "User Preferences",
                "section_description": "Personal settings and preferences",
                "fields": [
                    {
                        "field_id": "timezone",
                        "field_type": "select",
                        "label": "Timezone",
                        "description": "Your timezone for accurate scheduling and time-aware operations",
                        "default_value": "America/Toronto",
                        "required": True,
                        "options": [
                            {"value": "global", "label": "Use Global Timezone (from .env)"},
                            {"value": "America/Toronto", "label": "Eastern Time (Toronto)"},
                            {"value": "America/New_York", "label": "Eastern Time (New York)"},
                            {"value": "America/Chicago", "label": "Central Time"},
                            {"value": "America/Denver", "label": "Mountain Time"},
                            {"value": "America/Los_Angeles", "label": "Pacific Time"},
                            {"value": "Europe/London", "label": "London"},
                            {"value": "Europe/Paris", "label": "Paris"},
                            {"value": "Asia/Tokyo", "label": "Tokyo"},
                            {"value": "UTC", "label": "UTC"},
                        ],
                        "help_text": "CRITICAL: Timezone context is always included in the first system message so the agent knows current date/time"
                    },
                    # TODO: Add domain-specific preferences
                    # Example for Calendar:
                    # {
                    #     "field_id": "default_event_duration",
                    #     "field_type": "number",
                    #     "label": "Default Event Duration (minutes)",
                    #     "default_value": 60,
                    #     "min": 15,
                    #     "max": 480,
                    # },
                    # Example for Email:
                    # {
                    #     "field_id": "email_signature",
                    #     "field_type": "textarea",
                    #     "label": "Email Signature",
                    #     "default_value": "Best regards,\n[Your Name]",
                    # },
                    # Example for Contacts:
                    # {
                    #     "field_id": "default_contact_group",
                    #     "field_type": "text",
                    #     "label": "Default Contact Group",
                    #     "default_value": "myContacts",
                    # },
                ]
            },

            # ==================================================================
            # SECTION 3: LLM Configuration
            # ==================================================================
            {
                "section_id": "llm_config",
                "section_title": "LLM Configuration",
                "section_description": "Language model settings for this agent",
                "fields": [
                    {
                        "field_id": "model",
                        "field_type": "select",
                        "label": "LLM Model",
                        "description": "Language model to use for this agent",
                        "default_value": "claude-3-5-sonnet-20241022",
                        "required": True,
                        "options": [
                            {"value": "claude-3-5-sonnet-20241022", "label": "Claude 3.5 Sonnet (Recommended)"},
                            {"value": "claude-3-7-sonnet-20250219", "label": "Claude 3.7 Sonnet (Latest)"},
                            {"value": "gpt-4o", "label": "GPT-4o"},
                            {"value": "gpt-4o-mini", "label": "GPT-4o Mini"},
                        ],
                    },
                    {
                        "field_id": "temperature",
                        "field_type": "number",
                        "label": "Temperature",
                        "description": "Creativity vs consistency (0.0 = consistent, 1.0 = creative)",
                        "default_value": 0.1,
                        "required": True,
                        "min": 0.0,
                        "max": 1.0,
                        "step": 0.1,
                    },
                    {
                        "field_id": "max_tokens",
                        "field_type": "number",
                        "label": "Max Tokens",
                        "description": "Maximum response length",
                        "default_value": 4096,
                        "required": True,
                        "min": 256,
                        "max": 8192,
                        "step": 256,
                    },
                ]
            },

            # ==================================================================
            # SECTION 4: Prompt Templates
            # ==================================================================
            {
                "section_id": "prompt_templates",
                "section_title": "Prompt Templates",
                "section_description": "Customize agent instructions and behavior",
                "fields": [
                    {
                        "field_id": "agent_system_prompt",
                        "field_type": "textarea",
                        "label": "Agent System Prompt",
                        "description": "Main instructions for the agent (supports {current_time}, {timezone_name}, {today}, {tomorrow} placeholders)",
                        "default_value": "",  # Loaded from prompt.py if empty
                        "required": False,
                        "placeholder": "Leave empty to use default prompt from code",
                        "rows": 15,
                    },
                    # TODO: Add additional prompt templates if needed
                    # Example for approval workflows:
                    # {
                    #     "field_id": "approval_prompt",
                    #     "field_type": "textarea",
                    #     "label": "Approval Prompt",
                    #     "description": "Instructions for approval workflow",
                    #     "default_value": "",
                    # },
                ]
            },

            # ==================================================================
            # SECTION 5: Google Integration (OAuth & API settings)
            # ==================================================================
            {
                "section_id": "google_integration",
                "section_title": "Google Integration",
                "section_description": f"Google {AGENT_DISPLAY_NAME} API and OAuth settings",
                "fields": [
                    {
                        "field_id": "google_oauth_connected",
                        "field_type": "readonly",
                        "label": "OAuth Status",
                        "description": "Google account connection status",
                        "default_value": "Not Connected",
                        "help_text": "Click 'Connect Google Account' button to authenticate",
                    },
                    # TODO: Add domain-specific Google API settings
                    # Example for Calendar:
                    # {
                    #     "field_id": "primary_calendar_id",
                    #     "field_type": "text",
                    #     "label": "Primary Calendar ID",
                    #     "default_value": "primary",
                    #     "description": "ID of your primary calendar",
                    # },
                    # {
                    #     "field_id": "max_events",
                    #     "field_type": "number",
                    #     "label": "Max Events to Fetch",
                    #     "default_value": 10,
                    #     "min": 1,
                    #     "max": 100,
                    # },
                    #
                    # Example for Email:
                    # {
                    #     "field_id": "max_emails",
                    #     "field_type": "number",
                    #     "label": "Max Emails to Fetch",
                    #     "default_value": 20,
                    #     "min": 1,
                    #     "max": 100,
                    # },
                    # {
                    #     "field_id": "default_labels",
                    #     "field_type": "text",
                    #     "label": "Default Gmail Labels",
                    #     "default_value": "INBOX",
                    #     "description": "Comma-separated labels to filter by",
                    # },
                    #
                    # Example for Contacts:
                    # {
                    #     "field_id": "max_contacts",
                    #     "field_type": "number",
                    #     "label": "Max Contacts to Fetch",
                    #     "default_value": 50,
                    #     "min": 1,
                    #     "max": 200,
                    # },
                ]
            },

            # ==================================================================
            # SECTION 6: Behavior Settings (domain-specific)
            # ==================================================================
            {
                "section_id": "behavior",
                "section_title": "Behavior Settings",
                "section_description": "Agent behavior and feature flags",
                "fields": [
                    {
                        "field_id": "enable_verbose_logging",
                        "field_type": "toggle",
                        "label": "Verbose Logging",
                        "description": "Enable detailed logging for debugging",
                        "default_value": False,
                        "required": False,
                    },
                    # TODO: Add domain-specific behavior settings
                    # Example for agents with write operations:
                    # {
                    #     "field_id": "enable_human_in_loop",
                    #     "field_type": "toggle",
                    #     "label": "Require Approval",
                    #     "description": "Require human approval before making changes",
                    #     "default_value": True,
                    # },
                    # {
                    #     "field_id": "auto_confirm_simple_actions",
                    #     "field_type": "toggle",
                    #     "label": "Auto-Confirm Simple Actions",
                    #     "description": "Skip approval for low-risk actions",
                    #     "default_value": False,
                    # },
                ]
            },
        ],

        # ==================================================================
        # OAuth Configuration
        # ==================================================================
        "oauth_config": {
            "provider": "google",
            "scopes": [
                # TODO: Update with your required scopes
                # Must match config.py GOOGLE_OAUTH_SCOPES
                "https://www.googleapis.com/auth/REPLACE_WITH_YOUR_SCOPE",
            ],
            "callback_path": f"/api/oauth/google/{AGENT_NAME}/callback",
        },
    }


# ==========================================================================
# Validation Rules (Optional)
# ==========================================================================

def validate_config(config: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate agent configuration.

    Args:
        config: Configuration dict to validate

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    # Example validations
    if config.get("llm_config", {}).get("temperature", 0) > 1.0:
        errors.append("Temperature must be between 0.0 and 1.0")

    if config.get("llm_config", {}).get("max_tokens", 0) < 256:
        errors.append("Max tokens must be at least 256")

    # TODO: Add domain-specific validations
    # Example for Calendar:
    # if config.get("google_integration", {}).get("max_events", 0) > 100:
    #     errors.append("Max events cannot exceed 100")

    return len(errors) == 0, errors
