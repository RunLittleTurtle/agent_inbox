#!/usr/bin/env python3
"""
Test calendar config update functionality
"""

import json
import requests
import time

BASE_URL = "http://localhost:3004/api/config"

def test_updates():
    """Test updating calendar config fields"""
    print("=" * 50)
    print("TESTING CALENDAR CONFIG UPDATES")
    print("=" * 50)

    # Test 1: Update agent status
    print("\n📋 Testing agent status update...")
    response = requests.post(f"{BASE_URL}/update", json={
        "agentId": "calendar_agent",
        "configPath": "src/calendar_agent/ui_config.py",
        "sectionKey": "agent_identity",
        "fieldKey": "agent_status",
        "value": "disabled"
    })
    print(f"  Status update: {response.status_code}")
    if response.status_code == 200:
        print("  ✅ Agent status updated successfully")
    else:
        print(f"  ❌ Error: {response.text}")

    time.sleep(1)

    # Test 2: Update work hours
    print("\n⏰ Testing work hours update...")
    response = requests.post(f"{BASE_URL}/update", json={
        "agentId": "calendar_agent",
        "configPath": "src/calendar_agent/ui_config.py",
        "sectionKey": "user_preferences",
        "fieldKey": "work_hours_start",
        "value": "08:30"
    })
    print(f"  Work hours update: {response.status_code}")
    if response.status_code == 200:
        print("  ✅ Work hours updated successfully")
    else:
        print(f"  ❌ Error: {response.text}")

    # Test 3: Update meeting duration
    print("\n📅 Testing meeting duration update...")
    response = requests.post(f"{BASE_URL}/update", json={
        "agentId": "calendar_agent",
        "configPath": "src/calendar_agent/ui_config.py",
        "sectionKey": "user_preferences",
        "fieldKey": "default_meeting_duration",
        "value": "45"
    })
    print(f"  Meeting duration update: {response.status_code}")
    if response.status_code == 200:
        print("  ✅ Meeting duration updated successfully")
    else:
        print(f"  ❌ Error: {response.text}")

    # Test 4: Update temperature
    print("\n🌡️ Testing temperature update...")
    response = requests.post(f"{BASE_URL}/update", json={
        "agentId": "calendar_agent",
        "configPath": "src/calendar_agent/ui_config.py",
        "sectionKey": "llm",
        "fieldKey": "temperature",
        "value": 0.5
    })
    print(f"  Temperature update: {response.status_code}")
    if response.status_code == 200:
        print("  ✅ Temperature updated successfully")
    else:
        print(f"  ❌ Error: {response.text}")

    # Get updated values
    print("\n📖 Fetching updated values...")
    response = requests.get(f"{BASE_URL}/values", params={"agentId": "calendar_agent"})
    if response.status_code == 200:
        values = response.json()
        print("  Current configuration:")
        print(f"    Status: {values.get('agent_identity', {}).get('agent_status', 'N/A')}")
        print(f"    Work Start: {values.get('user_preferences', {}).get('work_hours_start', 'N/A')}")
        print(f"    Meeting Duration: {values.get('user_preferences', {}).get('default_meeting_duration', 'N/A')} min")
        print(f"    Temperature: {values.get('llm', {}).get('temperature', 'N/A')}")

    print("\n" + "=" * 50)
    print("✨ Update tests completed!")
    print("=" * 50)

if __name__ == "__main__":
    test_updates()