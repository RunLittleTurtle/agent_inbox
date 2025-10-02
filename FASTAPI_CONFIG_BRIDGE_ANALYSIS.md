# FastAPI Config Bridge - Implementation Analysis & Action Plan

**Date:** October 2, 2025 | **Status:** ⏳ Phase 4 Ready to Start (70% Total) | **Estimated Time:** 16-24 hours

---

## 🎯 Two-Way Sync Architecture Overview

This FastAPI service enables **bidirectional configuration sync** between TypeScript Config App and Python LangGraph agents:

```
┌────────────────────────────────────────────────────────────────┐
│                    TWO-WAY SYNC FLOW                            │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  TypeScript Config App (Next.js)                                │
│         ↓ READ                      ↓ WRITE                     │
│         ↓                           ↓                           │
│    ┌────────────────────────────────────────┐                  │
│    │        FastAPI Bridge (Port 8000)      │                  │
│    │  - GET /api/config/schemas             │                  │
│    │  - GET /api/config/values              │                  │
│    │  - POST /api/config/update             │                  │
│    │  - POST /api/config/reset              │                  │
│    └────────┬───────────────────────┬───────┘                  │
│             ↓ READ                  ↓ WRITE                     │
│             ↓                       ↓                           │
│  ┌──────────────────┐    ┌─────────────────────┐              │
│  │  Python Code     │    │  Supabase           │              │
│  │  (Defaults)      │    │  (User Overrides)   │              │
│  │  - prompt.py     │    │  - agent_configs    │              │
│  │  - config.py     │    │    table            │              │
│  │  IMMUTABLE ✅    │    │  - config_data JSON │              │
│  └──────────┬───────┘    │  - prompts JSONB    │              │
│             │             └─────────┬───────────┘              │
│             │ READ (defaults)       │ READ (overrides)         │
│             └───────────────────────┘                          │
│                         ↓                                       │
│              Python LangGraph Agents                           │
│              (Merge: override > default)                       │
│                                                                  │
└────────────────────────────────────────────────────────────────┘
```

**Key Points:**
- **TypeScript Config App**: Edits configs via FastAPI endpoints (never touches Python code)
- **FastAPI Bridge**: Reads schemas from Python code, reads/writes overrides to Supabase
- **Python Agents**: Read defaults from code + overrides from Supabase at runtime
- **Immutability**: Python code defaults NEVER auto-modified, always safe fallback
- **Per-Agent**: Each agent has its own specific defaults (calendar ≠ email ≠ executive)

---

## 📋 Project Implementation Checklist

### Phase 0: Architecture Setup (Config Consolidation) ✅ COMPLETE
- [x] **0.1** ~~Create `/src/shared_config/constants.py`~~ → Uses existing `shared_utils/` (more flexible)
- [x] **0.2** ~~Update each agent's `ui_config.py`~~ → Already imports from `shared_utils`
- [x] **0.3** Add `DEFAULTS` export to each agent's `prompt.py` ✅
  - [x] calendar_agent (6 prompts)
  - [x] multi_tool_rube_agent (3 prompts)
  - [x] executive-ai-assistant (9 prompts - lazy-loaded)
  - [x] _react_agent_mcp_template (3 prompts)
- [x] **0.4** Add `DEFAULTS` export to each agent's `config.py` ✅
  - [x] calendar_agent (llm, calendar_settings, agent_identity)
  - [x] multi_tool_rube_agent (llm, agent_identity, timezone)
  - [x] executive-ai-assistant (llm, agent_identity, timezone)
  - [x] _react_agent_mcp_template (llm, agent_identity, timezone, mcp_integration)
- [x] **0.5** Consolidate SQL: `/supabase/migrations/002_agent_configs.sql` ✅
- [x] **0.6** Create verification test: `test_phase_0_defaults.py` ✅

### ⚠️ SQL Files Consolidation Status
**Three SQL files exist - consolidation needed:**
1. ✅ `/supabase_setup.sql` - `user_secrets` table (KEEP - already in Supabase)
2. ⚠️ `/config-app/supabase_agent_configs.sql` - OLD `agent_configs` (missing `prompts` column)
3. ✅ `/supabase/migrations/002_agent_configs.sql` - NEW `agent_configs` (has `prompts` column)

**Action Required**: Use file #3 (`/supabase/migrations/002_agent_configs.sql`) as source of truth.
- If `agent_configs` table exists without `prompts` column → Add column via ALTER TABLE
- If table doesn't exist → Run full migration

