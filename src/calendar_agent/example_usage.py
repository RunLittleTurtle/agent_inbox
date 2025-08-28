"""
Calendar Agent Example Usage and Testing
Demonstrates how to use the calendar agent with MCP integration.
"""
import asyncio
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from .supervisor_integration import (
    create_calendar_supervisor_system,
    CalendarAgentIntegration,
    CalendarAgentConfig
)
from .subgraph import create_calendar_agent_subgraph
from .state import CalendarAgentState

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_calendar_agent_standalone():
    """Test the calendar agent as a standalone subgraph."""
    logger.info("🧪 Testing Calendar Agent Standalone...")
    
    # Check configuration
    config_status = CalendarAgentConfig.get_config_status()
    if not config_status["all_configured"]:
        logger.error(f"❌ Missing configuration: {config_status['missing_vars']}")
        return False
    
    try:
        # Create calendar agent
        model = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
        checkpointer = MemorySaver()
        
        calendar_agent = await create_calendar_agent_subgraph(
            model=model,
            name="calendar_agent",
            checkpointer=checkpointer
        )
        
        # Test cases
        test_cases = [
            "List my calendar events for today",
            "Show me my schedule for this week", 
            "Check my availability for tomorrow at 2 PM",
            "Create a meeting for Friday at 10 AM about project review"
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"\n📝 Test Case {i}: {test_case}")
            
            # Prepare initial state
            initial_state: CalendarAgentState = {
                "messages": [HumanMessage(content=test_case)],
                "calendar_events": [],
                "calendar_query": None,
                "calendar_analysis": None,
                "output": [],
                "user_email": config_status["user_email"],
                "calendar_ids": ["primary"],
                "timezone": "UTC",
                "mcp_tools_loaded": False,
                "mcp_session_active": False,
                "requires_human_approval": False,
                "human_feedback": None
            }
            
            # Run calendar agent
            result = await calendar_agent.ainvoke(
                initial_state,
                config={"thread_id": f"test_{i}"}
            )
            
            # Display results
            if result.get("messages"):
                last_message = result["messages"][-1]
                logger.info(f"✅ Response: {last_message.content}")
            
            if result.get("calendar_analysis"):
                analysis = result["calendar_analysis"]
                logger.info(f"📊 Analysis: {analysis.action_taken} (Success: {analysis.success})")
            
            if result.get("calendar_events"):
                events = result["calendar_events"]
                logger.info(f"📅 Events Found: {len(events)}")
        
        logger.info("✅ Standalone calendar agent tests completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Standalone test failed: {e}")
        return False


async def test_calendar_supervisor_system():
    """Test the calendar agent integrated with supervisor system."""
    logger.info("🧪 Testing Calendar Supervisor System...")
    
    try:
        # Create supervisor system with calendar agent
        model = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
        checkpointer = MemorySaver()
        
        supervisor_system = await create_calendar_supervisor_system(
            model=model,
            checkpointer=checkpointer
        )
        
        # Test supervisor routing
        test_requests = [
            "What's on my calendar today?",
            "Schedule a meeting with the team for next Tuesday at 3 PM",
            "Am I free tomorrow afternoon?",
            "Cancel my 2 PM meeting on Friday"
        ]
        
        for i, request in enumerate(test_requests, 1):
            logger.info(f"\n📝 Supervisor Test {i}: {request}")
            
            result = await supervisor_system.ainvoke(
                {"messages": [HumanMessage(content=request)]},
                config={"thread_id": f"supervisor_test_{i}"}
            )
            
            if result.get("messages"):
                last_message = result["messages"][-1]
                logger.info(f"✅ Supervisor Response: {last_message.content}")
        
        logger.info("✅ Supervisor system tests completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Supervisor test failed: {e}")
        return False


async def test_calendar_integration_helper():
    """Test the CalendarAgentIntegration helper class."""
    logger.info("🧪 Testing Calendar Integration Helper...")
    
    try:
        integration = CalendarAgentIntegration()
        
        # Initialize integration
        model = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
        success = await integration.initialize(model=model)
        
        if not success:
            logger.error("❌ Integration initialization failed")
            return False
        
        # Test request detection
        test_messages = [
            ("What's my schedule today?", True),
            ("Book a meeting for tomorrow", True), 
            ("What's the weather like?", False),
            ("Check my calendar availability", True),
            ("Send an email to John", False)
        ]
        
        for message, expected in test_messages:
            detected = integration.is_calendar_request(message)
            status = "✅" if detected == expected else "❌"
            logger.info(f"{status} '{message}' -> Calendar request: {detected}")
        
        # Test direct calendar processing
        calendar_request = "Show me my events for this week"
        result = await integration.process_calendar_request(
            calendar_request,
            context={"user_email": os.getenv("USER_GOOGLE_EMAIL")}
        )
        
        if result.get("success"):
            logger.info("✅ Direct calendar processing successful")
        else:
            logger.error(f"❌ Direct processing failed: {result.get('error')}")
        
        logger.info("✅ Integration helper tests completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Integration test failed: {e}")
        return False


