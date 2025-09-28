# Config Setup Guide

Complete guide for setting up configuration integration between your React Agent and the Agent Inbox config app.

## Overview

The config system provides a web UI at `http://localhost:3004/config` for managing agent settings with two-way sync between the UI and Python configuration files.

## Core Components

### 1. Configuration Files Structure

```
src/your_agent/
├── config.py           # Main configuration (Python values)
├── ui_config.py        # UI schema definition
├── prompt.py           # System prompts
└── ...
```

### 2. Config App Integration

The config app (located at `config-app/`) provides:
- Web UI for editing agent configurations
- API endpoints for reading/writing config values
- Two-way sync between UI and Python files

## Step-by-Step Setup

### Step 1: Configure Agent Identity

In your agent's `config.py`, replace ALL placeholder values:

```python
# TODO: Configure for your agent
AGENT_NAME = "gmail"  # Internal identifier (no spaces, lowercase)
AGENT_DISPLAY_NAME = "Gmail Agent"  # Human-readable name
AGENT_DESCRIPTION = "email management and organization"  # Brief description
MCP_SERVICE = "google_gmail"  # MCP service identifier
AGENT_STATUS = "active"  # "active" or "disabled"
```

**Critical**: Remove ALL `{PLACEHOLDER}` values - the config UI will not work with placeholders.

### Step 2: Set Up UI Configuration Schema

Edit `ui_config.py` to define the configuration interface:

```python
CONFIG_SECTIONS = [
    {
        'key': 'agent_identity',
        'label': 'Agent Identity',
        'description': 'Basic agent information',
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
        'key': 'llm',
        'label': 'Language Model',
        'fields': [
            {
                'key': 'model',
                'label': 'Model',
                'type': 'select',
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
                'validation': {'min': 0.0, 'max': 1.0, 'step': 0.1}
            }
        ]
    },
    {
        'key': 'mcp_integration',
        'label': 'MCP Configuration',
        'fields': [
            {
                'key': 'mcp_server_url',
                'label': 'MCP Server URL',
                'type': 'text',
                'envVar': 'PIPEDREAM_MCP_SERVER_google_gmail',  # Replace with your service
                'required': True,
                'description': 'Pipedream MCP server endpoint'
            }
        ]
    }
]
```

**Field Types Available:**
- `text` - Text input
- `textarea` - Multi-line text
- `password` - Hidden text input
- `number` - Numeric input with validation
- `boolean` - Toggle switch
- `select` - Dropdown with options

**Important**: Only include fields that are actually implemented in your agent.

### Step 3: Add Agent to Config App Discovery

Edit `config-app/src/app/api/config/agents/route.ts`:

```typescript
const AGENT_CONFIG_PATHS = [
  'ui_config.py',
  'src/_react_agent_mcp_template/ui_config.py',
  'src/your_agent/ui_config.py',  // ⬅️ ADD YOUR AGENT HERE
  // ... other agents
];
```

### Step 4: Add Config Reading Logic

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

### Step 5: Add Config Writing Logic

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

### Step 6: Environment Variables

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

Open `http://localhost:3004/config`

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