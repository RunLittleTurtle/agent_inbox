"""
FastAPI Config Bridge
Exposes Python agent configs to Next.js config-app
"""
from fastapi import FastAPI, HTTPException, Header, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
import sys
from pathlib import Path
from importlib import import_module
from dotenv import load_dotenv
from supabase import create_client, Client
import time

# Add parent directory to path for imports
parent_path = str(Path(__file__).parent.parent)
sys.path.insert(0, parent_path)

# Debug logging for import paths
print(f"🔍 Working directory: {os.getcwd()}")
print(f"🔍 Parent path added to sys.path: {parent_path}")
print(f"🔍 sys.path: {sys.path[:3]}...")  # First 3 paths

load_dotenv()

app = FastAPI(title="Agent Config API", version="1.0.0")

# CORS - Allow config-app to call this API
# Use regex pattern to allow all Vercel deployments
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.vercel\.app",  # All Vercel deployments
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Also allow localhost for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3004"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase client
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SECRET_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("⚠️  WARNING: Missing Supabase credentials - database features disabled")
    print("   Set NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SECRET_KEY in .env")
    supabase = None
else:
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✓ Supabase client initialized successfully")
    except Exception as e:
        print(f"⚠️  WARNING: Invalid Supabase credentials - database features disabled")
        print(f"   Error: {e}")
        print("   Get the correct anon/service_role key from Supabase dashboard:")
        print("   https://supabase.com/dashboard/project/lcswsadubzhynscruzfn/settings/api")
        supabase = None

# Agent directories to scan
AGENT_PATHS = [
    "calendar_agent",
    "multi_tool_rube_agent",
    "_react_agent_mcp_template",
    "executive-ai-assistant",
]

# Global environment config
GLOBAL_CONFIG_PATH = "ui_config"


class HealthCheck(BaseModel):
    """Response model for health check endpoint"""
    status: str = "healthy"
    timestamp: float
    service: str = "Agent Config API"
    version: str = "1.0.0"
    supabase_connected: bool


class UpdateConfigRequest(BaseModel):
    agent_id: str
    user_id: str
    section_key: str
    field_key: str
    value: Any


class BulkUpdateRequest(BaseModel):
    agent_id: str
    user_id: str
    config_data: Dict[str, Any]


def get_agent_defaults(agent_id: str) -> Dict[str, Any]:
    """
    Load immutable defaults from agent's Python code
    Returns defaults from prompt.py and config.py (if they exist)

    Each agent has its OWN defaults - NOT shared!
    calendar defaults ≠ email defaults ≠ executive defaults

    Note: prompt.py is optional - Executive AI Assistant doesn't use it
    """
    # Map agent_id to actual Python module name
    # This handles cases where agent_id differs from folder name
    # Example: "calendar" agent_id → "calendar_agent" module to avoid Python's built-in calendar
    AGENT_MODULE_MAP = {
        "calendar": "calendar_agent",
        "email": "email_agent",
        "executive": "executive_agent",
        "executive_ai_assistant": "executive-ai-assistant",  # Normalized agent_id (underscores) → folder (dashes)
        "executive-ai-assistant": "executive-ai-assistant",  # Folder uses dashes
        "multi_tool_rube": "multi_tool_rube_agent",  # agent_id without _agent suffix
    }

    module_name = AGENT_MODULE_MAP.get(agent_id, agent_id)

    defaults = {
        "prompts": {},
        "config": {}
    }

    # Try to load prompt.py (optional - gracefully skip if not found)
    try:
        prompt_module = import_module(f"{module_name}.prompt")
        if hasattr(prompt_module, "DEFAULTS"):
            defaults["prompts"] = prompt_module.DEFAULTS
            print(f"✅ Loaded {len(defaults['prompts'])} prompt defaults for {agent_id}")
        else:
            print(f"ℹ️  No DEFAULTS export found in {agent_id}.prompt (this is fine for some agents)")
    except ImportError:
        # prompt.py doesn't exist - this is expected for Executive AI Assistant
        print(f"ℹ️  No prompt.py for {agent_id} (triage prompts may be in config.py instead)")
    except Exception as e:
        print(f"⚠️  Warning: Could not load {agent_id} prompt defaults: {e}")

    # Load config.py (required)
    try:
        config_module = import_module(f"{module_name}.config")
        if hasattr(config_module, "DEFAULTS"):
            defaults["config"] = config_module.DEFAULTS
            print(f"✅ Loaded {len(defaults['config'])} config defaults for {agent_id}")
        else:
            print(f"⚠️  No DEFAULTS export found in {agent_id}.config")
    except Exception as e:
        print(f"⚠️  Warning: Could not load {agent_id} config defaults: {e}")

    return defaults


