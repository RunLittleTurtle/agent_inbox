# Config Setup Guide

Complete guide for setting up configuration integration between your React Agent and the Agent Inbox config app.

## Overview

The config system follows a clear hierarchy:

1. **Main .env file** - Contains all environment variables (MCP URLs, API keys)
2. **Agent's config.py** - Reads FROM .env using `os.getenv()`, specifies WHICH env vars to use
3. **UI config & prompts** - Read FROM config.py, never directly from .env

**Key Principle**: The config.py acts as the bridge - it reads from .env, while UI and prompts read from config.py.

The config system provides a modern web UI at `http://localhost:3004` for managing agent settings with a sophisticated card-based interface organized into 7 visual categories.

## Core Components

### 1. Configuration Files Structure

```
src/your_agent/
├── config.py           # Main configuration (Python values)
├── ui_config.py        # UI schema definition
├── prompt.py           # System prompts
└── ...
```

### 2. Data Flow Architecture

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│   Main      │  →→→  │   Agent's   │  →→→  │  UI Config  │
│   .env      │       │   config.py │       │  & Prompts  │
└─────────────┘       └─────────────┘       └─────────────┘
     ↑                       ↑                       ↑
     │                       │                       │
  MCP URLs,              os.getenv()            Read from
  API Keys               reads from             config.py
                            .env                   only
```

**Key Points**:
- The `.env` file contains the actual MCP server URLs and API keys
- Each agent's `config.py` uses `os.getenv()` to read FROM .env
- The UI config (`ui_config.py`) and prompts (`prompt.py`) read FROM config.py
- This ensures secrets stay in .env while agents manage their own configuration

### 3. Config App Integration

The config app (located at `config-app/`) provides:
- Modern card-based web UI with 7 distinct card types for different configuration categories
- Automatic card type selection and visual grouping
- API endpoints for reading/writing config values with real-time updates
- Two-way sync between UI and Python files
- Color-coded categories with visual headers for better organization

## Step-by-Step Setup

### Step 1: Configure Agent Identity

In your agent's `config.py`, replace ALL placeholder values.

**IMPORTANT**: The config.py file reads values FROM the main .env file using `os.getenv()`. The UI config and prompts then read FROM config.py, not directly from .env:

```python
# TODO: Configure for your agent
AGENT_NAME = "gmail"  # Internal identifier (no spaces, lowercase)
AGENT_DISPLAY_NAME = "Gmail Agent"  # Human-readable name
AGENT_DESCRIPTION = "email management and organization"  # Brief description
AGENT_STATUS = "active"  # "active" or "disabled"

# MCP Configuration - specify the exact environment variable name
# This is flexible - works with any MCP provider:
#   - Pipedream: "PIPEDREAM_MCP_SERVER_google_gmail"
#   - Composio: "COMPOSIO_MCP_SERVER_slack"
#   - Custom: "MY_CUSTOM_MCP_SERVER"
MCP_ENV_VAR = "PIPEDREAM_MCP_SERVER_google_gmail"  # Your MCP server env var
```

**Critical**:
- Remove ALL `{PLACEHOLDER}` values - the config UI will not work with placeholders
- The MCP_ENV_VAR specifies WHICH environment variable to read from .env
- The actual MCP server URL must exist in your main .env file
- The config.py uses `os.getenv(MCP_ENV_VAR)` to get the URL from .env

### Step 2: Set Up UI Configuration Schema

Edit `ui_config.py` to define the configuration interface. The config app uses a **smart 7-category card system** that automatically selects the appropriate card type:

```python
# Import standardized LLM model options - centrally managed
# This list is shared across all agents for consistency
STANDARD_LLM_MODEL_OPTIONS = [
    'claude-sonnet-4-20250514',
    'claude-3-5-haiku-20241022',
    'gpt-5',
    'gpt-4o',
    'o3',
    'claude-opus-4-1-20250805'
]

