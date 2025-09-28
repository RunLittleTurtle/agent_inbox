#!/usr/bin/env python3
"""
Test script to verify calendar agent configuration fields
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_calendar_config():
    """Test that all calendar config fields can be read"""
    from calendar_agent.config import (
        AGENT_NAME,
        AGENT_DISPLAY_NAME,
        AGENT_DESCRIPTION,
        AGENT_STATUS,
        MCP_SERVICE,
        LLM_CONFIG,
        MCP_SERVER_URL,
        USER_TIMEZONE,
        WORK_HOURS_START,
        WORK_HOURS_END,
        DEFAULT_MEETING_DURATION,
        is_agent_enabled
    )

    print("=" * 50)
    print("CALENDAR AGENT CONFIGURATION TEST")
    print("=" * 50)

    # Test Agent Identity
    print("\n📋 AGENT IDENTITY:")
    print(f"  Name: {AGENT_NAME}")
    print(f"  Display Name: {AGENT_DISPLAY_NAME}")
    print(f"  Description: {AGENT_DESCRIPTION}")
    print(f"  Status: {AGENT_STATUS}")
    print(f"  Enabled: {is_agent_enabled()}")
    print(f"  MCP Service: {MCP_SERVICE}")

    # Test LLM Configuration
    print("\n🤖 LLM CONFIGURATION:")
    print(f"  Model: {LLM_CONFIG.get('model', 'Not set')}")
    print(f"  Temperature: {LLM_CONFIG.get('temperature', 'Not set')}")
    print(f"  Streaming: {LLM_CONFIG.get('streaming', 'Not set')}")

    # Test MCP Server
    print("\n🔗 MCP SERVER:")
    print(f"  URL: {MCP_SERVER_URL[:50]}..." if len(MCP_SERVER_URL) > 50 else f"  URL: {MCP_SERVER_URL}")

    # Test User Preferences
    print("\n⚙️ USER PREFERENCES:")
    print(f"  Timezone: {USER_TIMEZONE}")
    print(f"  Work Hours: {WORK_HOURS_START} - {WORK_HOURS_END}")
    print(f"  Default Meeting Duration: {DEFAULT_MEETING_DURATION} minutes")

    # Test that values are the expected types
    print("\n✅ TYPE VALIDATION:")
    assert isinstance(AGENT_NAME, str), "AGENT_NAME should be string"
    assert isinstance(AGENT_STATUS, str), "AGENT_STATUS should be string"
    assert isinstance(LLM_CONFIG, dict), "LLM_CONFIG should be dict"
    assert isinstance(WORK_HOURS_START, str), "WORK_HOURS_START should be string"
    assert isinstance(WORK_HOURS_END, str), "WORK_HOURS_END should be string"
    assert isinstance(DEFAULT_MEETING_DURATION, str), "DEFAULT_MEETING_DURATION should be string"
    assert isinstance(is_agent_enabled(), bool), "is_agent_enabled() should return bool"
    print("  All types are correct!")

    print("\n" + "=" * 50)
    print("✨ All calendar configuration fields loaded successfully!")
    print("=" * 50)

    return True

if __name__ == "__main__":
    try:
        if test_calendar_config():
            sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)