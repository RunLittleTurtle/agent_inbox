-- Add LangFuse configuration columns to user_secrets table
-- This enables per-user LangFuse tracing configuration

ALTER TABLE user_secrets
ADD COLUMN IF NOT EXISTS langfuse_public_key TEXT,
ADD COLUMN IF NOT EXISTS langfuse_secret_key TEXT,
ADD COLUMN IF NOT EXISTS langfuse_host TEXT DEFAULT 'https://cloud.langfuse.com';

-- Add comment to document the new columns
COMMENT ON COLUMN user_secrets.langfuse_public_key IS 'LangFuse public API key for user-scoped tracing';
COMMENT ON COLUMN user_secrets.langfuse_secret_key IS 'LangFuse secret API key (encrypted)';
COMMENT ON COLUMN user_secrets.langfuse_host IS 'LangFuse server URL (cloud or self-hosted)';

-- Verify the schema update
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'user_secrets'
AND column_name IN ('langfuse_public_key', 'langfuse_secret_key', 'langfuse_host');