### Phase 1: Database Setup & Verification ✅ COMPLETE
- [x] **1.1** Create SQL migration files and verification scripts ✅
  - [x] `/supabase/migrations/001_check_schema.sql` - Diagnostic queries
  - [x] `/supabase/migrations/002a_add_prompts_column.sql` - Add prompts column
  - [x] `PHASE_1_MIGRATION_GUIDE.md` - Step-by-step instructions
- [x] **1.2** Run Supabase migration ✅ (`agent_configs` table created with `prompts` column)
- [x] **1.3** Verify RLS policies are enabled ✅ (4 policies: SELECT, INSERT, UPDATE, DELETE)
- [x] **1.4** Upgrade supabase-py for 2025 API keys ✅ (v2.7.4 → v2.20.0)
- [x] **1.5** Fix FastAPI `.single()` → `.maybe_single()` for create logic ✅
- [x] **1.6** Test FastAPI service locally ✅ (all endpoints working)
- [x] **1.7** Test endpoints with automated test suite ✅ (`test_fastapi_endpoints.py`)

**Achievements**:
- ✅ Discovered and fixed Supabase 2025 key format compatibility (upgraded supabase-py to v2.20.0)
- ✅ Database schema verified: `agent_configs` table with `config_data` + `prompts` JSONB columns
- ✅ All FastAPI endpoints tested and working: `/`, `/api/config/schemas`, `/api/config/values`, `/api/config/update`
- ✅ End-to-end test: Create config → Store in Supabase → Retrieve config → Delete config
- ✅ Supabase client initialized successfully with new `sb_secret_xxx` key format

### Phase 2: CLI Integration ✅ COMPLETE
- [x] **2.1** Add `config_api()` command to `/CLI/cli.py` ✅
- [x] **2.2** Integrate config-api into `start()` command ✅
- [x] **2.3** Test: `python cli.py config-api` ✅ (all endpoints working)
- [x] **2.4** Test: `python cli.py start` ✅ (config-api included in stack)

**Achievements**:
- ✅ Created standalone `config_api()` CLI command (CLI/cli.py:1072-1136)
- ✅ Command kills existing processes on port 8000 and starts uvicorn with --reload
- ✅ Integrated config-api into `start()` as Step 3 (after Executive Assistant, before UIs)
- ✅ Added config_api_process to port cleanup, monitoring loop, and graceful shutdown
- ✅ All tests passing: root endpoint, schemas (4 agents), values, update, cleanup
- ✅ Service starts on port 8000 and responds to all API endpoints correctly

### Phase 3: FastAPI Merge Logic (Defaults + Overrides) ✅ COMPLETE
- [x] **3.1** Create `get_agent_defaults()` function ✅ (reads from prompt.py + config.py)
- [x] **3.2** Update GET `/api/config/values` ✅ (returns default + user_override + current + is_overridden)
- [x] **3.3** POST `/api/config/reset` endpoint ✅ (reset field, section, or all)
- [x] **3.4** Test merge logic ✅ (10/10 tests passed)
- [x] **3.5** Fix `.maybe_single()` null handling ✅

**Achievements**:
- ✅ `get_agent_defaults()` dynamically loads defaults from Python code per agent
- ✅ Each field returns: `default` (immutable code), `user_override` (Supabase), `current` (merged), `is_overridden` (bool)
- ✅ Reset API supports 3 modes: reset_all (delete row), reset_section (remove section), reset_field (remove field)
- ✅ Comprehensive test suite: test_phase3_merge_logic.py (10 tests, all passing)
- ✅ Tested: create overrides, merge priority (override > default), resets at all levels
- ✅ Verified: defaults preserved after override, multi-user isolation working

### Phase 4: Config-App UI Integration (Call FastAPI Bridge) ⏳
**Goal:** Replace TypeScript config logic with FastAPI calls for two-way sync

- [ ] **4.1** Add `CONFIG_API_URL` env var to `config-app/.env.local`
  - Local: `http://localhost:8000`
  - Production: Railway URL (Phase 6)
- [ ] **4.2** Update Next.js API routes to proxy to FastAPI:
  - `app/api/config/agents/route.ts` → `GET {API_URL}/api/config/schemas`
  - `app/api/config/values/route.ts` → `GET {API_URL}/api/config/values?agent_id=X&user_id=Y`
  - `app/api/config/update/route.ts` → `POST {API_URL}/api/config/update`
  - `app/api/config/reset/route.ts` → `POST {API_URL}/api/config/reset`