CONFIG_SECTIONS = [
    {
        'key': 'agent_identity',  # → Grey AgentIdentityCard (Category 1)
        'label': 'Agent Identity',
        'description': 'Agent identification and status',
        'fields': [
            {
                'key': 'agent_display_name',
                'label': 'Display Name',
                'type': 'text',
                'required': True,
                'description': 'Human-readable agent name'
            },
            {
                'key': 'agent_status',
                'label': 'Status',
                'type': 'select',
                'options': ['active', 'disabled'],
                'required': True
            }
        ]
    },
    {
        'key': 'user_preferences',  # → Grey AgentIdentityCard (Category 2)
        'label': 'User Preferences',
        'description': 'Personal settings and preferences',
        'fields': [
            {
                'key': 'timezone',
                'label': 'Timezone',
                'type': 'select',
                'options': ['global', 'America/New_York', 'America/Los_Angeles', 'Europe/London'],
                'required': True
            }
        ]
    },
    {
        'key': 'llm',  # → Blue LLMCard with model icons (Category 3)
        'label': 'Language Model',
        'description': 'AI model configuration for agent operations',
        'fields': [
            {
                'key': 'model',
                'label': 'Model',
                'type': 'select',
                'options': STANDARD_LLM_MODEL_OPTIONS,  # Uses centralized list
                'required': True
            },
            {
                'key': 'temperature',
                'label': 'Temperature',
                'type': 'number',
                'validation': {'min': 0.0, 'max': 1.0, 'step': 0.1}
            }
        ]
    },
    {
        'key': 'prompt_templates',  # → Orange PromptCard (Category 4)
        'label': 'System Prompts',
        'description': 'Customize agent behavior through system prompts',
        'card_style': 'orange',  # Explicit style hint for orange cards
        'fields': [
            {
                'key': 'agent_system_prompt',
                'label': 'System Prompt',
                'type': 'textarea',
                'rows': 15,
                'required': True,
                'description': 'Main system prompt that defines agent behavior'
            }
        ]
    },
    {
        'key': 'api_credentials',  # → Yellow CredentialsCard (Category 5)
        'label': 'API Credentials',
        'description': 'API keys and authentication',
        'fields': [
            {
                'key': 'service_api_key',
                'label': 'Service API Key',
                'type': 'password',  # Password type triggers credentials card
                'envVar': 'SERVICE_API_KEY',  # Links to .env file
                'required': False,
                'description': 'API key for external service'
            }
        ]
    },
    {
        'key': 'mcp_integration',  # → Green MCPConfigCard (Category 6)
        'label': 'MCP Server Configuration',
        'description': 'API connection settings for external services',
        'fields': [
            {
                'key': 'mcp_env_var',
                'label': 'MCP Environment Variable',
                'type': 'text',
                'readonly': True,  # Shows which env var is used
                'description': 'Name of the environment variable containing the MCP server URL (read-only)',
                'placeholder': 'PIPEDREAM_MCP_SERVER_google_gmail',
                'required': False,
                'note': 'This shows which environment variable is used. Configured in agent code.'
            },
            {
                'key': 'mcp_server_url',
                'label': 'MCP Server URL',
                'type': 'text',
                'description': 'The MCP server URL (editable - updates .env file)',
                'placeholder': 'https://mcp.pipedream.net/xxx/google_gmail',
                'required': False,
                'note': 'Editing this updates the URL in your .env file'
            }
        ]
    }
]
```

**Field Types Available:**
- `text` - Text input with optional copy button
- `textarea` - Multi-line text (auto-expands based on content)
- `password` - Hidden text input with show/hide toggle and copy button
- `number` - Numeric input with min/max/step validation
- `boolean` - Toggle switch
- `select` - Dropdown with options (includes icons for LLM models)

### Card System Architecture (7 Categories)

The config app automatically selects card types based on section keys and organizes them into 7 visual categories:

| Order | Category | Card Type | Color | Icon | Section Key Patterns |
|-------|----------|-----------|--------|------|-----------------------|
| 1 | **Agent Identity** | AgentIdentityCard | Grey | User | `agent_identity`, `*identity*` (not user) |
| 2 | **User Identity & Preferences** | AgentIdentityCard | Grey | User | `user_identity`, `user_preferences` |
| 3 | **AI Models** | LLMCard | Blue | Brain | `llm*`, `*model*` (not api) |
| 4 | **Prompts & Instructions** | PromptCard | Orange | Edit | `*prompt*`, `*triage*`, `email_preferences`, `card_style: 'orange'` |
| 5 | **Credentials & API Keys** | CredentialsCard | Yellow | Key | `ai_models`, `*api*`, `*credentials*`, `langgraph_system`, `google_workspace`, fields with `type: 'password'` |
| 6 | **Integrations & Services** | MCPConfigCard | Green | Plug | `*mcp*`, `*integration*`, `*server*` |
| 7 | **Specialized Configuration** | GenericCard | White | - | Everything else, interface UIs |

**Important Notes:**
- The order above determines the visual layout in the UI
- Cards are grouped under category headers with matching colors
- `ai_models` section goes to Credentials (yellow) for API keys, not LLM (blue)
- Interface UI configs always use generic (white) cards

**Important**: Only include fields that are actually implemented in your agent.

### Step 3: Ensure Environment Variables Exist in Main .env

In your project's main `.env` file, add the MCP server URL:

```bash
# For Pipedream
PIPEDREAM_MCP_SERVER_google_gmail=https://mcp.pipedream.net/xxx/google_gmail

