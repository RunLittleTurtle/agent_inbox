# MCP Tools Runtime Loading Implementation Plan

**Project:** Fix Multi-Agent MCP Tool Access at Runtime
**Issue:** Agents initialized at graph compile time with `config=None` → 0 tools
**Solution:** Runtime tool loading pattern (like executive graphs)
**Status:** 🟡 Phase 2 In Progress
**Last Updated:** October 4, 2025

---

## 🎯 Feature Implementation Checklist

### ✅ Phase 1: Validation & Root Cause Analysis (COMPLETE)
- [x] Query Supabase to identify test users
- [x] Verify `agent_configs` table structure and MCP URL data
- [x] Test CONFIG API endpoint with real user IDs
- [x] Test direct Supabase queries from `config_utils.py`
- [x] Document root cause: static graph with `config=None`
- [x] Commit and deploy Phase 1 validation

**Result:** Config loading infrastructure works perfectly. Problem is architectural.

### 🟡 Phase 2: Runtime MCP Tool Loading (IN PROGRESS)
- [ ] Design runtime tool loading architecture
- [ ] Create runtime MCP tool fetching utility function
- [ ] Implement calendar_agent wrapper node with runtime tools
- [ ] Test calendar_agent with user who HAS MCP config
- [ ] Test calendar_agent with user who has NO MCP config (fallback)
- [ ] Implement multi_tool_rube_agent wrapper node
- [ ] Test multi_tool_rube_agent with both test users
- [ ] Commit and deploy Phase 2

**Target:** Agents get tools from user-specific MCP URLs at request time, not compile time.

### ⚪ Phase 3: Supervisor Integration
- [ ] Update `graph.py` to use wrapper nodes instead of compiled agents
- [ ] Remove static agent creation from `make_graph()`
- [ ] Test supervisor routing with runtime tool loading
- [ ] Verify tools are loaded per-request with correct user context
- [ ] Test end-to-end with LangSmith trace analysis
- [ ] Commit and deploy Phase 3

**Target:** Supervisor routes to wrapper nodes that load tools dynamically.

### ⚪ Phase 4: Cleanup & Production Hardening
- [ ] Remove unused static agent creation code
- [ ] Add comprehensive error handling for missing MCP URLs
- [ ] Add logging for MCP URL resolution and tool loading
- [ ] Update documentation for runtime config pattern
- [ ] Add fallback behavior when MCP servers are unreachable
- [ ] Create migration guide for other agents
- [ ] Final commit and deploy

**Target:** Production-ready runtime tool loading with observability.

---

## 📊 Current State

### Working Components
✅ **Supabase Database:**
- Table: `agent_configs`
- Structure: `clerk_id`, `agent_id`, `config_data (jsonb)`
- MCP URLs stored at: `config_data.mcp_integration.mcp_server_url`

✅ **CONFIG API (Railway):**
- URL: `https://agentinbox-production.up.railway.app/api/config/values`
- Parameters: `agent_id`, `user_id`
- Returns: Flattened config with `mcp_integration.mcp_server_url`

✅ **Direct Supabase Queries:**
- Function: `src/utils/config_utils.py::get_agent_config_from_supabase()`
- Works correctly for users with configs
- Returns empty dict for users without configs

### Broken Components
❌ **Supervisor Graph Agent Creation:**
- Location: `src/graph.py:496`
- Problem: `graph = make_graph(None)` creates agents at server startup
- Result: Agents frozen with 0 tools from `local_dev_user` fallback

❌ **Calendar Agent Initialization:**
- Location: `src/graph.py:133-167`
- Problem: `create_calendar_agent(config=None)` → `user_id="local_dev_user"`
- Result: Queries Supabase for non-existent user → HTTP 406 → 0 tools

❌ **Multi-Tool Rube Agent Initialization:**
- Location: `src/graph.py:174-313`
- Problem: Same pattern as calendar agent
- Result: 0 Rube tools loaded for all users

### Test Users

**User 1: HAS MCP Configs**
- Email: `info@800m.ca`
- Clerk ID: `user_33TJRkCZdUVfXdlChxi1qbx5O6k`
- Calendar MCP: `https://mcp.pipedream.net/cf246968-6ec2-468b-8b4b-bc1b9d0d928b/google_calendar`
- Rube MCP: `https://rube.app/mcp`
- Rube Token: Configured ✅

