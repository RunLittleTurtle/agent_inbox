-- Fix the Executive Main inbox graph_id from "executive-ai-assistant" to "executive_main"
-- Run this in your Supabase SQL editor

UPDATE user_inboxes
SET graph_id = 'executive_main'
WHERE graph_id = 'executive-ai-assistant'
  AND clerk_id = 'user_33Z8MWmIOt29U9ii3uA54m3FoU5';

-- Verify the fix
SELECT inbox_name, graph_id, deployment_url, selected
FROM user_inboxes
WHERE clerk_id = 'user_33Z8MWmIOt29U9ii3uA54m3FoU5'
ORDER BY is_default DESC, created_at ASC;