@app.get("/")
async def root():
    return {
        "service": "Agent Config API",
        "status": "running",
        "endpoints": [
            "/health",
            "/api/config/schemas",
            "/api/config/values",
            "/api/config/update",
            "/api/config/reset",
        ]
    }


@app.get(
    "/health",
    tags=["healthcheck"],
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
    status_code=status.HTTP_200_OK,
    response_model=HealthCheck,
)
async def health_check() -> HealthCheck:
    """
    Health check endpoint for Railway and monitoring services.

    Returns:
        HealthCheck: Service health status including:
            - status: "healthy" if service is running
            - timestamp: Current Unix timestamp
            - service: Service name
            - version: API version
            - supabase_connected: True if Supabase client is initialized

    This endpoint is used by:
    - Railway for deployment health checks
    - Container orchestration systems
    - Monitoring and alerting services
    """
    return HealthCheck(
        status="healthy",
        timestamp=time.time(),
        service="Agent Config API",
        version="1.0.0",
        supabase_connected=supabase is not None
    )


@app.get("/api/config/schemas")
async def get_all_schemas():
    """
    Get all agent configuration schemas from ui_config.py files
    Returns the CONFIG_INFO and CONFIG_SECTIONS for each agent
    """
    schemas = {}

    # Add global environment config
    try:
        mod = import_module("ui_config")
        schemas["global"] = {
            "id": "global",
            "path": "ui_config.py",
            "config": {
                "CONFIG_INFO": {
                    "name": getattr(mod, "CONFIG_INFO", {}).get("name", "Global Environment"),
                    "description": getattr(mod, "CONFIG_INFO", {}).get("description", ""),
                    "config_type": getattr(mod, "CONFIG_INFO", {}).get("config_type", "env_file"),
                    "config_path": getattr(mod, "CONFIG_INFO", {}).get("config_path", ".env"),
                },
                "CONFIG_SECTIONS": getattr(mod, "CONFIG_SECTIONS", [])
            }
        }
    except Exception as e:
        print(f"Error loading global config: {e}")

    # Add interface UIs config (read-only reference page)
    try:
        mod = import_module("interface_uis_config")
        schemas["interface_uis"] = {
            "id": "interface_uis",
            "path": "src/interface_uis_config.py",
            "config": {
                "CONFIG_INFO": {
                    "name": getattr(mod, "CONFIG_INFO", {}).get("name", "Interface UIs"),
                    "description": getattr(mod, "CONFIG_INFO", {}).get("description", ""),
                    "config_type": getattr(mod, "CONFIG_INFO", {}).get("config_type", "interface_uis"),
                    "config_path": getattr(mod, "CONFIG_INFO", {}).get("config_path", "interface_uis_config.py"),
                },
                "CONFIG_SECTIONS": getattr(mod, "CONFIG_SECTIONS", [])
            }
        }
    except Exception as e:
        print(f"Error loading interface_uis config: {e}")

    # Add agent-specific configs
    for agent_path in AGENT_PATHS:
        try:
            # Import the ui_config module
            mod = import_module(f"{agent_path}.ui_config")

            agent_id = agent_path.replace("-", "_")

            schemas[agent_id] = {
                "id": agent_id,
                "path": f"src/{agent_path}/ui_config.py",
                "config": {
                    "CONFIG_INFO": {
                        "name": getattr(mod, "CONFIG_INFO", {}).get("name", agent_path),
                        "description": getattr(mod, "CONFIG_INFO", {}).get("description", ""),
                        "config_type": getattr(mod, "CONFIG_INFO", {}).get("config_type", "agent_config"),
                        "config_path": getattr(mod, "CONFIG_INFO", {}).get("config_path", f"src/{agent_path}/config.py"),
                    },
                    "CONFIG_SECTIONS": getattr(mod, "CONFIG_SECTIONS", [])
                }
            }
        except Exception as e:
            import traceback
            print(f"❌ Error loading {agent_path}: {e}")
            print(f"   Traceback: {traceback.format_exc()}")
            continue

    return {"agents": list(schemas.values())}


