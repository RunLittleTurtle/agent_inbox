/**
 * Backfill User Emails Script
 *
 * This script fetches all users from Clerk and populates their emails
 * in the Supabase user_secrets table.
 *
 * Usage:
 *   npx tsx scripts/backfill_user_emails.ts
 *
 * Requirements:
 *   - CLERK_SECRET_KEY environment variable
 *   - NEXT_PUBLIC_SUPABASE_URL environment variable
 *   - SUPABASE_SECRET_KEY environment variable
 */

import { createClient } from '@supabase/supabase-js';

// Load environment variables
const CLERK_SECRET_KEY = process.env.CLERK_SECRET_KEY;
const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL;
const SUPABASE_SECRET_KEY = process.env.SUPABASE_SECRET_KEY;

if (!CLERK_SECRET_KEY) {
  console.error('❌ CLERK_SECRET_KEY environment variable is required');
  process.exit(1);
}

if (!SUPABASE_URL || !SUPABASE_SECRET_KEY) {
  console.error('❌ Supabase environment variables are required');
  process.exit(1);
}

const supabase = createClient(SUPABASE_URL, SUPABASE_SECRET_KEY);

interface ClerkUser {
  id: string;
  email_addresses: Array<{
    id: string;
    email_address: string;
    verification: {
      status: string;
    };
  }>;
}

/**
 * Fetch all users from Clerk API
 */
async function fetchClerkUsers(): Promise<ClerkUser[]> {
  const users: ClerkUser[] = [];
  let offset = 0;
  const limit = 100;
  let hasMore = true;

  console.log('📡 Fetching users from Clerk...');

  while (hasMore) {
    const response = await fetch(
      `https://api.clerk.com/v1/users?limit=${limit}&offset=${offset}`,
      {
        headers: {
          Authorization: `Bearer ${CLERK_SECRET_KEY}`,
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Clerk API error: ${response.statusText}`);
    }

    const batch = await response.json();
    users.push(...batch);

    offset += limit;
    hasMore = batch.length === limit;

    console.log(`   Fetched ${users.length} users so far...`);
  }

  console.log(`✅ Fetched ${users.length} total users from Clerk\n`);
  return users;
}

/**
 * Get existing user_secrets from Supabase
 */
async function fetchExistingUserSecrets(): Promise<Set<string>> {
  console.log('📊 Fetching existing user_secrets from Supabase...');

  const { data, error } = await supabase
    .from('user_secrets')
    .select('clerk_id');

  if (error) {
    throw new Error(`Supabase error: ${error.message}`);
  }

  const clerkIds = new Set(data?.map(row => row.clerk_id) || []);
  console.log(`✅ Found ${clerkIds.size} existing user_secrets records\n`);

  return clerkIds;
}

/**
 * Update email for a user in Supabase
 */
async function updateUserEmail(clerkId: string, email: string): Promise<boolean> {
  const { error } = await supabase
    .from('user_secrets')
    .update({ email })
    .eq('clerk_id', clerkId);

  if (error) {
    console.error(`   ❌ Failed to update ${clerkId}:`, error.message);
    return false;
  }

  return true;
}

/**
 * Main backfill function
 */
async function backfillEmails() {
  console.log('🚀 Starting email backfill process\n');
  console.log('=' .repeat(60));

  try {
    // 1. Fetch all users from Clerk
    const clerkUsers = await fetchClerkUsers();

    if (clerkUsers.length === 0) {
      console.log('⚠️  No users found in Clerk. Nothing to backfill.');
      return;
    }

    // 2. Fetch existing user_secrets
    const existingClerkIds = await fetchExistingUserSecrets();

    // 3. Filter to only users that exist in Supabase
    const usersToUpdate = clerkUsers.filter(user =>
      existingClerkIds.has(user.id)
    );

    console.log('📝 Backfill Summary:');
    console.log(`   Total Clerk users: ${clerkUsers.length}`);
    console.log(`   Users with user_secrets: ${usersToUpdate.length}`);
    console.log(`   Users without user_secrets: ${clerkUsers.length - usersToUpdate.length} (will be created on first visit)\n`);

    if (usersToUpdate.length === 0) {
      console.log('✅ No existing user_secrets need email backfill');
      return;
    }

    // 4. Update emails
    console.log('📧 Updating emails in Supabase...\n');

    let updated = 0;
    let skipped = 0;
    let failed = 0;

    for (const user of usersToUpdate) {
      const primaryEmail = user.email_addresses.find(
        email => email.verification?.status === 'verified'
      ) || user.email_addresses[0];

      if (!primaryEmail) {
        console.log(`   ⚠️  Skipping ${user.id} (no email found)`);
        skipped++;
        continue;
      }

      const email = primaryEmail.email_address;
      const success = await updateUserEmail(user.id, email);

      if (success) {
        console.log(`   ✅ Updated ${user.id} → ${email}`);
        updated++;
      } else {
        failed++;
      }
    }

    // 5. Summary
    console.log('\n' + '=' .repeat(60));
    console.log('✨ Backfill Complete!\n');
    console.log('📊 Results:');
    console.log(`   ✅ Updated: ${updated}`);
    console.log(`   ⚠️  Skipped: ${skipped}`);
    console.log(`   ❌ Failed: ${failed}`);
    console.log(`   📧 Total emails backfilled: ${updated}`);

    if (failed > 0) {
      console.log('\n⚠️  Some updates failed. Check the logs above for details.');
      process.exit(1);
    }

  } catch (error) {
    console.error('\n❌ Backfill failed:');
    console.error(error);
    process.exit(1);
  }
}

// Run the backfill
backfillEmails();