- [ ] **4.3** Update `ConfigField` component to display merged values:
  - Show `default` (from Python code, collapsed)
  - Show `user_override` (editable, highlighted if present)
  - Show `current` (what agent actually uses)
  - Show "Custom" badge if `is_overridden === true`
- [ ] **4.4** Add "Reset to default" button per field
- [ ] **4.5** Add "Reset all" button per agent section
- [ ] **4.6** Test full flow: UI reads from FastAPI → displays merged → user edits → writes to FastAPI → Supabase updated

### Phase 5: Python Agent Runtime Integration (Read Overrides from Supabase) ⏳
**Goal:** Make agents read user overrides from Supabase at runtime and merge with code defaults

- [ ] **5.1** Create `/src/shared_utils/supabase_config.py` helper module
  - `get_agent_config(agent_id, user_id)` → returns user overrides from Supabase
  - `update_agent_config(agent_id, user_id, config)` → writes to Supabase (for direct agent use)
  - `reset_agent_config(agent_id, user_id)` → deletes overrides (reverts to defaults)
- [ ] **5.2** Update calendar_agent graph nodes to read from Supabase
  - Extract `user_id` from RunnableConfig
  - Call `get_agent_config("calendar", user_id)`
  - Merge: `user_override or CODE_DEFAULT`
- [ ] **5.3** Update multi_tool_rube_agent graph nodes
- [ ] **5.4** Update executive-ai-assistant graph nodes
- [ ] **5.5** Update _react_agent_mcp_template (for future agents)
- [ ] **5.6** Update UI SDK calls (agent-inbox, agent-chat-ui) to pass `user_id` in RunnableConfig
- [ ] **5.7** Test: Change config in UI → Verify agent uses override → Reset → Verify agent uses default

### Phase 6: FastAPI Deployment (Railway) ⏳
- [ ] **6.1** Install Railway CLI
- [ ] **6.2** Deploy FastAPI to Railway
- [ ] **6.3** Set environment variables in Railway
- [ ] **6.4** Get production URL
- [ ] **6.5** Update Vercel env var: `CONFIG_API_URL`
- [ ] **6.6** Redeploy config-app on Vercel

### Phase 7: Testing & Validation ⏳
- [ ] **7.1** End-to-end local test (config change → agent execution)
- [ ] **7.2** Test "Reset to default" functionality
- [ ] **7.3** Verify data in Supabase `agent_configs` table
- [ ] **7.4** Production deployment test
- [ ] **7.5** Monitor logs for errors
- [ ] **7.6** Test multi-user isolation

---

## 🏗️ Architecture: Immutable Defaults + User Overrides

### Core Principle: Code as Safe Defaults, Supabase as Overrides