@app.get("/api/config/values")
async def get_config_values(agent_id: Optional[str] = None, user_id: Optional[str] = None):
    """
    Get merged configuration values: defaults from code + user overrides from Supabase

    Returns for EACH field:
    - default: from Python code (immutable, agent-specific)
    - user_override: from Supabase (can be null)
    - current: what agent actually uses (override > default)
    - is_overridden: bool
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    if not agent_id:
        raise HTTPException(status_code=400, detail="agent_id required")

    if not user_id:
        raise HTTPException(status_code=400, detail="user_id required")

    try:
        # Handle interface_uis specially (environment-aware deployment configs)
        if agent_id == "interface_uis":
            from interface_uis_config import CONFIG_SECTIONS

            # Get user-specific LangSmith keys from Supabase (if saved)
            result = supabase.table("agent_configs") \
                .select("config_data") \
                .eq("clerk_id", user_id) \
                .eq("agent_id", "interface_uis") \
                .maybe_single() \
                .execute()

            user_data = result.data.get("config_data", {}) if result and result.data else {}

            # Build response with defaults from config + user overrides
            values = {}
            for section in CONFIG_SECTIONS:
                section_key = section['key']
                values[section_key] = {}

                for field in section['fields']:
                    field_key = field['key']
                    default_value = field.get('default', '')
                    user_value = user_data.get(section_key, {}).get(field_key)

                    # For user-editable fields (like LangSmith keys), include user override
                    values[section_key][field_key] = user_value if user_value is not None else default_value

            return {
                "agent_id": "interface_uis",
                "values": values
            }

        if agent_id == "global":
            # Global config: read from Supabase user_secrets table
            # Return empty defaults if no data exists yet
            try:
                result = supabase.table("user_secrets") \
                    .select("*") \
                    .eq("clerk_id", user_id) \
                    .maybe_single() \
                    .execute()

                if result and result.data:
                    data = result.data
                    return {
                        "user_preferences": {
                            "user_timezone": data.get("timezone", "America/Toronto")
                        },
                        "ai_models": {
                            "anthropic_api_key": data.get("anthropic_api_key", ""),
                            "openai_api_key": data.get("openai_api_key", ""),
                        },
                        "langgraph_system": {
                            "langsmith_api_key": data.get("langsmith_api_key", ""),
                            "langchain_project": data.get("langchain_project", "ambient-email-agent"),
                        },
                        "google_workspace": {
                            "google_client_id": data.get("google_client_id", ""),
                            "google_client_secret": data.get("google_client_secret", ""),
                            "google_refresh_token": data.get("google_refresh_token", ""),
                        }
                    }
                else:
                    # No data yet - return empty defaults
                    print(f"[INFO] No user_secrets found for {user_id}, returning empty defaults")
                    return {
                        "user_preferences": {
                            "user_timezone": "America/Toronto"
                        },
                        "ai_models": {
                            "anthropic_api_key": "",
                            "openai_api_key": "",
                        },
                        "langgraph_system": {
                            "langsmith_api_key": "",
                            "langchain_project": "ambient-email-agent",
                        },
                        "google_workspace": {
                            "google_client_id": "",
                            "google_client_secret": "",
                            "google_refresh_token": "",
                        }
                    }
            except Exception as e:
                print(f"[ERROR] Supabase query failed for global config: {e}")
                # Return empty defaults on error
                return {
                    "user_preferences": {
                        "user_timezone": "America/Toronto"
                    },
                    "ai_models": {
                        "anthropic_api_key": "",
                        "openai_api_key": "",
                    },
                    "langgraph_system": {
                        "langsmith_api_key": "",
                        "langchain_project": "ambient-email-agent",
                    },
                    "google_workspace": {
                        "google_client_id": "",
                        "google_client_secret": "",
                        "google_refresh_token": "",
                    }
                }

        # 1. Get defaults from Python code (IMMUTABLE, PER-AGENT)
        defaults = get_agent_defaults(agent_id)
        print(f"[DEBUG] Defaults structure for {agent_id}: config keys = {list(defaults.get('config', {}).keys())}")

        # 2. Get user overrides from Supabase
        result = supabase.table("agent_configs") \
            .select("config_data, prompts") \
            .eq("clerk_id", user_id) \
            .eq("agent_id", agent_id) \
            .maybe_single() \
            .execute()

        user_overrides = {}
        if result and result.data:
            user_overrides = {
                **(result.data.get("config_data", {})),
                "prompts": result.data.get("prompts", {})
            }

        # 3. Merge: user override > default
        merged = {}

        # Merge config sections (llm, calendar_settings, etc.)
        for section_key, section_defaults in defaults.get("config", {}).items():
            if not isinstance(section_defaults, dict):
                # Handle non-dict defaults (skip for now)
                continue

            merged[section_key] = {}

            for field_key, default_value in section_defaults.items():
                user_value = user_overrides.get(section_key, {}).get(field_key) if isinstance(user_overrides.get(section_key), dict) else None

                merged[section_key][field_key] = {
                    "default": default_value,
                    "user_override": user_value,
                    "current": user_value if user_value is not None else default_value,
                    "is_overridden": user_value is not None
                }

        # Also include sections from user_overrides that don't have defaults
        # (e.g., credentials saved in Supabase but not defined in config.py)
        for section_key, section_values in user_overrides.items():
            if section_key == "prompts":
                continue  # Handle prompts separately below

            if section_key not in merged and isinstance(section_values, dict):
                merged[section_key] = {}
                for field_key, user_value in section_values.items():
                    merged[section_key][field_key] = {
                        "default": None,  # No default defined in Python
                        "user_override": user_value,
                        "current": user_value,
                        "is_overridden": True
                    }

        # Merge prompts (if agent has prompt.py - calendar/multi-tool do, executive doesn't)
        if defaults.get("prompts"):
            merged["prompt_templates"] = {}
            for prompt_key, default_prompt in defaults.get("prompts", {}).items():
                user_prompt = user_overrides.get("prompts", {}).get(prompt_key) if isinstance(user_overrides.get("prompts"), dict) else None

                merged["prompt_templates"][prompt_key] = {
                    "default": default_prompt,
                    "user_override": user_prompt,
                    "current": user_prompt if user_prompt else default_prompt,
                    "is_overridden": bool(user_prompt)
                }

        return {
            "agent_id": agent_id,
            "user_id": user_id,
            "values": merged
        }

    except Exception as e:
        print(f"Error fetching config values: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching config: {str(e)}")


@app.post("/api/config/update")
async def update_config(request: UpdateConfigRequest):
    """
    Update a single configuration value in Supabase
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    try:
        if request.agent_id == "global":
            # Update user_secrets table
            # Map config keys to database columns
            column_mapping = {
                "user_timezone": "timezone",
                "anthropic_api_key": "anthropic_api_key",
                "openai_api_key": "openai_api_key",
                "langsmith_api_key": "langsmith_api_key",
                "google_client_id": "google_client_id",
                "google_client_secret": "google_client_secret",
                "google_refresh_token": "google_refresh_token",
            }

            column_name = column_mapping.get(request.field_key)
            if not column_name:
                raise HTTPException(status_code=400, detail=f"Unknown field: {request.field_key}")

            # Upsert into user_secrets
            result = supabase.table("user_secrets") \
                .upsert({
                    "clerk_id": request.user_id,
                    column_name: request.value
                }, on_conflict="clerk_id") \
                .execute()

            return {"success": True, "updated": column_name}

        else:
            # Update agent_configs table
            # First, check if config exists
            try:
                existing = supabase.table("agent_configs") \
                    .select("config_data, prompts") \
                    .eq("clerk_id", request.user_id) \
                    .eq("agent_id", request.agent_id) \
                    .maybe_single() \
                    .execute()

                has_existing = existing.data is not None
            except Exception as e:
                print(f"Error checking existing config: {e}")
                has_existing = False

            if has_existing:
                # Update existing config
                # IMPORTANT: Prompts go in separate "prompts" column, not config_data
                if request.section_key == "prompt_templates":
                    # Update prompts column
                    prompts = existing.data.get("prompts", {})
                    prompts[request.field_key] = request.value

                    supabase.table("agent_configs") \
                        .update({"prompts": prompts}) \
                        .eq("clerk_id", request.user_id) \
                        .eq("agent_id", request.agent_id) \
                        .execute()
                else:
                    # Update config_data column
                    config_data = existing.data.get("config_data", {})
                    if request.section_key not in config_data:
                        config_data[request.section_key] = {}
                    config_data[request.section_key][request.field_key] = request.value

                    supabase.table("agent_configs") \
                        .update({"config_data": config_data}) \
                        .eq("clerk_id", request.user_id) \
                        .eq("agent_id", request.agent_id) \
                        .execute()
            else:
                # Create new config
                # Get agent name from schemas
                schemas_response = await get_all_schemas()
                agent_name = request.agent_id
                for agent in schemas_response["agents"]:
                    if agent["id"] == request.agent_id:
                        agent_name = agent["config"]["CONFIG_INFO"]["name"]
                        break

                # IMPORTANT: Prompts go in separate "prompts" column, not config_data
                if request.section_key == "prompt_templates":
                    supabase.table("agent_configs") \
                        .insert({
                            "clerk_id": request.user_id,
                            "agent_id": request.agent_id,
                            "agent_name": agent_name,
                            "config_data": {},
                            "prompts": {request.field_key: request.value}
                        }) \
                        .execute()
                else:
                    config_data = {
                        request.section_key: {
                            request.field_key: request.value
                        }
                    }

                    supabase.table("agent_configs") \
                        .insert({
                            "clerk_id": request.user_id,
                            "agent_id": request.agent_id,
                            "agent_name": agent_name,
                            "config_data": config_data
                        }) \
                        .execute()

            return {"success": True, "agent_id": request.agent_id}

    except Exception as e:
        print(f"Error updating config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/config/bulk-update")
