"""
LangGraph Platform Custom Authentication (2025)
================================================

This module implements custom authentication for LangGraph Platform using Clerk JWT tokens.
It enables multi-tenant isolation by automatically filtering threads by user_id.

Architecture:
- Validates Clerk JWT tokens on every LangGraph API call
- Adds user_id to thread metadata automatically
- Filters thread queries by owner
- Ensures complete isolation between users

References:
- https://blog.langchain.com/custom-authentication-and-access-control-in-langgraph/
- https://langchain-ai.github.io/langgraph/concepts/auth/
- https://clerk.com/docs/backend-requests/handling/manual-jwt
"""

from langgraph_sdk import Auth
import os
import httpx
from typing import Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize auth object
auth = Auth()

@auth.authenticate
async def get_current_user(authorization: str | None) -> Auth.types.MinimalUserDict:
    """
    Authenticate user via Clerk JWT token (2025 method).

    This function is called on EVERY request to LangGraph Platform API.
    It validates the Clerk JWT token and extracts user identity.

    Args:
        authorization: HTTP Authorization header (format: "Bearer <token>")

    Returns:
        MinimalUserDict with:
        - identity: Clerk user ID (used for filtering)
        - email: User email (optional)
        - is_authenticated: Boolean flag

    Flow:
        1. Extract Bearer token from header
        2. Validate with Clerk API
        3. Return user identity for LangGraph to use

    Note: This uses Clerk's session verification endpoint (2025 best practice).
    """
    # No authorization header = anonymous user
    if not authorization or not authorization.startswith("Bearer "):
        logger.warning("No authorization header provided")
        return {
            "identity": "anonymous",
            "is_authenticated": False
        }

    # Extract token
    token = authorization.replace("Bearer ", "").strip()

    # Get Clerk secret key
    clerk_secret_key = os.getenv("CLERK_SECRET_KEY")
    if not clerk_secret_key:
        logger.error("CLERK_SECRET_KEY not found in environment")
        return {
            "identity": "anonymous",
            "is_authenticated": False
        }

    try:
        # Validate token with Clerk API (2025 method)
        # Reference: https://clerk.com/docs/backend-requests/handling/manual-jwt
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.clerk.com/v1/sessions/verify",
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Clerk-Secret-Key": clerk_secret_key
                },
                timeout=5.0
            )

            if response.status_code == 200:
                session_data = response.json()
                user_id = session_data.get("user_id")

                if user_id:
                    logger.info(f"User authenticated successfully: {user_id}")
                    return {
                        "identity": user_id,
                        "email": session_data.get("email"),
                        "is_authenticated": True
                    }
            else:
                logger.warning(f"Clerk auth failed: {response.status_code}")

    except httpx.TimeoutException:
        logger.error("Clerk API timeout")
    except Exception as e:
        logger.error(f"Auth error: {e}")

    # Authentication failed
    return {
        "identity": "anonymous",
        "is_authenticated": False
    }

@auth.on
async def add_owner(ctx: Auth.types.AuthContext, value: dict):
    """
    Add user_id to thread metadata automatically (2025 method).

    This function is called when:
    - Creating a new thread
    - Querying threads
    - Creating runs

    It ensures:
    - All threads are tagged with owner (user_id)
    - Searches automatically filter by owner
    - Users can ONLY see their own threads

    Args:
        ctx: Auth context with user identity
        value: Thread/run metadata dictionary

    Returns:
        Filter dictionary applied to ALL queries

    Security:
        - Enforces authentication (raises error if not authenticated)
        - Automatically adds user_id to metadata
        - Returns filter that LangGraph Platform applies to queries

    Example:
        User A creates thread → metadata = {"user_id": "user_abc123"}
        User A queries threads → filter = {"user_id": "user_abc123"}
        User B cannot see User A's threads (filtered out automatically)
    """
    # Require authentication
    if not ctx.user.is_authenticated:
        logger.error("Unauthenticated access attempt")
        raise PermissionError("Authentication required to access LangGraph resources")

    user_id = ctx.user.identity

    # Add user_id to metadata (for creation operations)
    metadata = value.setdefault("metadata", {})
    metadata["user_id"] = user_id

    logger.info(f"Added user_id filter for user: {user_id}")

    # Return filter (for query operations)
    # LangGraph Platform automatically applies this to ALL thread queries
    return {"user_id": user_id}

# Optional: Add resource-specific authorization handlers
# These can be uncommented for fine-grained control

# @auth.on("threads.create")
# async def authorize_thread_creation(ctx: Auth.types.AuthContext, value: dict):
#     """Custom logic for thread creation"""
#     return await add_owner(ctx, value)

# @auth.on("threads.search")
# async def authorize_thread_search(ctx: Auth.types.AuthContext, value: dict):
#     """Custom logic for thread search"""
#     return await add_owner(ctx, value)

# @auth.on("runs.create")
# async def authorize_run_creation(ctx: Auth.types.AuthContext, value: dict):
#     """Custom logic for run creation"""
#     return await add_owner(ctx, value)

# Export auth object for langgraph.json
__all__ = ["auth"]
