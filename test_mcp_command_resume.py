#!/usr/bin/env python3
"""
Test MCP tool access and Command.resume() workflow
Tests the fixes for booking approval with human interrupt
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from langchain_core.messages import HumanMessage
from langgraph.types import Command


async def test_calendar_mcp_tools():
    """Test calendar agent MCP tool loading and routing"""
    print("🧪 Testing Calendar Agent MCP Tool Access...")
    
    try:
        from src.calendar_agent.calendar_orchestrator import CalendarAgentWithMCP
        
        # Initialize calendar agent
        print("📋 Initializing calendar agent...")
        agent = CalendarAgentWithMCP()
        await agent.initialize()
        
        # Check if MCP tools are loaded
        print(f"🔧 MCP Tools loaded: {len(agent.booking_tools)} booking tools, {len(agent.tools)} read-only tools")
        
        if agent.booking_tools:
            print("📝 Available booking tools:")
            for tool in agent.booking_tools:
                print(f"   • {tool.name}: {tool.description[:80]}...")
        else:
            print("❌ No booking tools loaded - MCP connection may have failed")
            return False
            
        # Get the graph
        graph = await agent.get_agent()
        if not graph:
            print("❌ Failed to create calendar graph")
            return False
            
        print("✅ Calendar graph created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error testing calendar agent: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_booking_approval_flow():
    """Test the booking approval flow with interrupt() and Command.resume()"""
    print("\n🎯 Testing Booking Approval Flow...")
    
    try:
        from src.calendar_agent.calendar_orchestrator import CalendarAgentWithMCP
        
        # Initialize calendar agent
        agent = CalendarAgentWithMCP()
        await agent.initialize()
        graph = await agent.get_agent()
        
        # Test booking request
        booking_request = "Schedule a team meeting for tomorrow at 2 PM with john@example.com"
        
        print(f"📅 Testing booking request: {booking_request}")
        
        # Create initial state
        config = {"configurable": {"thread_id": "test-booking-thread"}}
        initial_state = {"messages": [HumanMessage(content=booking_request)]}
        
        print("🔄 Invoking calendar graph...")
        
        # This should trigger the routing and interrupt for approval
        try:
            result = await graph.ainvoke(initial_state, config=config)
            print("📋 Graph execution result:")
            if result and "messages" in result:
                last_message = result["messages"][-1]
                print(f"   Last message: {last_message.content[:200]}...")
                
                # Check if we got an interrupt
                if "approval" in last_message.content.lower():
                    print("✅ Booking approval interrupt triggered successfully")
                    
                    # Now test Command.resume("approve")
                    print("\n⚡ Testing Command.resume('approve')...")
                    
                    # Simulate human approval
                    resume_result = await graph.ainvoke(
                        Command(resume="approve"),
                        config=config
                    )
                    
                    if resume_result and "messages" in resume_result:
                        final_message = resume_result["messages"][-1]
                        print(f"📋 Resume result: {final_message.content[:200]}...")
                        
                        if "confirmed" in final_message.content.lower() or "success" in final_message.content.lower():
                            print("✅ Command.resume() completed booking successfully")
                            return True
                        else:
                            print("⚠️ Command.resume() completed but booking may have failed")
                            return False
                    else:
                        print("❌ Command.resume() did not return expected result")
                        return False
                else:
                    print("⚠️ Expected booking approval interrupt but got different response")
                    return False
            else:
                print("❌ No messages in graph result")
                return False
                
        except Exception as e:
            print(f"❌ Error during graph execution: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error in booking approval test: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("🚀 Testing MCP Tool Access and Command.resume() Workflow\n")
    
    # Test 1: MCP tool loading
    tools_ok = await test_calendar_mcp_tools()
    
    # Test 2: Booking approval flow
    if tools_ok:
        booking_ok = await test_booking_approval_flow()
        
        if booking_ok:
            print("\n✅ All tests passed! MCP tools are accessible and Command.resume() works")
        else:
            print("\n⚠️ MCP tools loaded but Command.resume() flow has issues")
    else:
        print("\n❌ MCP tool loading failed - check PIPEDREAM_MCP_SERVER environment variable")
    
    print(f"\n📊 Environment Status:")
    print(f"   PIPEDREAM_MCP_SERVER: {'✅' if os.getenv('PIPEDREAM_MCP_SERVER') else '❌'}")
    print(f"   ANTHROPIC_API_KEY: {'✅' if os.getenv('ANTHROPIC_API_KEY') else '❌'}")


if __name__ == "__main__":
    asyncio.run(main())
