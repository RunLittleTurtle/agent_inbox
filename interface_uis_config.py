"""
Interface UIs Configuration
Reference values for connecting UI interfaces
"""

CONFIG_INFO = {
    'name': 'Interface UIs',
    'description': 'Configuration reference for UI interfaces',
    'config_type': 'interface_uis',
    'config_path': 'interface_uis_config.py'
}

CONFIG_SECTIONS = [
    {
        'key': 'agent_chat_ui_1',
        'label': 'Agent Chat UI 1 - Multi-Agent System',
        'description': 'Copy these values for your first Agent Chat UI instance',
        'fields': [
            {
                'key': 'chat1_deployment_url',
                'label': 'Deployment URL',
                'type': 'text',
                'envVar': 'LANGGRAPH_DEPLOYMENT_URL',
                'readonly': True,
                'showCopyButton': True,
                'description': 'LangGraph deployment URL from environment'
            },
            {
                'key': 'chat1_graph_id',
                'label': 'Assistant / Graph ID',
                'type': 'text',
                'envVar': 'AGENT_INBOX_GRAPH_ID',
                'readonly': True,
                'showCopyButton': True,
                'description': 'Graph ID from environment'
            },
            {
                'key': 'chat1_langsmith_key',
                'label': 'LangSmith API Key',
                'type': 'password',
                'envVar': 'LANGSMITH_API_KEY',
                'readonly': True,
                'showCopyButton': True,
                'description': 'Optional for local development'
            }
        ]
    },
    {
        'key': 'agent_chat_ui_2',
        'label': 'Agent Chat UI 2 - Multi-Agent System',
        'description': 'Copy these values for your second Agent Chat UI instance',
        'fields': [
            {
                'key': 'chat2_deployment_url',
                'label': 'Deployment URL',
                'type': 'text',
                'envVar': 'LANGGRAPH_DEPLOYMENT_URL',
                'readonly': True,
                'showCopyButton': True,
                'description': 'Same deployment URL for parallel conversations'
            },
            {
                'key': 'chat2_graph_id',
                'label': 'Assistant / Graph ID',
                'type': 'text',
                'envVar': 'AGENT_INBOX_GRAPH_ID',
                'readonly': True,
                'showCopyButton': True,
                'description': 'Same graph ID for parallel conversations'
            },
            {
                'key': 'chat2_langsmith_key',
                'label': 'LangSmith API Key',
                'type': 'password',
                'envVar': 'LANGSMITH_API_KEY',
                'readonly': True,
                'showCopyButton': True,
                'description': 'Optional for local development'
            }
        ]
    },
    {
        'key': 'agent_inbox_multi',
        'label': 'Agent Inbox - Multi-Agent System',
        'description': 'For general multi-agent workflows with human oversight',
        'fields': [
            {
                'key': 'multi_graph_id',
                'label': 'Assistant/Graph ID',
                'type': 'text',
                'envVar': 'AGENT_INBOX_GRAPH_ID',
                'readonly': True,
                'showCopyButton': True,
                'description': 'Multi-agent system graph ID'
            },
            {
                'key': 'multi_deployment_url',
                'label': 'Deployment URL',
                'type': 'text',
                'envVar': 'LANGGRAPH_DEPLOYMENT_URL',
                'readonly': True,
                'showCopyButton': True,
                'description': 'Multi-agent system deployment URL'
            },
            {
                'key': 'multi_name',
                'label': 'Name',
                'type': 'text',
                'default': 'Multi-Agent System',
                'readonly': True,
                'showCopyButton': True,
                'description': 'Display name for this inbox configuration'
            }
        ]
    },
    {
        'key': 'agent_inbox_executive',
        'label': 'Agent Inbox - Executive AI Assistant',
        'description': 'For executive decision workflows and strategic planning',
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
                'default': 'http://localhost:2025',
                'readonly': True,
                'showCopyButton': True,
                'description': 'Executive AI runs on port 2025'
            },
            {
                'key': 'exec_name',
                'label': 'Name',
                'type': 'text',
                'default': 'Executive AI Assistant',
                'readonly': True,
                'showCopyButton': True,
                'description': 'Display name for executive inbox'
            }
        ]
    }
]