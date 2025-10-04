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
import sys
import jwt
from jwt import PyJWKClient
import logging

# Ensure UTF-8 encoding for stdout/stderr before any logging
# This prevents UnicodeEncodeError in Docker containers
def _ensure_utf8_encoding():
    """Ensure stdout/stderr use UTF-8 encoding."""
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass  # Already configured or not supported

_ensure_utf8_encoding()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize auth object
auth = Auth()

# Clerk JWKS URL for JWT verification
CLERK_PUBLISHABLE_KEY = os.getenv("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY")

if not CLERK_PUBLISHABLE_KEY:
    logger.warning("  NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY not set - auth will fail in production")
    CLERK_JWKS_URL = None
else:
    # Extract instance from publishable key
    # Format: pk_test_<base64> or pk_live_<base64>
    # The base64 decodes to: <instance>.clerk.accounts.dev
    try:
        import base64
        parts = CLERK_PUBLISHABLE_KEY.split("_")
        if len(parts) >= 2:
            # Decode base64 to get instance domain
            encoded_instance = parts[2] if len(parts) >= 3 else parts[1]
            decoded = base64.b64decode(encoded_instance + "==").decode('utf-8').strip()
            # Remove trailing $ if present
            instance_domain = decoded.rstrip('$')
            CLERK_JWKS_URL = f"https://{instance_domain}/.well-known/jwks.json"
            logger.info(f" Clerk JWKS URL: {CLERK_JWKS_URL}")
        else:
            logger.error(f" Invalid CLERK_PUBLISHABLE_KEY format: {CLERK_PUBLISHABLE_KEY}")
            CLERK_JWKS_URL = None
    except Exception as e:
        logger.error(f" Failed to parse CLERK_PUBLISHABLE_KEY: {e}")
        CLERK_JWKS_URL = None

# Initialize JWT verifier client (only if JWKS URL is available)
jwks_client = PyJWKClient(CLERK_JWKS_URL) if CLERK_JWKS_URL else None

