"""
LangGraph Application Entry Point with LangFuse Integration (2025 Best Practices)

This module wraps the main graph to automatically inject LangFuse tracing following
2025 best practices from LangFuse documentation:

1. Singleton CallbackHandler (reused across requests)
2. User ID passed via metadata (not constructor)
3. Session ID from thread_id (for conversation tracking)

Architecture:
    1. User invokes graph via LangGraph Platform
    2. Extract user_id and thread_id from config
    3. Load user's LangFuse keys from Supabase
    4. Get singleton handler for those keys
    5. Inject handler + metadata into config
    6. Traces tagged with user_id and session_id automatically

Export:
    app: Wrapped graph with automatic LangFuse integration
"""
import asyncio
from typing import Any, Dict
from langchain_core.runnables import RunnableConfig
from eaia.main.graph import graph as original_graph
from eaia.main.config import get_config
from shared_utils.langfuse_callback import get_singleton_handler


class LangFuseWrappedGraph:
    """
    Wrapper around LangGraph that automatically injects LangFuse callbacks.

    Implements 2025 best practices:
    - Singleton handlers (one per unique credentials)
    - Metadata-based user/session tracking
    - Proper conversation threading
    """

    def __init__(self, graph):
        self.graph = graph

    async def ainvoke(self, input_data: Dict[str, Any], config: RunnableConfig = None):
        """
        Async invoke with automatic LangFuse callback and metadata injection.

        2025 Best Practice:
        - Gets singleton handler (reused across requests)
        - Passes user_id via metadata.langfuse_user_id
        - Passes thread_id via metadata.langfuse_session_id

        Args:
            input_data: Input to the graph
            config: LangGraph configuration (contains user_id, thread_id)

        Returns:
            Graph execution result
        """
        config = config or {}

        # Extract user_id and thread_id from config
        configurable = config.get("configurable", {})
        user_id = configurable.get("user_id")
        thread_id = configurable.get("thread_id")

        # Load user configuration (includes LangFuse keys)
        config_data = await get_config(config)

        # Get singleton LangFuse handler if configured
        langfuse_handler = get_singleton_handler(config_data) if config_data else None

        if langfuse_handler and user_id:
            # Inject callback into config
            if "callbacks" not in config:
                config["callbacks"] = []
            if isinstance(config["callbacks"], list):
                config["callbacks"].append(langfuse_handler)

            # Inject metadata for user/session tracking (2025 best practice)
            if "metadata" not in config:
                config["metadata"] = {}

            # Set LangFuse-specific metadata fields
            config["metadata"]["langfuse_user_id"] = user_id
            if thread_id:
                config["metadata"]["langfuse_session_id"] = thread_id
            config["metadata"]["langfuse_tags"] = ["production", "agent_inbox"]

            print(f" [LangFuse] Tracing with user_id={user_id}, session_id={thread_id}")

        # Invoke original graph with callbacks + metadata
        return await self.graph.ainvoke(input_data, config=config)

    def invoke(self, input_data: Dict[str, Any], config: RunnableConfig = None):
        """
        Sync invoke with automatic LangFuse callback injection.

        Args:
            input_data: Input to the graph
            config: LangGraph configuration (contains user_id)

        Returns:
            Graph execution result
        """
        # Run async version in event loop
        return asyncio.run(self.ainvoke(input_data, config))

    def __getattr__(self, name):
        """
        Forward all other attributes to the original graph.

        This makes the wrapper transparent - LangGraph Platform can call
        any method it expects on a compiled graph.
        """
        return getattr(self.graph, name)


# Export wrapped graph as 'app' for LangGraph Platform
app = LangFuseWrappedGraph(original_graph)
