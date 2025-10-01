# 🚀 LANGGRAPH PLATFORM DEPLOYMENT GUIDE 2025

**Date:** 2025-10-01
**LangGraph Version:** 1.0.0a1
**Platform:** LangGraph Platform Plus ($39/mo)

---

## 📑 TABLE OF CONTENTS

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Deployment Checklist](#deployment-checklist)
4. [Configuration Files](#configuration-files)
5. [Environment Variables](#environment-variables)
6. [Deployment Steps](#deployment-steps)
7. [Post-Deployment Testing](#post-deployment-testing)
8. [Troubleshooting](#troubleshooting)

---

## 🏗️ ARCHITECTURE OVERVIEW

### LangGraph Platform Responsibilities

```
┌─────────────────────────────────────────────────────────────┐
│                LANGGRAPH PLATFORM (Backend)                  │
│                                                              │
│  ✅ Thread Management        (1 thread = 1 conversation)    │
│  ✅ State Persistence        (messages auto-saved)          │
│  ✅ PostgreSQL Checkpointer  (platform-managed)             │
│  ✅ Scalability              (auto-scaling)                 │
│  ✅ Streaming                (SSE responses)                │
│  ✅ LangSmith Tracing        (observability)                │
│                                                              │
│  ❌ NO User Authentication   (handled by Clerk)             │
│  ❌ NO Secrets Storage       (handled by Supabase)          │
│  ⚠️  Receives secrets per-request via config.configurable   │
└──────────────────────────────────────────────────────────────┘
```

### Key 2025 Best Practices

1. **NO checkpointer in code** - LangGraph Platform provides PostgreSQL automatically
2. **Export graph as `graph`** - Required for platform deployment
3. **Use `config.configurable`** - For multi-tenant API key passing
4. **Use prebuilt components** - `create_react_agent`, `create_supervisor`
5. **Enable semantic search** - Via `store` in langgraph.json

---

## ✅ PREREQUISITES

### 1. LangGraph Platform Account
- ✅ Plan: **Plus** ($39/mo)
- Features:
  - 1 dev deployment (24/7 uptime)
  - 100K node executions/month
  - PostgreSQL persistence (managed)
  - Thread management
  - LangSmith integration

### 2. GitHub Repository
- ✅ Code pushed to GitHub
- ✅ Repository connected to LangGraph Platform

### 3. Environment Variables Ready
```bash
# AI Model API Keys
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-api03-...

# LangSmith (observability)
LANGSMITH_API_KEY=lsv2_pt_...
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=agent-inbox

# MCP Servers (optional)
RUBE_MCP_SERVER=https://rube.app/mcp
RUBE_AUTH_TOKEN=eyJ...
```

---

## 📋 DEPLOYMENT CHECKLIST

### Phase 1: Code Preparation

- [x] **langgraph.json** configured correctly
- [x] **requirements.txt** includes all dependencies
- [x] **src/graph.py** exports `graph` variable
- [x] **No checkpointer** in agent code (platform provides it)
- [x] **config.configurable** support implemented

### Phase 2: Platform Configuration

- [ ] LangGraph Platform account created
- [ ] GitHub repository connected
- [ ] Environment variables configured
- [ ] Deployment created via dashboard
- [ ] Deployment URL obtained

### Phase 3: Verification

- [ ] Health check returns `200 OK`
- [ ] Test curl call succeeds
- [ ] Streaming works
- [ ] Thread persistence verified
- [ ] LangSmith traces visible

---

## 📄 CONFIGURATION FILES

### 1. langgraph.json

**Location:** `/langgraph.json` (project root)

```json
{
  "dependencies": ["."],
  "graphs": {
    "agent": "./src/graph.py:graph"
  },
  "env": ".env",
  "python_version": "3.11",
  "store": {
    "index": {
      "embed": "openai:text-embedding-3-small",
      "dims": 1536,
      "fields": ["$"]
    }
  }
}
```

**Key Fields:**
- `dependencies`: Python dependencies location
- `graphs.agent`: Path to graph export (format: `file:variable`)
- `env`: Environment variables file
- `python_version`: Python runtime version
- `store.index`: Semantic search configuration (optional but recommended)

---

### 2. requirements.txt

**Critical Dependencies for 2025:**

```txt
# LangGraph & LangChain Core (v1-alpha)
langgraph==1.0.0a1
langchain==1.0.0a3
langchain-core>=0.3.75

# LangGraph Checkpointer (for platform compatibility)
langgraph-checkpoint-postgres>=2.0.0

# Prebuilt Components
langgraph-supervisor>=0.0.29

# AI Models
langchain-openai>=0.2.0
langchain-anthropic>=0.2.0

# Observability
langsmith>=0.2.0
```

---

### 3. src/graph.py

**Required Structure:**

```python
# 1. Export graph at module level
async def create_supervisor_graph():
    # ... build your graph ...
    compiled_graph = workflow.compile()
    return compiled_graph

# 2. Factory function for async initialization
async def make_graph():
    return await create_supervisor_graph()

# 3. Synchronous wrapper
def create_graph():
    return asyncio.run(make_graph())

# 4. REQUIRED: Export as 'graph' variable
graph = create_graph()
```

**Key Points:**
- ✅ **NO checkpointer** in `.compile()` call
- ✅ Export variable must be named `graph`
- ✅ Graph must be compiled (not just built)

---

## 🔐 ENVIRONMENT VARIABLES

### Production Environment Variables

**Configure in LangGraph Platform Dashboard:**

```bash
# =============================================================================
# AI MODEL API KEYS (Required)
# =============================================================================
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-api03-...

# =============================================================================
# LANGSMITH (Recommended for observability)
# =============================================================================
LANGSMITH_API_KEY=lsv2_pt_...
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=agent-inbox

# =============================================================================
# MCP SERVERS (Optional - for tool integrations)
# =============================================================================
RUBE_MCP_SERVER=https://rube.app/mcp
RUBE_AUTH_TOKEN=eyJ...
PIPEDREAM_MCP_SERVER=https://mcp.pipedream.net/...

# =============================================================================
# SYSTEM SETTINGS
# =============================================================================
ENVIRONMENT=production
LOG_LEVEL=INFO
USER_TIMEZONE=America/Toronto
```

**Security Notes:**
- ⚠️ NEVER commit `.env` files to git
- ⚠️ Use platform dashboard for secrets management
- ⚠️ Rotate API keys regularly

---

## 🚀 DEPLOYMENT STEPS

### Step 1: Verify Local Development Server

**Before deploying, ensure local server works:**

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start local LangGraph server
langgraph dev

# Expected output:
# Ready!
# - API: http://localhost:2024
```

**Test local server:**

```bash
# Health check
curl http://localhost:2024/health

# Expected: {"status":"ok"}

# Test streaming
curl -X POST http://localhost:2024/runs/stream \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "agent",
    "input": {"messages": [{"role": "user", "content": "Hello"}]},
    "config": {
      "configurable": {
        "openai_api_key": "YOUR_KEY",
        "user_id": "test_user"
      }
    }
  }'
```

**Success Criteria:**
- ✅ Server starts without errors
- ✅ Health check returns `200 OK`
- ✅ Test request streams response

---

### Step 2: Prepare GitHub Repository

```bash
# 1. Commit all changes
git add langgraph.json requirements.txt src/graph.py
git commit -m "feat: configure for LangGraph Platform deployment"

# 2. Push to GitHub
git push origin main

# 3. Verify push succeeded
git log -1
```

---

### Step 3: Create Deployment via LangGraph Platform Dashboard

**Access Dashboard:**
1. Go to: https://smith.langchain.com
2. Navigate to: **LangGraph Platform** → **Deployments**
3. Click: **+ New Deployment**

**Configuration:**

| Field | Value |
|-------|-------|
| **Deployment Name** | `agent-inbox-production` |
| **Git Repository** | Your GitHub repo URL |
| **Branch** | `main` |
| **Config File Path** | `langgraph.json` |
| **Deployment Type** | **Production** (for stable 24/7) or **Development** (for testing) |

**Environment Variables:**
- Click **Add Environment Variable**
- Add all variables from [Environment Variables section](#environment-variables)
- Mark sensitive values as **Secret**

**Deployment Options:**
- ✅ Enable **Automatic Updates** (re-deploy on git push)
- ✅ Enable **LangGraph Studio** access (for debugging)
- ✅ Enable **LangSmith Tracing**

**Click:** **Create Deployment**

---

### Step 4: Monitor Deployment

**Build Logs:**
1. Dashboard → Your Deployment → **Build Logs**
2. Watch for:
   - ✅ Dependencies installation
   - ✅ Graph compilation
   - ✅ Server startup

**Expected Build Time:** ~3-5 minutes

**Deployment States:**
- 🟡 **Building** - Installing dependencies, compiling graph
- 🟢 **Running** - Deployment successful, server live
- 🔴 **Failed** - Check build logs for errors

---

### Step 5: Obtain Deployment URL

**Once deployment is Running:**
1. Dashboard → Your Deployment → **Overview**
2. Copy **Deployment URL** (format: `https://your-deployment.langchain.app`)

**Save this URL:**
- You'll use it in frontend API routes
- Configure as: `LANGGRAPH_API_URL` in Vercel

---

## 🧪 POST-DEPLOYMENT TESTING

### Test 1: Health Check

```bash
curl https://your-deployment.langchain.app/health
```

**Expected Response:**
```json
{"status":"ok"}
```

---

### Test 2: Stream a Message

```bash
curl -X POST https://your-deployment.langchain.app/runs/stream \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_LANGSMITH_API_KEY" \
  -d '{
    "assistant_id": "agent",
    "input": {
      "messages": [
        {"role": "user", "content": "What is 2+2?"}
      ]
    },
    "config": {
      "configurable": {
        "openai_api_key": "YOUR_OPENAI_KEY",
        "user_id": "test_user_123"
      }
    }
  }'
```

**Expected Response:**
- Stream of Server-Sent Events (SSE)
- Final message with agent's response

**Success Criteria:**
- ✅ Agent responds with correct answer
- ✅ No API key errors
- ✅ Response streams in real-time

---

### Test 3: Thread Persistence

**Create a thread:**
```bash
curl -X POST https://your-deployment.langchain.app/threads \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_LANGSMITH_API_KEY" \
  -d '{
    "metadata": {"user_id": "test_user_123"}
  }'
```

**Expected Response:**
```json
{
  "thread_id": "abc-123-def",
  "created_at": "2025-10-01T12:00:00Z",
  "metadata": {"user_id": "test_user_123"}
}
```

**Send message to thread:**
```bash
curl -X POST https://your-deployment.langchain.app/runs/stream \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_LANGSMITH_API_KEY" \
  -d '{
    "assistant_id": "agent",
    "thread_id": "abc-123-def",
    "input": {"messages": [{"role": "user", "content": "Remember, my name is Alice"}]}
  }'
```

**Verify persistence:**
```bash
curl https://your-deployment.langchain.app/threads/abc-123-def/state \
  -H "x-api-key: YOUR_LANGSMITH_API_KEY"
```

**Expected:**
- Thread state includes all messages
- History persists across requests

---

### Test 4: LangSmith Traces

1. Go to: https://smith.langchain.com
2. Navigate to: **Projects** → `agent-inbox`
3. Verify: Traces appear for your test requests

**What to Check:**
- ✅ Agent execution steps visible
- ✅ Token usage tracked
- ✅ Latency metrics recorded
- ✅ Errors (if any) captured

---

## 🆘 TROUBLESHOOTING

### Error: "Graph export 'graph' not found"

**Cause:** `src/graph.py` doesn't export variable named `graph`

**Solution:**
```python
# Add at end of src/graph.py
graph = create_graph()  # NOT app, NOT compiled_graph
```

---

### Error: "Invalid API key"

**Cause:** Environment variable not configured or wrong key

**Solution:**
1. Dashboard → Deployment → Settings → Environment Variables
2. Verify `OPENAI_API_KEY` is set
3. Test key locally first:
   ```bash
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer YOUR_KEY"
   ```

---

### Error: "Checkpointer not configured"

**Cause:** Code includes `.compile(checkpointer=...)`

**Solution:**
```python
# WRONG (for platform deployment)
from langgraph.checkpoint.memory import MemorySaver
graph = workflow.compile(checkpointer=MemorySaver())

# CORRECT (platform provides checkpointer)
graph = workflow.compile()  # No checkpointer arg!
```

---

### Error: "Module not found: langgraph_supervisor"

**Cause:** Missing dependency in `requirements.txt`

**Solution:**
```bash
# Add to requirements.txt
langgraph-supervisor>=0.0.29

# Commit and push
git add requirements.txt
git commit -m "fix: add langgraph-supervisor dependency"
git push origin main
```

Platform will auto-redeploy if **Automatic Updates** enabled.

---

### Deployment Stuck in "Building" State

**Causes:**
1. Large dependencies taking time
2. Network issues
3. Syntax error in graph code

**Debug Steps:**
1. Check **Build Logs** for errors
2. Verify `langgraph dev` works locally
3. Check GitHub Actions logs (if using CI/CD)
4. Contact LangGraph support if stuck >10 min

---

### Streaming Not Working

**Cause:** Incorrect API call format

**Solution:**
```bash
# Use /runs/stream endpoint (NOT /runs)
curl -X POST https://your-deployment.langchain.app/runs/stream \
  # ... rest of request
```

---

## 📊 MONITORING & OBSERVABILITY

### LangSmith Integration

**Automatic Tracing:**
- All agent executions traced to LangSmith
- View in: https://smith.langchain.com/projects

**What's Tracked:**
- ✅ Agent steps (nodes executed)
- ✅ LLM calls (prompts, responses, tokens)
- ✅ Tool calls (parameters, outputs)
- ✅ Latency (per step and total)
- ✅ Errors and exceptions

**Filtering Traces:**
- By `user_id` (from `config.configurable`)
- By `thread_id`
- By date range
- By status (success, error)

---

### Deployment Metrics

**Access Metrics:**
1. Dashboard → Your Deployment → **Metrics**

**Available Metrics:**
- Request rate (requests/minute)
- Latency (p50, p95, p99)
- Error rate
- Node executions (count towards monthly limit)

---

## 💰 COST MANAGEMENT

### LangGraph Platform Plus ($39/mo)

**Included:**
- 1 dev deployment (24/7)
- 100K node executions/month
- PostgreSQL persistence
- Unlimited threads
- LangSmith integration

**Additional Costs:**
- $0.001 per node execution after 100K/month

**Calculating Node Executions:**
- 1 message to agent = ~3-5 nodes (varies by graph complexity)
- Example: 10,000 user messages/month = ~40K nodes

**When to Upgrade to Production Plan ($156/mo):**
- Need 99.9% uptime SLA
- >100K node executions/month regularly
- Mission-critical production workload

---

## 🔐 SECURITY BEST PRACTICES

### 1. API Keys Management

**DO:**
- ✅ Store in LangGraph Platform dashboard (encrypted at rest)
- ✅ Rotate keys quarterly
- ✅ Use different keys for dev/prod
- ✅ Monitor usage in provider dashboards

**DON'T:**
- ❌ Hardcode in `src/graph.py`
- ❌ Commit to git (even in `.env`)
- ❌ Share keys between environments
- ❌ Expose in client-side code

---

### 2. Multi-Tenant Isolation

**Pass user-specific keys via `config.configurable`:**

```python
# In frontend API route
response = langgraph_client.stream_run(
    assistant_id="agent",
    input={"messages": messages},
    config={
        "configurable": {
            "openai_api_key": user_openai_key,  # From Supabase
            "user_id": clerk_user_id
        }
    }
)
```

**Why this matters:**
- User A's API key != User B's API key
- LangGraph Platform doesn't store keys (stateless)
- Keys passed per-request = isolation guaranteed

---

### 3. Thread Access Control

**Ensure only owner can access their threads:**

```python
# Backend API route
user_id = get_user_id_from_clerk_session()

# When creating thread
thread = langgraph_client.create_thread(
    metadata={"user_id": user_id}
)

# When accessing thread
thread_state = langgraph_client.get_thread_state(thread_id)
if thread_state.metadata["user_id"] != user_id:
    return 403  # Forbidden
```

---

## 📚 ADDITIONAL RESOURCES

### Official Documentation
- [LangGraph Platform Docs](https://langchain-ai.github.io/langgraph/cloud/)
- [Deployment Guide](https://langchain-ai.github.io/langgraph/cloud/deployment/cloud/)
- [API Reference](https://langchain-ai.github.io/langgraph/cloud/reference/sdk/python_sdk_ref/)

### Community Resources
- [LangGraph GitHub](https://github.com/langchain-ai/langgraph)
- [LangChain Discord](https://discord.gg/langchain)
- [Example Templates](https://github.com/langchain-ai/langgraph/tree/main/examples)

---

## 🎯 SUCCESS CHECKLIST

### Pre-Deployment
- [x] `langgraph.json` configured
- [x] `requirements.txt` complete with postgres checkpointer
- [x] `src/graph.py` exports `graph`
- [x] No checkpointer in code
- [x] Local `langgraph dev` works

### Deployment
- [ ] GitHub repo connected
- [ ] Environment variables configured
- [ ] Deployment created
- [ ] Build succeeded
- [ ] Deployment URL obtained

### Verification
- [ ] Health check: `200 OK`
- [ ] Streaming test: Agent responds
- [ ] Thread persistence: Messages saved
- [ ] LangSmith traces: Visible
- [ ] Multi-user test: Isolation works

### Production Ready
- [ ] Custom domain configured (optional)
- [ ] Monitoring alerts set up
- [ ] Cost tracking enabled
- [ ] Backup strategy documented
- [ ] Incident response plan ready

---

**🚀 Your LangGraph deployment is ready for production!**

For questions or issues, contact:
- LangGraph Support: support@langchain.com
- Community Discord: https://discord.gg/langchain