```
┌─────────────────────────────────────────────────────────────────────────┐
│                   IMMUTABLE DEFAULTS + OVERRIDES ARCHITECTURE            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌───────────────────────────┐                                          │
│  │   Python Code (Defaults)  │  ⚠️ NEVER auto-modified                 │
│  │   ✅ Version controlled    │  ⚠️ Git is source of truth              │
│  │   ✅ Always safe fallback  │  ⚠️ Per-agent specific                 │
│  │                            │                                          │
│  │  /src/calendar_agent/      │                                          │
│  │    ├── prompt.py           │  ← AGENT_SYSTEM_PROMPT (default)       │
│  │    ├── config.py           │  ← LLM_CONFIG_DEFAULTS (default)       │
│  │    └── ui_config.py        │  ← Schema + imports shared constants   │
│  │                            │                                          │
│  │  /src/email_agent/         │                                          │
│  │    ├── prompt.py           │  ← EMAIL_SYSTEM_PROMPT (different!)    │
│  │    ├── config.py           │  ← EMAIL_CONFIG_DEFAULTS (different!)  │
│  │    └── ui_config.py        │                                          │
│  └────────────┬───────────────┘                                          │
│               │                                                           │
│               │ FastAPI reads defaults from code                         │
│               ↓                                                           │
│  ┌────────────────────────────┐                                         │
│  │       FastAPI              │                                          │
│  │   Merge Logic (Smart)      │                                          │
│  │                            │                                          │
│  │  def get_values():         │                                          │
│  │    defaults = load_from_code(agent_id)                               │
│  │    overrides = load_from_supabase(user_id, agent_id)                 │
│  │    return merge(defaults, overrides)                                  │
│  │                            │                                          │
│  │  Returns:                  │                                          │
│  │    - default: from code    │                                          │
│  │    - user_override: from Supabase (can be null)                      │
│  │    - current: what agent uses                                         │
│  │    - is_overridden: bool   │                                          │
│  └────────────┬───────────────┘                                          │
│               │                                                           │
│               │ Config-app displays both                                 │
│               ↓                                                           │
│  ┌────────────────────────────┐      ┌────────────────────────────┐    │
│  │      Config-App (UI)       │      │      Supabase              │    │
│  │                            │      │   (User Overrides Only)    │    │
│  │  Shows:                    │◄────►│                            │    │
│  │  ├─ Default (collapsed)    │      │  agent_configs table:      │    │
│  │  ├─ Override (editable)    │      │  ├─ clerk_id: user_123     │    │
│  │  ├─ "Custom" badge         │      │  ├─ agent_id: calendar     │    │
│  │  └─ "Reset" button         │      │  ├─ config_data: {...}     │    │
│  │                            │      │  └─ prompts: {...}         │    │
│  └────────────────────────────┘      └────────────────────────────┘    │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │              LangGraph Agents (Runtime)                          │   │
│  │                                                                   │   │
│  │  def calendar_node(state, config):                               │   │
│  │      user_id = config.get("configurable", {}).get("user_id")    │   │
│  │      user_config = get_agent_config("calendar", user_id)        │   │
│  │                                                                   │   │
│  │      # Priority: Override > Default                              │   │
│  │      model = user_config.get("llm", {}).get("model")            │   │
│  │               or CALENDAR_LLM_DEFAULTS["model"]  ✅              │   │
│  │                                                                   │   │
│  │      prompt = user_config.get("prompts", {}).get("system_prompt")│   │
│  │                or CALENDAR_SYSTEM_PROMPT  ✅                      │   │
│  │                                                                   │   │
│  │  Each agent has OWN defaults - no global defaults!               │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

### Per-Agent Defaults (NOT Global!)

**CRITICAL: Each agent has its OWN defaults:**

```python
# ✅ /src/calendar_agent/prompt.py
AGENT_SYSTEM_PROMPT = """You are a CALENDAR assistant..."""
SCHEDULING_PROMPT = """When scheduling meetings..."""

# ✅ /src/email_agent/prompt.py
EMAIL_SYSTEM_PROMPT = """You are an EMAIL assistant..."""  # ← DIFFERENT!
DRAFT_PROMPT = """When drafting emails..."""              # ← DIFFERENT!

# ✅ /src/multi_tool_rube_agent/prompt.py
RUBE_SYSTEM_PROMPT = """You are a MULTI-TOOL assistant..."""  # ← DIFFERENT!
```

**Each node within an agent can ALSO have its own defaults:**

```python
# /src/calendar_agent/config.py
NODE_SPECIFIC_DEFAULTS = {
    "scheduler_node": {
        "model": "gpt-4o",           # Scheduler needs faster model
        "temperature": 0.1
    },
    "email_composer_node": {
        "model": "claude-sonnet-4-5",  # Composer needs better writing
        "temperature": 0.7
    }
}
```

---

## 🏗️ Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        PRODUCTION STACK                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────┐      ┌──────────────┐      ┌────────────────┐ │
│  │  Vercel     │      │   Railway    │      │   Supabase     │ │
│  │  (UIs)      │─────▶│  (FastAPI)   │─────▶│  (Overrides)   │ │
│  └─────────────┘      └──────────────┘      └────────────────┘ │
│       │                      ▲                       ▲           │
│       │                      │                       │           │
│       │                      │ Reads defaults        │           │
│       │                      │ from code             │           │
│       ▼                      │                       │           │
│  ┌────────────────────────────────────────────────┴─────────┐  │
│  │            LangGraph Platform (Agents)                    │  │
│  │  - Reads defaults from prompt.py, config.py (immutable)  │  │
│  │  - Reads overrides from Supabase (per-user)              │  │
│  │  - Merge: override > default                             │  │
│  │  - Postgres (checkpoints, threads, state)                │  │
│  │  - Redis (task queue, caching)                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Database Responsibilities

| Database | Purpose | What's Stored |
|----------|---------|---------------|
| **Supabase** | User overrides, API keys | `user_secrets`, `agent_configs` (overrides only) |
| **Python Code** | Immutable defaults | `prompt.py`, `config.py` (version controlled) |
| **LangGraph Postgres** | Graph runtime state | Checkpoints, threads, persistent store |
| **LangGraph Redis** | Caching, queues | Task queue, temporary cache |

**Best Practice:**
- ✅ Code (Git) = Defaults, safe fallback, version controlled
- ✅ Supabase = User overrides, can be reset anytime
- ✅ LangGraph Postgres/Redis = Graph state (separate concern)
- ❌ NEVER mix: defaults stay in code, overrides in Supabase

---

## 🔧 Implementation Details

### 1. Agent-Specific Defaults (Immutable in Code)

**Each agent has its OWN defaults:**

**`/src/calendar_agent/prompt.py`:**
```python
"""
Calendar Agent Default Prompts
⚠️ IMMUTABLE - Never modified automatically
✅ Version controlled - Git is source of truth
"""

