"""
MCP OAuth Token Management Utilities
Loads and decrypts OAuth tokens from Supabase for MCP servers
"""

import os
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from supabase import create_client, Client
import httpx


def get_encryption_key() -> bytes:
    """
    Get encryption key from environment
    Key must be 32 bytes (64 hex characters)
    """
    key_hex = os.getenv("ENCRYPTION_KEY")

    if not key_hex:
        raise ValueError("ENCRYPTION_KEY not found in environment variables")

    if len(key_hex) != 64:
        raise ValueError(f"ENCRYPTION_KEY must be 64 hex characters (32 bytes), got {len(key_hex)}")

    return bytes.fromhex(key_hex)


def decrypt_token(encrypted_text: str) -> str:
    """
    Decrypt an encrypted token
    Format: iv:authTag:encrypted (all hex)
    """
    key = get_encryption_key()

    parts = encrypted_text.split(':')
    if len(parts) != 3:
        raise ValueError('Invalid encrypted text format. Expected: iv:authTag:encrypted')

    iv_hex, auth_tag_hex, encrypted_hex = parts

    iv = bytes.fromhex(iv_hex)
    auth_tag = bytes.fromhex(auth_tag_hex)
    encrypted = bytes.fromhex(encrypted_hex)

    # Combine encrypted data and auth tag for AES-GCM
    ciphertext_with_tag = encrypted + auth_tag

    # Decrypt using AES-256-GCM
    aesgcm = AESGCM(key)
    decrypted = aesgcm.decrypt(iv, ciphertext_with_tag, None)

    return decrypted.decode('utf-8')


def encrypt_token(text: str) -> str:
    """
    Encrypt a token (for token refresh)
    Returns format: iv:authTag:encrypted (all hex)
    """
    import secrets

    key = get_encryption_key()
    iv = secrets.token_bytes(16)  # 16 bytes for GCM

    aesgcm = AESGCM(key)
    ciphertext_with_tag = aesgcm.encrypt(iv, text.encode('utf-8'), None)

    # Split ciphertext and auth tag
    encrypted = ciphertext_with_tag[:-16]
    auth_tag = ciphertext_with_tag[-16:]

    return f"{iv.hex()}:{auth_tag.hex()}:{encrypted.hex()}"


def get_supabase_client() -> Client:
    """Get Supabase client"""
    url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    key = os.getenv("SUPABASE_SECRET_KEY")

    if not url or not key:
        raise ValueError("NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SECRET_KEY required")

    return create_client(url, key)


def get_mcp_oauth_tokens(user_id: str, agent_id: str) -> Optional[Dict[str, Any]]:
    """
    Load OAuth tokens for MCP from agent_configs (per-agent tokens)
    Returns decrypted access token ready for use

    NOTE: This function loads AGENT-SPECIFIC tokens from agent_configs
    For GLOBAL tokens, use get_mcp_oauth_tokens_global()
    """
    try:
        supabase = get_supabase_client()

        # Get agent config from Supabase
        result = supabase.table("agent_configs") \
            .select("config_data") \
            .eq("clerk_id", user_id) \
            .eq("agent_id", agent_id) \
            .maybe_single() \
            .execute()

        if not result.data:
            print(f"[MCP Auth] No agent config found for {agent_id}")
            return None

        config_data = result.data.get("config_data", {})
        mcp_integration = config_data.get("mcp_integration", {})
        oauth_tokens = mcp_integration.get("oauth_tokens")

        if not oauth_tokens:
            print(f"[MCP Auth] No OAuth tokens found for {agent_id}")
            return None

        # Check if token is expired
        expires_at_str = oauth_tokens.get("expires_at")
        if expires_at_str:
            expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
            if datetime.now(expires_at.tzinfo) >= expires_at:
                print(f"[MCP Auth] Token expired, refreshing...")
                return refresh_oauth_token(user_id, agent_id, mcp_integration)

        # Decrypt access token
        encrypted_access_token = oauth_tokens.get("access_token")
        if not encrypted_access_token:
            print(f"[MCP Auth] No access token found")
            return None

        access_token = decrypt_token(encrypted_access_token)

        return {
            "access_token": access_token,
            "token_type": oauth_tokens.get("token_type", "Bearer"),
            "mcp_url": mcp_integration.get("mcp_server_url")
        }

    except Exception as e:
        print(f"[MCP Auth] Error loading tokens: {e}")
        return None


