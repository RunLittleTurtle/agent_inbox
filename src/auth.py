"""
LangGraph Platform Custom Authentication (2025)
================================================

This module implements custom authentication for LangGraph Platform using Clerk JWT tokens.
It enables multi-tenant isolation by automatically filtering threads by user_id.

Architecture:
- Validates Clerk JWT tokens using JWKS (proper 2025 method)
- Adds owner metadata to all resources automatically
- Filters queries by owner to ensure user isolation
- Ensures complete isolation between users

References:
- https://docs.langchain.com/langgraph-platform/custom-auth
- https://langchain-ai.github.io/langgraph/tutorials/auth/getting_started/
- https://clerk.com/docs/backend-requests/handling/manual-jwt
"""

from langgraph_sdk import Auth
import os
import jwt
from jwt import PyJWKClient
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize auth object
auth = Auth()

# Clerk JWKS URL for JWT verification
CLERK_PUBLISHABLE_KEY = os.getenv("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY")

if not CLERK_PUBLISHABLE_KEY:
    logger.warning("⚠️  NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY not set - auth will fail in production")
    CLERK_JWKS_URL = None
else:
    # Extract instance ID from publishable key
    # Format: pk_test_<instance>_<random> or pk_live_<instance>_<random>
    parts = CLERK_PUBLISHABLE_KEY.split("_")
    if len(parts) >= 3:
        instance_id = parts[2]
        CLERK_JWKS_URL = f"https://{instance_id}.clerk.accounts.dev/.well-known/jwks.json"
        logger.info(f"🔐 Clerk JWKS URL: {CLERK_JWKS_URL}")
    else:
        logger.error(f"❌ Invalid CLERK_PUBLISHABLE_KEY format: {CLERK_PUBLISHABLE_KEY}")
        CLERK_JWKS_URL = None

# Initialize JWT verifier client (only if JWKS URL is available)
jwks_client = PyJWKClient(CLERK_JWKS_URL) if CLERK_JWKS_URL else None

@auth.authenticate
async def get_current_user(authorization: str | None) -> Auth.types.MinimalUserDict:
    """
    Authenticate user via Clerk JWT token using JWKS verification (2025 method).

    This function is called on EVERY request to LangGraph Platform API.
    It validates the Clerk JWT token using public key cryptography (JWKS).

    Args:
        authorization: HTTP Authorization header (format: "Bearer <token>")

    Returns:
        MinimalUserDict with:
        - identity: Clerk user ID (used for filtering)
        - is_authenticated: Boolean flag

    Raises:
        Auth.exceptions.HTTPException: If authentication fails

    Flow:
        1. Extract Bearer token from header
        2. Verify JWT signature using Clerk's JWKS
        3. Extract user ID from 'sub' claim
        4. Return user identity for LangGraph to use

    Note: Uses JWKS for cryptographic verification (no API calls needed).
    """
    # Check if JWKS client is available
    if not jwks_client:
        logger.error("❌ JWKS client not initialized - check NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY")
        raise Auth.exceptions.HTTPException(
            status_code=500,
            detail="Authentication not configured"
        )

    # Check authorization header
    if not authorization or not authorization.startswith("Bearer "):
        logger.error("❌ No authorization header provided")
        raise Auth.exceptions.HTTPException(
            status_code=401,
            detail="Authentication required"
        )

    # Extract token
    token = authorization.replace("Bearer ", "").strip()

    try:
        # Get signing key from Clerk's JWKS
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        # Verify JWT signature and decode payload
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_exp": True}
        )

        # Extract user ID from 'sub' claim
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Token missing 'sub' claim")

        logger.info(f"✅ Authenticated user: {user_id}")

        return {
            "identity": user_id,
            "is_authenticated": True,
        }

    except jwt.ExpiredSignatureError:
        logger.error("❌ JWT token has expired")
        raise Auth.exceptions.HTTPException(
            status_code=401,
            detail="Token expired"
        )
    except jwt.InvalidTokenError as e:
        logger.error(f"❌ Invalid JWT token: {e}")
        raise Auth.exceptions.HTTPException(
            status_code=401,
            detail="Invalid token"
        )
    except Exception as e:
        logger.error(f"❌ Authentication error: {e}")
        raise Auth.exceptions.HTTPException(
            status_code=401,
            detail="Authentication failed"
        )

@auth.on
async def authorize_all_resources(value: dict, user: Auth.types.MinimalUserDict) -> Auth.types.FilterType:
    """
    AUTHORIZATION LAYER - Single-Owner Resources Pattern (2025).

    This function is called for EVERY resource access (threads, runs, assistants, crons).
    It enforces that users can only access resources they own.

    Pattern: "Single-Owner Resources"
    - Adds 'owner' metadata to all created resources
    - Filters queries to only return user's own resources

    Args:
        value: The mutable data being sent to the endpoint
        user: The authenticated user object

    Returns:
        Filter dict to restrict access to user's resources

    Security:
        - Enforces authentication (user must be authenticated)
        - Automatically adds owner to metadata
        - Returns filter applied to ALL queries

    Example:
        User A creates thread → metadata = {"owner": "user_abc123"}
        User A queries threads → filter = {"owner": "user_abc123"}
        User B cannot see User A's threads (filtered out automatically)

    References:
        - https://docs.langchain.com/langgraph-platform/custom-auth
    """

    # Add 'owner' metadata to resources being created
    # This tags the resource with the user's identity
    if "metadata" in value:
        if value["metadata"] is None:
            value["metadata"] = {}
        value["metadata"]["owner"] = user.identity
        logger.info(f"📝 Tagged resource with owner: {user.identity}")

    # Return filter: only show resources owned by this user
    # This is applied to all queries (search, read, list, etc.)
    return {"owner": user.identity}


logger.info("✅ Auth handler initialized - Clerk JWT with single-owner resource isolation")

# Export auth object for langgraph.json
__all__ = ["auth"]
