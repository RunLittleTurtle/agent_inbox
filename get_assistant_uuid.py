#!/usr/bin/env python3
"""
Get the correct assistant UUID from LangGraph server
"""

import asyncio
import aiohttp
import json

async def get_assistant_uuid():
    """Find the correct assistant UUID from LangGraph server"""
    
    base_url = "http://localhost:2024"
    
    async with aiohttp.ClientSession() as session:
        
        # Try to get all assistants
        print("🔍 Looking for assistants...")
        
        # Method 1: Try GET /assistants
        try:
            async with session.get(f"{base_url}/assistants") as resp:
                print(f"GET /assistants: {resp.status}")
                if resp.status == 200:
                    assistants = await resp.json()
                    print(f"Assistants: {assistants}")
                    return
        except Exception as e:
            print(f"GET /assistants failed: {e}")
        
        # Method 2: Try POST /assistants to create one
        try:
            create_data = {
                "graph_id": "agent",
                "config": {},
                "metadata": {"name": "agent"}
            }
            async with session.post(f"{base_url}/assistants", json=create_data) as resp:
                print(f"POST /assistants: {resp.status}")
                if resp.status in [200, 201]:
                    assistant = await resp.json()
                    assistant_id = assistant.get("assistant_id")
                    print(f"✅ Created/Found assistant: {assistant_id}")
                    
                    # Update .env.local
                    env_path = "/Users/samuelaudette/Documents/code_projects/agent_inbox_1.17/agent-chat-ui/.env.local"
                    with open(env_path, 'w') as f:
                        f.write(f"# Agent Chat UI Configuration\n")
                        f.write(f"NEXT_PUBLIC_API_URL=http://localhost:2024\n")
                        f.write(f"NEXT_PUBLIC_ASSISTANT_ID={assistant_id}\n")
                    
                    print(f"✅ Updated .env.local with assistant ID: {assistant_id}")
                    return assistant_id
                else:
                    text = await resp.text()
                    print(f"Create assistant failed: {text}")
        except Exception as e:
            print(f"POST /assistants failed: {e}")
        
        # Method 3: Check the server logs for existing UUID
        print("\n🔍 Check the LangGraph server logs for existing assistant UUIDs")
        print("Look for lines like: 'assistant_id=<UUID>' in the server output")

if __name__ == "__main__":
    asyncio.run(get_assistant_uuid())
