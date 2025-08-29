# Environment Setup Guide

## Overview

This LangGraph-based agent inbox system requires several environment variables to function properly. The "fetch failed" errors are typically due to missing or incorrect environment configuration.

## Required Environment Variables

### 1. OpenAI API Key
```bash
export OPENAI_API_KEY="your_openai_api_key_here"
```

### 2. LangSmith Configuration (Optional but Recommended)
```bash
export LANGSMITH_API_KEY="your_langsmith_api_key_here"
export LANGSMITH_TRACING=true
export LANGCHAIN_PROJECT="agent-inbox-project"
```

### 3. MCP Server Configuration
```bash
export PIPEDREAM_MCP_SERVER="your_pipedream_mcp_server_url"
```

## Quick Setup

1. **Copy the environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` file with your actual values:**
   ```bash
   # Edit the .env file with your API keys and server URLs
   nano .env
   ```

3. **Load environment variables:**
   ```bash
   source .env
   ```

4. **Activate virtual environment:**
   ```bash
   source .venv/bin/activate
   ```

## Pipedream MCP Server Setup

The calendar functionality requires a Pipedream MCP server for Google Calendar integration:

1. **Set up Pipedream account:** Create account at pipedream.com
2. **Create MCP endpoint:** Follow Pipedream's MCP integration guide
3. **Configure Google Calendar:** Connect your Google Calendar to Pipedream
4. **Get MCP server URL:** Usually in format `https://your-account.m.pipedream.net/mcp`

## Testing the Setup

Run this test to verify everything is working:

```bash
# Test environment variables
python -c "
import os
required_vars = ['OPENAI_API_KEY', 'PIPEDREAM_MCP_SERVER']
for var in required_vars:
    value = os.getenv(var)
    print(f'{var}: {\"✅ Set\" if value else \"❌ Missing\"}')"

# Test calendar agent
python -m src.calendar_agent.langchain_mcp_integration
```

## Common Issues

### "fetch failed" Error
- **Cause:** Missing `PIPEDREAM_MCP_SERVER` environment variable
- **Solution:** Set the correct Pipedream MCP server URL

### OpenAI API Error
- **Cause:** Missing or invalid `OPENAI_API_KEY`
- **Solution:** Verify your OpenAI API key is correct and has credits

### LangGraph Server Issues
- **Cause:** Missing `LANGSMITH_API_KEY` for development mode
- **Solution:** Set LangSmith API key or use production license

## Environment Variable Priority

The system looks for environment variables in this order:
1. Explicitly set environment variables
2. `.env` file in project root
3. System environment variables

## Security Notes

- **Never commit `.env` files** - they're in `.gitignore`
- **Use `.env.example`** as a template only
- **Store sensitive keys securely** in production environments
