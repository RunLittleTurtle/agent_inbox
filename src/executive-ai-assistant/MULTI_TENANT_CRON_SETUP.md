# Multi-Tenant Cron Architecture (2025 Pattern)

## Overview

The Executive AI Assistant now uses **per-user cron jobs** following 2025 LangGraph Cloud best practices. Each user gets their own cron job that runs every **1 minute**, processing only their emails with proper multi-tenant isolation.

## Architecture Changes

### Before (Broken)
```
❌ Single Global Cron → config.yaml → Only processes info@800m.ca
```

### After (2025 Pattern)
```
✅ User 1 Cron (every 1 min) → User 1 emails → User 1 threads (owner: user_1)
✅ User 2 Cron (every 1 min) → User 2 emails → User 2 threads (owner: user_2)
✅ User N Cron (every 1 min) → User N emails → User N threads (owner: user_N)
```

## Components Modified

### 1. Supabase Database
**New Table:** `user_crons`
```sql
CREATE TABLE user_crons (
    id UUID PRIMARY KEY,
    user_id TEXT NOT NULL UNIQUE,
    cron_id TEXT NOT NULL,
    email TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    schedule TEXT DEFAULT '* * * * *',  -- Every 1 minute
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Migration:** `src/executive-ai-assistant/supabase/migrations/create_user_crons_table.sql`

### 2. Config API (Railway FastAPI)
**File:** `src/config_api/main.py`

**New Endpoints:**
- `POST /api/webhooks/gmail-connected` - Creates per-user cron job
- `POST /api/cron/manage` - Manage cron (pause/resume/delete)
- `GET /api/cron/status` - Check user's cron status

**New Function:**
- `create_user_cron(user_id, email, schedule)` - Creates LangGraph cron via SDK

### 3. Executive AI Assistant Cron Graph
**File:** `src/executive-ai-assistant/eaia/cron_graph.py`

**Changes:**
- Removed user looping (now single-user context)
- Added detailed logging for debugging
- User context comes from cron job's assistant config
- Processes emails for ONE user per cron execution

### 4. Manual Cron Creation Script
**File:** `src/executive-ai-assistant/scripts/create_user_cron.py`

**Usage:**
```bash
# Create cron for first user
python scripts/create_user_cron.py \
  --user-id user_33Z8MWmIOt29U9ii3uA54m3FoU5 \
  --email info@800m.ca

# Create cron for second user
python scripts/create_user_cron.py \
  --user-id USER_ID_HERE \
  --email user2@example.com

# Custom schedule (e.g., every 5 minutes)
python scripts/create_user_cron.py \
  --user-id USER_ID \
  --email EMAIL \
  --schedule "*/5 * * * *"
```

## How It Works

### Cron Creation Flow

1. **User completes Gmail OAuth** (in config-app)
2. **Config app calls webhook:** `POST /api/webhooks/gmail-connected`
   ```json
   {
     "user_id": "user_33Z8MWmIOt29U9ii3uA54m3FoU5",
     "email": "info@800m.ca",
     "schedule": "* * * * *"
   }
   ```
3. **Config API creates:**
   - LangGraph Assistant with user's config
   - LangGraph Cron Job for that assistant
   - Stores `cron_id` in Supabase `user_crons` table

4. **Every 1 minute:**
   - LangGraph Platform triggers user's cron
   - Cron runs `executive_cron` graph with user's config
   - `cron_graph.py` fetches emails for that user only
   - Creates threads with `owner` metadata
   - Threads visible only to that user (via `auth.py` filtering)

### Multi-Tenant Isolation

**How users are isolated:**

1. **Cron Level:** Each user has separate cron job with their config
2. **Metadata Level:** Threads created with `"owner": user_id`
3. **Auth Level:** `auth.py` filters all queries by `{"owner": user.identity}`
4. **Config Level:** Each cron's assistant has user-specific config

**Result:** User A cannot see User B's threads, even though both use the same `graph_id: "executive_main"`

## Testing Steps

### Step 1: Apply Supabase Migration
```bash
cd src/executive-ai-assistant
mcp__supabase__apply_migration \
  --name create_user_crons_table \
  --query "$(cat supabase/migrations/create_user_crons_table.sql)"