# For Composio
COMPOSIO_MCP_SERVER_slack=https://mcp.composio.dev/xxx/slack

# For custom
MY_CUSTOM_MCP_SERVER=https://your-server.com/mcp
```

**Remember**: The agent's config.py will read this value using `os.getenv()`.

### Step 4: Add Agent to Config App Discovery

Edit `config-app/src/app/api/config/agents/route.ts`:

```typescript
const AGENT_CONFIG_PATHS = [
  'ui_config.py',
  'src/_react_agent_mcp_template/ui_config.py',
  'src/your_agent/ui_config.py',  // ⬅️ ADD YOUR AGENT HERE
  // ... other agents
];
```

### Step 5: Add Config Reading Logic

Edit `config-app/src/app/api/config/values/route.ts` in the `getPythonConfigValues()` function:

```typescript
if (agentId === 'your_agent') {
  const projectRoot = path.join(process.cwd(), '..');
  const configPath = path.join(projectRoot, 'src/your_agent/config.py');

  if (fs.existsSync(configPath)) {
    const content = fs.readFileSync(configPath, 'utf8');

    // Extract configuration values using regex
    const modelMatch = content.match(/"model":\s*"([^"]+)"/);
    const tempMatch = content.match(/"temperature":\s*([\d.]+)/);
    const agentNameMatch = content.match(/AGENT_NAME\s*=\s*"([^"]+)"/);
    const displayNameMatch = content.match(/AGENT_DISPLAY_NAME\s*=\s*"([^"]+)"/);
    const statusMatch = content.match(/AGENT_STATUS\s*=\s*"([^"]+)"/);

    return {
      llm: {
        model: modelMatch?.[1] || 'claude-sonnet-4-20250514',
        temperature: tempMatch ? parseFloat(tempMatch[1]) : 0.3,
      },
      agent_identity: {
        agent_name: agentNameMatch?.[1] || '',
        agent_display_name: displayNameMatch?.[1] || '',
        agent_status: statusMatch?.[1] || 'disabled',
      }
    };
  }
}
```

### Step 6: Add Config Writing Logic

Edit `config-app/src/app/api/config/update/route.ts` in the `updateConfigFile()` function:

```typescript
// Handle your_agent configuration updates
if (configPath.includes('your_agent')) {
  const configPyPath = fullPath.replace('ui_config.py', 'config.py');

  if (!fs.existsSync(configPyPath)) {
    console.error(`Config file not found: ${configPyPath}`);
    return false;
  }

  let configContent = fs.readFileSync(configPyPath, 'utf8');

  // Update LLM configuration
  if (sectionKey === 'llm') {
    if (fieldKey === 'model') {
      configContent = configContent.replace(
        /("model":\s*")([^"]+)(")/,
        `$1${value}$3`
      );
    } else if (fieldKey === 'temperature') {
      configContent = configContent.replace(
        /("temperature":\s*)([\d.]+)/,
        `$1${value}`
      );
    }
  }

  // Update agent identity
  else if (sectionKey === 'agent_identity') {
    const fieldMappings = {
      'agent_name': 'AGENT_NAME',
      'agent_display_name': 'AGENT_DISPLAY_NAME',
      'agent_description': 'AGENT_DESCRIPTION',
      'agent_status': 'AGENT_STATUS'
    };

    const varName = fieldMappings[fieldKey];
    if (varName) {
      const regex = new RegExp(`(${varName}\\s*=\\s*")([^"]+)(")`, 'g');
      configContent = configContent.replace(regex, `$1${value}$3`);
    }
  }

  fs.writeFileSync(configPyPath, configContent, 'utf8');
  console.log(`Updated ${fieldKey} in ${configPyPath}`);
  return true;
}
```

### Step 7: Environment Variables

Add your MCP server URL to the main `.env` file:

```bash
# MCP Server for your agent
PIPEDREAM_MCP_SERVER_google_gmail=https://mcp.pipedream.net/your-id/google_gmail