**User 2: NO MCP Configs**
- Email: `samuel.audette1@gmail.com`
- Clerk ID: `user_33Z8890Y98MrO5TpwRP7fh5A4bR`
- Calendar MCP: ❌ Not configured
- Rube MCP: ❌ Not configured
- Expected: Should fall back to .env or graceful error

---

## 🏗️ Architecture: Runtime Tool Loading Pattern

### Executive Graph Pattern (✅ Working Reference)
```python
# src/executive-ai-assistant/eaia/main/graph.py:143-155
async def send_cal_invite_node(state, config):
    config_data = await get_config(config)  # ✅ Runtime fetch
    email = config_data["email"]
    timezone = config_data.get("timezone", "America/Toronto")
    # Use config_data at runtime...
```

**Key insight:** Config is fetched **inside nodes**, not at graph compile time.

### New Supervisor Pattern - 2025 Best Practices (🎯 Target Implementation)

```python
# src/graph.py - 2025 PATTERN with Runtime Context API

from dataclasses import dataclass
from langgraph.runtime import Runtime, get_runtime
from langchain_mcp_adapters.client import MultiServerMCPClient

# 1. Define context schema (NEW in LangGraph v0.6.0)
@dataclass
class UserContext:
    """User-specific runtime context"""
    user_id: str
    mcp_calendar_url: str | None = None
    mcp_rube_url: str | None = None
    rube_auth_token: str | None = None

# 2. Wrapper nodes that load tools at runtime (2025 pattern)
async def calendar_agent_node(state: MessagesState, runtime: Runtime[UserContext]):
    """Wrapper node that loads calendar tools at runtime using 2025 Runtime API"""
    # Access user context (type-safe!)
    user_id = runtime.context.user_id
    mcp_url = runtime.context.mcp_calendar_url

    logger.info(f"Loading calendar tools for user: {user_id}")

    # Fallback to .env if no URL provided
    if not mcp_url:
        mcp_url = os.getenv("PIPEDREAM_MCP_SERVER")
        logger.warning(f"No MCP URL in context, using .env fallback")

    # Load MCP tools dynamically (2025 pattern - supported in workflow nodes)
    tools = []
    if mcp_url:
        try:
            client = MultiServerMCPClient({
                "calendar": {
                    "url": mcp_url,
                    "transport": "streamable_http"
                }
            })
            tools = await client.get_tools()
            logger.info(f"Loaded {len(tools)} calendar tools")
        except Exception as e:
            logger.error(f"Failed to load MCP tools: {e}")
            tools = []

    # Create agent with loaded tools
    calendar_agent = create_react_agent(model, tools, prompt)

    # Invoke and return
    result = await calendar_agent.ainvoke(state)
    return result

# 3. Supervisor uses wrapper nodes
def make_graph():
    """Factory function - uses 2025 Runtime API for context"""
    workflow = create_supervisor(
        agents=[
            {"name": "calendar_agent", "node": calendar_agent_node},  # ✅ Node, not graph
            {"name": "multi_tool_agent", "node": multi_tool_agent_node}
        ],
        context_schema=UserContext,  # NEW: Type-safe context
        ...
    )
    return workflow.compile(name="multi_agent_system")

# 4. Static export for platform registration
graph = make_graph()

# 5. Invoke with 2025 Runtime Context API
graph.invoke(
    {"messages": [{"role": "user", "content": "Check my calendar"}]},
    context={  # NEW: context parameter (v0.6.0+)
        "user_id": "user_123",
        "mcp_calendar_url": "https://mcp.pipedream.net/...",
        "mcp_rube_url": "https://rube.app/mcp",
        "rube_auth_token": "token_abc"
    }
)
```

**2025 Best Practices Applied:**
- ✅ `Runtime[UserContext]` for type-safe context access
- ✅ `context={}` parameter instead of `config['configurable']`
- ✅ MCP tools loaded in workflow nodes (officially supported!)
- ✅ `@dataclass` for context schemas
- ✅ No manual config.get() extractions

### Utility Function: Runtime MCP Tool Loading

