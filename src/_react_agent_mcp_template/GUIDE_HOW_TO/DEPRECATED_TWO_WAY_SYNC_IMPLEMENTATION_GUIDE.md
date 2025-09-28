# 🚨 DEPRECATED - Two-Way Sync Implementation Guide

> **This guide is deprecated**. Please use the new comprehensive guides:
> - `01_CONFIG_SETUP_GUIDE.md` - For complete configuration setup with two-way sync
> - `02_AGENT_SETUP_GUIDE.md` - For agent setup and deployment
> - `03_PROMPT_MANAGEMENT_GUIDE.md` - For prompt management
>
> This file is kept for reference only.

# Two-Way Sync Implementation Guide

## Problem Analysis
The configuration UI can't save changes because the update.ts API endpoint only has hardcoded handling for specific agents (`_react_agent_mcp_template` and `email_agent`). Other agents and global config fields fail silently.

## How Two-Way Sync Works

### 1. Environment Variable Fields
Fields with `envVar` property update the .env file directly:
```python
{
    'key': 'anthropic_api_key',
    'envVar': 'ANTHROPIC_API_KEY',  # ← This links to .env
    'type': 'password'
}
```

### 2. Python Config Fields
Fields without `envVar` update the Python config.py file:
```python
{
    'key': 'model',
    'type': 'select',
    # No envVar = updates config.py
}
```

## Implementation Requirements

### For Each Agent's Two-Way Sync

#### 1. Add to agents.ts
```typescript
const AGENT_CONFIG_PATHS = [
  'ui_config.py',  // Global
  'src/YOUR_AGENT/ui_config.py',  // ← Add your agent
];
```

#### 2. Add to values.ts
```typescript
if (agentId === 'YOUR_AGENT') {
  const configPath = path.join(projectRoot, 'src/YOUR_AGENT/config.py');
  // Read config values with regex
  const modelMatch = content.match(/"model":\s*"([^"]+)"/);
  return {
    llm: {
      model: modelMatch?.[1] || 'default-model'
    }
  };
}
```

#### 3. Add to update.ts
```typescript
if (configPath.includes('YOUR_AGENT')) {
  const configPyPath = fullPath.replace('ui_config.py', 'config.py');
  let configContent = fs.readFileSync(configPyPath, 'utf8');

  // Update fields based on sectionKey and fieldKey
  if (sectionKey === 'llm' && fieldKey === 'model') {
    configContent = configContent.replace(
      /("model":\s*")([^"]+)(")/,
      `$1${value}$3`
    );
  }

  fs.writeFileSync(configPyPath, configContent, 'utf8');
  return true;
}
```

## Critical Fields to Fix

### Global Config (ui_config.py)
Remove `readonly: True` from these editable fields:
- `agent_inbox_graph_id`
- `agent_inbox_assistant_id`
- `use_enhanced_calendar_agent`

These should remain readonly:
- `langgraph_api_url` (system setting)
- `agent_inbox_api_url` (system setting)

### Agent Configs
Ensure all agents have update handlers in update.ts:
- calendar_agent
- drive_react_agent
- job_search_agent
- email_agent ✓ (already done)

## Quick Fix for Webpack Error

The webpack error is likely due to:
1. Cache corruption → Run clear-cache script
2. Missing "use client" directive → Check components
3. Async/await in wrong context → Review config.tsx

## Testing Two-Way Sync

1. **Environment Variable Field**:
   - Change ANTHROPIC_API_KEY in UI
   - Check .env file updates
   - Refresh page - value persists

2. **Config.py Field**:
   - Change model selection in UI
   - Check config.py file updates
   - Refresh page - value persists

## Common Issues

1. **Field reverts after typing**: Update handler not implemented for that agent
2. **Readonly field**: Remove `readonly: True` from ui_config.py
3. **Value doesn't persist**: Check regex patterns in values.ts match actual config.py format
4. **Webpack error**: Clear cache and check for async/await issues

## Implementation Priority

1. Fix global config fields (remove readonly where appropriate)
2. Add update handlers for all agents in update.ts
3. Add value readers for all agents in values.ts
4. Test each field type (text, select, boolean, password)