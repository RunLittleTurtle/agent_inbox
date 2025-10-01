# 🧪 AGENT INBOX - COMPREHENSIVE TESTING GUIDE (2025)

**Date:** 2025-10-01
**Purpose:** Complete testing guide for multi-tenant Agent Inbox with LangGraph Platform features
**Audience:** Developers and QA testers

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Testing Philosophy](#testing-philosophy)
3. [Prerequisites](#prerequisites)
4. [Phase 1: Local Development Tests](#phase-1-local-development-tests)
5. [Phase 2: Deploy to LangGraph Platform](#phase-2-deploy-to-langgraph-platform)
6. [Phase 3: Multi-User Isolation Tests](#phase-3-multi-user-isolation-tests)
7. [Phase 4: LangGraph Platform Feature Tests](#phase-4-langgraph-platform-feature-tests)
8. [Phase 5: Production Verification](#phase-5-production-verification)
9. [Troubleshooting](#troubleshooting)
10. [Success Criteria Checklist](#success-criteria-checklist)

---

## Overview

This guide covers comprehensive testing of:
- **4-Layer Multi-Tenant Security** (Clerk + LangGraph Auth + Supabase RLS + Runtime)
- **LangGraph Platform Persistence** (Postgres checkpointer - automatic)
- **Cross-Thread Memory** (Store with semantic search)
- **Human-in-the-Loop** (Agent Inbox interrupts + resume)
- **Custom Authentication** (Thread-level isolation - 2025)

**Architecture:**
```
┌──────────────────────────────────────────┐
│ Layer 1: Frontend (Clerk Middleware)    │
├──────────────────────────────────────────┤
│ Layer 2: Backend (LangGraph Auth)       │ ⭐ NEW 2025
├──────────────────────────────────────────┤
│ Layer 3: Database (Supabase RLS)        │
├──────────────────────────────────────────┤
│ Layer 4: Execution (config.configurable)│
└──────────────────────────────────────────┘
```

---

## Testing Philosophy

### Defense-in-Depth Testing

Each security layer must be tested **independently** AND **together**:
- ✅ **Layer 1 fails?** → Layer 2 still protects
- ✅ **Layer 2 bypassed?** → Layer 3 still isolates
- ✅ **Layer 3 compromised?** → Layer 4 still separates

### Feature Completeness Testing

All LangGraph Platform features must be validated:
- ✅ **Persistence** → Conversations survive restarts
- ✅ **Store** → Memories persist across threads
- ✅ **Semantic Search** → Find relevant memories by meaning
- ✅ **Interrupts** → Human-in-the-loop workflows functional

---

## Prerequisites

### Accounts & Credentials

**Required accounts:**
- ✅ Clerk account (`modest-sunbeam-39.clerk.accounts.dev`)
- ✅ Supabase project (`lcswsadubzhynscruzfn.supabase.co`)
- ✅ LangSmith account (for tracing/monitoring)
- ✅ OpenAI API key (for testing)
- ✅ Anthropic API key (for testing)

**Test users to create:**
```bash
# Create these accounts in Clerk dashboard:
alice@test.com (password: Test123!@#)
bob@test.com (password: Test123!@#)
```

### Tools Needed

```bash
# Install required CLI tools
npm install -g vercel
pip install langgraph-cli

# Test API access
curl --version
jq --version  # For JSON parsing in scripts
```

### Environment Setup

```bash
# Verify .env files exist
ls agent-inbox/.env.development.local
ls agent-chat-ui-2/.env.development.local
ls config-app/.env.development.local

# Verify Python environment
source .venv/bin/activate
python --version  # Should be 3.11+
```

---

## Phase 1: Local Development Tests

**Duration:** 15 minutes
**Objective:** Verify auth handler and configuration before deployment

### Test 1.1: Auth Module Import

```bash
cd /path/to/agent_inbox_1.18
source .venv/bin/activate

# Test auth module loads
python -c "from src.auth import auth; print('✅ Auth module imported')"
# Expected: "✅ Auth module imported"
```

**Success criteria:** No ImportError, auth object is langgraph_sdk.auth.Auth type

### Test 1.2: LangGraph JSON Validation

```bash
# Validate JSON syntax
python -c "import json; config = json.load(open('langgraph.json')); print('✅ Valid JSON')"

# Check auth section exists
python -c "import json; config = json.load(open('langgraph.json')); print(f'Auth path: {config[\"auth\"][\"path\"]}')"
# Expected: "Auth path: ./src/auth.py:auth"

# Check store section exists
python -c "import json; config = json.load(open('langgraph.json')); print(f'Store embed: {config[\"store\"][\"index\"][\"embed\"]}')"
# Expected: "Store embed: openai:text-embedding-3-small"
```

**Success criteria:** All commands succeed, config sections present

### Test 1.3: Auth Function Callable

```bash
# Test anonymous access
python -c "
import asyncio
from src.auth import get_current_user

result = asyncio.run(get_current_user(None))
assert result['identity'] == 'anonymous'
assert result['is_authenticated'] == False
print('✅ Anonymous user handling correct')
"
# Expected: "✅ Anonymous user handling correct"

# Test with fake Bearer token
python -c "
import asyncio
from src.auth import get_current_user

result = asyncio.run(get_current_user('Bearer fake_token_123'))
assert result['identity'] == 'anonymous'  # Should fail validation
print('✅ Invalid token handling correct')
"
# Expected: "✅ Invalid token handling correct"
```

**Success criteria:** Auth function returns correct user dict structures

### Test 1.4: Graph Import

```bash
# Test graph loads without errors
python -c "
from src.graph import graph
print(f'✅ Graph type: {type(graph).__name__}')
print(f'✅ Graph nodes: {list(graph.nodes.keys()) if hasattr(graph, \"nodes\") else \"CompiledGraph\"}')
"
# Expected: Graph loads successfully
```

**Success criteria:** Graph imports without errors

### Test 1.5: Local LangGraph Dev Server

```bash
# Start local dev server (in background or separate terminal)
langgraph dev

# In another terminal, test health endpoint
curl http://localhost:2024/health
# Expected: {"status":"healthy"} or similar

# Test threads endpoint (should require auth)
curl http://localhost:2024/threads
# Expected: May work locally or return auth error (depends on local auth config)
```

**Success criteria:** Dev server starts, health endpoint responds

---

## Phase 2: Deploy to LangGraph Platform

**Duration:** 20 minutes
**Objective:** Deploy to production environment with auth enabled

### Test 2.1: Pre-Deployment Checklist

```bash
# Verify all auth files committed
git status
# Should show: src/auth.py, langgraph.json, frontend changes

# Verify no .env secrets in git
git ls-files | grep "\.env"
# Should be empty or only .env.example
```

### Test 2.2: Deploy to LangGraph Platform

**Via LangSmith Dashboard:**
1. Go to https://smith.langchain.com
2. Navigate to: LangGraph Platform → Deployments → + New Deployment
3. Configuration:
   - **Name:** `agent-inbox-production`
   - **Repository:** Your GitHub repo
   - **Branch:** `main`
   - **Config File:** `langgraph.json`
   - **Environment:** Production

4. **Environment Variables:**
```bash
# LLM APIs (fallback - users provide own)
OPENAI_API_KEY=sk-proj-xxx
ANTHROPIC_API_KEY=sk-ant-api03-xxx

# LangSmith
LANGSMITH_API_KEY=lsv2_pt_xxx
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=agent-inbox

# MCP Servers
RUBE_MCP_SERVER=https://rube.app/mcp
RUBE_AUTH_TOKEN=eyJxxx

# ⭐ CRITICAL: Custom Auth (2025)
CLERK_SECRET_KEY=sk_test_uYhzMtZM8ERcSQnc8mj3EGlRvznFPKFcHzoInZP0Ys

# Environment
ENVIRONMENT=production
LOG_LEVEL=INFO
USER_TIMEZONE=America/Toronto
```

5. **Deploy** → Wait for build to complete (~5 minutes)

### Test 2.3: Verify Deployment

```bash
# Save deployment URL
export DEPLOYMENT_URL="https://agent-inbox-prod-abc123.us.langgraph.app"

# Test health endpoint
curl $DEPLOYMENT_URL/health
# Expected: {"status":"ok"}

# Test auth enforcement (no token)
curl $DEPLOYMENT_URL/threads
# Expected: HTTP 403 Forbidden ✅ (auth working!)
```

**Success criteria:**
- ✅ Deployment succeeds
- ✅ Health endpoint returns 200
- ✅ Unauthenticated requests return 403

### Test 2.4: Check Deployment Logs

**Via LangSmith Dashboard:**
1. Go to Deployment → Logs
2. Look for auth initialization:
   ```
   INFO:src.auth:Auth module loaded
   INFO:langgraph_sdk:Custom auth handler registered
   ```

**Success criteria:** No errors in logs, auth handler loaded

---

## Phase 3: Multi-User Isolation Tests

**Duration:** 30 minutes
**Objective:** Verify 4-layer security enforcement

### Setup: Create Test Users

**Via Clerk Dashboard:**
1. Go to https://dashboard.clerk.com
2. Navigate to: Users → + Add User
3. Create:
   - alice@test.com (password: Test123!@#)
   - bob@test.com (password: Test123!@#)

### Test 3.1: Layer 1 - Frontend (Clerk Middleware)

**Test 3.1.1: Page Protection**
```bash
# 1. Open agent-inbox in incognito browser
open https://YOUR_VERCEL_URL/agent-inbox

# Expected: Redirect to Clerk login page
```

**Test 3.1.2: Authenticated Access**
```bash
# 1. Login as alice@test.com
# 2. Navigate to config-app
# Expected: Access granted, UserButton shows alice's avatar
```

**Success criteria:** Unauthenticated users cannot access protected pages

### Test 3.2: Layer 2 - Backend (LangGraph Custom Auth) ⭐ NEW 2025

**Test 3.2.1: Thread Isolation (Alice vs Bob)**

**Step 1: Alice creates threads**
```bash
# Get Alice's Clerk JWT (from browser DevTools → Application → Cookies → __session)
export ALICE_JWT="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."

# Alice creates 3 threads
for i in {1..3}; do
  curl -X POST $DEPLOYMENT_URL/threads \
    -H "Authorization: Bearer $ALICE_JWT" \
    -H "Content-Type: application/json" \
    -d "{\"metadata\": {\"graph_id\": \"agent\", \"name\": \"Alice Thread $i\"}}"
done
# Expected: 3 thread_ids returned
```

**Step 2: Alice lists her threads**
```bash
curl $DEPLOYMENT_URL/threads \
  -H "Authorization: Bearer $ALICE_JWT"
# Expected: Returns 3 threads (all alice's)
```

**Step 3: Bob lists threads**
```bash
# Get Bob's Clerk JWT (login as bob in separate browser)
export BOB_JWT="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."

curl $DEPLOYMENT_URL/threads \
  -H "Authorization: Bearer $BOB_JWT"
# Expected: Returns 0 threads ✅ (Bob can't see Alice's threads)
```

**Test 3.2.2: Cross-User Thread Access Prevention**
```bash
# Alice gets one of her thread IDs
export ALICE_THREAD_ID="thread_abc123"

# Bob tries to access Alice's specific thread
curl $DEPLOYMENT_URL/threads/$ALICE_THREAD_ID \
  -H "Authorization: Bearer $BOB_JWT"
# Expected: HTTP 404 Not Found ✅ (LangGraph auth filters it out)
```

**Test 3.2.3: Unauthenticated Access Blocked**
```bash
# Try without JWT token
curl $DEPLOYMENT_URL/threads
# Expected: HTTP 403 Forbidden ✅

# Try with invalid token
curl $DEPLOYMENT_URL/threads \
  -H "Authorization: Bearer invalid_token_xyz"
# Expected: HTTP 403 Forbidden ✅
```

**Success criteria:**
- ✅ Alice sees only her threads
- ✅ Bob sees only his threads (0 initially)
- ✅ Bob CANNOT access Alice's threads even with direct thread_id
- ✅ Unauthenticated requests blocked

### Test 3.3: Layer 3 - Database (Supabase RLS)

**Test 3.3.1: API Keys Isolation**

**Setup:** Configure API keys for both users
```bash
# 1. Login as alice@test.com → config-app
# 2. Add Alice's OpenAI key: sk-proj-alice...
# 3. Logout

# 4. Login as bob@test.com → config-app
# 5. Add Bob's OpenAI key: sk-proj-bob...
```

**Verification via Supabase SQL Editor:**
```sql
-- Switch to alice's JWT in Supabase dashboard
-- (Settings → API → JWT: paste alice's token)

SELECT * FROM user_secrets;
-- Expected: Returns ONLY alice's row

-- Switch to bob's JWT
SELECT * FROM user_secrets;
-- Expected: Returns ONLY bob's row

-- Try direct access (no auth)
SET request.jwt.claims TO '{}';
SELECT * FROM user_secrets;
-- Expected: Returns 0 rows (RLS blocks)
```

**Success criteria:** Each user sees ONLY their own API keys

### Test 3.4: Layer 4 - Execution (config.configurable)

**Test 3.4.1: Runtime API Key Injection**

**Alice's chat:**
```bash
# Alice sends message
curl -X POST $DEPLOYMENT_URL/runs/stream \
  -H "Authorization: Bearer $ALICE_JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "agent",
    "thread_id": "thread_runtime_test_alice",
    "input": {"messages": [{"role": "user", "content": "Hello"}]},
    "config": {
      "configurable": {
        "openai_api_key": "sk-proj-alice...",
        "user_id": "alice_clerk_id"
      }
    }
  }'
# → Agent responds using Alice's API key
```

**Verify in LangSmith:**
1. Go to https://smith.langchain.com
2. Find trace for thread_runtime_test_alice
3. Check LLM call → Verify API key starts with "sk-proj-alice..."

**Bob's chat (parallel):**
```bash
curl -X POST $DEPLOYMENT_URL/runs/stream \
  -H "Authorization: Bearer $BOB_JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "agent",
    "thread_id": "thread_runtime_test_bob",
    "input": {"messages": [{"role": "user", "content": "Hello"}]},
    "config": {
      "configurable": {
        "openai_api_key": "sk-proj-bob...",
        "user_id": "bob_clerk_id"
      }
    }
  }'
# → Agent responds using Bob's API key
```

**Success criteria:**
- ✅ Alice's requests use Alice's API key (check LangSmith trace)
- ✅ Bob's requests use Bob's API key (check LangSmith trace)
- ✅ No cross-contamination

---

## Phase 4: LangGraph Platform Feature Tests

**Duration:** 1 hour 30 minutes
**Objective:** Validate persistence, store, and interrupts

### Test 4.1: Persistence (Postgres Checkpointer)

**Context:** LangGraph Platform includes automatic Postgres persistence. No manual checkpointer configuration needed.

**Test 4.1.1: Conversation Continuity**
```bash
# Step 1: Alice starts conversation
curl -X POST $DEPLOYMENT_URL/runs/stream \
  -H "Authorization: Bearer $ALICE_JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "agent",
    "thread_id": "thread_persistence_test",
    "input": {"messages": [{"role": "user", "content": "Remember: my favorite color is blue"}]},
    "config": {
      "configurable": {
        "openai_api_key": "sk-proj-alice...",
        "user_id": "alice_clerk_id"
      }
    }
  }'
# → Agent responds: "Got it! Your favorite color is blue."

# Step 2: Continue conversation (5 minutes later)
curl -X POST $DEPLOYMENT_URL/runs/stream \
  -H "Authorization: Bearer $ALICE_JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "agent",
    "thread_id": "thread_persistence_test",
    "input": {"messages": [{"role": "user", "content": "What is my favorite color?"}]},
    "config": {
      "configurable": {
        "openai_api_key": "sk-proj-alice...",
        "user_id": "alice_clerk_id"
      }
    }
  }'
# → Agent responds: "Your favorite color is blue" ✅
```

**Success criteria:** Agent remembers context from previous message

**Test 4.1.2: Thread State Retrieval**
```bash
# Get full thread state
curl $DEPLOYMENT_URL/threads/thread_persistence_test/state \
  -H "Authorization: Bearer $ALICE_JWT" \
  | jq .

# Expected output:
# {
#   "values": {
#     "messages": [
#       {"role": "user", "content": "Remember: my favorite color is blue"},
#       {"role": "assistant", "content": "Got it! ..."},
#       {"role": "user", "content": "What is my favorite color?"},
#       {"role": "assistant", "content": "Your favorite color is blue"}
#     ]
#   },
#   "next": [],
#   "checkpoint": {...}
# }
```

**Success criteria:** All messages present in thread state

**Test 4.1.3: Restart Survival**
```bash
# Step 1: Create conversation (as above)
# Step 2: Restart deployment
#   → LangSmith Dashboard → Deployments → agent-inbox-production → Restart

# Step 3: Wait for restart (~30 seconds)

# Step 4: Resume conversation
curl -X POST $DEPLOYMENT_URL/runs/stream \
  -H "Authorization: Bearer $ALICE_JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "agent",
    "thread_id": "thread_persistence_test",
    "input": {"messages": [{"role": "user", "content": "Do you still remember my favorite color?"}]},
    "config": {
      "configurable": {
        "openai_api_key": "sk-proj-alice...",
        "user_id": "alice_clerk_id"
      }
    }
  }'
# → Agent responds: "Yes, it's blue" ✅ (survived restart!)
```

**Success criteria:** Conversation state survives deployment restart

### Test 4.2: Cross-Thread Memory (Store)

**Context:** LangGraph Store allows memories to persist across threads. Already configured in langgraph.json with semantic search.

**Test 4.2.1: Store Data Across Threads**

**Note:** This requires the agent graph to implement store operations. Check if your agent uses `store.put()` and `store.search()`.

**Test script (Python SDK):**
```python
from langgraph_sdk import get_client
import os

# Setup
client = get_client(url=os.getenv("DEPLOYMENT_URL"))
alice_jwt = os.getenv("ALICE_JWT")

# Thread 1: Teach agent a preference
response1 = client.runs.create(
    thread_id="thread_prefs_store",
    assistant_id="agent",
    input={"messages": [{"role": "user", "content": "I prefer Python for data science"}]},
    config={
        "configurable": {
            "openai_api_key": "sk-proj-alice...",
            "user_id": "alice_clerk_id"
        }
    },
    headers={"Authorization": f"Bearer {alice_jwt}"}
)

print("Thread 1 response:", response1)
# Agent should store: store.put(namespace=["memories", "alice_clerk_id"], key="language_pref", value={"pref": "Python"})

# Thread 2: Different conversation (different thread_id)
response2 = client.runs.create(
    thread_id="thread_work_store",  # ← DIFFERENT thread
    assistant_id="agent",
    input={"messages": [{"role": "user", "content": "What language should I use for data analysis?"}]},
    config={
        "configurable": {
            "openai_api_key": "sk-proj-alice...",
            "user_id": "alice_clerk_id"
        }
    },
    headers={"Authorization": f"Bearer {alice_jwt}"}
)

print("Thread 2 response:", response2)
# Agent should search: store.search(namespace=["memories", "alice_clerk_id"], query="language preference")
# Expected: Agent recalls "I prefer Python for data science" and responds accordingly ✅
```

**Success criteria:** Agent recalls memory from different thread

**Test 4.2.2: Semantic Search**

**Test script:**
```python
# Direct store access (if implemented in agent)
# Store multiple facts
facts = [
    "I love hiking in the mountains on weekends",
    "My favorite food is sushi from Japan",
    "I enjoy outdoor activities like camping"
]

# Agent stores these across multiple conversations...

# Later, search with semantic query (not exact match)
# Agent uses: store.search(namespace=["memories", "alice_clerk_id"], query="What outdoor hobbies does Alice have?")
# Expected: Returns "hiking in mountains" and "outdoor activities like camping"
# (NOT "favorite food is sushi" - semantic filtering works) ✅
```

**Success criteria:** Search returns semantically similar memories

**Test 4.2.3: Store Isolation Between Users**
```python
# Alice stores secret
# agent.store.put(namespace=["memories", "alice_clerk_id"], key="secret", value={"data": "Alice's secret project"})

# Bob tries to search Alice's namespace (via his own agent session)
# agent.store.search(namespace=["memories", "alice_clerk_id"], query="secret")
# Expected: Returns empty OR auth error ✅ (can't access other user's namespace)
```

**Success criteria:** Users cannot access each other's store namespaces

### Test 4.3: Human-in-the-Loop (Agent Inbox Interrupts)

**Context:** Agent Inbox UI provides human-in-the-loop workflow. Agent creates interrupts, human responds via UI.

**Test 4.3.1: Create Interrupt**

**Verify agent creates interrupts:**
1. Open agent-chat-ui-2 (logged in as alice@test.com)
2. Send message that triggers interrupt (depends on your agent's logic)
   Example: "Send an email to my boss about the project"
3. Agent should create interrupt and pause

**Verify in agent-inbox UI:**
1. Open agent-inbox (same browser, alice logged in)
2. Check threads list
3. **Expected:** New thread with status "interrupted" appears
4. Click thread → View interrupt details:
   - **action_request.action:** "send_email"
   - **action_request.args:** `{"to": "boss@company.com", "subject": "Project update"}`
   - **Buttons available:** Accept, Ignore, Respond, Edit

**Test 4.3.2: Resume with Accept**
1. Click "Accept" button in agent-inbox UI
2. **Expected:** Thread status changes to "processing" or "completed"
3. **Expected:** Agent resumes execution and sends email (or simulates)

**Verify via API:**
```bash
# Check thread state after accept
curl $DEPLOYMENT_URL/threads/THREAD_ID/state \
  -H "Authorization: Bearer $ALICE_JWT" \
  | jq .

# Expected: Thread no longer interrupted, execution completed
```

**Test 4.3.3: Resume with Edit**
1. Create new interrupt (repeat 4.3.1)
2. Click "Edit" button in agent-inbox UI
3. Modify args:
   - Change `to: "different@email.com"`
   - Change `subject: "Modified subject"`
4. Submit
5. **Expected:** Agent resumes with MODIFIED args

**Test 4.3.4: Resume with Ignore**
1. Create new interrupt
2. Click "Ignore" button
3. **Expected:** Agent skips action and continues to next step

**Test 4.3.5: Cross-User Interrupt Isolation**
1. Alice creates interrupt (logged in as alice)
2. Bob opens agent-inbox (logged in as bob in different browser)
3. **Expected:** Bob does NOT see Alice's interrupt ✅
4. **Expected:** Bob sees 0 interrupted threads (isolation working)

**Success criteria:**
- ✅ Interrupts appear in agent-inbox UI with correct data
- ✅ Resume with accept/edit/ignore all work correctly
- ✅ Users only see their own interrupts (isolation enforced)

---

## Phase 5: Production Verification

**Duration:** 15 minutes
**Objective:** Final production readiness checks

### Test 5.1: End-to-End User Journey (Alice)

**Complete user flow:**
```bash
# 1. Signup/Login
# → Open https://YOUR_VERCEL_URL
# → Login as alice@test.com

# 2. Configure API Keys
# → Open config-app
# → Add OpenAI API key
# → Save → Expected: Success toast

# 3. Chat with Agent
# → Open agent-chat-ui-2
# → Send: "Hello, remember my name is Alice"
# → Expected: Agent responds with greeting

# 4. Test Persistence
# → Send: "What is my name?"
# → Expected: Agent responds "Alice" (remembered from checkpoint)

# 5. Create Interrupt
# → Send: "Send an email to boss@company.com"
# → Expected: Agent creates interrupt

# 6. Approve via Agent Inbox
# → Open agent-inbox
# → Find interrupted thread
# → Click "Accept"
# → Expected: Thread resumes and completes

# 7. Cross-Thread Memory (if implemented)
# → Open agent-chat-ui-2 (new conversation)
# → Send: "What's my name?" (different thread_id)
# → Expected: Agent recalls from store (if implemented)
```

**Success criteria:** Entire flow completes without errors

### Test 5.2: End-to-End User Journey (Bob) - Parallel

**Run simultaneously with Alice's journey:**
```bash
# 1. Signup/Login (different browser or incognito)
# → Login as bob@test.com

# 2. Configure API Keys
# → Add Bob's DIFFERENT OpenAI key
# → Expected: Does NOT see Alice's key

# 3. Chat with Agent
# → Send: "Hello, my name is Bob"
# → Expected: Agent responds (using Bob's API key)

# 4. Verify Isolation
# → Open agent-inbox
# → Expected: Does NOT see any of Alice's threads ✅
# → Expected: Only sees Bob's own threads
```

**Success criteria:**
- ✅ Bob's journey completes successfully
- ✅ Bob NEVER sees Alice's data (threads, memories, API keys)
- ✅ Both users operate independently without interference

### Test 5.3: Monitoring & Observability

**LangSmith Traces:**
1. Go to https://smith.langchain.com
2. Navigate to: Projects → agent-inbox
3. Filter by user_id:
   - Search for traces containing "alice_clerk_id"
   - Search for traces containing "bob_clerk_id"
4. **Expected:** Separate traces for each user ✅

**LangGraph Platform Logs:**
1. Go to: LangSmith → Deployments → agent-inbox-production → Logs
2. Look for auth messages:
   ```
   INFO:src.auth:User authenticated successfully: user_2abc123xyz
   INFO:src.auth:Added user_id filter for user: user_2abc123xyz
   ```
3. **Expected:** No permission errors or auth failures

**Supabase Logs:**
1. Go to: Supabase Dashboard → Logs → PostgreSQL
2. Check RLS enforcement:
   ```sql
   SELECT * FROM auth.audit_log_entries WHERE action = 'SELECT';
   ```
3. **Expected:** All queries filtered by clerk_id (RLS working)

**Success criteria:** All monitoring systems show healthy operation with isolation

---

## Troubleshooting

### Issue 1: "HTTP 403 Forbidden" on All Requests

**Symptoms:**
- All API calls return 403
- Logs show: "Authentication required to access LangGraph resources"

**Diagnosis:**
```bash
# Check if CLERK_SECRET_KEY is set
curl $DEPLOYMENT_URL/threads -v \
  -H "Authorization: Bearer $ALICE_JWT"
# Look for error message in response body
```

**Solutions:**
1. **Verify CLERK_SECRET_KEY in deployment:**
   - LangSmith Dashboard → Deployments → Environment Variables
   - Check `CLERK_SECRET_KEY=sk_test_...` is present

2. **Verify JWT token is valid:**
   ```bash
   # Decode JWT (without verification)
   echo "$ALICE_JWT" | cut -d'.' -f2 | base64 -d | jq .
   # Check "exp" (expiration) is in the future
   ```

3. **Verify Clerk session:**
   - Browser DevTools → Application → Cookies
   - Check `__session` cookie exists and is not expired

**Fix:** Add CLERK_SECRET_KEY to deployment, redeploy

---

### Issue 2: Users Seeing Each Other's Threads

**Symptoms:**
- Bob sees Alice's threads in agent-inbox
- Thread isolation not working

**Diagnosis:**
```bash
# Check auth logs
# LangSmith Dashboard → Deployments → Logs
# Look for: "Added user_id filter for user: xxx"
# If missing, auth handler not applying filter

# Check thread metadata
curl $DEPLOYMENT_URL/threads/THREAD_ID \
  -H "Authorization: Bearer $ALICE_JWT" \
  | jq '.metadata'
# Should contain: {"user_id": "alice_clerk_id"}
```

**Solutions:**
1. **Verify auth handler is loaded:**
   - Check deployment logs for "Custom auth handler registered"
   - If missing, verify `langgraph.json` has auth section
   - Redeploy if needed

2. **Verify JWT contains user_id:**
   ```bash
   echo "$ALICE_JWT" | cut -d'.' -f2 | base64 -d | jq '.sub'
   # Should return Clerk user ID
   ```

3. **Verify add_owner function runs:**
   - Add debug logging to src/auth.py (if needed)
   - Check logs for "Added user_id filter for user: xxx"

**Fix:** Ensure auth handler is properly deployed and JWT validation works

---

### Issue 3: Persistence Not Working (Agent Forgets Context)

**Symptoms:**
- Agent doesn't remember previous messages
- Continuation messages fail

**Diagnosis:**
```bash
# Check thread state
curl $DEPLOYMENT_URL/threads/THREAD_ID/state \
  -H "Authorization: Bearer $ALICE_JWT" \
  | jq '.values.messages'
# Should contain all previous messages
```

**Solutions:**
1. **Verify same thread_id used:**
   - Check that continuation requests use SAME thread_id as original
   - Different thread_id = different conversation (expected behavior)

2. **Verify checkpoint storage:**
   - LangSmith Dashboard → Deployments → Logs
   - Look for "Checkpoint saved" messages
   - If missing, checkpointer may not be configured

3. **Verify Postgres connection:**
   - LangGraph Platform automatically configures Postgres
   - Check deployment status (green = healthy)

**Fix:** Ensure thread_id consistency across requests

---

### Issue 4: Semantic Search Not Finding Memories

**Symptoms:**
- Store memories saved but search returns empty
- Agent doesn't recall stored information

**Diagnosis:**
```python
# Check if embeddings are being generated
# LangSmith Dashboard → Traces → Look for embedding calls
# Should see: openai.embeddings.create() calls
```

**Solutions:**
1. **Verify store configuration in langgraph.json:**
   ```json
   {
     "store": {
       "index": {
         "embed": "openai:text-embedding-3-small",
         "dims": 1536,
         "fields": ["$"]
       }
     }
   }
   ```

2. **Verify OPENAI_API_KEY in deployment:**
   - Check Environment Variables includes OpenAI key
   - Embedding calls need this key

3. **Verify namespace consistency:**
   - store.put() and store.search() must use SAME namespace
   - Example: `["memories", "alice_clerk_id"]`

**Fix:** Ensure store config and API keys are correct

---

### Issue 5: Interrupts Not Appearing in Agent Inbox

**Symptoms:**
- Agent creates interrupt but UI shows nothing
- Thread stuck in "interrupted" state

**Diagnosis:**
```bash
# Check thread status
curl $DEPLOYMENT_URL/threads/THREAD_ID \
  -H "Authorization: Bearer $ALICE_JWT" \
  | jq '.status'
# Should return: "interrupted"

# Check interrupt data
curl $DEPLOYMENT_URL/threads/THREAD_ID/state \
  -H "Authorization: Bearer $ALICE_JWT" \
  | jq '.tasks[0].interrupts'
# Should contain interrupt data
```

**Solutions:**
1. **Verify agent-inbox fetches interrupted threads:**
   - Check Network tab in DevTools
   - Should see API call to `/threads?status=interrupted`

2. **Verify frontend JWT:**
   - agent-inbox must send Authorization header
   - Check ThreadContext.tsx for `clerkToken` usage

3. **Verify interrupt format:**
   - Interrupt must follow schema (action_request, config, description)
   - Check src/multi_tool_rube_agent/human_inbox.py

**Fix:** Ensure agent-inbox properly fetches and displays interrupted threads

---

## Success Criteria Checklist

### ✅ Authentication & Authorization

- [ ] Clerk login/logout works for all 3 UIs
- [ ] Unauthenticated users redirected to login
- [ ] JWT tokens generated and included in API calls
- [ ] CLERK_SECRET_KEY configured in deployment
- [ ] Custom auth handler validates tokens correctly

### ✅ Multi-User Isolation (4 Layers)

**Layer 1: Frontend**
- [ ] Alice cannot access Bob's pages (even with URL)
- [ ] Bob cannot access Alice's pages

**Layer 2: Backend (LangGraph Auth)**
- [ ] Alice sees only her threads via API
- [ ] Bob sees only his threads via API
- [ ] Alice cannot GET Bob's thread (even with thread_id)
- [ ] Unauthenticated requests return HTTP 403

**Layer 3: Database (Supabase RLS)**
- [ ] Alice sees only her API keys in config-app
- [ ] Bob sees only his API keys in config-app
- [ ] Direct SQL queries filtered by clerk_id

**Layer 4: Execution (config.configurable)**
- [ ] Alice's requests use Alice's OpenAI key (check LangSmith)
- [ ] Bob's requests use Bob's OpenAI key (check LangSmith)
- [ ] No API key cross-contamination

### ✅ LangGraph Platform Features

**Persistence (Checkpointer):**
- [ ] Agent remembers context between messages (same thread)
- [ ] Thread state retrievable via API
- [ ] Conversations survive deployment restarts

**Cross-Thread Memory (Store):**
- [ ] Memories persist across different threads (same user)
- [ ] Semantic search finds relevant memories (not just exact match)
- [ ] Store namespaces isolated by user (Bob can't access Alice's)

**Human-in-the-Loop (Interrupts):**
- [ ] Interrupts created correctly (thread status = "interrupted")
- [ ] Agent-inbox UI displays interrupt with action_request
- [ ] Resume works: accept, edit, ignore, respond
- [ ] Users only see their own interrupts (isolation)

### ✅ Production Readiness

- [ ] All environment variables configured correctly
- [ ] No secrets in git repository
- [ ] Deployment logs show no errors
- [ ] LangSmith traces show user isolation
- [ ] Monitoring systems healthy (LangSmith, Supabase)
- [ ] End-to-end user journey works (Alice + Bob)

### ✅ Documentation

- [ ] PRODUCTION_DEPLOYMENT_PLAN.md up to date
- [ ] LANGGRAPH_AUTH_INTEGRATION_REPORT.md complete
- [ ] TESTING_GUIDE_2025.md (this document) complete
- [ ] README includes deployment instructions

---

## Conclusion

This testing guide provides comprehensive coverage of:
- ✅ Multi-tenant security (4 layers)
- ✅ LangGraph Platform features (persistence, store, interrupts)
- ✅ Custom authentication (2025 best practices)
- ✅ Production readiness verification

**Total Testing Time:** ~4 hours (first time), ~2 hours (subsequent runs)

**Next Steps After Testing:**
1. Document any issues found → Create GitHub issues
2. Fix critical issues → Retest
3. Update deployment plan with actual timings
4. Proceed to production deployment (Epic 6)

**Questions or Issues?**
- Check troubleshooting section above
- Review LangGraph Platform docs: https://langchain-ai.github.io/langgraph/
- Check LANGGRAPH_AUTH_INTEGRATION_REPORT.md for architecture details

---

**Document Version:** 1.0
**Last Updated:** 2025-10-01
**Author:** AI Assistant (Claude Code)
