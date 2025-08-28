#!/usr/bin/env python3
"""
Test calendar agent directly vs through supervisor to isolate tool calling issue
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test_direct_calendar_agent():
    """Test calendar agent directly without supervisor"""
    from src.calendar_agent.langchain_mcp_integration import get_calendar_tools_for_supervisor
    from langgraph.prebuilt import create_react_agent
    from langchain_openai import ChatOpenAI

    print("🧪 Testing Direct Calendar Agent...")
    
    # Load tools
    calendar_tools = await get_calendar_tools_for_supervisor()
    print(f"📋 Loaded {len(calendar_tools)} tools")
    
    # Create model
    model = ChatOpenAI(
        model="gpt-4o",
        temperature=0.1,
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Create calendar agent
    calendar_agent = create_react_agent(
        model=model,
        tools=calendar_tools,
        name="calendar_agent"
    )
    
    # Test message
    test_input = {
        "messages": [
            {"role": "user", "content": "Can you book a meeting for tomorrow at 2pm titled 'Test Meeting'?"}
        ]
    }
    
    print("\n🔄 Invoking direct calendar agent...")
    try:
        result = calendar_agent.invoke(test_input)
        print(f"📤 Result: {result}")
        
        # Check if tools were called
        messages = result.get("messages", [])
        tool_calls = []
        for msg in messages:
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                tool_calls.extend(msg.tool_calls)
        
        if tool_calls:
            print(f"✅ TOOLS CALLED: {len(tool_calls)} tool calls made!")
            for tc in tool_calls:
                print(f"   🔧 {tc.get('name', 'unknown')}")
        else:
            print("❌ NO TOOLS CALLED - Agent responded with text only")
            
    except Exception as e:
        print(f"❌ Error: {e}")

async def test_supervisor_calendar_agent():
    """Test calendar agent through supervisor"""
    from src.graph import make_graph
    
    print("\n🏢 Testing Supervisor-Managed Calendar Agent...")
    
    supervisor_graph = await make_graph()
    
    test_input = {
        "messages": [
            {"role": "user", "content": "Can you book a meeting for tomorrow at 2pm titled 'Test Meeting'?"}
        ]
    }
    
    print("\n🔄 Invoking supervisor...")
    try:
        result = supervisor_graph.invoke(test_input)
        print(f"📤 Result: {result}")
        
        # Check if tools were called
        messages = result.get("messages", [])
        tool_calls = []
        for msg in messages:
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                tool_calls.extend(msg.tool_calls)
        
        if tool_calls:
            print(f"✅ TOOLS CALLED: {len(tool_calls)} tool calls made!")
            for tc in tool_calls:
                print(f"   🔧 {tc.get('name', 'unknown')}")
        else:
            print("❌ NO TOOLS CALLED - Only handoff tools used")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    async def main():
        await test_direct_calendar_agent()
        await test_supervisor_calendar_agent()
    
    asyncio.run(main())