# Required API key
ANTHROPIC_API_KEY=your_api_key_here
```

## Testing Configuration

### Start Config Server

```bash
cd config-app
npm run dev:config
```

### Access Config UI

Open `http://localhost:3004`

**UI Features:**
- **7-Category Organization** - Cards automatically grouped into 7 visual categories
- **Smart Card Selection** - Appropriate card type chosen based on section content
- **Color-Coded Headers** - Each category has a distinct color for visual navigation
- **Model Performance Icons** - LLM models shown with cost/speed indicators (💨 Haiku, 🧠 Sonnet, 💻 Opus)
- **Secure Credential Handling** - Password fields with show/hide toggles and copy buttons
- **Live Validation** - Real-time field validation with helpful error messages
- **Responsive Design** - Optimized for both desktop and mobile devices

### Verify Two-Way Sync

1. **Check agent appears**: Your agent should appear in the sidebar
2. **Load values**: Configuration fields should populate with current values
3. **Test updates**: Make changes and verify they save to Python files
4. **Refresh test**: Reload page and confirm changes persist

### Troubleshooting

**Agent not appearing in sidebar:**
- Check `AGENT_CONFIG_PATHS` in `agents/route.ts`
- Verify `ui_config.py` exists and is valid Python

**Values not loading:**
- Check regex patterns in `values/route.ts` match your `config.py` format
- Verify file paths are correct

**Changes not saving:**
- Check update logic in `update/route.ts`
- Verify file permissions allow writing
- Check console for error messages

**UI styling issues:**
```bash
# Clear Next.js cache
cd config-app
rm -rf .next
npm cache clean --force
npm run dev:config
```

## Field Configuration Patterns

### Environment Variable Fields

For fields that should update `.env` files:

```python
{
    'key': 'api_key',
    'label': 'API Key',
    'type': 'password',
    'envVar': 'SERVICE_API_KEY',  # ⬅️ Links to .env
    'required': True
}
```

### Python Config Fields

For fields that should update Python configuration:

```python
{
    'key': 'model',
    'label': 'Model Name',
    'type': 'select',
    'options': ['claude-3-5-sonnet-20241022', 'gpt-4o'],
    # No envVar = updates config.py
}
```

