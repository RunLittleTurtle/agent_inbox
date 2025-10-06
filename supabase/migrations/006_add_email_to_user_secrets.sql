-- ============================================
-- ADD EMAIL TO USER_SECRETS TABLE
-- ============================================
-- Migration 006: Add email column to store user email from Clerk JWT
-- Date: 2025-10-06
-- Purpose: Store user email for notifications, analytics, and user management

-- ============================================
-- 1. ADD EMAIL COLUMN
-- ============================================
ALTER TABLE public.user_secrets
ADD COLUMN IF NOT EXISTS email TEXT;

-- ============================================
-- 2. CREATE INDEX FOR EMAIL LOOKUPS
-- ============================================
-- Allows fast queries by email (e.g., for admin panels, analytics)
CREATE INDEX IF NOT EXISTS idx_user_secrets_email
ON public.user_secrets(email);

-- ============================================
-- 3. VERIFICATION
-- ============================================
-- Check that the email column was added
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'user_secrets' AND column_name = 'email';

-- Check that the index was created
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'user_secrets' AND indexname = 'idx_user_secrets_email';

-- ============================================
-- MIGRATION COMPLETE
-- ============================================
-- Email will be automatically captured from Clerk JWT during lazy creation
-- Next step: Update TypeScript interfaces and getOrCreateUserSecrets()