```python
# src/utils/mcp_tools_utils.py - NEW FILE

from typing import List, Optional
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
import asyncio
import logging

logger = logging.getLogger(__name__)

async def load_mcp_tools(
    mcp_url: Optional[str],
    server_name: str,
    auth_token: Optional[str] = None,
    timeout: float = 30.0
) -> List[BaseTool]:
    """
    Load MCP tools from a URL at runtime

    Args:
        mcp_url: MCP server URL
        server_name: Name for this MCP server (e.g., "calendar", "rube")
        auth_token: Optional Bearer token for authentication
        timeout: Connection timeout in seconds

    Returns:
        List of LangChain tools from MCP server, or empty list if unavailable
    """
    if not mcp_url:
        logger.warning(f"No MCP URL provided for {server_name}")
        return []

    try:
        # Configure MCP server
        server_config = {
            "url": mcp_url,
            "transport": "streamable_http"
        }

        if auth_token:
            server_config["headers"] = {
                "Authorization": f"Bearer {auth_token}"
            }

        # Create MCP client
        client = MultiServerMCPClient({server_name: server_config})

        # Load tools with timeout
        tools = await asyncio.wait_for(
            client.get_tools(),
            timeout=timeout
        )

        logger.info(f"Loaded {len(tools)} MCP tools from {server_name}: {[t.name for t in tools]}")
        return tools

    except asyncio.TimeoutError:
        logger.error(f"MCP tools loading timed out for {server_name}")
        return []
    except Exception as e:
        logger.error(f"Failed to load MCP tools from {server_name}: {e}")
        return []
```

---

## 🧪 Learning Log: What We Tried

### ❌ Attempt 1: Fix Static Graph Creation
**What we tried:** Modify `make_graph()` to accept `config` parameter
**Why it failed:** LangGraph Platform calls `make_graph()` once at startup, not per-request
**Learning:** Can't inject per-user config into static graph compilation
**Reference:** `src/graph.py:472-491`

### ❌ Attempt 2: Use Config Propagation
**What we tried:** Rely on RunnableConfig propagation through compiled graph
**Why it failed:** Agents are already compiled with 0 tools by the time config arrives
**Learning:** Tools must be loaded inside nodes, not during agent creation
**Reference:** LangGraph docs on context propagation

### ❌ Attempt 3: Fix HTTP 406 from Supabase
**What we tried:** Investigated Supabase query headers and schema
**Why it succeeded:** Query works fine! Problem was `user_id="local_dev_user"` doesn't exist
**Learning:** Config loading works perfectly - wrong architecture pattern
**Reference:** `phase1_validate.py` test results

### ✅ Solution: Runtime Tool Loading (Executive Pattern)
**What we're implementing:** Load tools inside wrapper nodes at runtime
**Why it works:** Each request gets fresh tools with correct user MCP URL
**Reference:** `src/executive-ai-assistant/eaia/main/graph.py:143`
**Status:** Phase 2 implementation in progress

### ✅ Update: 2025 Best Practices Discovered
**What we found:** LangGraph v0.6.0+ has Runtime Context API
**Key changes:**
- `Runtime[ContextSchema]` replaces manual `config.get("configurable")`
- `context={}` parameter replaces `config={'configurable': {}}`
- `@dataclass` context schemas for type safety
- MCP tool loading in nodes is officially supported pattern

**Benefits:**
- Type-safe context access
- Cleaner API (no nested dict access)
- Better IDE autocomplete
- Matches official 2025 documentation

**Reference:** https://langchain-ai.github.io/langgraph/agents/context/
**Status:** Updating implementation to use 2025 patterns

---

## 📁 Key Files & Locations

### Configuration Loading
- `src/utils/config_utils.py:40-90` - Direct Supabase queries
- `src/config_api/main.py` - FastAPI bridge (Railway)
- `src/executive-ai-assistant/eaia/main/config.py:45-81` - Executive runtime config

### Agent Creation (Current - Broken)
- `src/graph.py:133-167` - `create_calendar_agent()` - Creates at compile time ❌
- `src/graph.py:174-313` - `create_multi_tool_rube_agent()` - Creates at compile time ❌
- `src/graph.py:496` - Static graph export with `config=None` ❌

### Agent Orchestrators
- `src/calendar_agent/calendar_orchestrator.py:45-98` - CalendarAgentWithMCP class
- `src/multi_tool_rube_agent/tools.py:70-162` - AgentMCPConnection class

### Working Reference (Executive Graphs)
- `src/executive-ai-assistant/eaia/main/graph.py` - Runtime config loading ✅
- `src/executive-ai-assistant/eaia/main/config.py` - get_config() pattern ✅

### Validation Scripts
- `phase1_validate.py` - Comprehensive Supabase/CONFIG API tests
- `PHASE1_VALIDATION_RESULTS.md` - Phase 1 findings and test users

---

## 🚀 Phase 2 Implementation Steps (2025 Best Practices)

### Step 1: Define UserContext Schema
**File:** `src/graph.py` (UPDATE)
**Add:** `@dataclass class UserContext` with MCP URLs
**Purpose:** Type-safe context for Runtime API

