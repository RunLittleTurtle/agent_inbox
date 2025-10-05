-- ============================================
-- ADD CLIENT_ID TO OAUTH_STATES
-- ============================================
-- Migration 005: Store dynamically registered client_id
-- Date: 2025-01-20
-- Purpose: Store client_id from dynamic registration for callback use

ALTER TABLE public.oauth_states
ADD COLUMN IF NOT EXISTS client_id TEXT;

-- Add index for client_id lookups
CREATE INDEX IF NOT EXISTS idx_oauth_states_client_id ON public.oauth_states(client_id);

-- Verify column was added
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'oauth_states' AND column_name = 'client_id';
