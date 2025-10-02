-- ============================================
-- AGENT CONFIGS TABLE FOR CONFIG-APP
-- ============================================
-- Stores per-user agent configuration values
-- Executed: Run this in Supabase SQL Editor

-- ============================================
-- 1. AGENT_CONFIGS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS public.agent_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- User identification (from Clerk JWT)
    clerk_id TEXT NOT NULL,

    -- Agent identification
    agent_id TEXT NOT NULL,
    agent_name TEXT NOT NULL,

    -- Configuration data stored as JSON
    config_data JSONB NOT NULL DEFAULT '{}',

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Ensure one config per user per agent
    UNIQUE(clerk_id, agent_id)
);

-- ============================================
-- 2. ENABLE ROW LEVEL SECURITY
-- ============================================
ALTER TABLE public.agent_configs ENABLE ROW LEVEL SECURITY;

-- ============================================
-- 3. RLS POLICIES
-- ============================================

-- Policy: Users can view their own agent configs
CREATE POLICY "Users can view own agent configs"
    ON public.agent_configs
    FOR SELECT
    USING ((auth.jwt()->>'sub') = clerk_id);

-- Policy: Users can update their own agent configs
CREATE POLICY "Users can update own agent configs"
    ON public.agent_configs
    FOR UPDATE
    USING ((auth.jwt()->>'sub') = clerk_id);

-- Policy: Users can insert their own agent configs
CREATE POLICY "Users can insert own agent configs"
    ON public.agent_configs
    FOR INSERT
    WITH CHECK ((auth.jwt()->>'sub') = clerk_id);

-- Policy: Users can delete their own agent configs
CREATE POLICY "Users can delete own agent configs"
    ON public.agent_configs
    FOR DELETE
    USING ((auth.jwt()->>'sub') = clerk_id);

-- ============================================
-- 4. INDEXES FOR PERFORMANCE
-- ============================================
CREATE INDEX IF NOT EXISTS idx_agent_configs_clerk_id ON public.agent_configs(clerk_id);
CREATE INDEX IF NOT EXISTS idx_agent_configs_agent_id ON public.agent_configs(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_configs_clerk_agent ON public.agent_configs(clerk_id, agent_id);

-- ============================================
-- 5. TRIGGER FOR UPDATED_AT
-- ============================================
CREATE TRIGGER update_agent_configs_updated_at
    BEFORE UPDATE ON public.agent_configs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 6. VERIFICATION
-- ============================================
-- Check if RLS is enabled
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public' AND tablename = 'agent_configs';

-- Check policies
SELECT schemaname, tablename, policyname, permissive, cmd
FROM pg_policies
WHERE tablename = 'agent_configs'
ORDER BY cmd;