def get_mcp_oauth_tokens_global(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Load OAuth tokens for MCP from user_secrets (global tokens)
    Returns decrypted access token ready for use

    This loads GLOBAL MCP tokens that are shared across all agents.
    Use this for agents that don't have agent-specific MCP tokens.
    """
    try:
        supabase = get_supabase_client()

        # Get user_secrets from Supabase
        result = supabase.table("user_secrets") \
            .select("mcp_universal") \
            .eq("clerk_id", user_id) \
            .maybe_single() \
            .execute()

        if not result.data:
            print(f"[MCP Auth Global] No user_secrets found for user {user_id}")
            return None

        mcp_universal = result.data.get("mcp_universal")
        if not mcp_universal:
            print(f"[MCP Auth Global] No mcp_universal found in user_secrets")
            return None

        oauth_tokens = mcp_universal.get("oauth_tokens")
        if not oauth_tokens:
            print(f"[MCP Auth Global] No oauth_tokens in mcp_universal")
            return None

        # Check if token is expired
        expires_at_str = oauth_tokens.get("expires_at")
        if expires_at_str:
            expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
            if datetime.now(expires_at.tzinfo) >= expires_at:
                print(f"[MCP Auth Global] Token expired, refreshing...")
                return refresh_mcp_universal_token(user_id, mcp_universal)

        # Decrypt access token
        encrypted_access_token = oauth_tokens.get("access_token")
        if not encrypted_access_token:
            print(f"[MCP Auth Global] No access token found")
            return None

        access_token = decrypt_token(encrypted_access_token)

        return {
            "access_token": access_token,
            "token_type": oauth_tokens.get("token_type", "Bearer"),
            "mcp_url": mcp_universal.get("mcp_server_url"),
            "provider": mcp_universal.get("provider", "generic")
        }

    except Exception as e:
        print(f"[MCP Auth Global] Error loading tokens from user_secrets: {e}")
        return None


def get_mcp_oauth_tokens_dual(user_id: str, agent_id: str = None) -> Optional[Dict[str, Any]]:
    """
    Load OAuth tokens with dual strategy: global first, then per-agent fallback

    Priority order:
    1. Global tokens from user_secrets.mcp_universal (shared across all agents)
    2. Agent-specific tokens from agent_configs (if agent_id provided)
    3. None (no tokens available)

    Args:
        user_id: Clerk user ID
        agent_id: Optional agent ID for per-agent fallback

    Returns:
        OAuth token dict or None
    """
    # Try global tokens first
    global_tokens = get_mcp_oauth_tokens_global(user_id)
    if global_tokens:
        print(f"[MCP Auth Dual] Using global MCP tokens for user {user_id}")
        return global_tokens

    # Fallback to per-agent tokens if agent_id provided
    if agent_id:
        agent_tokens = get_mcp_oauth_tokens(user_id, agent_id)
        if agent_tokens:
            print(f"[MCP Auth Dual] Using agent-specific MCP tokens for {agent_id}")
            return agent_tokens

    print(f"[MCP Auth Dual] No MCP tokens found (global or agent-specific)")
    return None


def refresh_mcp_universal_token(user_id: str, mcp_universal: dict) -> Optional[Dict[str, Any]]:
    """
    Refresh expired OAuth token for global MCP (user_secrets.mcp_universal)
    """
    try:
        oauth_tokens = mcp_universal.get("oauth_tokens", {})
        encrypted_refresh_token = oauth_tokens.get("refresh_token")

        if not encrypted_refresh_token:
            print(f"[MCP Auth Global] No refresh token available")
            return None

        refresh_token = decrypt_token(encrypted_refresh_token)
        mcp_url = mcp_universal.get("mcp_server_url")

        # Discover token endpoint
        metadata_url = f"{mcp_url.split('/mcp')[0]}/.well-known/oauth-authorization-server"

        response = httpx.get(metadata_url, timeout=10)
        response.raise_for_status()
        metadata = response.json()

        token_endpoint = metadata.get("token_endpoint")
        if not token_endpoint:
            print(f"[MCP Auth Global] No token endpoint found in metadata")
            return None

        # Exchange refresh token for new access token
        client_id = os.getenv("MCP_CLIENT_ID")

        token_response = httpx.post(
            token_endpoint,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": client_id,
                "resource": mcp_url
            },
            timeout=10
        )

        if not token_response.is_success:
            print(f"[MCP Auth Global] Token refresh failed: {token_response.text}")
            return None

        new_tokens = token_response.json()

        # Encrypt new tokens
        encrypted_access = encrypt_token(new_tokens["access_token"])
        encrypted_refresh = encrypt_token(new_tokens.get("refresh_token", refresh_token))

        expires_at = datetime.now() + timedelta(seconds=new_tokens.get("expires_in", 3600))

        # Update user_secrets in Supabase
        supabase = get_supabase_client()

        mcp_universal["oauth_tokens"]["access_token"] = encrypted_access
        mcp_universal["oauth_tokens"]["refresh_token"] = encrypted_refresh
        mcp_universal["oauth_tokens"]["expires_at"] = expires_at.isoformat()

        supabase.table("user_secrets").update({
            "mcp_universal": mcp_universal
        }).eq("clerk_id", user_id).execute()

        print(f"[MCP Auth Global] Token refreshed successfully for user {user_id}")

        return {
            "access_token": new_tokens["access_token"],
            "token_type": new_tokens.get("token_type", "Bearer"),
            "mcp_url": mcp_url,
            "provider": mcp_universal.get("provider", "generic")
        }

    except Exception as e:
        print(f"[MCP Auth Global] Token refresh error: {e}")
        return None


def refresh_oauth_token(user_id: str, agent_id: str, mcp_integration: dict) -> Optional[Dict[str, Any]]:
    """
    Refresh expired OAuth token for per-agent MCP (agent_configs)
    """
    try:
        oauth_tokens = mcp_integration.get("oauth_tokens", {})
        encrypted_refresh_token = oauth_tokens.get("refresh_token")

        if not encrypted_refresh_token:
            print(f"[MCP Auth] No refresh token available")
            return None

        refresh_token = decrypt_token(encrypted_refresh_token)
        mcp_url = mcp_integration.get("mcp_server_url")

        # Discover token endpoint
        metadata_url = f"{mcp_url.split('/mcp')[0]}/.well-known/oauth-authorization-server"

        response = httpx.get(metadata_url, timeout=10)
        response.raise_for_status()
        metadata = response.json()

        token_endpoint = metadata.get("token_endpoint")
        if not token_endpoint:
            print(f"[MCP Auth] No token endpoint found in metadata")
            return None

        # Exchange refresh token for new access token
        client_id = os.getenv("MCP_CLIENT_ID")

        token_response = httpx.post(
            token_endpoint,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": client_id,
                "resource": mcp_url
            },
            timeout=10
        )

        if not token_response.is_success:
            print(f"[MCP Auth] Token refresh failed: {token_response.text}")
            return None

        new_tokens = token_response.json()

        # Encrypt new tokens
        encrypted_access = encrypt_token(new_tokens["access_token"])
        encrypted_refresh = encrypt_token(new_tokens.get("refresh_token", refresh_token))

        expires_at = datetime.now() + timedelta(seconds=new_tokens.get("expires_in", 3600))

        # Update agent_configs in Supabase
        supabase = get_supabase_client()

        mcp_integration["oauth_tokens"]["access_token"] = encrypted_access
        mcp_integration["oauth_tokens"]["refresh_token"] = encrypted_refresh
        mcp_integration["oauth_tokens"]["expires_at"] = expires_at.isoformat()

        supabase.table("agent_configs").update({
            "config_data": {"mcp_integration": mcp_integration}
        }).eq("clerk_id", user_id).eq("agent_id", agent_id).execute()

        print(f"[MCP Auth] Token refreshed successfully for {agent_id}")

        return {
            "access_token": new_tokens["access_token"],
            "token_type": new_tokens.get("token_type", "Bearer"),
            "mcp_url": mcp_url
        }

    except Exception as e:
        print(f"[MCP Auth] Token refresh error: {e}")
        return None
