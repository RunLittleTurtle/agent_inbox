# MCP Agent Configuration Guide

## 🚨 CRITICAL: Current System Limitations

The current configuration system has **hardcoded references** that must be updated manually for each new agent. It is **NOT** fully dynamic.

## ⚠️ Issues Identified in Current Implementation

### 1. Hardcoded Agent Discovery
- **File**: `agent-inbox/src/pages/api/config/agents.ts`
- **Issue**: `AGENT_CONFIG_PATHS` array is hardcoded
- **Impact**: New agents won't appear in config UI without manual addition

### 2. Template-Specific API Logic
- **Files**: `update.ts` and `values.ts`
- **Issue**: Special handling for `_react_agent_mcp_template` is hardcoded
- **Impact**: Duplicated agents won't have working two-way sync

## ✅ Duplication Checklist for New MCP Agents

### Step 1: Copy and Customize Template Files

```bash
# 1. Copy template directory
cp -r src/_react_agent_mcp_template src/{NEW_AGENT_NAME}_agent

# 2. Navigate to new agent directory
cd src/{NEW_AGENT_NAME}_agent
```

### Step 2: Update Configuration Files

#### A. `config.py` - Main Configuration
```python
# TODO: Configure for your agent
AGENT_NAME = "{AGENT_NAME}"  # Change to: "sheets", "drive", "gmail", etc.
AGENT_DISPLAY_NAME = "{AGENT_DISPLAY_NAME}"  # Change to: "Google Sheets", "Google Drive", etc.
AGENT_DESCRIPTION = "{AGENT_DESCRIPTION}"  # Change to: "spreadsheet operations", "file management", etc.
MCP_SERVICE = "{MCP_SERVICE}"  # Change to: "google_sheets", "google_drive", etc.
```

**✅ These placeholders MUST be replaced for configuration UI to work properly.**

#### B. `ui_config.py` - Configuration UI Schema

**🔥 CRITICAL PRINCIPLE: Only include fields that are actually implemented and connected to code.**

##### Configuration Rules:
1. **Two-way sync requirement**: Every field must have either:
   - `envVar` pointing to actual environment variable, OR
   - Be connected to actual Python config file value

2. **No placeholder fields**: Remove any sections/fields that aren't implemented

3. **MCP Environment Variables**: Follow pattern:
   ```python
   "envVar": "PIPEDREAM_MCP_SERVER_{MCP_SERVICE}"
   ```

##### Example Minimal Working Configuration:
```python
CONFIG_SECTIONS = [
    {
        "key": "agent_identity",
        "label": "Agent Identity",
        "description": "Basic agent identification",
        "fields": [
            {
                "key": "agent_name",
                "label": "Agent Name",
                "type": "text",
                "default": "{AGENT_NAME}",  # Will be populated from config.py
                "description": "Internal agent identifier",
                "required": True
            }
        ]
    },
    {
        "key": "llm",
        "label": "Language Model",
        "description": "AI model configuration",
        "fields": [
            {
                "key": "model",
                "label": "Model Name",
                "type": "select",
                "default": "claude-sonnet-4-20250514",
                "options": ["claude-sonnet-4-20250514", "claude-3-5-sonnet-20241022"],
                "required": True
            }
        ]
    },
    {
        "key": "mcp_integration",
        "label": "MCP Server",
        "description": "MCP server configuration",
        "fields": [
            {
                "key": "mcp_server_url",
                "label": "MCP Server URL",
                "type": "text",
                "envVar": "PIPEDREAM_MCP_SERVER_{MCP_SERVICE}",  # Replace {MCP_SERVICE}
                "required": True
            }
        ]
    }
]
```

### Step 3: Update API Endpoints (MANDATORY)

#### A. Add to Agent Discovery
**File**: `agent-inbox/src/pages/api/config/agents.ts`

```typescript
const AGENT_CONFIG_PATHS = [
  'ui_config.py',
  'src/_react_agent_mcp_template/ui_config.py',
  'src/calendar_agent/ui_config.py',
  'src/drive_react_agent/ui_config.py',
  'src/executive-ai-assistant/ui_config_wrapper.py',
  'src/job_search_agent/ui_config.py',
  'src/{NEW_AGENT_NAME}_agent/ui_config.py',  // ⬅️ ADD THIS LINE
];
```

#### B. Add Config Reading Logic
**File**: `agent-inbox/src/pages/api/config/values.ts`

Add this block in `getPythonConfigValues()` function:

```typescript
if (agentId === '{NEW_AGENT_NAME}_agent') {
  // Read values from the agent's config.py
  const projectRoot = path.join(process.cwd(), '..');
  const configPath = path.join(projectRoot, 'src/{NEW_AGENT_NAME}_agent/config.py');

  if (fs.existsSync(configPath)) {
    const content = fs.readFileSync(configPath, 'utf8');

    // Extract LLM_CONFIG values
    const modelMatch = content.match(/"model":\s*"([^"]+)"/);
    const tempMatch = content.match(/"temperature":\s*([\d.]+)/);
    // ... add other regex matches as needed

    // Extract agent identity values
    const agentNameMatch = content.match(/AGENT_NAME\s*=\s*"([^"]+)"/);
    const displayNameMatch = content.match(/AGENT_DISPLAY_NAME\s*=\s*"([^"]+)"/);
    // ... add other regex matches as needed

    return {
      llm: {
        model: modelMatch?.[1] || 'claude-sonnet-4-20250514',
        temperature: tempMatch ? parseFloat(tempMatch[1]) : 0.2,
        // ... other LLM config
      },
      agent_identity: {
        agent_name: agentNameMatch?.[1] || '{AGENT_NAME}',
        agent_display_name: displayNameMatch?.[1] || '{AGENT_DISPLAY_NAME}',
        // ... other identity fields
      }
    };
  }
}
```

#### C. Add Config Update Logic
**File**: `agent-inbox/src/pages/api/config/update.ts`

Add this block in `updateConfigFile()` function:

```typescript
// Special handling for {NEW_AGENT_NAME}_agent
if (configPath.includes('{NEW_AGENT_NAME}_agent')) {
  // For the agent, update the config.py file instead of ui_config.py
  const configPyPath = fullPath.replace('ui_config.py', 'config.py');

  if (!fs.existsSync(configPyPath)) {
    console.error(`Agent config.py not found: ${configPyPath}`);
    return false;
  }

  let configContent = fs.readFileSync(configPyPath, 'utf8');

  // Update LLM_CONFIG fields
  if (sectionKey === 'llm') {
    if (fieldKey === 'model') {
      configContent = configContent.replace(
        /("model":\s*")([^"]+)(")/,
        `$1${value}$3`
      );
    }
    // ... add other LLM field updates
  }
  // Update agent identity fields
  else if (sectionKey === 'agent_identity') {
    const mappings: Record<string, string> = {
      'agent_name': 'AGENT_NAME',
      'agent_display_name': 'AGENT_DISPLAY_NAME',
      'agent_description': 'AGENT_DESCRIPTION',
      'mcp_service': 'MCP_SERVICE'
    };

    const varName = mappings[fieldKey];
    if (varName) {
      const regex = new RegExp(`(${varName}\\s*=\\s*")([^"]+)(")`, 'g');
      configContent = configContent.replace(regex, `$1${value}$3`);
    }
  }

  // Write the updated content back
  fs.writeFileSync(configPyPath, configContent, 'utf8');
  console.log(`Successfully updated ${fieldKey} in ${configPyPath}`);
  return true;
}
```

### Step 4: Environment Configuration

Add to main `.env` file:
```bash
# MCP Server for your new agent
PIPEDREAM_MCP_SERVER_{MCP_SERVICE}=https://mcp.pipedream.net/{your-id}/{service}

# Other environment variables as needed
```

### Step 5: Test Configuration UI

1. **Start config server**: `npm run dev:config`
2. **Open**: `http://localhost:3004/config`
3. **Verify**:
   - New agent appears in sidebar
   - Configuration fields load correctly
   - Changes save and persist
   - UI immediately reflects saved changes

## 🎯 Configuration Best Practices

### Field Design Principles

1. **Only Real Fields**: Never include fields that aren't connected to actual functionality
2. **Clear Labels**: Use human-readable labels and descriptions
3. **Proper Types**: Match field types to data (select for choices, boolean for toggles, etc.)
4. **Validation**: Add appropriate validation constraints
5. **Environment Variables**: Use consistent naming patterns

### Field Type Guide