### Validation Rules

```python
{
    'key': 'temperature',
    'type': 'number',
    'validation': {
        'min': 0.0,
        'max': 1.0,
        'step': 0.1
    }
}
```

## Best Practices

1. **Only Real Fields**: Never add UI fields that aren't actually used in your agent
2. **Clear Descriptions**: Provide helpful descriptions for each field
3. **Proper Validation**: Add appropriate validation constraints
4. **Consistent Naming**: Use consistent field keys between UI and Python config
5. **Test Everything**: Always test both reading and writing of configuration values
6. **Card Organization**: Name sections appropriately to trigger the right card type:
   - Use `agent_identity` for agent info → Grey card
   - Use `user_*` prefixes for user settings → Grey card
   - Use `llm` prefix for model configs → Blue card
   - Use `prompt` or set `card_style: 'orange'` → Orange card
   - Include password fields or `api`/`credentials` → Yellow card
   - Use `mcp` or `integration` → Green card
   - Everything else → White generic card
7. **Use Standard Options**: Always import `STANDARD_LLM_MODEL_OPTIONS` for model lists
8. **Group Related Fields**: Keep related settings in the same section for better UX

## UX-Optimized Field Selection Guidelines

**CRITICAL**: The config app is designed for end-users, not developers. Field selection must prioritize user experience and safety.

### User-Centric Field Selection

**Include fields that:**
- ✅ **Directly impact user experience** (model selection, temperature, timezone)
- ✅ **Users frequently need to change** (API keys, server URLs, agent status)
- ✅ **Affect agent behavior** in ways users care about (prompts, descriptions)
- ✅ **Are safe to modify** without breaking core functionality
- ✅ **Already exist in the codebase** and are actively used

**NEVER include fields that:**
- ❌ **Risk breaking dependencies** or core system functionality
- ❌ **Are for developer debugging only** (log levels, internal timeouts)
- ❌ **Don't exist yet in the codebase** ("future" or planned features)
- ❌ **Users shouldn't modify** (internal configuration paths, system settings)
- ❌ **Could corrupt agent state** if incorrectly configured

### Examples of Good vs Bad Field Choices

**✅ Good User Fields:**
```python
{
    'key': 'agent_display_name',  # Users want to customize names
    'key': 'model',               # Users want different AI models
    'key': 'timezone',            # Users have different timezones
    'key': 'agent_status',        # Users enable/disable agents
}
```

**❌ Bad Developer Fields:**
```python
{
    'key': 'debug_mode',          # Risk: Could flood logs, break production
    'key': 'internal_timeout',    # Risk: Could break MCP connections
    'key': 'cache_size',          # Risk: Memory issues if misconfigured
    'key': 'future_feature',      # Risk: Doesn't exist in codebase yet
}
```

### Validation Questions for Each Field

Before adding any field to the config UI, ask:

1. **Existence**: Does this field actually exist and work in the current codebase?
2. **User Value**: Will end-users actually need to change this setting?
3. **Safety**: Can users break the agent by modifying this incorrectly?
4. **Dependencies**: Does changing this field require other technical knowledge?
5. **Frequency**: How often would users realistically change this?

### Implementation Safety Rules

1. **Code-First**: Field must exist in working code before adding to UI
2. **Test Extensively**: Test all edge cases and invalid values
3. **Default Safely**: Provide safe defaults that work out-of-the-box
4. **Validate Strictly**: Add proper validation to prevent dangerous values
5. **Document Clearly**: Explain what the field does in user-friendly language

Remember: **A missing field is better than a field that breaks the agent.** When in doubt, leave it out until there's clear user demand and proven safety.

## Security Notes

- API keys and sensitive data should use `type: 'password'`
- Environment variables are automatically handled for security
- Never commit sensitive values to git repositories
- The config system handles `.env` file updates safely