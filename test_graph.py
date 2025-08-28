#!/usr/bin/env python3
"""
Simple test to verify the email agent graph works correctly.
This will create a minimal test run to generate traces for Agent Chat UI.
"""

import asyncio
from src.graph import graph, AgentState, EmailMessage
from langchain_core.messages import HumanMessage

async def test_graph():
    """Test the email agent graph with a simple message"""
    
    print("🧪 Testing email agent graph...")
    
    # Create a simple test state
    test_email = EmailMessage(
        id="test-001",
        subject="Test Email for Graph Verification", 
        body="This is a simple test to verify the graph works correctly.",
        sender="test@example.com",
        recipients=["assistant@example.com"],
        timestamp="2025-08-28T13:00:00Z"
    )
    
    initial_state = AgentState(
        email=test_email,
        messages=[HumanMessage(content="Process this test email")]
    )
    
    try:
        # Run the graph
        print("▶️  Running graph...")
        result = await graph.ainvoke(
            initial_state,
            config={"configurable": {"thread_id": "test-thread-001"}}
        )
        
        print("✅ Graph execution successful!")
        print(f"📊 Status: {result.status}")
        print(f"🎯 Intent: {result.intent}")
        print(f"💬 Messages: {len(result.messages)}")
        print(f"📋 Agent outputs: {len(result.output)}")
        
        # Show agent outputs
        for i, output in enumerate(result.output):
            print(f"  Agent {i+1}: {output.agent_name} (confidence: {output.confidence})")
        
        return True
        
    except Exception as e:
        print(f"❌ Graph execution failed: {e}")
        return False

def test_graph_sync():
    """Synchronous version for easier CLI usage"""
    
    print("🧪 Testing email agent graph (sync)...")
    
    # Create a simple test state  
    test_email = EmailMessage(
        id="test-002",
        subject="Sync Test Email", 
        body="Testing sync execution of the email graph.",
        sender="test@example.com", 
        recipients=["assistant@example.com"],
        timestamp="2025-08-28T13:00:00Z"
    )
    
    initial_state = AgentState(
        email=test_email,
        messages=[HumanMessage(content="Process this test email synchronously")]
    )
    
    try:
        # Run the graph synchronously
        print("▶️  Running graph synchronously...")
        result = graph.invoke(
            initial_state,
            config={"configurable": {"thread_id": "test-thread-002"}}
        )
        
        print("✅ Graph execution successful!")
        print(f"📊 Result type: {type(result)}")
        
        # Handle both dict and AgentState results
        if isinstance(result, dict):
            status = result.get('status', 'unknown')
            intent = result.get('intent', 'unknown') 
            messages = result.get('messages', [])
            output = result.get('output', [])
        else:
            status = result.status
            intent = result.intent
            messages = result.messages
            output = result.output
            
        print(f"📊 Status: {status}")
        print(f"🎯 Intent: {intent}")
        print(f"💬 Messages: {len(messages)}")
        print(f"📋 Agent outputs: {len(output)}")
        
        # Show the last message
        if messages:
            last_msg = messages[-1]
            print(f"🔚 Last message: {last_msg.content[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Graph execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Run synchronous test
    success = test_graph_sync()
    
    if success:
        print("\n🎉 Graph test completed successfully!")
        print("💡 The graph is working and should now have traces for Agent Chat UI")
        print("🔗 You can now connect Agent Chat UI to: http://localhost:2024")
        print("📊 Graph ID: email_agent")
    else:
        print("\n💥 Graph test failed - check the error above")
