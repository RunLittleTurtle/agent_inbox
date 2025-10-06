-- Migration: Add langsmith_api_key to user_secrets table
-- Purpose: Store per-user LangSmith API keys for Agent Inbox authentication
-- Security: Encrypted storage with RLS policies

-- Add langsmith_api_key column to user_secrets
ALTER TABLE public.user_secrets
ADD COLUMN IF NOT EXISTS langsmith_api_key TEXT;

-- Index for performance (sparse index for users who have configured key)
CREATE INDEX IF NOT EXISTS idx_user_secrets_langsmith
  ON public.user_secrets(clerk_id)
  WHERE langsmith_api_key IS NOT NULL;

-- Comment for documentation
COMMENT ON COLUMN public.user_secrets.langsmith_api_key IS 'LangSmith API key for authenticating LangGraph requests (per-user, encrypted)';
