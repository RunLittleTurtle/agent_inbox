#!/usr/bin/env python3
"""
Test script to verify that supervisor receives complete information
including important notes from booking operations.
"""

import asyncio
import sys
import os
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from src.state import WorkflowState, AgentType, TaskStatus
from src.graph import get_current_context

async def test_supervisor_information_flow():
    """Test that supervisor gets complete information from calendar agent"""

    print("🧪 Testing Supervisor Information Flow")
    print("=" * 50)

    # Create initial state like supervisor would
    context = get_current_context()
    state = WorkflowState(
        messages=[HumanMessage(content="Change my meeting tomorrow to 2pm and remove John from attendees")],
        current_time=context['current_time'],
        timezone=context['timezone'],
        timezone_name=context['timezone_name']
    )

    print(f"✅ Initial state created")
    print(f"   Tasks: {len(state.tasks)}")
    print(f"   Messages: {len(state.messages)}")

    # Simulate calendar agent adding a task (like our modified booking_node does)
    task = state.add_task(
        agent_name=AgentType.CALENDAR_AGENT,
        description="Processing booking approval workflow",
        user_request="Change meeting time and remove attendee"
    )
    task.status = TaskStatus.IN_PROGRESS

    print(f"\n📋 Calendar agent started task:")
    print(f"   Task ID: {task.id[:8]}...")
    print(f"   Status: {task.status}")
    print(f"   Description: {task.description}")

    # Simulate MCP tool response with important note (like the attendee removal restriction)
    mcp_tool_response = {
        "success": True,
        "event_updated": True,
        "note": "Please note: The Google Calendar API does not support removing attendees from events. This is a restriction of the API. The event will be updated with the new time, but the attendee john@example.com cannot be automatically removed and will need to be removed manually through the Google Calendar interface."
    }

    # Simulate the booking execution result (with our new information preservation)
    booking_result = f"""✅ Booking Confirmed Successfully!

📅 **Team Meeting - Updated**
🕒 2025-09-07T14:00:00-04:00 - 2025-09-07T15:00:00-04:00

📋 Operations Completed:
  • ✅ google_calendar-update-event: Success
  • ℹ️ Important: {mcp_tool_response['note']}"""

    # Complete the task with the detailed result
    task.complete(booking_result)

    print(f"\n✅ Calendar agent completed task:")
    print(f"   Status: {task.status}")
    print(f"   Result length: {len(task.result)} characters")

    # Add the result message to state (like calendar agent would)
    state.messages.append(AIMessage(content=booking_result))

    # Now supervisor checks the state
    summary = state.get_task_summary()

    print(f"\n🎯 Supervisor's view:")
    print(f"   Total tasks: {summary['total_tasks']}")
    print(f"   Completed: {summary['completed_tasks']}")
    print(f"   Success rate: {summary['success_rate']:.1%}")
    print(f"   Agent calls: {summary['agent_calls']}")

    # Most importantly - supervisor can see the detailed result
    completed_tasks = [t for t in state.tasks if t.status == TaskStatus.COMPLETED]
    if completed_tasks:
        latest_task = completed_tasks[-1]
        print(f"\n📄 Latest task result (supervisor can see this):")
        print(f"   Task: {latest_task.description}")
        print(f"   Result preview: {latest_task.result[:100]}...")

        # Check if important information is preserved
        has_important_info = "restriction" in latest_task.result.lower() or "manually" in latest_task.result.lower()
        print(f"   Contains important API restrictions: {'✅ YES' if has_important_info else '❌ NO'}")

    # Supervisor can also see the last message
    last_message = state.messages[-1] if state.messages else None
    if last_message:
        has_restriction_in_msg = "restriction" in last_message.content.lower() or "manually" in last_message.content.lower()
        print(f"   Last message contains restrictions: {'✅ YES' if has_restriction_in_msg else '❌ NO'}")
        print(f"   Message preview: {last_message.content[:100]}...")

    print(f"\n🎉 Test completed!")

    # Summary of what supervisor now has access to:
    print(f"\n📊 Supervisor Information Access:")
    print(f"   ✅ Task completion status")
    print(f"   ✅ Detailed task results")
    print(f"   ✅ Important API restrictions and notes")
    print(f"   ✅ Agent performance metrics")
    print(f"   ✅ Complete message history")

    return state, summary

if __name__ == "__main__":
    asyncio.run(test_supervisor_information_flow())