AGENT_SYSTEM_PROMPT = """You are a helpful calendar assistant.

Your responsibilities:
- Manage Google Calendar events
- Schedule meetings intelligently
- Resolve scheduling conflicts
- Suggest optimal meeting times

Always be professional and efficient.
"""

SCHEDULING_PROMPT = """When scheduling meetings:
1. Check calendar availability
2. Respect work hours ({work_hours_start} - {work_hours_end})
3. Avoid double-booking
4. Prefer {default_meeting_duration} minute slots
"""

# Export for FastAPI
DEFAULTS = {
    "system_prompt": AGENT_SYSTEM_PROMPT,
    "scheduling_prompt": SCHEDULING_PROMPT
}
```

**`/src/calendar_agent/config.py`:**
```python
"""
Calendar Agent Default Configuration
⚠️ IMMUTABLE - Never modified automatically
"""
from shared_config.constants import DEFAULT_LLM_MODEL, DEFAULT_TEMPERATURE

AGENT_NAME = "calendar"

# Per-agent defaults (calendar-specific)
LLM_CONFIG_DEFAULTS = {
    "model": "gpt-4o",           # Calendar prefers GPT-4o
    "temperature": 0.2,
    "streaming": False
}

CALENDAR_SETTINGS_DEFAULTS = {
    "work_hours_start": "09:00",
    "work_hours_end": "17:00",
    "default_meeting_duration": 30
}

# Export for FastAPI
DEFAULTS = {
    "llm": LLM_CONFIG_DEFAULTS,
    "calendar_settings": CALENDAR_SETTINGS_DEFAULTS
}
```

**`/src/email_agent/prompt.py` (DIFFERENT defaults!):**
```python
"""
Email Agent Default Prompts
⚠️ IMMUTABLE - Different from calendar agent!
"""

EMAIL_SYSTEM_PROMPT = """You are a professional email assistant.

Your responsibilities:
- Draft professional email responses
- Triage incoming emails by priority
- Suggest email templates
- Maintain appropriate tone

Always be courteous and clear.
"""

# Export for FastAPI
DEFAULTS = {
    "system_prompt": EMAIL_SYSTEM_PROMPT,
    "draft_prompt": "...",
    "triage_prompt": "..."
}
```

### 2. FastAPI: Merge Defaults + Overrides

**`/src/config_api/main.py`:**
```python
"""
FastAPI Config Bridge
Returns: defaults (from code) + user overrides (from Supabase)
"""
from fastapi import FastAPI
import importlib
from src.shared_utils.supabase_config import get_agent_config

app = FastAPI()

def get_agent_defaults(agent_id: str):
    """
    Load immutable defaults from agent's Python code
    Each agent has its own defaults - NOT shared!
    """
    try:
        # Import prompt defaults (agent-specific)
        prompt_module = importlib.import_module(f"src.{agent_id}_agent.prompt")
        prompt_defaults = prompt_module.DEFAULTS

        # Import config defaults (agent-specific)
        config_module = importlib.import_module(f"src.{agent_id}_agent.config")
        config_defaults = config_module.DEFAULTS

        return {
            "prompts": prompt_defaults,
            "config": config_defaults
        }
    except Exception as e:
        print(f"❌ Error loading defaults for {agent_id}: {e}")
        return {}