def display_configuration_status():
    """Display current configuration status."""
    logger.info("📋 Configuration Status:")
    
    config = CalendarAgentConfig.get_config_status()
    
    for var, configured in config["validation_details"].items():
        status = "✅" if configured else "❌"
        logger.info(f"  {status} {var}")
    
    if config["pipedream_server"]:
        logger.info(f"  📡 Pipedream MCP Server: {config['pipedream_server']}")
    
    if config["user_email"]:
        logger.info(f"  👤 User Email: {config['user_email']}")
    
    if not config["all_configured"]:
        logger.warning(f"  ⚠️  Missing: {', '.join(config['missing_vars'])}")
        logger.info("  💡 Please set missing environment variables in .env file")


async def run_all_tests():
    """Run all calendar agent tests."""
    logger.info("🚀 Starting Calendar Agent Tests...")
    
    # Display configuration
    display_configuration_status()
    
    config = CalendarAgentConfig.get_config_status()
    if not config["all_configured"]:
        logger.error("❌ Cannot run tests - missing required configuration")
        return
    
    # Run tests
    tests = [
        ("Standalone Calendar Agent", test_calendar_agent_standalone),
        ("Calendar Supervisor System", test_calendar_supervisor_system), 
        ("Calendar Integration Helper", test_calendar_integration_helper)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            success = await test_func()
            results[test_name] = success
        except Exception as e:
            logger.error(f"❌ Test '{test_name}' failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("📊 Test Summary")
    logger.info(f"{'='*50}")
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"  {status}: {test_name}")
    
    logger.info(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Calendar agent is ready to use.")
    else:
        logger.warning("⚠️  Some tests failed. Check logs for details.")


async def demo_calendar_operations():
    """Demonstrate calendar operations with sample data."""
    logger.info("🎬 Calendar Agent Demo")
    
    config = CalendarAgentConfig.get_config_status()
    if not config["all_configured"]:
        logger.error("❌ Demo requires proper configuration")
        return
    
    try:
        # Create integration
        integration = CalendarAgentIntegration()
        model = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
        await integration.initialize(model=model)
        
        # Demo scenarios
        scenarios = [
            {
                "name": "📅 List Today's Events",
                "request": "What meetings do I have today?",
                "description": "Retrieves today's calendar events"
            },
            {
                "name": "🔍 Check Availability", 
                "request": "Am I available tomorrow at 3 PM for a 1-hour meeting?",
                "description": "Checks calendar availability for scheduling"
            },
            {
                "name": "➕ Schedule New Meeting",
                "request": "Schedule a team standup for Monday at 9 AM",
                "description": "Creates a new calendar event"
            },
            {
                "name": "📋 Weekly Overview",
                "request": "Show me my schedule for next week",
                "description": "Lists events for the upcoming week"
            }
        ]
        
        for scenario in scenarios:
            logger.info(f"\n{'='*60}")
            logger.info(f"{scenario['name']}")
            logger.info(f"{'='*60}")
            logger.info(f"Description: {scenario['description']}")
            logger.info(f"Request: '{scenario['request']}'")
            logger.info("-" * 60)
            
            # Process request
            result = await integration.process_calendar_request(
                scenario["request"],
                context={
                    "user_email": config["user_email"],
                    "timezone": "UTC"
                }
            )
            
            if result.get("success") and result.get("messages"):
                response = result["messages"][-1].content
                logger.info(f"Response: {response}")
            else:
                error = result.get("error", "Unknown error")
                logger.error(f"❌ Error: {error}")
                
        logger.info("\n🎬 Demo completed!")
        
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "demo":
            asyncio.run(demo_calendar_operations())
        elif sys.argv[1] == "config":
            display_configuration_status()
        else:
            print("Usage: python example_usage.py [demo|config]")
    else:
        asyncio.run(run_all_tests())
