-- Create table for tracking per-user cron jobs
-- This enables multi-tenant executive AI assistant where each user gets their own cron job

CREATE TABLE IF NOT EXISTS user_crons (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT NOT NULL UNIQUE,
    cron_id TEXT NOT NULL,
    email TEXT NOT NULL,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'paused', 'deleted')),
    schedule TEXT DEFAULT '* * * * *',  -- Every 1 minute
    last_run_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE user_crons ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see and manage their own cron jobs
CREATE POLICY "Users can manage their own crons"
    ON user_crons FOR ALL
    USING (auth.jwt() ->> 'sub' = user_id);

-- Index for fast lookups
CREATE INDEX idx_user_crons_user_id ON user_crons(user_id);
CREATE INDEX idx_user_crons_status ON user_crons(status);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_user_crons_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at
CREATE TRIGGER user_crons_updated_at
    BEFORE UPDATE ON user_crons
    FOR EACH ROW
    EXECUTE FUNCTION update_user_crons_updated_at();

COMMENT ON TABLE user_crons IS 'Tracks LangGraph Platform cron jobs for each user''s executive AI assistant';
COMMENT ON COLUMN user_crons.user_id IS 'Clerk user ID (e.g., user_33Z8MWmIOt29U9ii3uA54m3FoU5)';
COMMENT ON COLUMN user_crons.cron_id IS 'LangGraph Platform cron job ID returned from API';
COMMENT ON COLUMN user_crons.email IS 'Gmail address being monitored for this user';
COMMENT ON COLUMN user_crons.schedule IS 'Cron expression for job schedule';