@app.get("/api/config/values")
async def get_values(agent_id: str, user_id: str):
    """
    Returns for EACH field:
    - default: from Python code (immutable, agent-specific)
    - user_override: from Supabase (can be null)
    - current: what agent actually uses (override > default)
    - is_overridden: bool
    """
    # 1. Get defaults from code (IMMUTABLE, PER-AGENT)
    defaults = get_agent_defaults(agent_id)

    # 2. Get user overrides from Supabase
    user_overrides = get_agent_config(agent_id, user_id)

    # 3. Merge: user override > default
    merged = {}

    # Merge config sections
    for section_key, section_defaults in defaults.get("config", {}).items():
        merged[section_key] = {}

        for field_key, default_value in section_defaults.items():
            user_value = user_overrides.get(section_key, {}).get(field_key)

            merged[section_key][field_key] = {
                "default": default_value,          # From code (agent-specific)
                "user_override": user_value,       # From Supabase (can be null)
                "current": user_value if user_value is not None else default_value,
                "is_overridden": user_value is not None
            }

    # Merge prompts
    for prompt_key, default_prompt in defaults.get("prompts", {}).items():
        if "prompts" not in merged:
            merged["prompts"] = {}

        user_prompt = user_overrides.get("prompts", {}).get(prompt_key)

        merged["prompts"][prompt_key] = {
            "default": default_prompt,             # From code (agent-specific)
            "user_override": user_prompt,
            "current": user_prompt if user_prompt else default_prompt,
            "is_overridden": bool(user_prompt)
        }

    return {
        "agent_id": agent_id,
        "user_id": user_id,
        "values": merged
    }

@app.post("/api/config/update")
async def update_config(data: dict):
    """Update user override OR reset to default"""
    from src.shared_utils.supabase_config import update_agent_config

    agent_id = data["agent_id"]
    user_id = data["user_id"]
    section_key = data["section_key"]
    field_key = data["field_key"]
    value = data["value"]

    # Empty string or null = remove override (revert to default)
    if value == "" or value is None:
        update_agent_config(agent_id, user_id, {
            section_key: {field_key: None}
        }, remove_field=True)

        return {"success": True, "action": "reset_to_default"}

    # Update override
    update_agent_config(agent_id, user_id, {
        section_key: {field_key: value}
    })

    return {"success": True, "action": "override"}

@app.post("/api/config/reset")
async def reset_to_defaults(data: dict):
    """Reset ALL user overrides to defaults"""
    from src.shared_utils.supabase_config import reset_agent_config

    reset_agent_config(data["agent_id"], data["user_id"])

    return {"success": True, "action": "reset_all"}
```

### 3. Agent Runtime: Override > Default

**`/src/calendar_agent/graph.py`:**
```python
"""
Calendar Agent Graph
Priority: User override > Agent-specific default
"""
from shared_utils.supabase_config import get_agent_config
from shared_utils.llm_utils import get_llm
from .config import LLM_CONFIG_DEFAULTS, CALENDAR_SETTINGS_DEFAULTS
from .prompt import AGENT_SYSTEM_PROMPT, SCHEDULING_PROMPT

def calendar_node(state: State, config: RunnableConfig):
    """
    Each agent uses ITS OWN defaults
    Calendar defaults ≠ Email defaults ≠ Rube defaults
    """
    user_id = config.get("configurable", {}).get("user_id")

    if user_id:
        # Get user overrides from Supabase
        user_config = get_agent_config("calendar", user_id)

        # ✅ Merge: user override > CALENDAR-SPECIFIC default
        model = user_config.get("llm", {}).get("model") or LLM_CONFIG_DEFAULTS["model"]
        temperature = user_config.get("llm", {}).get("temperature") or LLM_CONFIG_DEFAULTS["temperature"]

        system_prompt = user_config.get("prompts", {}).get("system_prompt") or AGENT_SYSTEM_PROMPT

        work_hours_start = user_config.get("calendar_settings", {}).get("work_hours_start") \
                           or CALENDAR_SETTINGS_DEFAULTS["work_hours_start"]

        print(f"[Calendar] Model: {model} ({'custom' if user_config.get('llm', {}).get('model') else 'default'})")
        print(f"[Calendar] Prompt: {'custom' if user_config.get('prompts', {}).get('system_prompt') else 'default'})")
    else:
        # No user_id: use all calendar-specific defaults
        model = LLM_CONFIG_DEFAULTS["model"]
        temperature = LLM_CONFIG_DEFAULTS["temperature"]
        system_prompt = AGENT_SYSTEM_PROMPT
        work_hours_start = CALENDAR_SETTINGS_DEFAULTS["work_hours_start"]

        print(f"[Calendar] Using all defaults (no user_id)")

    # Use values
    llm = get_llm(model, temperature)

    messages = [
        SystemMessage(content=system_prompt),
        # ... rest
    ]

    response = llm.invoke(messages)
    # ...
