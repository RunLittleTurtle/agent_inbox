# MCP Agent Configuration Guide

## Timezone Handling (Now Implemented)

### How it Works:
1. **Global Default**: Main `.env` has `USER_TIMEZONE=America/Toronto`
2. **Agent Override**: Calendar agent can have its own timezone setting
   - `'global'` = Use main .env's USER_TIMEZONE
   - Any other value = Use this specific timezone

### Configuration Flow:
```python
# src/calendar_agent/config.py
CALENDAR_TIMEZONE = 'global'  # Updated by config UI

if CALENDAR_TIMEZONE == 'global':
    USER_TIMEZONE = os.getenv('USER_TIMEZONE', 'America/Toronto')  # From main .env
else:
    USER_TIMEZONE = CALENDAR_TIMEZONE  # Agent-specific override
```

This gives you the flexibility you wanted:
- Default behavior uses global timezone
- Users can override per-agent through the UI
- No environment variable pollution

## MCP URL Storage Best Practices

### Where to Store MCP URLs

**MCP URLs should be stored in the main `.env` file** (current approach is correct)

#### Rationale:
1. **Environment-specific configuration**: MCP URLs are external service endpoints that vary between environments (dev/staging/prod)
2. **Security**: URLs contain sensitive endpoints that should not be in version control
3. **Centralization**: Multiple agents may share the same MCP server, so centralized configuration reduces duplication
4. **Standard practice**: Environment variables are the industry standard for storing external service URLs

### Configuration Architecture

```
.env (root directory)
├── PIPEDREAM_MCP_SERVER=https://mcp.pipedream.net/.../google_calendar
├── PIPEDREAM_MCP_SERVER_google_gmail=https://mcp.pipedream.net/.../gmail
└── PIPEDREAM_MCP_SERVER_google_drive=https://mcp.pipedream.net/.../drive

src/calendar_agent/config.py
└── MCP_SERVER_URL = os.getenv('PIPEDREAM_MCP_SERVER', '')

src/email_agent/config.py
└── MCP_SERVER_URL = os.getenv('PIPEDREAM_MCP_SERVER_google_gmail', '')
```

### Agent Configuration Files

Each agent's `config.py` should:
1. Import MCP URL from environment: `os.getenv('PIPEDREAM_MCP_SERVER', '')`
2. Define agent-specific logic settings (temperature, prompts, etc.)
3. Never hardcode MCP URLs directly

### UI Configuration

The `ui_config.py` files define which fields are editable through the UI:
- Fields with `envVar` property update the `.env` file
- Fields without `envVar` update the agent's `config.py` directly

Example:
```python
{
    'key': 'calendar_mcp_url',
    'label': 'Calendar MCP URL',
    'type': 'text',
    'envVar': 'PIPEDREAM_MCP_SERVER',  # This makes it update .env
    'required': True
}
```

## Known Issues & Solutions

### Why NOT to Use Agent-Specific .env Files

While it might seem logical to have `src/calendar_agent/.env`, this approach has significant drawbacks:

1. **Deployment Complexity**: Most deployment platforms (Vercel, Railway, Heroku) expect ONE .env file
2. **Precedence Confusion**: Which .env wins? Root or agent-specific?
3. **Security Management**: Harder to rotate secrets across multiple files
4. **Git Complexity**: Multiple .gitignore entries to manage
5. **Environment Switching**: Nightmare to switch between dev/staging/prod

### Recommended Approach for Agent-Specific URLs

If agents need different MCP servers, use namespaced variables in main .env:
```bash
# Main .env - Clear, organized, single source of truth
CALENDAR_MCP_SERVER=https://mcp.pipedream.net/.../google_calendar
EMAIL_MCP_SERVER=https://mcp.pipedream.net/.../google_gmail
DRIVE_MCP_SERVER=https://mcp.pipedream.net/.../google_drive
```

Then in each agent's config.py:
```python
# calendar_agent/config.py
MCP_SERVER_URL = os.getenv('CALENDAR_MCP_SERVER', '')

# email_agent/config.py
MCP_SERVER_URL = os.getenv('EMAIL_MCP_SERVER', '')
```

### Issue: UI doesn't show updated values after saving
**Solution**: The API now reads directly from the `.env` file instead of relying on cached `process.env` values. A small delay is added after saving to ensure file writes complete before reloading.

### Issue: Multiple agents sharing the same MCP server
**Solution**: Use the same environment variable name across agents that share a server. For example, if both calendar and tasks agents use the same Google Workspace MCP server, they can both reference `PIPEDREAM_MCP_SERVER`.