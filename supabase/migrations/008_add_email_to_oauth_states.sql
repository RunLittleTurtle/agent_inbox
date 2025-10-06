-- ============================================
-- ADD EMAIL TO OAUTH_STATES TABLE
-- ============================================
-- Migration 008: Add email column to oauth_states for easier debugging
-- Date: 2025-10-06
-- Purpose: Denormalize email from user_secrets for easier OAuth flow debugging

-- ============================================
-- 1. ADD EMAIL COLUMN
-- ============================================
ALTER TABLE public.oauth_states
ADD COLUMN IF NOT EXISTS email TEXT;

-- ============================================
-- 2. CREATE INDEX FOR EMAIL LOOKUPS
-- ============================================
-- Allows fast queries by email (e.g., "show all OAuth states for user@example.com")
CREATE INDEX IF NOT EXISTS idx_oauth_states_email
ON public.oauth_states(email);

-- ============================================
-- 3. BACKFILL EMAILS FROM USER_SECRETS
-- ============================================
-- Copy emails from user_secrets to oauth_states based on clerk_id
UPDATE public.oauth_states os
SET email = us.email
FROM public.user_secrets us
WHERE os.clerk_id = us.clerk_id
AND us.email IS NOT NULL;

-- ============================================
-- 4. VERIFICATION
-- ============================================
-- Check that the email column was added
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'oauth_states' AND column_name = 'email';

-- Check that emails were backfilled
SELECT
    COUNT(*) as total_states,
    COUNT(email) as states_with_email,
    COUNT(*) - COUNT(email) as states_without_email
FROM public.oauth_states;

-- Sample of backfilled data
SELECT clerk_id, email, provider, mcp_url, created_at, expires_at
FROM public.oauth_states
ORDER BY created_at DESC
LIMIT 5;

-- ============================================
-- MIGRATION COMPLETE
-- ============================================
-- Email will be automatically populated when new OAuth states are created
-- Note: oauth_states are temporary (auto-cleaned), so manual backfill may not be needed
