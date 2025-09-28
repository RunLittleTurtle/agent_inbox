#!/usr/bin/env python3
"""
Test script to verify calendar booking approval workflow
with the new centralized prompts from prompt.py
"""

import asyncio
import httpx
import json
from datetime import datetime, timedelta

async def test_booking_workflow():
    """Test a booking request that should trigger approval workflow"""

    # Test creating a meeting for tomorrow
    tomorrow = datetime.now() + timedelta(days=1)
    meeting_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)

    test_message = f"Schedule a meeting with team tomorrow at 2pm to discuss project updates"

    # Send to the calendar agent through supervisor
    async with httpx.AsyncClient() as client:
        print("🧪 Testing booking approval workflow...")
        print(f"📅 Request: {test_message}")

        response = await client.post(
            "http://localhost:2024/threads",
            json={
                "assistant_id": "fe096781-5601-53d2-b2f6-0d3403f7e9ca",
                "metadata": {}
            }
        )

        if response.status_code == 200:
            thread = response.json()
            thread_id = thread["thread_id"]
            print(f"✅ Thread created: {thread_id}")

            # Send the booking request
            response = await client.post(
                f"http://localhost:2024/threads/{thread_id}/runs",
                json={
                    "assistant_id": "fe096781-5601-53d2-b2f6-0d3403f7e9ca",
                    "input": {
                        "messages": [
                            {
                                "role": "human",
                                "content": test_message
                            }
                        ]
                    }
                }
            )

            if response.status_code == 200:
                print("✅ Request sent successfully")

                # Stream the response
                async with client.stream(
                    "GET",
                    f"http://localhost:2024/threads/{thread_id}/runs/stream",
                    params={"assistant_id": "fe096781-5601-53d2-b2f6-0d3403f7e9ca"}
                ) as stream:
                    print("\n📝 Monitoring response for routing prompts...")
                    async for line in stream.aiter_lines():
                        if line.startswith("data: "):
                            try:
                                data = json.loads(line[6:])
                                if "messages" in str(data):
                                    print(f"   → {data}")
                            except:
                                pass
            else:
                print(f"❌ Failed to send request: {response.status_code}")
        else:
            print(f"❌ Failed to create thread: {response.status_code}")

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Calendar Booking Approval with New Prompts")
    print("=" * 60)
    asyncio.run(test_booking_workflow())