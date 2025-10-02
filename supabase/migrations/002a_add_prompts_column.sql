-- ============================================
-- ADD PROMPTS COLUMN TO EXISTING agent_configs TABLE
-- ============================================
-- Run this ONLY if agent_configs table exists but is missing the prompts column
-- (Use 001_check_schema.sql first to verify)

-- ============================================
-- 1. ADD PROMPTS COLUMN
-- ============================================
-- Add the prompts JSONB column for storing prompt overrides
-- Separate from config_data to allow independent management
ALTER TABLE public.agent_configs
ADD COLUMN IF NOT EXISTS prompts JSONB NOT NULL DEFAULT '{}';

-- ============================================
-- 2. ADD GIN INDEX FOR PROMPTS
-- ============================================
-- Enable fast JSONB queries on prompts column
CREATE INDEX IF NOT EXISTS idx_agent_configs_prompts_gin
    ON public.agent_configs USING GIN(prompts);

-- ============================================
-- 3. VERIFICATION
-- ============================================
-- Check that the column was added successfully
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'agent_configs'
AND column_name = 'prompts';

-- Expected output:
-- column_name | data_type | is_nullable | column_default
-- prompts     | jsonb     | NO          | '{}'::jsonb

-- ============================================
-- SUCCESS MESSAGE
-- ============================================
SELECT '✅ prompts column added successfully! Ready for Phase 1.3' as status;