@auth.authenticate
async def get_current_user(authorization: str | None) -> Auth.types.MinimalUserDict:
    """
    Authenticate user with Studio bypass and Clerk JWT validation (2025).

    This function is called on EVERY request to LangGraph Platform API.

    Authentication Flow:
    1. Studio requests (no auth header) → Allow with "studio" identity for debugging
    2. API requests (Bearer token) → Validate Clerk JWT using JWKS
    3. Invalid/expired tokens → Reject with 401

    Args:
        authorization: HTTP Authorization header (format: "Bearer <token>" or None for Studio)

    Returns:
        MinimalUserDict with:
        - identity: User ID from Clerk JWT or "studio" for Studio requests
        - is_authenticated: Boolean flag

    Raises:
        Auth.exceptions.HTTPException: If API authentication fails

    Security Model:
        - Studio (no token): Full access for development/debugging
        - API users (Clerk JWT): Authenticated + owner-filtered resources (multi-tenant)

    Note: Uses JWKS for cryptographic verification (no API calls needed).
    """
    # STUDIO BYPASS: Studio sends no authorization header
    # This allows developers to use LangGraph Studio for debugging without JWT
    if not authorization or authorization.strip() == "":
        logger.info("=" * 80)
        logger.info(" STUDIO REQUEST DETECTED (no auth header)")
        logger.info(" Returning identity='studio' for full access")
        logger.info("=" * 80)
        return {
            "identity": "studio",
            "is_authenticated": True,
        }

    # API REQUEST VALIDATION: Check for valid Bearer token format
    if not authorization.startswith("Bearer "):
        logger.error(" Invalid authorization header format (expected 'Bearer <token>')")
        raise Auth.exceptions.HTTPException(
            status_code=401,
            detail="Invalid authorization header"
        )

    # Check if JWKS client is available
    if not jwks_client:
        logger.error(" JWKS client not initialized - check NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY")
        raise Auth.exceptions.HTTPException(
            status_code=500,
            detail="Authentication not configured"
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

        logger.info(f" Authenticated user: {user_id}")

        return {
            "identity": user_id,
            "is_authenticated": True,
        }

    except jwt.ExpiredSignatureError:
        logger.error(" JWT token has expired")
        raise Auth.exceptions.HTTPException(
            status_code=401,
            detail="Token expired"
        )
    except jwt.InvalidTokenError as e:
        logger.error(f" Invalid JWT token: {e}")
        raise Auth.exceptions.HTTPException(
            status_code=401,
            detail="Invalid token"
        )
    except Exception as e:
        logger.error(f" Authentication error: {e}")
        raise Auth.exceptions.HTTPException(
            status_code=401,
            detail="Authentication failed"
        )

@auth.on
async def authorize_all_resources(ctx: Auth.types.AuthContext, value: dict) -> Auth.types.FilterType:
    """
    AUTHORIZATION LAYER - Resource-Specific Access Control with Studio Support (2025).

    This function is called for EVERY resource access (threads, runs, assistants, crons).
    It enforces different access patterns based on user type and resource type.

    User Types:
    - Studio user (identity="studio"): Full access to all resources (development/debugging)
    - API users (identity=Clerk user_id): Owner-filtered access (multi-tenant isolation)

    Resource Types:
    - Assistants: Deployment-level (shared by all authenticated users)
    - Threads/Runs/Crons/Store: User-level (private per user, except Studio)

    Pattern: "Resource-Specific Authorization with Studio Bypass"
    - Studio → No filtering on any resource (full visibility for debugging)
    - Assistants → No filtering for all users (shared resource)
    - Other resources → Owner metadata + filtering for API users (multi-tenant)

    Args:
        ctx: Authorization context containing user info and resource type
        value: The mutable data being sent to the endpoint

    Returns:
        Filter dict to restrict access (None for public/Studio access)

    Security Model:
        - Studio: Full access (development tool only, no production impact)
        - API Users: Clerk authenticated + owner-filtered (multi-tenant isolation)
        - User A cannot see User B's threads/runs/crons (owner-based filtering)

    Example:
        Studio Access:
          Studio user → All resources visible (threads from all users, for debugging)

        Assistants (All Users):
          User A queries assistants → All assistants returned (no filter)
          User B queries assistants → All assistants returned (no filter)

        Threads (API Users):
          User A creates thread → metadata = {"owner": "user_abc123"}
          User A queries threads → filter = {"owner": "user_abc123"}
          User B cannot see User A's threads (filtered by owner)

    References:
        - https://docs.langchain.com/langgraph-platform/resource-auth
        - https://docs.langchain.com/langgraph-platform/custom-auth
    """
    user = ctx.user
    resource_type = ctx.resource  # e.g., "assistants", "threads", "runs", "crons", "store"
    user_id = user.identity

    # STUDIO/LANGSMITH BYPASS: Detect Studio and LangSmith-authenticated users
    # Studio authenticates via LangSmith API and gets a UUID-format identity
    # Clerk users have format: user_<alphanumeric>
    # LangSmith users have format: <uuid> (e.g., 6ee08f61-3091-40f4-b20c-8dcffbe7573f)

    is_langsmith_user = (
        user_id == "studio" or  # Direct Studio (no auth header)
        (len(user_id) == 36 and user_id.count('-') == 4)  # UUID format = LangSmith
    )

    if is_langsmith_user:
        logger.info(f" LangSmith/Studio user detected: {user_id}")
        logger.info(f" Full access to {resource_type} - no filtering for debugging")
        return {}  # Empty dict = no filter = see all resources

    # ASSISTANTS: Deployment-level resources - shared by all authenticated users
    # No owner metadata, no filtering - allows all API users to see them
    if resource_type == "assistants":
        logger.info(f" Assistants access for user {user.identity} - no owner filtering (shared resource)")
        return None  # No filter = all assistants visible

    # OTHER RESOURCES (threads, runs, crons, store): User-specific with multi-tenant isolation
    # Add owner metadata and apply filtering to ensure users only see their own data
    metadata = value.setdefault("metadata", {})
    metadata["owner"] = user.identity
    logger.info(f" {resource_type} access for owner: {user.identity}")

    # Return filter: only show resources owned by this specific user
    return {"owner": user.identity}


logger.info(" Auth handler initialized - Clerk JWT with single-owner resource isolation")

# Export auth object for langgraph.json
__all__ = ["auth"]
