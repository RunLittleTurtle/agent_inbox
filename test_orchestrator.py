#!/usr/bin/env python3
"""
Test script for Complete Job Search Orchestrator
Tests the orchestrator functionality and validates the workflow
"""

import sys
import os
import asyncio
from pathlib import Path

# Add the src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# Now import the orchestrator
try:
    from job_search_agent.job_search_orchestrator import (
        create_complete_job_search_orchestrator,
        create_orchestrator_instance,
        JobSearchOrchestrator
    )
    from job_search_agent.state import JobSearchState
    from langchain_core.messages import HumanMessage
    print("✅ All imports successful!")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


def test_orchestrator_creation():
    """Test basic orchestrator creation"""
    print("\n🧪 Test 1: Orchestrator Creation")

    try:
        # Test instance creation
        orchestrator = create_orchestrator_instance()
        print("✅ Orchestrator instance created")

        # Test workflow creation
        workflow = create_complete_job_search_orchestrator()
        print("✅ Complete workflow created")

        return True

    except Exception as e:
        print(f"❌ Creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_orchestrator_components():
    """Test individual orchestrator components"""
    print("\n🧪 Test 2: Component Testing")

    try:
        orchestrator = JobSearchOrchestrator()

        # Test React agent creation
        agent = orchestrator.create_react_agent()
        print("✅ React agent created")

        # Test graph building
        graph = orchestrator.build_graph()
        print("✅ Graph built successfully")

        # Test compilation
        compiled = orchestrator.compile_workflow()
        print("✅ Workflow compiled")

        return True

    except Exception as e:
        print(f"❌ Component test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_simple_invocation():
    """Test simple workflow invocation"""
    print("\n🧪 Test 3: Simple Invocation")

    try:
        # Create orchestrator
        orchestrator = JobSearchOrchestrator()
        workflow = orchestrator.create_complete_workflow()

        # Prepare test input
        test_input = {
            "messages": [HumanMessage(content="Hello, I need help with my job search")]
        }

        # Test configuration
        config = {"configurable": {"thread_id": "test_thread_123"}}

        print("🚀 Invoking workflow...")

        # Invoke workflow
        result = await workflow.ainvoke(test_input, config)

        print("✅ Workflow invocation successful!")
        print(f"📊 Result keys: {list(result.keys())}")
        print(f"📨 Messages: {len(result.get('messages', []))}")

        # Print last message if available
        messages = result.get('messages', [])
        if messages:
            last_message = messages[-1]
            print(f"🗨️ Last message: {last_message.content[:100]}...")

        return True

    except Exception as e:
        print(f"❌ Invocation failed: {e}")
        import traceback
        traceback.print_exc()
        return False




def test_factory_functions():
    """Test factory functions"""
    print("\n🧪 Test 4: Factory Functions")

    try:
        # Test complete orchestrator factory
        workflow1 = create_complete_job_search_orchestrator()
        print("✅ Factory function 1 successful")

        # Test instance factory
        instance = create_orchestrator_instance()
        print("✅ Factory function 2 successful")

        # Test custom config
        custom_config = {
            "model": "gpt-4o",
            "temperature": 0,
            "max_tokens": 1000
        }
        workflow2 = create_complete_job_search_orchestrator(custom_config)
        print("✅ Custom config factory successful")

        return True

    except Exception as e:
        print(f"❌ Factory functions failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("🚀 Testing Complete Job Search Orchestrator")
    print("=" * 50)

    results = []

    # Run tests
    results.append(test_orchestrator_creation())
    results.append(test_orchestrator_components())
    results.append(await test_simple_invocation())
    results.append(test_factory_functions())

    # Summary
    print("\n" + "=" * 50)
    print("🏁 Test Results Summary")

    passed = sum(results)
    total = len(results)

    print(f"✅ Passed: {passed}/{total}")

    if passed == total:
        print("🎉 All tests passed! The orchestrator is working correctly.")
    else:
        print(f"❌ {total - passed} tests failed. Check the logs above.")

    return passed == total


if __name__ == "__main__":
    """Main execution"""
    print("🔧 Setting up test environment...")

    # Check if we're in the right directory
    if not (Path.cwd() / "src" / "job_search_agent").exists():
        print("❌ Please run this script from the project root directory")
        sys.exit(1)

    print("📁 Project structure validated")

    # Run async tests
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
