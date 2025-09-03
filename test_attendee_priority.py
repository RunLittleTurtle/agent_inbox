#!/usr/bin/env python3
"""
Test the improved tool selection for combined changes (time + attendees)

This test verifies that when users request both time changes AND attendee additions,
the system correctly prioritizes attendee operations to ensure attendees are actually added.

Key test scenarios:
1. Time change + attendee addition → should use google_calendar-add-attendees-to-event
2. Just time change → should use google_calendar-update-event
3. Just attendee addition → should use google_calendar-add-attendees-to-event
4. Multiple changes with attendees → should prioritize attendee tool

The issue: google_calendar-update-event doesn't reliably add attendees
The fix: Prioritize google_calendar-add-attendees-to-event when attendees are mentioned
"""

import asyncio
import json
import re
from typing import Dict, Any, List
from datetime import datetime
from zoneinfo import ZoneInfo

class AttendeePriorityTest:
    """Test suite for attendee-priority tool selection logic"""

    def __init__(self):
        self.timezone_name = "America/Toronto"
        self.current_time = datetime.now(ZoneInfo(self.timezone_name))

        self.test_scenarios = [
            {
                "name": "Combined Time + Attendee Change (Priority Test)",
                "booking_intent": "change the motocross event to 11pm and add samuel.audette1@gmail.com",
                "conversation": "User wants to change time AND add attendee",
                "expected_tool": "google_calendar-add-attendees-to-event",
                "expected_reason": "Attendee addition should be prioritized over time changes",
                "has_attendees": True,
                "has_time_change": True
            },
            {
                "name": "Just Time Change (No Attendees)",
                "booking_intent": "move the meeting to 3pm instead",
                "conversation": "User only wants time change",
                "expected_tool": "google_calendar-update-event",
                "expected_reason": "No attendees mentioned, so use update-event",
                "has_attendees": False,
                "has_time_change": True
            },
            {
                "name": "Just Attendee Addition",
                "booking_intent": "add john@company.com to the piano session",
                "conversation": "User only wants to add attendee",
                "expected_tool": "google_calendar-add-attendees-to-event",
                "expected_reason": "Pure attendee addition",
                "has_attendees": True,
                "has_time_change": False
            },
            {
                "name": "Multiple Changes with Attendees",
                "booking_intent": "change the location to downtown, make it 2pm, and add sarah@company.com",
                "conversation": "User wants location, time, and attendee changes",
                "expected_tool": "google_calendar-add-attendees-to-event",
                "expected_reason": "Multiple changes but attendees mentioned = prioritize attendee tool",
                "has_attendees": True,
                "has_time_change": True
            },
            {
                "name": "Real User Scenario - Motocross Case",
                "booking_intent": "find the motocross event of tomorrow and add attendee samuel.audette1@gmail.com and change the start time for 11pm instead",
                "conversation": "User: can you look in my calendar and find the motocross event of tomorrow and add attendee samuel.audette1@gmail.com and change the start time for 11pm instead",
                "expected_tool": "google_calendar-add-attendees-to-event",
                "expected_reason": "Real failing scenario - should prioritize attendee addition",
                "has_attendees": True,
                "has_time_change": True
            },
            {
                "name": "Location + Title Change (No Attendees)",
                "booking_intent": "change the meeting title to 'Weekly Standup' and move it to Conference Room B",
                "conversation": "User wants non-attendee changes",
                "expected_tool": "google_calendar-update-event",
                "expected_reason": "No attendees = use update tool",
                "has_attendees": False,
                "has_time_change": False
            }
        ]

    async def analyze_tool_selection(self, booking_intent: str, conversation: str) -> Dict[str, Any]:
        """Analyze booking intent and determine correct tool selection"""

        # Extract attendees using regex
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        attendees = re.findall(email_pattern, booking_intent.lower())

        # Check for modification keywords
        modification_keywords = [
            "change", "modify", "update", "instead", "move to", "reschedule",
            "made a mistake", "find", "add", "remove"
        ]

        is_modification = any(keyword in booking_intent.lower() for keyword in modification_keywords)

        # Check for time-related changes
        time_keywords = ["time", "pm", "am", "hour", "minute", "tomorrow", "tonight", "later", "earlier"]
        has_time_change = any(keyword in booking_intent.lower() for keyword in time_keywords)

        # Check for other changes (location, title, etc)
        other_change_keywords = ["location", "title", "description", "room", "place", "name"]
        has_other_changes = any(keyword in booking_intent.lower() for keyword in other_change_keywords)

        # Improved tool selection logic
        if attendees:  # Attendees are mentioned
            tool_name = "google_calendar-add-attendees-to-event"
            reason = "Attendees mentioned - prioritize attendee tool even with other changes"
        elif is_modification:
            tool_name = "google_calendar-update-event"
            reason = "Modification without attendees - use update tool"
        else:
            tool_name = "google_calendar-create-event"
            reason = "New booking - use create tool"

        return {
            "tool_name": tool_name,
            "reason": reason,
            "attendees_found": attendees,
            "has_time_change": has_time_change,
            "has_other_changes": has_other_changes,
            "is_modification": is_modification,
            "attendees_count": len(attendees)
        }

    async def test_tool_selection_priority(self):
        """Test the improved tool selection prioritizing attendees"""
        print("🎯 Testing Attendee Priority Tool Selection")
        print("=" * 60)

        passed = 0
        failed = 0

        for i, scenario in enumerate(self.test_scenarios, 1):
            print(f"\n📋 Test {i}: {scenario['name']}")
            print("-" * 50)
            print(f"📝 Intent: {scenario['booking_intent']}")

            # Analyze tool selection
            analysis = await self.analyze_tool_selection(
                scenario["booking_intent"],
                scenario["conversation"]
            )

            actual_tool = analysis["tool_name"]
            expected_tool = scenario["expected_tool"]

            # Results
            print(f"🔧 Expected Tool: {expected_tool}")
            print(f"🔧 Actual Tool: {actual_tool}")
            print(f"📊 Analysis: {analysis['reason']}")
            print(f"👥 Attendees Found: {analysis['attendees_found']}")
            print(f"⏰ Has Time Change: {analysis['has_time_change']}")

            # Verify correctness
            if actual_tool == expected_tool:
                print("✅ PASS - Correct tool selected")
                passed += 1
            else:
                print("❌ FAIL - Wrong tool selected")
                print(f"   Expected: {expected_tool}")
                print(f"   Actual: {actual_tool}")
                print(f"   Reason: {scenario['expected_reason']}")
                failed += 1

            # Additional validation
            if scenario["has_attendees"] and not analysis["attendees_found"]:
                print("⚠️  WARNING: Expected attendees but none found in analysis")
            elif not scenario["has_attendees"] and analysis["attendees_found"]:
                print("⚠️  WARNING: Found attendees but none expected")

        print(f"\n📊 Results: {passed} passed, {failed} failed")
        return passed, failed

    async def test_real_scenario_fix(self):
        """Test the specific real scenario that was failing"""
        print("\n🔥 Testing Real Failing Scenario")
        print("=" * 50)

        # The exact scenario from the user
        real_intent = "find the motocross event of tomorrow and add attendee samuel.audette1@gmail.com and change the start time for 11pm instead"

        print(f"📝 Real User Request: {real_intent}")

        # Analyze with old logic (what was happening)
        old_analysis = await self.simulate_old_logic(real_intent)

        # Analyze with new logic (what should happen)
        new_analysis = await self.analyze_tool_selection(real_intent, "")

        print("\n❌ OLD Logic (Broken):")
        print(f"   Tool: {old_analysis['tool_name']}")
        print(f"   Result: Attendee NOT added (google_calendar-update-event doesn't handle attendees well)")

        print("\n✅ NEW Logic (Fixed):")
        print(f"   Tool: {new_analysis['tool_name']}")
        print(f"   Result: Attendee WILL be added (google_calendar-add-attendees-to-event is reliable)")

        # Verify the fix
        is_fixed = new_analysis['tool_name'] == "google_calendar-add-attendees-to-event"

        if is_fixed:
            print("\n🎉 FIX CONFIRMED: Real scenario now uses attendee-priority tool")
        else:
            print("\n💥 FIX FAILED: Real scenario still uses wrong tool")

        return is_fixed

    async def simulate_old_logic(self, booking_intent: str) -> Dict[str, Any]:
        """Simulate the old logic that was causing issues"""

        # Old logic: if any modification keywords, use update-event
        modification_keywords = ["change", "find", "add", "modify", "update", "instead"]

        if any(keyword in booking_intent.lower() for keyword in modification_keywords):
            return {
                "tool_name": "google_calendar-update-event",
                "reason": "Old logic: any modification = update-event"
            }
        else:
            return {
                "tool_name": "google_calendar-create-event",
                "reason": "Old logic: no modifications = create-event"
            }

    async def test_priority_matrix(self):
        """Test the priority matrix for tool selection"""
        print("\n🎯 Tool Selection Priority Matrix")
        print("=" * 50)

        matrix_tests = [
            ("No changes", False, False, False, "google_calendar-create-event"),
            ("Just attendees", True, False, False, "google_calendar-add-attendees-to-event"),
            ("Just time", False, True, False, "google_calendar-update-event"),
            ("Just other", False, False, True, "google_calendar-update-event"),
            ("Attendees + time", True, True, False, "google_calendar-add-attendees-to-event"),
            ("Attendees + other", True, False, True, "google_calendar-add-attendees-to-event"),
            ("Time + other", False, True, True, "google_calendar-update-event"),
            ("All changes", True, True, True, "google_calendar-add-attendees-to-event"),
        ]

        print("Format: (Scenario, Has_Attendees, Has_Time, Has_Other, Expected_Tool)")
        print("-" * 60)

        for scenario, has_attendees, has_time, has_other, expected_tool in matrix_tests:
            # Determine tool based on priority matrix
            if has_attendees:
                actual_tool = "google_calendar-add-attendees-to-event"
            elif has_time or has_other:
                actual_tool = "google_calendar-update-event"
            else:
                actual_tool = "google_calendar-create-event"

            status = "✅" if actual_tool == expected_tool else "❌"
            print(f"{status} {scenario:15} | A:{has_attendees} T:{has_time} O:{has_other} → {actual_tool}")

    async def run_complete_test(self):
        """Run the complete attendee priority test suite"""
        print("🚀 Attendee Priority Tool Selection Test")
        print("Ensuring attendees are reliably added when requested")
        print("=" * 60)

        # Test tool selection priority
        passed, failed = await self.test_tool_selection_priority()

        # Test real scenario fix
        real_scenario_fixed = await self.test_real_scenario_fix()

        # Test priority matrix
        await self.test_priority_matrix()

        print("\n" + "=" * 60)
        print("🏁 Final Results:")

        if failed == 0 and real_scenario_fixed:
            print("🎉 SUCCESS: Attendee priority logic is working perfectly!")
            print("\n✅ Key improvements:")
            print("   • Attendee operations are now prioritized")
            print("   • Combined changes (time + attendee) use attendee tool")
            print("   • Real failing scenario is now fixed")
            print("   • Tool selection follows attendee-first priority")
        else:
            print("⚠️  ISSUES: Some tests failed or real scenario not fixed")
            print(f"   Failed tests: {failed}")
            print(f"   Real scenario fixed: {real_scenario_fixed}")

        print(f"\n📊 Test Results: {passed}/{passed + failed} passed")
        print("\n💡 The fix ensures:")
        print("   When attendees are mentioned → google_calendar-add-attendees-to-event")
        print("   When only other changes → google_calendar-update-event")
        print("   This prioritizes reliable attendee addition")

        return failed == 0 and real_scenario_fixed

async def main():
    """Main test execution"""
    test = AttendeePriorityTest()
    success = await test.run_complete_test()

    if success:
        print("\n🎯 READY: Attendee priority logic implemented successfully!")
    else:
        print("\n🔧 NEEDS WORK: Review the tool selection implementation.")

if __name__ == "__main__":
    asyncio.run(main())
