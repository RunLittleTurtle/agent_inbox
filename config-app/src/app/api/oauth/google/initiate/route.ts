/**
 * Initiate Google OAuth Flow
 * Gets refresh_token for Gmail + Calendar access
 */

import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@clerk/nextjs/server';
import { createClient } from '@supabase/supabase-js';

// Google OAuth endpoints
const GOOGLE_AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth';

// Required scopes for Executive AI Assistant
const GOOGLE_SCOPES = [
  'https://www.googleapis.com/auth/gmail.modify',
  'https://www.googleapis.com/auth/calendar',
  'https://www.googleapis.com/auth/userinfo.email',
].join(' ');

export async function POST(request: NextRequest) {
  try {
    // 1. Get authenticated user from Clerk
    const { userId } = await auth();
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    console.log(`[Google OAuth Init] Starting for user ${userId}`);

    // 2. Get global Google OAuth credentials from environment
    const clientId = process.env.GOOGLE_CLIENT_ID;
    const clientSecret = process.env.GOOGLE_CLIENT_SECRET;

    if (!clientId || !clientSecret) {
      return NextResponse.json(
        {
          error: 'Google OAuth not configured',
          message: 'Administrator has not configured Google OAuth credentials. Please contact support.'
        },
        { status: 500 }
      );
    }

    console.log('[Google OAuth Init] Using global OAuth credentials');

    // 3. Generate state for CSRF protection (simple random string)
    const state = Buffer.from(
      JSON.stringify({
        clerk_id: userId,
        timestamp: Date.now(),
        nonce: Math.random().toString(36).substring(2)
      })
    ).toString('base64url');

    // 4. Build callback URL
    const appUrl = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3004';
    const redirectUri = `${appUrl}/api/oauth/google/callback`;

    // 5. Build authorization URL
    const authUrl = new URL(GOOGLE_AUTH_URL);
    authUrl.searchParams.set('client_id', clientId);
    authUrl.searchParams.set('redirect_uri', redirectUri);
    authUrl.searchParams.set('response_type', 'code');
    authUrl.searchParams.set('scope', GOOGLE_SCOPES);
    authUrl.searchParams.set('access_type', 'offline'); // Required for refresh_token
    authUrl.searchParams.set('prompt', 'consent'); // Force consent to always get refresh_token
    authUrl.searchParams.set('state', state);

    console.log('[Google OAuth Init] Authorization URL generated');

    return NextResponse.json({
      authUrl: authUrl.toString(),
      state
    });

  } catch (error: any) {
    console.error('[Google OAuth Init] Error:', error);
    return NextResponse.json(
      { error: error.message || 'OAuth initiation failed' },
      { status: 500 }
    );
  }
}
