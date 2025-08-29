"""
Enhanced LangGraph SDK Streaming Service
Implements multi-mode streaming with real-time updates, token streaming, and custom events.
"""

import os
import sys
import asyncio
import json
from typing import Dict, Any, List, Optional, AsyncIterator, Union
from datetime import datetime
from dataclasses import dataclass

# Add local libraries to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../library/langgraph'))

try:
    from langgraph_sdk import get_client
    LANGGRAPH_SDK_AVAILABLE = True
except ImportError:
    LANGGRAPH_SDK_AVAILABLE = False
    print("⚠️ langgraph_sdk not available, using fallback streaming")


@dataclass
class StreamEvent:
    """Structured streaming event"""
    event_type: str
    data: Dict[str, Any]
    timestamp: str
    node: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class EnhancedStreamService:
    """Enhanced streaming service using direct LangGraph SDK with multi-mode support"""
    
    def __init__(self, api_url: str = "http://localhost:2024", api_key: Optional[str] = None):
        self.api_url = api_url
        self.api_key = api_key
        self.client = None
        
        if LANGGRAPH_SDK_AVAILABLE:
            try:
                self.client = get_client(url=api_url, api_key=api_key)
                print(f"✅ LangGraph SDK client initialized: {api_url}")
            except Exception as e:
                print(f"❌ Failed to initialize LangGraph SDK client: {e}")
                self.client = None
        
    async def create_thread(self) -> Optional[str]:
        """Create a new thread and return thread_id"""
        if not self.client:
            return None
            
        try:
            thread = await self.client.threads.create()
            return thread.get("thread_id")
        except Exception as e:
            print(f"❌ Failed to create thread: {e}")
            return None
    
    async def stream_multi_mode(
        self, 
        thread_id: str, 
        assistant_id: str, 
        input_data: Dict[str, Any],
        stream_modes: List[str] = None
    ) -> AsyncIterator[StreamEvent]:
        """
        Stream with multiple modes: updates, messages-tuple, custom
        Yields structured StreamEvent objects
        """
        
        if not self.client:
            yield StreamEvent(
                event_type="error",
                data={"message": "LangGraph SDK client not available"},
                timestamp=datetime.now().isoformat()
            )
            return
            
        if stream_modes is None:
            stream_modes = ["updates", "messages-tuple", "custom"]
        
        try:
            async for chunk in self.client.runs.stream(
                thread_id=thread_id,
                assistant_id=assistant_id,
                input=input_data,
                stream_mode=stream_modes
            ):
                # Process different types of streaming events
                event = self._process_chunk(chunk)
                if event:
                    yield event
                    
        except Exception as e:
            yield StreamEvent(
                event_type="error",
                data={"message": f"Streaming error: {str(e)}"},
                timestamp=datetime.now().isoformat()
            )
    
    def _process_chunk(self, chunk) -> Optional[StreamEvent]:
        """Process different types of streaming chunks into StreamEvent objects"""
        
        try:
            # Handle different chunk types based on LangGraph SDK structure
            if hasattr(chunk, 'event'):
                event_type = chunk.event
                
                if event_type == "updates":
                    # Node execution updates
                    return StreamEvent(
                        event_type="node_update",
                        data=chunk.data,
                        timestamp=datetime.now().isoformat(),
                        node=self._extract_node_name(chunk.data)
                    )
                
                elif event_type == "messages":
                    # Token streaming with metadata
                    if hasattr(chunk, 'data') and len(chunk.data) >= 2:
                        message_chunk, metadata = chunk.data
                        return StreamEvent(
                            event_type="token",
                            data={
                                "content": message_chunk.get("content", "") if isinstance(message_chunk, dict) else str(message_chunk),
                                "message_chunk": message_chunk,
                                "metadata": metadata
                            },
                            timestamp=datetime.now().isoformat(),
                            node=metadata.get("langgraph_node") if isinstance(metadata, dict) else None,
                            metadata=metadata if isinstance(metadata, dict) else None
                        )
                
                elif event_type == "custom":
                    # Custom events from graph nodes
                    return StreamEvent(
                        event_type="custom",
                        data=chunk.data,
                        timestamp=datetime.now().isoformat(),
                        node=chunk.data.get("node") if isinstance(chunk.data, dict) else None
                    )
                    
            # Fallback for other chunk types
            return StreamEvent(
                event_type="raw",
                data={"chunk": str(chunk)},
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            return StreamEvent(
                event_type="error",
                data={"message": f"Chunk processing error: {str(e)}", "chunk": str(chunk)},
                timestamp=datetime.now().isoformat()
            )
    
    def _extract_node_name(self, data) -> Optional[str]:
        """Extract node name from update data"""
        if isinstance(data, dict):
            # Look for node name in various possible locations
            for key in data.keys():
                if isinstance(key, str) and key not in ["messages", "output", "status"]:
                    return key
        return None
    
    async def get_thread_history(self, thread_id: str) -> List[Dict[str, Any]]:
        """Get thread message history"""
        if not self.client:
            return []
            
        try:
            # This would depend on the actual LangGraph SDK API
            # For now, return empty list as placeholder
            return []
        except Exception as e:
            print(f"❌ Failed to get thread history: {e}")
            return []


# Singleton instance for the application
_stream_service = None

def get_stream_service(api_url: str = "http://localhost:2024", api_key: Optional[str] = None) -> EnhancedStreamService:
    """Get singleton stream service instance"""
    global _stream_service
    if _stream_service is None:
        _stream_service = EnhancedStreamService(api_url=api_url, api_key=api_key)
    return _stream_service


# Example usage for testing
async def test_streaming():
    """Test the enhanced streaming service"""
    service = get_stream_service()
    
    # Create thread
    thread_id = await service.create_thread()
    if not thread_id:
        print("❌ Could not create thread")
        return
    
    print(f"✅ Created thread: {thread_id}")
    
    # Test streaming
    async for event in service.stream_multi_mode(
        thread_id=thread_id,
        assistant_id="agent",
        input_data={"messages": [{"role": "user", "content": "Hello, test streaming"}]}
    ):
        print(f"📡 Stream Event: {event.event_type} - {event.data}")


if __name__ == "__main__":
    asyncio.run(test_streaming())