```

### 4. Config-App UI: Show Both Values

**`/config-app/src/components/ConfigField.tsx`:**
```typescript
"use client";

interface ConfigFieldProps {
  field: {
    key: string;
    label: string;
    type: string;
  };
  values: {
    default: any;           // From code (agent-specific)
    user_override: any | null;
    current: any;           // What agent uses
    is_overridden: boolean;
  };
  onUpdate: (value: any) => void;
  onReset: () => void;
}

export function ConfigField({ field, values, onUpdate, onReset }: ConfigFieldProps) {
  const [editValue, setEditValue] = useState(values.current);

  return (
    <div className="space-y-3 p-4 border rounded-lg">
      {/* Header */}
      <div className="flex items-center justify-between">
        <label className="font-medium">
          {field.label}
          {values.is_overridden && (
            <span className="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
              Custom
            </span>
          )}
        </label>

        {/* Reset Button (only show if overridden) */}
        {values.is_overridden && (
          <button
            onClick={onReset}
            className="text-xs text-gray-500 hover:text-red-600"
          >
            🔄 Reset to default
          </button>
        )}
      </div>

      {/* Default Value (collapsed, read-only) */}
      <details className="bg-gray-50 p-2 rounded">
        <summary className="text-xs text-gray-600 cursor-pointer">
          📘 Default value (from code, agent-specific)
        </summary>
        <pre className="text-xs mt-2 text-gray-700 whitespace-pre-wrap">
          {JSON.stringify(values.default, null, 2)}
        </pre>
      </details>

      {/* Current/Override Value (editable) */}
      <div>
        <label className="text-sm text-gray-600">
          {values.is_overridden ? "Your Custom Value" : "Current Value (using default)"}
        </label>

        {field.type === "textarea" ? (
          <textarea
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            onBlur={() => onUpdate(editValue)}
            className={`w-full mt-2 p-2 border rounded ${
              values.is_overridden ? 'border-blue-300 bg-blue-50' : 'border-gray-300'
            }`}
            rows={8}
            placeholder="Using default (edit to override)"
          />
        ) : (
          <input
            type={field.type}
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            onBlur={() => onUpdate(editValue)}
            className={`w-full mt-2 p-2 border rounded ${
              values.is_overridden ? 'border-blue-300 bg-blue-50' : 'border-gray-300'
            }`}
            placeholder="Using default (edit to override)"
          />
        )}
      </div>

      {/* Help Text */}
      <p className="text-xs text-gray-500">
        {values.is_overridden
          ? "💡 Customized value. Click 'Reset' to revert to agent's default."
          : "💡 Using agent-specific default. Edit to create your custom value."
        }
      </p>
    </div>
  );
}
```

---

## ✅ Benefits of This Architecture

| Feature | Status |
|---------|--------|
| Defaults immutable (Git) | ✅ Never auto-modified |
| Per-agent defaults | ✅ Each agent has own prompts/configs |
| Per-node defaults | ✅ Can specify different models per node |
| User can override anything | ✅ Stored in Supabase |
| Reset to default (per field) | ✅ 1 button per field |
| Reset all to defaults | ✅ 1 button per agent |
| Developer updates defaults | ✅ Git commit → agents use new defaults |
| No sync conflicts | ✅ No bidirectional sync |
| UI shows both values | ✅ Default (collapsed) + override (highlighted) |
| Safe fallback always | ✅ Code defaults always available |

---

## 🎯 Key Principles

### 1. Per-Agent Defaults (NOT Global)
- ❌ **Wrong:** One `SYSTEM_PROMPT` for all agents
- ✅ **Right:** `CALENDAR_SYSTEM_PROMPT`, `EMAIL_SYSTEM_PROMPT`, `RUBE_SYSTEM_PROMPT`

### 2. Per-Node Defaults (When Needed)
```python
# /src/calendar_agent/config.py
NODE_DEFAULTS = {
    "scheduler_node": {"model": "gpt-4o", "temperature": 0.1},
    "composer_node": {"model": "claude-sonnet-4-5", "temperature": 0.7}
}
```

### 3. Code = Safe, Supabase = Override
- Code defaults **NEVER** modified automatically
- Supabase **ONLY** stores user overrides
- Empty/null in Supabase = use default from code

### 4. Reset is Trivial
- Delete Supabase row = instant reset to all defaults
- Set field to null = reset that field only

---

## 📊 Progress Tracking

**Current Status:** ⏳ Phase 4 Ready to Start (70% Total)

| Phase | Estimated Time | Status |
|-------|---------------|--------|
| Phase 0: Architecture | 2-3 hours | ✅ **COMPLETE** |
| Phase 1: DB Setup | 1-2 hours | ✅ **COMPLETE** |
| Phase 2: CLI Integration | 1-2 hours | ✅ **COMPLETE** |
| Phase 3: FastAPI Merge Logic | 2-3 hours | ✅ **COMPLETE** |
| Phase 4: Config-App UI | 3-4 hours | ⏳ Ready to Start |
| Phase 5: Agents Runtime | 3-4 hours | ⏳ Not Started |
| Phase 6: Deployment | 2-3 hours | ⏳ Not Started |
| Phase 7: Testing | 2-3 hours | ⏳ Not Started |

**Total:** 16-24 hours | **Completed:** 10 hours | **Next:** Phase 4 | **Remaining:** 6-14 hours

---

---

## 🎉 Phase 0 Completion Report

**Status:** ✅ Complete | **Date:** October 2, 2025

### What Was Completed:

#### 1. Agent DEFAULTS Exports Added ✅
All agents now export `DEFAULTS` from `config.py` and `prompt.py`:

**Calendar Agent:**
- `prompt.py` → 6 prompts (system, no_tools, routing, booking_extraction, role, guidelines)
- `config.py` → 3 sections (llm, calendar_settings, agent_identity)

**Multi-Tool Rube Agent:**
- `prompt.py` → 3 prompts (system, role, guidelines)
- `config.py` → 3 sections (llm, agent_identity, timezone)

**Executive AI Assistant (Special Handling):**
- `prompt.py` → 9 prompts (lazy-loaded from inline sources to avoid circular imports)
- `config.py` → 3 sections (llm with per-node configs, agent_identity, timezone)
- `ui_config.py` → Combined DEFAULTS export (config + prompts)
- ⚠️ Uses lazy-loading pattern to preserve LangChain's original code structure

**React Agent MCP Template:**
- `prompt.py` → 3 prompts (template placeholders preserved)
- `config.py` → 4 sections (llm, agent_identity, timezone, mcp_integration)
- Future agents will inherit DEFAULTS structure automatically

#### 2. Database Migration Created ✅
- `supabase/migrations/002_agent_configs.sql`
- Includes `prompts` JSONB column for prompt overrides
- Row-level security policies for user isolation
- GIN indexes for JSONB query performance
- Helper function for resetting configs to defaults

#### 3. Verification Test Created ✅
- `test_phase_0_defaults.py` - Automated verification script
- Tests all 4 agents for proper DEFAULTS exports
- All agents pass: 4/4 ✅

#### 4. Git Commits Pushed ✅
1. `e4fd695` - FastAPI config bridge foundation
2. `723fa14` - calendar + multi_tool_rube DEFAULTS
3. `ae932a7` - executive-ai-assistant DEFAULTS (lazy-loading)
4. `fda7b1a` - react_agent_mcp_template DEFAULTS

### Architecture Achieved:

```
┌─────────────────────────────────────────────────────────────┐
│                  PHASE 0 ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Code (Git) → DEFAULTS → [Ready for FastAPI]                │
│    ↓                                                          │
│  Immutable defaults (version-controlled, safe)               │
│                                                               │
│  Supabase: agent_configs table ready                        │
│    ↓                                                          │
│  User overrides storage (can be reset anytime)              │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Key Decisions Made:

1. **Used existing `shared_utils/`** instead of creating new `shared_config/`
   - More flexible (JSON-based configuration)
   - Already provides shared constants across agents

2. **Lazy-loading for executive-ai-assistant**
   - Avoids refactoring LangChain's complex graph structure
   - Preserves inline prompts in original node files
   - Non-breaking: config.yaml still loads normally at runtime

3. **Template updated**
   - Future agents automatically include DEFAULTS
   - Consistent pattern across all agents

### Verification:

Run automated test to verify no regressions:
```bash
source .venv/bin/activate
python test_phase_0_defaults.py
```

Expected output: `4/4 agents passed`

### Ready for Phase 1:

✅ All agents have DEFAULTS exports
✅ Database migration ready to execute
✅ Architecture supports two-way sync
✅ Verification test passes
✅ No regressions introduced

**Next:** Execute SQL migration in Supabase and build FastAPI merge logic.
