-- ============================================
-- SCHEMA VERIFICATION SCRIPT
-- ============================================
-- Run this in Supabase SQL Editor to check current schema state
-- This helps determine what migration steps are needed

-- ============================================
-- CHECK 1: Does agent_configs table exist?
-- ============================================
SELECT
    CASE
        WHEN EXISTS (
            SELECT FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename = 'agent_configs'
        )
        THEN '✅ agent_configs table EXISTS'
        ELSE '❌ agent_configs table DOES NOT EXIST - Need to run full migration'
    END as table_status;

-- ============================================
-- CHECK 2: What columns does agent_configs have?
-- ============================================
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'agent_configs'
ORDER BY ordinal_position;

-- ============================================
-- CHECK 3: Does the prompts column exist?
-- ============================================
SELECT
    CASE
        WHEN EXISTS (
            SELECT FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = 'agent_configs'
            AND column_name = 'prompts'
        )
        THEN '✅ prompts column EXISTS'
        ELSE '⚠️ prompts column MISSING - Need to add it'
    END as prompts_status;

-- ============================================
-- CHECK 4: Is RLS enabled?
-- ============================================
SELECT
    tablename,
    CASE
        WHEN rowsecurity THEN '✅ RLS ENABLED'
        ELSE '❌ RLS DISABLED'
    END as rls_status
FROM pg_tables
WHERE schemaname = 'public'
AND tablename = 'agent_configs';

-- ============================================
-- CHECK 5: What RLS policies exist?
-- ============================================
SELECT
    policyname,
    cmd,
    permissive
FROM pg_policies
WHERE tablename = 'agent_configs'
ORDER BY cmd;

-- ============================================
-- CHECK 6: What indexes exist?
-- ============================================
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'agent_configs'
ORDER BY indexname;

-- ============================================
-- INTERPRETATION:
-- ============================================
-- If table doesn't exist:
--   → Run: /supabase/migrations/002_agent_configs.sql (full migration)
--
-- If table exists but prompts column missing:
--   → Run: ALTER TABLE public.agent_configs ADD COLUMN prompts JSONB NOT NULL DEFAULT '{}';
--   → Run: CREATE INDEX IF NOT EXISTS idx_agent_configs_prompts_gin ON public.agent_configs USING GIN(prompts);
--
-- If table exists with prompts column:
--   → ✅ Ready to go! Proceed to Phase 1.4 (test FastAPI)