async def bulk_update_config(request: BulkUpdateRequest):
    """
    Bulk update all config values for an agent
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    try:
        # Get agent name
        schemas_response = await get_all_schemas()
        agent_name = request.agent_id
        for agent in schemas_response["agents"]:
            if agent["id"] == request.agent_id:
                agent_name = agent["config"]["CONFIG_INFO"]["name"]
                break

        # Upsert entire config
        supabase.table("agent_configs") \
            .upsert({
                "clerk_id": request.user_id,
                "agent_id": request.agent_id,
                "agent_name": agent_name,
                "config_data": request.config_data
            }, on_conflict="clerk_id,agent_id") \
            .execute()

        return {"success": True, "agent_id": request.agent_id}

    except Exception as e:
        print(f"Error bulk updating config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class ResetConfigRequest(BaseModel):
    agent_id: str
    user_id: str
    section_key: Optional[str] = None  # If provided, reset only this section
    field_key: Optional[str] = None     # If provided, reset only this field


@app.post("/api/config/reset")
async def reset_config(request: ResetConfigRequest):
    """
    Reset configuration to defaults

    Options:
    1. Reset all: delete entire agent_configs row (reverts everything to code defaults)
    2. Reset section: set section to null (reverts section to code defaults)
    3. Reset field: set field to null (reverts field to code default)
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    try:
        if request.section_key is None and request.field_key is None:
            # Reset ALL: Delete entire row
            supabase.table("agent_configs") \
                .delete() \
                .eq("clerk_id", request.user_id) \
                .eq("agent_id", request.agent_id) \
                .execute()

            return {
                "success": True,
                "action": "reset_all",
                "message": f"All configs for {request.agent_id} reset to defaults"
            }

        # Partial reset: Need to update specific fields/sections
        result = supabase.table("agent_configs") \
            .select("config_data, prompts") \
            .eq("clerk_id", request.user_id) \
            .eq("agent_id", request.agent_id) \
            .maybe_single() \
            .execute()

        if not result or not result.data:
            # No overrides exist, nothing to reset
            return {
                "success": True,
                "action": "nothing_to_reset",
                "message": "No overrides found, already using defaults"
            }

        config_data = result.data.get("config_data", {})
        prompts = result.data.get("prompts", {})

        if request.field_key:
            # Reset specific field
            if request.section_key == "prompt_templates":
                if request.field_key in prompts:
                    del prompts[request.field_key]
            else:
                if request.section_key in config_data and request.field_key in config_data[request.section_key]:
                    del config_data[request.section_key][request.field_key]
                    # If section is now empty, remove it
                    if not config_data[request.section_key]:
                        del config_data[request.section_key]

            action = "reset_field"
            message = f"Field {request.section_key}.{request.field_key} reset to default"

        elif request.section_key:
            # Reset entire section
            if request.section_key == "prompt_templates":
                prompts = {}
            elif request.section_key in config_data:
                del config_data[request.section_key]

            action = "reset_section"
            message = f"Section {request.section_key} reset to defaults"

        # Update Supabase with modified config
        supabase.table("agent_configs") \
            .update({
                "config_data": config_data,
                "prompts": prompts
            }) \
            .eq("clerk_id", request.user_id) \
            .eq("agent_id", request.agent_id) \
            .execute()

        return {
            "success": True,
            "action": action,
            "message": message
        }

    except Exception as e:
        print(f"Error resetting config: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
