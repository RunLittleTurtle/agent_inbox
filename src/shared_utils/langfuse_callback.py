"""
LangFuse Integration for User-Scoped and Team-Based Tracing (2025 Best Practices)

This module provides singleton LangFuse callback handlers following 2025 best practices:
- Singleton pattern: One handler per user credentials (prevents memory leaks)
- Metadata-based user/session tracking (user_id passed via config.metadata)
- Team-based and individual tracing support

Architecture:
    - Sliding Tools Team: 3 users share same API keys → see each other's traces
    - Individual Users: Each has own API keys → see only their traces
    - Developer: Uses LangSmith → sees all traces across all users

2025 Best Practices (per LangFuse docs):
    1. Singleton CallbackHandler - reuse across requests
    2. User ID via metadata - NOT constructor (deprecated)
    3. Session ID for conversations - also via metadata

Usage:
    from shared_utils.langfuse_callback import get_singleton_handler

    # At startup or first use:
    config_data = await get_config(config)
    handler = get_singleton_handler(config_data)

    # In graph invocation:
    result = await graph.ainvoke(
        input_data,
        config={
            "callbacks": [handler] if handler else [],
            "metadata": {
                "langfuse_user_id": "clerk_user_xxx",
                "langfuse_session_id": "thread_yyy",  # Optional
                "langfuse_tags": ["production", "agent_inbox"]
            }
        }
    )
"""
from typing import Optional, Dict, Any, Tuple

# Global cache for singleton handlers
# Key: (public_key, secret_key, host) tuple
# Value: CallbackHandler instance
_HANDLER_CACHE: Dict[Tuple[str, str, str], Any] = {}


def get_singleton_handler(config_data: Dict[str, Any]) -> Optional[Any]:
    """
    Get or create a singleton LangFuse CallbackHandler (2025 best practice).

    This function implements the singleton pattern recommended by LangFuse:
    - Creates ONE handler per unique set of credentials
    - Reuses handlers across requests (prevents memory leaks)
    - User ID and session ID passed via metadata, NOT constructor

    Team-Based Tracing:
        - Users with same API keys → same handler → shared traces
        - Users with different API keys → different handlers → isolated traces

    Args:
        config_data: Dictionary containing user configuration from Supabase
                     Expected structure: {
                         "langfuse_public_key": "pk-lf-...",
                         "langfuse_secret_key": "sk-lf-...",
                         "langfuse_host": "https://cloud.langfuse.com"
                     }

    Returns:
        Singleton LangFuse CallbackHandler, or None if not configured

    Example:
        >>> config_data = await get_config(config)
        >>> handler = get_singleton_handler(config_data)
        >>> graph.ainvoke(
        ...     input_data,
        ...     config={
        ...         "callbacks": [handler],
        ...         "metadata": {
        ...             "langfuse_user_id": "user_123",
        ...             "langfuse_session_id": "thread_abc"
        ...         }
        ...     }
        ... )
    """
    # Extract LangFuse credentials
    public_key = config_data.get("langfuse_public_key")
    secret_key = config_data.get("langfuse_secret_key")
    host = config_data.get("langfuse_host", "https://cloud.langfuse.com")

    # Graceful degradation: Return None if not configured
    if not public_key or not secret_key:
        return None

    # Create cache key from credentials
    cache_key = (public_key, secret_key, host)

    # Return cached handler if exists (singleton pattern)
    if cache_key in _HANDLER_CACHE:
        return _HANDLER_CACHE[cache_key]

    # Create new handler (only once per unique credentials)
    try:
        from langfuse.langchain import CallbackHandler

        # Create handler WITHOUT user_id (use metadata instead - 2025 best practice)
        handler = CallbackHandler(
            public_key=public_key,
            secret_key=secret_key,
            host=host,
            # Note: DO NOT pass user_id here - deprecated in LangFuse 3.x
            # User ID should be passed via metadata in config
        )

        # Cache for reuse (singleton)
        _HANDLER_CACHE[cache_key] = handler

        print(f" [LangFuse] Handler created for host: {host}")
        print(f" [LangFuse] Pass user_id via config.metadata.langfuse_user_id")

        return handler

    except ImportError:
        print("  [LangFuse] SDK not installed - skipping tracing")
        return None
    except Exception as e:
        print(f"  [LangFuse] Failed to initialize handler: {e}")
        return None
