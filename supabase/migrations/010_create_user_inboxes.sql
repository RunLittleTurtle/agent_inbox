-- Migration: Create user_inboxes table for multi-device inbox sync
-- Purpose: Store agent inboxes in Supabase instead of localStorage
-- Benefits: Multi-device sync, auto-configured defaults, centralized management

-- Create user_inboxes table
CREATE TABLE IF NOT EXISTS public.user_inboxes (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  clerk_id TEXT NOT NULL,
  email TEXT,
  inbox_name TEXT NOT NULL,
  graph_id TEXT NOT NULL,
  deployment_url TEXT NOT NULL,
  is_default BOOLEAN DEFAULT false,
  selected BOOLEAN DEFAULT false,
  tenant_id TEXT,
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now(),

  -- Ensure one inbox per user per graph
  CONSTRAINT unique_user_graph UNIQUE(clerk_id, graph_id)
);

-- Enable Row Level Security
ALTER TABLE public.user_inboxes ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only access their own inboxes
CREATE POLICY "Users can manage their own inboxes"
  ON public.user_inboxes FOR ALL
  USING (clerk_id = (auth.jwt()->>'sub'));

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_inboxes_clerk_id
  ON public.user_inboxes(clerk_id);

CREATE INDEX IF NOT EXISTS idx_user_inboxes_selected
  ON public.user_inboxes(clerk_id, selected)
  WHERE selected = true;

CREATE INDEX IF NOT EXISTS idx_user_inboxes_email
  ON public.user_inboxes(email);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_user_inboxes_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER user_inboxes_updated_at
  BEFORE UPDATE ON public.user_inboxes
  FOR EACH ROW
  EXECUTE FUNCTION update_user_inboxes_updated_at();

-- Comments for documentation
COMMENT ON TABLE public.user_inboxes IS 'Stores user agent inbox configurations for multi-device sync';
COMMENT ON COLUMN public.user_inboxes.is_default IS 'True for auto-created default inboxes (Agent, Executive Main)';
COMMENT ON COLUMN public.user_inboxes.selected IS 'True for currently active inbox in UI';
COMMENT ON COLUMN public.user_inboxes.tenant_id IS 'LangGraph tenant ID for deployed graphs';
