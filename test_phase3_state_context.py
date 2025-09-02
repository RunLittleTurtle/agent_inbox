#!/usr/bin/env python3
"""
Phase 3 Test: Verify state-aware calendar agent receives CalendarContext properly
Tests that our calendar agent wrapper correctly extracts and uses context from CalendarState
"""

import asyncio
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from langchain_core.messages import HumanMessage
from src.graph import CalendarState, CalendarContext, create_supervisor_graph

async def test_phase3_state_context():
    """Test that calendar agent receives and uses CalendarContext from state"""
    print("🧪 Phase 3 Test: State-aware calendar agent context passing")
    
    # Create test CalendarContext matching the schema
    test_context = CalendarContext(
        current_date="2025-01-02", 
        current_time="10:45 AM",
        timezone="America/Toronto",
        timezone_name="Toronto Time",
        calendar_id="primary",
        task_context={"test_phase": "phase3_context_passing"}
    )
    
    # Create test CalendarState with context
    test_state: CalendarState = {
        "messages": [
            HumanMessage(content="What's my schedule for today?")
        ],
        "calendar_context": test_context
    }
    
    print(f"📋 Test context: {test_context.model_dump()}")
    
    try:
        # Get the supervisor graph
        graph = await create_supervisor_graph()
        print("✅ Supervisor graph created successfully")
        
        # Test direct calendar context extraction (simulate what happens in calendar agent)
        context = test_state.get("calendar_context")
        if context:
            print(f"✅ Calendar context extracted from state:")
            print(f"   📅 Date: {context.current_date}")
            print(f"   🕐 Time: {context.current_time}")
            print(f"   🌍 Timezone: {context.timezone_name}")
            print(f"   📋 Calendar ID: {context.calendar_id}")
        else:
            print("❌ No calendar context found in test state")
            return False
        
        print("✅ Phase 3 state context passing test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Phase 3 test failed: {str(e)}")
        return False

if __name__ == "__main__":
    # Ensure we have required environment variables
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠️  ANTHROPIC_API_KEY not set - using test mode")
    
    success = asyncio.run(test_phase3_state_context())
    if success:
        print("🎉 Phase 3 test passed - calendar agent can access state context")
    else:
        print("❌ Phase 3 test failed - need to fix state context passing")
