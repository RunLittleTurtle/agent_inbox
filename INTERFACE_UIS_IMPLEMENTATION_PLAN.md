# Interface UIs Implementation Plan

## Context: Why Interface UIs Section

### Goal
Provide users with a centralized location to view all the configuration values they need to connect to different UI interfaces (Agent Chat, Agent Inbox) without having to hunt through environment files or guess values.

### User Experience Problem Solved
Currently, when users want to set up Agent Chat UI or Agent Inbox, they see setup dialogs asking for:
- Deployment URL
- Assistant/Graph ID
- LangSmith API Key

Users have to manually find these values in `.env` files or guess them. This creates friction and potential errors.

### Solution: Interface UIs Configuration Section
A read-only reference section showing exact values to copy for each interface:

**Agent Chat UI**: Real-time conversation interface
- Purpose: Direct chat with multi-agent system
- Fields: All read-only, sourced from environment variables
- User copies values into Agent Chat UI setup dialog

**Agent Chat UI 2**: Secondary conversation interface
- Purpose: Parallel conversations (same config as UI 1)
- Benefit: Users can have multiple conversations simultaneously
- Fields: Identical to Agent Chat UI (separate section for clarity)

**Agent Inbox**: Human-in-the-loop workflow management
- **Multi-Agent System**: Main workflow management (graph ID: `agent`, port: 2024)
- **Executive AI Assistant**: Strategic decision workflows (graph ID: `main`, port: 2025)
- Purpose: Users choose appropriate inbox based on workflow needs

### Field Behavior
- **All fields read-only**: Users cannot edit, only copy values
- **Environment sync**: Values automatically reflect current `.env` settings
- **Copy-friendly**: Values displayed clearly for easy copying into interface setup dialogs

### User Workflow
1. User opens Interface UIs section in config
2. User sees current values for all interfaces
3. User copies appropriate values into interface setup dialog
4. Interface connects successfully with correct configuration

## Current System Analysis

### How Existing Agent Configs Work:
1. **Agent Discovery**: `/api/config/agents` scans `AGENT_CONFIG_PATHS` array for ui_config.py files
2. **Auto-sidebar**: Agents with `config_type !== 'env_file'` appear automatically in sidebar
3. **Two-way Sync**: Fields with `envVar` property update .env file; others update config files
4. **Read-only Fields**: Fields with `readonly: True` are not editable
5. **Values Loading**: `/api/config/values` loads current values from .env or config files

### Pattern Used by All Agents:
```python
CONFIG_INFO = {
    'name': 'Agent Name',
    'description': 'Description',
    'config_type': 'some_config',  # anything except 'env_file'
    'config_path': 'src/agent_name/ui_config.py'
}

CONFIG_SECTIONS = [
    {
        'key': 'section_name',
        'fields': [
            {
                'key': 'field_name',
                'type': 'text',
                'envVar': 'ENVIRONMENT_VAR',  # enables .env two-way sync
                'readonly': True,             # makes field non-editable
                'description': 'Field description'
            }
        ]
    }
]
```

## Simple Implementation Plan

### Step 1: Add to Agent Discovery (1 line change)
**File**: `config-app/src/app/api/config/agents/route.ts`
**Change**: Add `'src/interface_uis/ui_config.py'` to `AGENT_CONFIG_PATHS` array

### Step 2: Create Interface UIs Config (1 new file)
**File**: `src/interface_uis/ui_config.py`
**Content**: Follow exact same pattern as other agents with:
- `CONFIG_INFO` with unique `config_type`
- `CONFIG_SECTIONS` with read-only fields using `envVar` for .env values
- Fields for Agent Inbox (2 configs), Agent Chat UI, Agent Chat UI 2

### Step 3: Test Auto-Integration
- No frontend changes needed
- No API changes needed
- Uses existing `/api/config/values` and `/api/config/update`
- Appears automatically in sidebar
- Two-way sync works automatically

## Interface UIs Sections Structure

```python
CONFIG_SECTIONS = [
    {
        'key': 'agent_inbox',
        'label': 'Agent Inbox Configurations',
        'fields': [
            # Multi-Agent System fields (readonly, envVar mapped)
            # Executive AI System fields (readonly, hardcoded values)
        ]
    },
    {
        'key': 'agent_chat_ui',
        'label': 'Agent Chat UI',
        'fields': [
            # Deployment URL (readonly, envVar: 'LANGGRAPH_DEPLOYMENT_URL')
            # Graph ID (readonly, envVar: 'AGENT_INBOX_GRAPH_ID')
            # LangSmith Key (readonly, envVar: 'LANGSMITH_API_KEY')
        ]
    },
    {
        'key': 'agent_chat_ui_2',
        'label': 'Agent Chat UI 2',
        'fields': [
            # Same as agent_chat_ui (for parallel usage)
        ]
    }
]
```

## Why This Works
- **Zero complexity**: Uses existing system exactly as designed
- **Auto-discovery**: No special handling needed
- **Two-way sync**: Automatic via `envVar` properties
- **Read-only**: Automatic via `readonly: True`
- **5-minute implementation**: Just 1 line change + 1 new file

## Total Changes Required
1. **1 line**: Add path to `AGENT_CONFIG_PATHS`
2. **1 file**: Create `src/interface_uis/ui_config.py`
3. **0 frontend changes**: Uses existing components
4. **0 API changes**: Uses existing endpoints

This follows Next.js and existing codebase patterns perfectly.