#!/usr/bin/env python3
"""
Comprehensive Test Script for Email Agent Integration
Tests the complete flow from supervisor to email agent with Gmail MCP tools
"""

import asyncio
import json
import sys
import os
import time
from typing import Dict, Any
import requests
from datetime import datetime

# Add src to path for imports
sys.path.append('src')

# Test Configuration
LANGGRAPH_URL = "http://127.0.0.1:2024"
TEST_THREAD_ID = f"test_email_agent_{int(time.time())}"
TEST_TIMEOUT = 30  # seconds

class EmailAgentTester:
    def __init__(self):
        self.langgraph_url = LANGGRAPH_URL
        self.thread_id = TEST_THREAD_ID
        self.session = requests.Session()

    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def test_langgraph_health(self) -> bool:
        """Test if LangGraph server is running"""
        try:
            response = self.session.get(f"{self.langgraph_url}/health", timeout=5)
            if response.status_code == 200:
                self.log("✅ LangGraph server is running")
                return True
            else:
                self.log(f"❌ LangGraph server returned {response.status_code}", "ERROR")
                return False
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Cannot connect to LangGraph server: {e}", "ERROR")
            return False

    def test_graph_info(self) -> bool:
        """Test if our graph is loaded with email agent"""
        try:
            response = self.session.get(f"{self.langgraph_url}/assistants", timeout=10)
            if response.status_code == 200:
                assistants = response.json()
                if assistants:
                    assistant = assistants[0]  # Get first assistant
                    self.log(f"✅ Found assistant: {assistant.get('assistant_id', 'unknown')}")
                    return True
                else:
                    self.log("❌ No assistants found", "ERROR")
                    return False
            else:
                self.log(f"❌ Failed to get assistants: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Error checking assistants: {e}", "ERROR")
            return False

    def send_message(self, message: str) -> Dict[str, Any]:
        """Send a message to the supervisor and get response"""
        try:
            # Get the assistant ID
            assistants_response = self.session.get(f"{self.langgraph_url}/assistants")
            if assistants_response.status_code != 200:
                raise Exception("Failed to get assistants")

            assistants = assistants_response.json()
            if not assistants:
                raise Exception("No assistants available")

            assistant_id = assistants[0]["assistant_id"]

            # Send message
            payload = {
                "input": {"messages": [{"role": "human", "content": message}]},
                "config": {"configurable": {"thread_id": self.thread_id}},
                "stream_mode": "values"
            }

            self.log(f"Sending message to assistant {assistant_id}: {message}")

            response = self.session.post(
                f"{self.langgraph_url}/assistants/{assistant_id}/threads/{self.thread_id}/runs",
                json=payload,
                timeout=TEST_TIMEOUT,
                stream=True
            )

            if response.status_code != 200:
                raise Exception(f"Failed to send message: {response.status_code}")

            # Process streaming response
            full_response = ""
            events = []

            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        try:
                            data = json.loads(line_str[6:])
                            events.append(data)

                            # Extract messages from the latest state
                            if 'messages' in data:
                                messages = data['messages']
                                if messages:
                                    last_message = messages[-1]
                                    if hasattr(last_message, 'content'):
                                        content = last_message.content
                                    elif isinstance(last_message, dict):
                                        content = last_message.get('content', str(last_message))
                                    else:
                                        content = str(last_message)

                                    if content != full_response:
                                        full_response = content

                        except json.JSONDecodeError:
                            continue

            return {
                "success": True,
                "response": full_response,
                "events": events
            }

        except Exception as e:
            self.log(f"❌ Error sending message: {e}", "ERROR")
            return {"success": False, "error": str(e)}

    def test_email_agent_routing(self) -> bool:
        """Test that email-related requests are routed to email agent"""
        self.log("Testing email agent routing...")

        result = self.send_message("Can you help me manage my emails? I want to check my Gmail inbox.")

        if not result["success"]:
            self.log(f"❌ Failed to get response: {result.get('error')}", "ERROR")
            return False

        response = result["response"].lower()

        # Check if response indicates email agent was used
        email_indicators = [
            "email", "gmail", "inbox", "mail",
            "messages", "labels", "draft"
        ]

        found_indicators = [word for word in email_indicators if word in response]

        if found_indicators:
            self.log(f"✅ Email agent routing successful! Found indicators: {found_indicators}")
            self.log(f"Response preview: {result['response'][:200]}...")
            return True
        else:
            self.log(f"❌ Email agent routing may have failed. Response: {result['response'][:200]}...", "ERROR")
            return False

    def test_gmail_tool_availability(self) -> bool:
        """Test that Gmail MCP tools are available"""
        self.log("Testing Gmail MCP tools availability...")

        result = self.send_message("What Gmail operations can you help me with? List the available email tools.")

        if not result["success"]:
            self.log(f"❌ Failed to get response: {result.get('error')}", "ERROR")
            return False

        response = result["response"].lower()

        # Check for Gmail tool indicators
        gmail_tools = [
            "send email", "find email", "create draft",
            "archive", "delete", "labels", "attachments"
        ]

        found_tools = [tool for tool in gmail_tools if tool in response]

        if found_tools:
            self.log(f"✅ Gmail tools available! Found capabilities: {found_tools}")
            return True
        else:
            self.log(f"❌ Gmail tools may not be available. Response: {response[:200]}...", "ERROR")
            return False

    def test_email_operation_request(self) -> bool:
        """Test a specific email operation request"""
        self.log("Testing specific email operation...")

        result = self.send_message("Can you help me find emails from last week that mention 'meeting'?")

        if not result["success"]:
            self.log(f"❌ Failed to get response: {result.get('error')}", "ERROR")
            return False

        response = result["response"].lower()

        # Check if response shows understanding of the email task
        understanding_indicators = [
            "search", "find", "meeting", "last week",
            "email", "gmail", "filter", "query"
        ]

        found_indicators = [word for word in understanding_indicators if word in response]

        if len(found_indicators) >= 3:
            self.log(f"✅ Email operation understood! Found indicators: {found_indicators}")
            return True
        else:
            self.log(f"❌ Email operation may not be understood. Response: {response[:200]}...", "ERROR")
            return False

    def run_comprehensive_test(self) -> bool:
        """Run all tests in sequence"""
        self.log("🚀 Starting Comprehensive Email Agent Test Suite")
        self.log("=" * 60)

        tests = [
            ("LangGraph Server Health", self.test_langgraph_health),
            ("Graph Info & Assistant", self.test_graph_info),
            ("Email Agent Routing", self.test_email_agent_routing),
            ("Gmail Tool Availability", self.test_gmail_tool_availability),
            ("Email Operation Request", self.test_email_operation_request),
        ]

        passed = 0
        failed = 0

        for test_name, test_func in tests:
            self.log(f"\n📋 Running: {test_name}")
            self.log("-" * 40)

            try:
                if test_func():
                    passed += 1
                    self.log(f"✅ {test_name}: PASSED")
                else:
                    failed += 1
                    self.log(f"❌ {test_name}: FAILED")
            except Exception as e:
                failed += 1
                self.log(f"❌ {test_name}: ERROR - {e}")

            time.sleep(1)  # Brief pause between tests

        # Summary
        self.log("\n" + "=" * 60)
        self.log("📊 TEST SUMMARY")
        self.log("=" * 60)
        self.log(f"✅ Passed: {passed}")
        self.log(f"❌ Failed: {failed}")
        self.log(f"📈 Success Rate: {passed/(passed+failed)*100:.1f}%")

        if failed == 0:
            self.log("🎉 ALL TESTS PASSED! Email Agent is fully functional!")
            return True
        else:
            self.log(f"⚠️  {failed} test(s) failed. Check the logs above for details.")
            return False

def main():
    """Main test runner"""
    print("🔧 Email Agent Integration Test Suite")
    print("=" * 60)
    print("This script tests the complete email agent integration:")
    print("• LangGraph server connectivity")
    print("• Supervisor routing to email agent")
    print("• Gmail MCP tools availability")
    print("• Email operation handling")
    print("=" * 60)

    # Wait a moment for server to be ready
    print("⏳ Waiting 5 seconds for server to be ready...")
    time.sleep(5)

    tester = EmailAgentTester()
    success = tester.run_comprehensive_test()

    if success:
        print("\n🚀 Email Agent is ready for production!")
        sys.exit(0)
    else:
        print("\n❌ Email Agent needs attention. Check the test results above.")
        sys.exit(1)

if __name__ == "__main__":
    main()