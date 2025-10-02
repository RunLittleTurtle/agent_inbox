-- ============================================
-- AGENT CONFIGS TABLE - Consolidated Migration
-- ============================================
-- Architecture: Immutable Defaults (Code) + User Overrides (Supabase)
-- This migration creates the agent_configs table for storing user overrides
-- Defaults remain in code (src/*/config.py, src/*/prompt.py)
--
-- Execution: Run this in Supabase SQL Editor
-- Migration: 002_agent_configs.sql

-- ============================================
-- 1. CREATE AGENT_CONFIGS TABLE
-- ============================================
-- Stores per-user configuration overrides for agents
-- Each row represents user-specific overrides for ONE agent
CREATE TABLE IF NOT EXISTS public.agent_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- User identification (from Clerk JWT)
    clerk_id TEXT NOT NULL,

    -- Agent identification
    agent_id TEXT NOT NULL,
    agent_name TEXT NOT NULL,

    -- Configuration data stored as JSON (LLM settings, agent-specific settings)
    config_data JSONB NOT NULL DEFAULT '{}',

    -- Prompt overrides stored separately from config
    -- Allows users to customize prompts per agent
    prompts JSONB NOT NULL DEFAULT '{}',

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
-- 3. RLS POLICIES (User Isolation)
-- ============================================
-- Each user can only access their own configs

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
CREATE INDEX IF NOT EXISTS idx_agent_configs_clerk_id
    ON public.agent_configs(clerk_id);

CREATE INDEX IF NOT EXISTS idx_agent_configs_agent_id
    ON public.agent_configs(agent_id);

CREATE INDEX IF NOT EXISTS idx_agent_configs_clerk_agent
    ON public.agent_configs(clerk_id, agent_id);

-- GIN indexes for JSONB queries
CREATE INDEX IF NOT EXISTS idx_agent_configs_config_data_gin
    ON public.agent_configs USING GIN(config_data);

CREATE INDEX IF NOT EXISTS idx_agent_configs_prompts_gin
    ON public.agent_configs USING GIN(prompts);

-- ============================================
-- 5. TRIGGER FOR UPDATED_AT
-- ============================================
-- First, create the trigger function if it doesn't exist
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Then create the trigger
DROP TRIGGER IF EXISTS update_agent_configs_updated_at ON public.agent_configs;
CREATE TRIGGER update_agent_configs_updated_at
    BEFORE UPDATE ON public.agent_configs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 6. HELPER FUNCTIONS (Optional)
-- ============================================
-- Function to reset all overrides for a user+agent (revert to code defaults)
CREATE OR REPLACE FUNCTION reset_agent_config(
    p_clerk_id TEXT,
    p_agent_id TEXT
)
RETURNS VOID AS $$
BEGIN
    UPDATE public.agent_configs
    SET
        config_data = '{}',
        prompts = '{}'
    WHERE clerk_id = p_clerk_id AND agent_id = p_agent_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- 7. VERIFICATION QUERIES
-- ============================================
-- Run these to verify the migration succeeded

-- Check if RLS is enabled
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public' AND tablename = 'agent_configs';

-- Check policies
SELECT schemaname, tablename, policyname, permissive, cmd
FROM pg_policies
WHERE tablename = 'agent_configs'
ORDER BY cmd;

-- Check indexes
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'agent_configs'
ORDER BY indexname;

-- ============================================
-- 8. SAMPLE DATA (Optional - for testing)
-- ============================================
-- Uncomment to insert sample config for testing
/*
INSERT INTO public.agent_configs (clerk_id, agent_id, agent_name, config_data, prompts)
VALUES
    ('user_test123', 'calendar', 'Calendar Agent',
     '{"llm": {"model": "gpt-4o", "temperature": 0.5}}',
     '{"system_prompt": "Custom calendar prompt"}')
ON CONFLICT (clerk_id, agent_id) DO NOTHING;
*/

-- ============================================
-- MIGRATION COMPLETE
-- ============================================
-- This migration creates the foundation for the config override system.
-- Remember: Code = Defaults (immutable), Supabase = Overrides (user-specific)
