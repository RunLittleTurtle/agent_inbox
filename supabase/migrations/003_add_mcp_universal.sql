-- ============================================
-- ADD MCP_UNIVERSAL TO USER_SECRETS
-- ============================================
-- Migration 003: Add global MCP OAuth tokens structure
-- Date: 2025-01-20
-- Purpose: Store MCP OAuth tokens globally (accessible by all agents)
-- Architecture: Keeps per-agent tokens in agent_configs + adds global tokens in user_secrets

-- ============================================
-- 1. ADD MCP_UNIVERSAL COLUMN
-- ============================================
-- Stores OAuth tokens for universal MCP access (Rube, Composio, Pipedream)
-- This allows all agents to use the same MCP connection

ALTER TABLE public.user_secrets
ADD COLUMN IF NOT EXISTS mcp_universal JSONB DEFAULT NULL;

-- ============================================
-- 2. ADD GIN INDEX FOR JSONB QUERIES
-- ============================================
-- Optimize queries on mcp_universal structure

CREATE INDEX IF NOT EXISTS idx_user_secrets_mcp_universal_gin
    ON public.user_secrets USING GIN(mcp_universal);

-- ============================================
-- 3. STRUCTURE DOCUMENTATION
-- ============================================
-- mcp_universal JSONB structure:
-- {
--   "provider": "rube" | "pipedream" | "composio" | "generic",
--   "mcp_server_url": "https://rube.app/mcp",
--   "oauth_tokens": {
--     "access_token": "encrypted_token_string",  -- Encrypted with ENCRYPTION_KEY
--     "refresh_token": "encrypted_token_string", -- Encrypted with ENCRYPTION_KEY
--     "expires_at": "2025-01-20T15:30:00Z",      -- ISO 8601 timestamp
--     "token_type": "Bearer"
--   }
-- }

-- ============================================
-- 4. SAMPLE DATA STRUCTURE (DO NOT RUN)
-- ============================================
-- This is just documentation - actual data will be inserted via OAuth flow

/*
UPDATE public.user_secrets
SET mcp_universal = '{
  "provider": "rube",
  "mcp_server_url": "https://rube.app/mcp",
  "oauth_tokens": {
    "access_token": "iv:authTag:encrypted...",
    "refresh_token": "iv:authTag:encrypted...",
    "expires_at": "2025-01-20T15:30:00Z",
    "token_type": "Bearer"
  }
}'::jsonb
WHERE clerk_id = 'user_test123';
*/

-- ============================================
-- 5. MIGRATION NOTES
-- ============================================
-- IMPORTANT:
-- - This ADDS global MCP tokens (user_secrets.mcp_universal)
-- - KEEPS per-agent MCP tokens (agent_configs.config_data.mcp_integration)
-- - Both structures coexist for flexibility
-- - Priority: agent-specific tokens > global tokens > fallback
--
-- MIGRATION PATH:
-- - Existing per-agent tokens remain intact
-- - Users can optionally set global tokens via Config UI
-- - Executive AI Assistant will use global tokens first, then fallback

-- ============================================
-- 6. VERIFICATION QUERIES
-- ============================================
-- Check column exists
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'user_secrets' AND column_name = 'mcp_universal';

-- Check index exists
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'user_secrets' AND indexname = 'idx_user_secrets_mcp_universal_gin';

-- ============================================
-- MIGRATION COMPLETE
-- ============================================
-- Next steps:
-- 1. Update src/utils/mcp_auth.py to support dual loading
-- 2. Add MCP section to src/ui_config.py
-- 3. Create MCPConfigCard in config-app