```python
# Text input
{
    "key": "field_name",
    "label": "Display Name",
    "type": "text",
    "description": "Helper text",
    "placeholder": "Example value",
    "required": True
}

# Password input
{
    "key": "api_key",
    "label": "API Key",
    "type": "password",
    "envVar": "SERVICE_API_KEY",
    "required": True
}

# Boolean toggle
{
    "key": "enable_feature",
    "label": "Enable Feature",
    "type": "boolean",
    "default": True,
    "description": "Enable/disable this feature"
}

# Select dropdown
{
    "key": "model",
    "label": "Model Name",
    "type": "select",
    "options": ["option1", "option2"],
    "default": "option1"
}

# Number input
{
    "key": "temperature",
    "label": "Temperature",
    "type": "number",
    "validation": {"min": 0, "max": 1, "step": 0.1},
    "default": 0.2
}

# Textarea
{
    "key": "description",
    "label": "Description",
    "type": "textarea",
    "placeholder": "Multi-line text..."
}
```

## 🔄 Two-Way Sync Requirements

### For Environment Variables
- Set `envVar` field pointing to actual environment variable
- API automatically handles .env file updates

### For Python Config Values
- Ensure regex patterns in API endpoints match your config.py structure
- Test both reading and writing of values
- Handle type conversion properly (string ↔ number ↔ boolean)

## 🚫 Common Pitfalls to Avoid

1. **Phantom Fields**: Adding UI fields that aren't actually used in code
2. **Missing API Updates**: Forgetting to update all three API endpoints
3. **Placeholder Values**: Leaving {PLACEHOLDER} values in production configs
4. **Inconsistent Naming**: Using different field keys between UI and Python config
5. **Missing Validation**: Not testing that changes actually save and load
6. **Environment Variables**: Forgetting to add required env vars to main .env

## 🔧 Debugging Configuration Issues

### Common Issues:

1. **Agent not appearing**: Check AGENT_CONFIG_PATHS in agents.ts
2. **Values not loading**: Check getPythonConfigValues() regex patterns
3. **Updates not saving**: Check updateConfigFile() logic
4. **UI not refreshing**: Check handleValueChange() in config page
5. **Type errors**: Check field type definitions and conversions
6. **Next.js cache corruption**: See runtime error section below

### 🚨 CRITICAL: Next.js Cache Corruption Error

**Error Message:**
```
ENOENT: no such file or directory, open '.next/server/pages/_document.js'
```

**Symptoms:**
- Configuration page shows "black and white" unstyled UI
- Runtime errors about missing build files
- Server fails to load properly styled components

**Solution (ALWAYS WORKS):**
```bash
# Stop all development servers
# Kill any running processes on port 3004
lsof -ti:3004 | xargs kill -9 2>/dev/null

# Clear ALL Next.js cache
cd agent-inbox
rm -rf .next
rm -rf node_modules/.cache
npm cache clean --force

# Restart development server
npm run dev:config
```

**Why This Happens:**
Next.js caches build artifacts in `.next` directory. When these get corrupted or partially deleted (especially during development), the server tries to load non-existent cached files. This is a common issue during active development with frequent file changes.

**Prevention:**
- Always use the cache clearing commands when switching between development sessions
- If you see styling issues, immediately clear the cache before troubleshooting other issues

### Debug Steps:

1. **First step for any UI issues**: Clear Next.js cache (see above)
2. Check browser console for errors
3. Check Next.js server logs for API errors
4. Verify config files exist at expected paths
5. Test API endpoints directly with curl
6. Verify environment variables are loaded

## 📝 Documentation Requirements

For each new agent, document:

1. **Purpose**: What the agent does
2. **MCP Service**: Which MCP server it connects to
3. **Configuration Fields**: What each field controls
4. **Environment Variables**: What env vars are required
5. **Dependencies**: Any external service dependencies

## 🎯 Future Improvements Needed

The current system should be refactored to:

1. **Dynamic Discovery**: Auto-discover agents instead of hardcoded paths
2. **Generic API Logic**: Remove agent-specific hardcoded logic
3. **Configuration Templates**: Better templating system for new agents
4. **Validation Framework**: Centralized field validation
5. **Type Safety**: Better TypeScript interfaces

---

## 📋 Quick Duplication Summary

For your future self, the minimum steps to duplicate an agent with working config UI:

1. ✅ Copy template directory
2. ✅ Replace all `{PLACEHOLDER}` values in config.py
3. ✅ Update ui_config.py with only implemented fields
4. ✅ Add path to AGENT_CONFIG_PATHS in agents.ts
5. ✅ Add reading logic to values.ts
6. ✅ Add writing logic to update.ts
7. ✅ Add environment variables to .env
8. ✅ Test in config UI at http://localhost:3004/config

**Remember: The system is not fully dynamic - manual API updates are required for each new agent.**