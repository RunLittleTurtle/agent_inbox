-- ============================================
-- ADD EMAIL TO AGENT_CONFIGS AND OAUTH_STATES
-- ============================================
-- Combined migration: 007 + 008
-- Date: 2025-10-06
-- Purpose: Add email column to both tables for easier debugging

-- ============================================
-- 1. ADD EMAIL TO AGENT_CONFIGS
-- ============================================
ALTER TABLE public.agent_configs
ADD COLUMN IF NOT EXISTS email TEXT;

CREATE INDEX IF NOT EXISTS idx_agent_configs_email
ON public.agent_configs(email);

-- Backfill emails from user_secrets
UPDATE public.agent_configs ac
SET email = us.email
FROM public.user_secrets us
WHERE ac.clerk_id = us.clerk_id
AND us.email IS NOT NULL;

-- ============================================
-- 2. ADD EMAIL TO OAUTH_STATES
-- ============================================
ALTER TABLE public.oauth_states
ADD COLUMN IF NOT EXISTS email TEXT;

CREATE INDEX IF NOT EXISTS idx_oauth_states_email
ON public.oauth_states(email);

-- Backfill emails from user_secrets
UPDATE public.oauth_states os
SET email = us.email
FROM public.user_secrets us
WHERE os.clerk_id = us.clerk_id
AND us.email IS NOT NULL;

-- ============================================
-- 3. VERIFICATION & RESULTS
-- ============================================

-- Show agent_configs with emails
SELECT
    'agent_configs' as table_name,
    COUNT(*) as total_rows,
    COUNT(email) as rows_with_email,
    COUNT(*) - COUNT(email) as rows_without_email
FROM public.agent_configs
UNION ALL
SELECT
    'oauth_states' as table_name,
    COUNT(*) as total_rows,
    COUNT(email) as rows_with_email,
    COUNT(*) - COUNT(email) as rows_without_email
FROM public.oauth_states;

-- Sample data from agent_configs
SELECT clerk_id, email, agent_id, agent_name, created_at
FROM public.agent_configs
ORDER BY created_at DESC
LIMIT 5;

-- Sample data from oauth_states (if any exist)
SELECT clerk_id, email, provider, mcp_url, created_at, expires_at
FROM public.oauth_states
WHERE expires_at > NOW()
ORDER BY created_at DESC
LIMIT 5;

-- ============================================
-- MIGRATION COMPLETE
-- ============================================
