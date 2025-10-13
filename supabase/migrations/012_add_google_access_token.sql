-- ============================================
-- ADD GOOGLE_ACCESS_TOKEN TO USER_SECRETS
-- ============================================
-- Migration 012: Add google_access_token column for Google Calendar OAuth
-- Date: 2025-10-13
-- Purpose: Store Google access token alongside refresh token for Calendar API access
--
-- CONTEXT:
-- The original schema (supabase_setup.sql) included google_refresh_token but was
-- missing google_access_token. Google OAuth requires both tokens:
-- - access_token: Short-lived (1 hour) token for API calls
-- - refresh_token: Long-lived token to obtain new access tokens
--
-- This migration adds the missing google_access_token column.

-- ============================================
-- 1. ADD GOOGLE_ACCESS_TOKEN COLUMN
-- ============================================
ALTER TABLE public.user_secrets
ADD COLUMN IF NOT EXISTS google_access_token TEXT;

-- ============================================
-- 2. VERIFICATION
-- ============================================
-- Check that the google_access_token column was added
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'user_secrets' AND column_name = 'google_access_token';

-- ============================================
-- COMPLETE GOOGLE OAUTH SCHEMA
-- ============================================
-- After this migration, user_secrets has complete Google OAuth support:
-- - google_access_token: Current access token (expires in ~1 hour)
-- - google_refresh_token: Refresh token (long-lived)
-- - google_client_id: OAuth client ID
-- - google_client_secret: OAuth client secret
--
-- All tokens are managed by the FastAPI config API on Railway and stored securely.

-- ============================================
-- MIGRATION COMPLETE
-- ============================================
-- Next steps:
-- 1. Ensure Config App has Google OAuth flow to populate these fields
-- 2. Calendar agent will now be able to load complete Google credentials
-- 3. Test by connecting Google Calendar through Config App
