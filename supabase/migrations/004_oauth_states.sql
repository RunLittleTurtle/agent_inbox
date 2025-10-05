-- ============================================
-- OAUTH_STATES TABLE FOR MCP OAUTH FLOW
-- ============================================
-- Migration 004: Store PKCE state for OAuth 2.1 flows
-- Date: 2025-01-20
-- Purpose: Temporary storage of OAuth state during authorization flow

-- ============================================
-- 1. CREATE OAUTH_STATES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS public.oauth_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- OAuth state parameter (CSRF protection)
    state TEXT UNIQUE NOT NULL,

    -- User identification
    clerk_id TEXT NOT NULL,

    -- PKCE parameters
    code_verifier TEXT NOT NULL,

    -- MCP configuration
    mcp_url TEXT NOT NULL,
    provider TEXT, -- 'rube', 'pipedream', 'composio', etc.

    -- OAuth type
    is_global BOOLEAN DEFAULT false, -- true = user_secrets (global), false = agent_configs (per-agent)
    agent_id TEXT, -- Only set if is_global = false

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- ============================================
-- 2. ENABLE ROW LEVEL SECURITY
-- ============================================
ALTER TABLE public.oauth_states ENABLE ROW LEVEL SECURITY;

-- ============================================
-- 3. RLS POLICIES
-- ============================================
-- Users can only access their own OAuth states
CREATE POLICY "Users can view own oauth states"
    ON public.oauth_states
    FOR SELECT
    USING ((auth.jwt()->>'sub') = clerk_id);

CREATE POLICY "Users can insert own oauth states"
    ON public.oauth_states
    FOR INSERT
    WITH CHECK ((auth.jwt()->>'sub') = clerk_id);

CREATE POLICY "Users can delete own oauth states"
    ON public.oauth_states
    FOR DELETE
    USING ((auth.jwt()->>'sub') = clerk_id);

-- ============================================
-- 4. INDEXES
-- ============================================
CREATE INDEX IF NOT EXISTS idx_oauth_states_state ON public.oauth_states(state);
CREATE INDEX IF NOT EXISTS idx_oauth_states_clerk_id ON public.oauth_states(clerk_id);
CREATE INDEX IF NOT EXISTS idx_oauth_states_expires_at ON public.oauth_states(expires_at);

-- ============================================
-- 5. CLEANUP FUNCTION
-- ============================================
-- Automatically delete expired states
CREATE OR REPLACE FUNCTION cleanup_expired_oauth_states()
RETURNS void AS $$
BEGIN
    DELETE FROM public.oauth_states
    WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Optional: Schedule periodic cleanup (requires pg_cron extension)
-- SELECT cron.schedule('cleanup-oauth-states', '*/5 * * * *', 'SELECT cleanup_expired_oauth_states()');

-- ============================================
-- 6. VERIFICATION
-- ============================================
-- Check table exists
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'oauth_states';

-- Check RLS is enabled
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public' AND tablename = 'oauth_states';

-- ============================================
-- MIGRATION COMPLETE
-- ============================================
