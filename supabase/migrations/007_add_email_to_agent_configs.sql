-- ============================================
-- ADD EMAIL TO AGENT_CONFIGS TABLE
-- ============================================
-- Migration 007: Add email column to agent_configs for easier debugging
-- Date: 2025-10-06
-- Purpose: Denormalize email from user_secrets for easier queries and admin panels

-- ============================================
-- 1. ADD EMAIL COLUMN
-- ============================================
ALTER TABLE public.agent_configs
ADD COLUMN IF NOT EXISTS email TEXT;

-- ============================================
-- 2. CREATE INDEX FOR EMAIL LOOKUPS
-- ============================================
-- Allows fast queries by email (e.g., "show all configs for user@example.com")
CREATE INDEX IF NOT EXISTS idx_agent_configs_email
ON public.agent_configs(email);

-- ============================================
-- 3. BACKFILL EMAILS FROM USER_SECRETS
-- ============================================
-- Copy emails from user_secrets to agent_configs based on clerk_id
UPDATE public.agent_configs ac
SET email = us.email
FROM public.user_secrets us
WHERE ac.clerk_id = us.clerk_id
AND us.email IS NOT NULL;

-- ============================================
-- 4. VERIFICATION
-- ============================================
-- Check that the email column was added
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'agent_configs' AND column_name = 'email';

-- Check that emails were backfilled
SELECT
    COUNT(*) as total_configs,
    COUNT(email) as configs_with_email,
    COUNT(*) - COUNT(email) as configs_without_email
FROM public.agent_configs;

-- Sample of backfilled data
SELECT clerk_id, email, agent_id, agent_name, created_at
FROM public.agent_configs
ORDER BY created_at DESC
LIMIT 5;

-- ============================================
-- MIGRATION COMPLETE
-- ============================================
-- Email will be automatically populated via trigger on INSERT/UPDATE
-- Next step: Create trigger to auto-sync email when clerk_id changes