### Step 2: Create Calendar Agent Wrapper Node (2025 Pattern)
**File:** `src/graph.py` (NEW FUNCTION)
**Function:** `async def calendar_agent_node(state, runtime: Runtime[UserContext])`
**Logic:**
1. Access context: `user_id = runtime.context.user_id`
2. Get MCP URL: `mcp_url = runtime.context.mcp_calendar_url`
3. Fallback to `.env` if None
4. Load tools: `client = MultiServerMCPClient({...}); tools = await client.get_tools()`
5. Create agent: `create_react_agent(model, tools, prompt)`
6. Invoke and return result

### Step 3: Create Multi-Tool Rube Agent Wrapper Node (2025 Pattern)
**File:** `src/graph.py` (NEW FUNCTION)
**Function:** `async def multi_tool_agent_node(state, runtime: Runtime[UserContext])`
**Logic:** Same as calendar but uses `runtime.context.mcp_rube_url` and `rube_auth_token`

### Step 4: Update Supervisor Integration (2025 Pattern)
**File:** `src/graph.py::make_graph()`
**Changes:**
- Remove `create_calendar_agent()` and `create_multi_tool_rube_agent()` calls
- Pass wrapper node functions to `create_supervisor()`
- Add `context_schema=UserContext` parameter
- Keep static graph export: `graph = make_graph()`

### Step 5: Update Graph Invocation Layer
**File:** Frontend/API that invokes the graph
**Changes:**
- Fetch MCP URLs from Supabase for user
- Pass via `context={"user_id": ..., "mcp_calendar_url": ...}`
- Remove old `config={'configurable': {...}}` pattern

### Step 5: Test with Both Users
**Test 1:** User with MCP configs (`user_33TJRkCZdUVfXdlChxi1qbx5O6k`)
**Expected:** Agents load tools from Supabase MCP URLs

**Test 2:** User without MCP configs (`user_33Z8890Y98MrO5TpwRP7fh5A4bR`)
**Expected:** Agents fall back to .env or return graceful error

**Test 3:** Verify in LangSmith trace
**Expected:** Tool calls visible in trace with correct tool names

---

## 📞 Debugging & Monitoring

### Key Log Messages to Add
```python
logger.info(f"Loading MCP tools for user: {user_id}, agent: {agent_id}")
logger.info(f"MCP URL resolved: {mcp_url[:50] if mcp_url else 'None (using fallback)'}")
logger.info(f"Loaded {len(tools)} tools: {[t.name for t in tools]}")
logger.error(f"Failed to load MCP tools: {e}")
```

### LangSmith Trace Verification
- Check for tool calls in agent execution
- Verify tool names match expected MCP tools
- Confirm different users get different tools

### Error Cases to Handle
1. **No MCP URL in Supabase** → Fallback to .env
2. **MCP server unreachable** → Return empty tools + log error
3. **MCP server timeout** → Return empty tools + log timeout
4. **Invalid MCP URL** → Return empty tools + log invalid URL
5. **No user_id in config** → Use `local_dev_user` fallback

---

## 🎓 Key Learnings

### Architecture Patterns
1. **Static vs Dynamic:** Graphs can be static, but tool loading must be dynamic
2. **Config Propagation:** RunnableConfig flows through nodes automatically
3. **Per-Request Resources:** Load external resources (MCP tools) in nodes, not at compile time

### LangGraph Platform Specifics
1. **Graph Factory:** `make_graph()` is called once at server startup
2. **Config Injection:** Platform injects user-specific config via `RunnableConfig` per request
3. **Node Functions:** Nodes receive `(state, config)` - use config for runtime decisions

### Multi-Tenancy
1. **User Isolation:** Each request must load user-specific resources
2. **No Shared State:** Can't bake user data into compiled graph
3. **Runtime Configuration:** All user-specific data must come from config or databases

---

## 📝 Next Actions

1. ✅ Create this plan document
2. 🔄 Implement `src/utils/mcp_tools_utils.py`
3. 🔄 Create `calendar_agent_node` wrapper
4. 🔄 Test with user who has MCP config
5. 🔄 Test with user who doesn't have MCP config
6. 🔄 Create `multi_tool_agent_node` wrapper
7. 🔄 Update supervisor integration
8. 🔄 Deploy and test end-to-end

**Current Focus:** Step 2 - Implement runtime tool loading utility

---

*This document is a living plan. Update as we learn and implement.*