```

### Step 2: Deploy Config API to Railway
```bash
cd src/config_api
git add .
git commit -m "feat: add per-user cron job creation endpoints"
git push
```

Railway will automatically deploy the updated Config API.

### Step 3: Deploy Executive AI Assistant to LangGraph Cloud
```bash
cd src/executive-ai-assistant
git add .
git commit -m "feat: update cron_graph for per-user execution"
git push
```

LangGraph Cloud will automatically deploy the updated graph.

### Step 4: Create Crons for Existing Users

**For first user (info@800m.ca):**
```bash
cd src/executive-ai-assistant
python scripts/create_user_cron.py \
  --user-id user_33Z8MWmIOt29U9ii3uA54m3FoU5 \
  --email info@800m.ca
```

**For second user:**
```bash
python scripts/create_user_cron.py \
  --user-id YOUR_SECOND_USER_ID \
  --email second.user@example.com
```

### Step 5: Verify Crons Are Running

**Check cron status:**
```bash
curl "https://agentinbox-production.up.railway.app/api/cron/status?user_id=user_33Z8MWmIOt29U9ii3uA54m3FoU5"
```

**Check LangSmith traces:**
- Go to LangSmith dashboard
- Filter by `metadata.owner` to see each user's cron runs
- Each user should have separate traces

### Step 6: Verify Thread Isolation

**User 1 checks Agent Inbox:**
- Should see threads with `owner: user_33Z8MWmIOt29U9ii3uA54m3FoU5`
- Should NOT see User 2's threads

**User 2 checks Agent Inbox:**
- Should see threads with `owner: USER_2_ID`
- Should NOT see User 1's threads

## Cron Schedule

**Current:** Every **1 minute** (`* * * * *`)

**To change for a user:**
```bash
python scripts/create_user_cron.py \
  --user-id USER_ID \
  --email EMAIL \
  --schedule "*/5 * * * *"  # Every 5 minutes
```

**Common schedules:**
- Every 1 minute: `* * * * *`
- Every 5 minutes: `*/5 * * * *`
- Every 15 minutes: `*/15 * * * *`
- Every hour: `0 * * * *`

## Troubleshooting

### Cron not running
1. Check cron exists in Supabase: `SELECT * FROM user_crons WHERE user_id = 'USER_ID';`
2. Check LangGraph Platform: https://smith.langchain.com/settings/crons
3. Check cron logs in LangSmith traces

### Threads not appearing in Agent Inbox
1. Verify thread has `owner` metadata: Check LangSmith trace
2. Verify thread has `graph_id: "executive_main"` metadata
3. Check auth.py is filtering correctly
4. Verify user is signed in with correct Clerk user ID

### Wrong user seeing threads
1. Check thread metadata in LangSmith
2. Verify `owner` field matches user's Clerk ID
3. Run backfill script if needed: `scripts/backfill_owner_metadata.py`

## Monitoring

**Cron Job Health:**
- Check Railway logs for Config API
- Check LangSmith traces for `executive_cron` graph
- Monitor `user_crons` table in Supabase

**User Metrics:**
- Emails processed per user (count threads)
- Cron job execution time (LangSmith)
- Error rates per user (Railway logs)

## Future Enhancements

1. **Auto-create cron on OAuth:** Integrate webhook call into OAuth callback
2. **UI for cron management:** Add cron controls to config-app
3. **Supabase config table:** Store per-user assistant preferences
4. **Dynamic scheduling:** Allow users to customize cron frequency
5. **Pause/resume UI:** Let users temporarily disable email processing

## Related Files

- `src/config_api/main.py` - Cron creation endpoints
- `src/executive-ai-assistant/eaia/cron_graph.py` - Per-user email processing
- `src/executive-ai-assistant/scripts/create_user_cron.py` - Manual cron creation
- `src/executive-ai-assistant/scripts/backfill_owner_metadata.py` - Fix old threads
- `src/executive-ai-assistant/supabase/migrations/create_user_crons_table.sql` - Database schema
- `src/auth.py` - Multi-tenant filtering logic
