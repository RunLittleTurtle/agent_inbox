# LangFuse Deployment on Railway

This directory contains the configuration for deploying LangFuse on Railway.

## What is LangFuse?

LangFuse is an open-source LLM observability platform that provides per-user trace isolation.
Unlike LangSmith (which uses workspace-level isolation), LangFuse allows each user to see only their own traces.

## Architecture

```
┌─────────────────┐
│   LangFuse UI   │  ← Users see only their traces
│  (Railway App)  │
└────────┬────────┘
         │
    ┌────┴────┐
    │ PostSQL │  ← Trace storage
    └─────────┘
```

## Deployment Steps

### 1. Deploy PostgreSQL on Railway

```bash
# Railway will auto-provision PostgreSQL when you add it to your project
# No manual setup needed
```

### 2. Deploy LangFuse

Railway will deploy using the official LangFuse Docker image.

### 3. Environment Variables (Auto-configured by Railway)

- `DATABASE_URL` - PostgreSQL connection string (auto-set by Railway)
- `NEXTAUTH_URL` - Your Railway app URL
- `NEXTAUTH_SECRET` - Random secret for NextAuth (generate with openssl)
- `SALT` - Random salt for encryption (generate with openssl)

### 4. Generate Secrets

```bash
# Generate NEXTAUTH_SECRET
openssl rand -base64 32

# Generate SALT
openssl rand -base64 32
```

## Integration with Agent Inbox

Once deployed, add these environment variables to your LangGraph agents:

```bash
# In your agent .env or Railway environment variables
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_SECRET_KEY=sk-lf-xxx
LANGFUSE_HOST=https://your-langfuse-app.railway.app
```

LangFuse will automatically capture all LangChain/LangGraph traces via the LangChain integration.

## User Access

Each user will:
1. Sign up/login to your LangFuse instance
2. See only traces tagged with their `user_id`
3. View conversation history, token usage, and costs

## Alternative: LangFuse Cloud

Instead of self-hosting, you can use LangFuse Cloud:
- Sign up at https://cloud.langfuse.com
- Get API keys from dashboard
- Set LANGFUSE_HOST=https://cloud.langfuse.com
