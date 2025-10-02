"""
FastAPI Config Bridge
Exposes Python agent configs to Next.js config-app
"""
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
import sys
from pathlib import Path
from importlib import import_module
from dotenv import load_dotenv
from supabase import create_client, Client

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv()

app = FastAPI(title="Agent Config API", version="1.0.0")

# CORS - Allow config-app to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3004",  # Local config-app
        "https://config-*.vercel.app",  # Production config-app
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase client
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SECRET_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: Missing Supabase credentials")
    supabase = None
else:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Agent directories to scan
AGENT_PATHS = [
    "calendar_agent",
    "multi_tool_rube_agent",
    "_react_agent_mcp_template",
    "executive-ai-assistant",
]

# Global environment config
GLOBAL_CONFIG_PATH = "ui_config"


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


@app.get("/")
async def root():
    return {
        "service": "Agent Config API",
        "status": "running",
        "endpoints": [
            "/api/config/schemas",
            "/api/config/values",
            "/api/config/update",
        ]
    }


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
            print(f"Error loading {agent_path}: {e}")
            continue

    return {"agents": list(schemas.values())}


@app.get("/api/config/values")
async def get_config_values(agent_id: Optional[str] = None, user_id: Optional[str] = None):
    """
    Get configuration values for an agent from Supabase

    If agent_id is 'global', returns user_secrets
    Otherwise returns agent_configs for the specified agent
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    if not user_id:
        raise HTTPException(status_code=400, detail="user_id required")

    try:
        if agent_id == "global":
            # Get user secrets (API keys, global preferences)
            result = supabase.table("user_secrets") \
                .select("*") \
                .eq("clerk_id", user_id) \
                .single() \
                .execute()

            if result.data:
                # Convert to config format
                data = result.data
                return {
                    "user_preferences": {
                        "user_timezone": data.get("timezone", "America/Toronto")
                    },
                    "ai_models": {
                        "anthropic_api_key": data.get("anthropic_api_key"),
                        "openai_api_key": data.get("openai_api_key"),
                    },
                    "langgraph_system": {
                        "langsmith_api_key": data.get("langsmith_api_key"),
                        "langchain_project": "ambient-email-agent",
                    }
                }
            else:
                # Return empty config - user hasn't set up yet
                return {}
        else:
            # Get agent-specific config
            result = supabase.table("agent_configs") \
                .select("config_data") \
                .eq("clerk_id", user_id) \
                .eq("agent_id", agent_id) \
                .single() \
                .execute()

            if result.data:
                return result.data.get("config_data", {})
            else:
                # Return empty config
                return {}

    except Exception as e:
        print(f"Error fetching config values: {e}")
        return {}


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
            # First, get existing config
            existing = supabase.table("agent_configs") \
                .select("config_data") \
                .eq("clerk_id", request.user_id) \
                .eq("agent_id", request.agent_id) \
                .single() \
                .execute()

            if existing.data:
                # Update existing config
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
                config_data = {
                    request.section_key: {
                        request.field_key: request.value
                    }
                }

                # Get agent name from schemas
                schemas_response = await get_all_schemas()
                agent_name = request.agent_id
                for agent in schemas_response["agents"]:
                    if agent["id"] == request.agent_id:
                        agent_name = agent["config"]["CONFIG_INFO"]["name"]
                        break

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
