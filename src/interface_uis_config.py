"""
Interface UIs Configuration
Environment-aware configuration for connecting UI interfaces to LangGraph deployments

This page displays deployment values for configuring:
- Agent Chat UI instances (agent-chat-ui-1, agent-chat-ui-2)
- Agent Inbox instances (multi-agent system, executive AI)

Deployment URLs are read-only and pulled from environment.
LangSmith API keys are user-specific and stored in Supabase.
"""
import os

# Detect environment mode
DEPLOYMENT_ENV = os.getenv('DEPLOYMENT_ENV', 'local')  # 'local' or 'production'

# Production LangGraph Cloud URL (all graphs use same deployment)
PRODUCTION_DEPLOYMENT_URL = os.getenv('LANGGRAPH_CLOUD_URL', 'https://multi-agent-app-1d1e061875eb5640a47e3bb201edb076.us.langgraph.app')

# Local development URLs (different ports for different graphs)
LOCAL_MULTI_AGENT_URL = 'http://localhost:2024'
LOCAL_EXECUTIVE_URL = 'http://localhost:2025'

# Choose URLs based on environment
# In production: same URL, different graph IDs
# In local: different URLs (ports) for each graph
MULTI_AGENT_DEPLOYMENT_URL = PRODUCTION_DEPLOYMENT_URL if DEPLOYMENT_ENV == 'production' else LOCAL_MULTI_AGENT_URL
EXECUTIVE_DEPLOYMENT_URL = PRODUCTION_DEPLOYMENT_URL if DEPLOYMENT_ENV == 'production' else LOCAL_EXECUTIVE_URL

CONFIG_INFO = {
    'name': 'Interface UIs',
    'description': f'UI interface configuration ({DEPLOYMENT_ENV} mode)',
    'config_type': 'interface_uis',
    'config_path': 'src/interface_uis_config.py'
}

CONFIG_SECTIONS = [
    {
        'key': 'agent_chat_ui_2',
        'label': 'Agent Chat UI 2 - Multi-Agent System',
        'description': 'Configuration for your second Agent Chat UI instance (parallel conversations)',
        'fields': [
            {
                'key': 'chat2_deployment_url',
                'label': 'Deployment URL',
                'type': 'text',
                'default': MULTI_AGENT_DEPLOYMENT_URL,
                'readonly': True,
                'showCopyButton': True,
                'description': f'Same multi-agent deployment URL ({DEPLOYMENT_ENV})'
            },
            {
                'key': 'chat2_graph_id',
                'label': 'Assistant / Graph ID',
                'type': 'text',
                'default': 'agent',
                'readonly': True,
                'showCopyButton': True,
                'description': 'Same graph ID for parallel conversations'
            },
            {
                'key': 'chat2_langsmith_key',
                'label': 'Your LangSmith API Key',
                'type': 'password',
                'default': '',
                'readonly': False,
                'showCopyButton': False,
                'description': 'Your personal LangSmith API key for tracing (optional)',
                'placeholder': 'lsv2_pt_...'
            }
        ]
    },
    {
        'key': 'agent_inbox_multi',
        'label': 'Agent Inbox - Multi-Agent System',
        'description': 'Configuration for Agent Inbox with multi-agent workflows',
        'fields': [
            {
                'key': 'multi_graph_id',
                'label': 'Assistant/Graph ID',
                'type': 'text',
                'default': 'agent',
                'readonly': True,
                'showCopyButton': True,
                'description': 'Multi-agent system graph ID'
            },
            {
                'key': 'multi_deployment_url',
                'label': 'Deployment URL',
                'type': 'text',
                'default': MULTI_AGENT_DEPLOYMENT_URL,
                'readonly': True,
                'showCopyButton': True,
                'description': f'Multi-agent deployment URL ({DEPLOYMENT_ENV})'
            },
            {
                'key': 'multi_name',
                'label': 'Inbox Name',
                'type': 'text',
                'default': 'Multi-Agent System',
                'readonly': False,
                'showCopyButton': False,
                'description': 'Optional display name for this inbox',
                'placeholder': 'Multi-Agent System'
            }
        ]
    },
    {
        'key': 'agent_inbox_executive',
        'label': 'Agent Inbox - Executive AI Assistant',
        'description': 'Configuration for Executive AI Assistant inbox',
        'fields': [
            {
                'key': 'exec_graph_id',
                'label': 'Assistant/Graph ID',
                'type': 'text',
                'default': 'main',
                'readonly': True,
                'showCopyButton': True,
                'description': 'Executive AI uses main graph'
            },
            {
                'key': 'exec_deployment_url',
                'label': 'Deployment URL',
                'type': 'text',
                'default': EXECUTIVE_DEPLOYMENT_URL,
                'readonly': True,
                'showCopyButton': True,
                'description': f'Executive AI deployment URL ({DEPLOYMENT_ENV})'
            },
            {
                'key': 'exec_name',
                'label': 'Inbox Name',
                'type': 'text',
                'default': 'Executive AI Assistant',
                'readonly': False,
                'showCopyButton': False,
                'description': 'Optional display name for executive inbox',
                'placeholder': 'Executive AI Assistant'
            }
        ]
    }
]
