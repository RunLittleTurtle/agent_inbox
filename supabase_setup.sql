-- ============================================
-- SUPABASE SCHEMA - MODERN 2025 ARCHITECTURE
-- ============================================
-- Updated: 2025-10-01
-- Architecture: Native Supabase Third-Party Auth with Clerk
--
-- KEY CHANGES FROM OLD APPROACH:
-- ✅ No separate 'users' table needed (Supabase reads Clerk JWT directly)
-- ✅ Simplified RLS using auth.jwt()->>'sub'
-- ✅ No webhook for user sync (lazy creation on first access)
-- ✅ Follows official Clerk + Supabase 2025 best practices
--
-- Execute this in Supabase SQL Editor:
-- https://supabase.com/dashboard/project/lcswsadubzhynscruzfn/editor

-- ============================================
-- 1. USER_SECRETS TABLE (SIMPLIFIED)
-- ============================================
-- Stores encrypted API keys and credentials per user
-- One row per Clerk user (identified by clerk_id from JWT)

CREATE TABLE IF NOT EXISTS public.user_secrets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Clerk User ID (from JWT 'sub' claim)
    clerk_id TEXT UNIQUE NOT NULL,

    -- AI Model API Keys
    openai_api_key TEXT,
    anthropic_api_key TEXT,
    google_api_key TEXT,

    -- LangSmith Tracing
    langsmith_api_key TEXT,

    -- Google OAuth Credentials
    google_client_id TEXT,
    google_client_secret TEXT,
    google_refresh_token TEXT,

    -- MCP Integration Tokens
    rube_token TEXT,
    composio_token TEXT,
    pipedream_token TEXT,

    -- User Preferences
    timezone TEXT DEFAULT 'America/Toronto',
    preferred_model TEXT DEFAULT 'claude-3-5-sonnet-20241022',
    temperature NUMERIC(3,2) DEFAULT 0.00,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- 2. ENABLE ROW LEVEL SECURITY (RLS)
-- ============================================
ALTER TABLE public.user_secrets ENABLE ROW LEVEL SECURITY;

-- ============================================
-- 3. RLS POLICIES - MODERN 2025 APPROACH
-- ============================================
-- Uses auth.jwt() to access Clerk session token claims directly

-- Policy: Users can view their own secrets
CREATE POLICY "Users can view own secrets"
    ON public.user_secrets
    FOR SELECT
    USING ((auth.jwt()->>'sub') = clerk_id);

-- Policy: Users can update their own secrets
CREATE POLICY "Users can update own secrets"
    ON public.user_secrets
    FOR UPDATE
    USING ((auth.jwt()->>'sub') = clerk_id);

-- Policy: Users can insert their own secrets
CREATE POLICY "Users can insert own secrets"
    ON public.user_secrets
    FOR INSERT
    WITH CHECK ((auth.jwt()->>'sub') = clerk_id);

-- Policy: Users can delete their own secrets
CREATE POLICY "Users can delete own secrets"
    ON public.user_secrets
    FOR DELETE
    USING ((auth.jwt()->>'sub') = clerk_id);

-- ============================================
-- 4. INDEXES FOR PERFORMANCE
-- ============================================
CREATE INDEX IF NOT EXISTS idx_user_secrets_clerk_id ON public.user_secrets(clerk_id);

-- ============================================
-- 5. TRIGGER FOR UPDATED_AT
-- ============================================
-- Automatically update updated_at timestamp on changes

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_user_secrets_updated_at
    BEFORE UPDATE ON public.user_secrets
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 6. VERIFICATION QUERIES
-- ============================================
-- Run these to verify setup

-- Check if RLS is enabled (should show rowsecurity = true)
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public' AND tablename = 'user_secrets';

-- Check policies (should show 4 policies: SELECT, UPDATE, INSERT, DELETE)
SELECT schemaname, tablename, policyname, permissive, cmd
FROM pg_policies
WHERE tablename = 'user_secrets'
ORDER BY cmd;

-- Test query (should return 0 rows initially - empty table)
SELECT COUNT(*) as total_users FROM user_secrets;

-- ============================================
-- 7. SETUP THIRD-PARTY AUTH IN SUPABASE UI
-- ============================================
-- IMPORTANT: After running this SQL, you MUST configure Supabase to accept Clerk tokens:
--
-- 1. Go to: https://supabase.com/dashboard/project/lcswsadubzhynscruzfn/settings/auth
-- 2. Scroll to "Third-Party Auth Providers"
-- 3. Click "Add Provider" → Select "Clerk"
-- 4. Enter your Clerk domain: modest-sunbeam-39.clerk.accounts.dev
-- 5. Save changes
--
-- This tells Supabase to trust JWT tokens from Clerk and makes auth.jwt() work correctly.

-- ============================================
-- NOTES - MODERN 2025 ARCHITECTURE
-- ============================================
--
-- ✅ ADVANTAGES:
-- - No separate users table needed (Supabase reads Clerk JWT directly)
-- - No webhook complexity for user sync
-- - Simpler RLS policies with auth.jwt()->>'sub'
-- - Lazy creation: user_secrets row created on first Config App visit
-- - Better performance: no extra table joins
--
-- 🔐 SECURITY:
-- - RLS automatically enforces user isolation via Clerk JWT
-- - Each user can ONLY access their own row
-- - Secret Key (sb_secret_...) bypasses RLS - use ONLY in backend API routes
-- - Publishable Key (sb_publishable_...) enforces RLS - safe for frontend
--
-- 📊 DATA FLOW:
-- 1. User logs in via Clerk → gets JWT token
-- 2. Frontend creates Supabase client with Clerk token
-- 3. Supabase validates JWT and extracts 'sub' (clerk_id)
-- 4. RLS policies ensure user only accesses their own secrets
-- 5. First access to Config App creates user_secrets row automatically
--
-- 🚀 DEPLOYMENT:
-- 1. Run this SQL in Supabase SQL Editor
-- 2. Configure Third-Party Auth (step 7 above)
-- 3. Deploy Next.js apps with createClerkSupabaseClient() utility
-- 4. Test: Sign in → Config App should auto-create your secrets row
