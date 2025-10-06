/**
 * Google OAuth Callback Handler
 * Exchanges authorization code for access_token + refresh_token
 * Saves refresh_token to Supabase user_secrets
 */

import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

const GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const code = searchParams.get('code');
    const state = searchParams.get('state');
    const error = searchParams.get('error');

    // Handle OAuth errors (user denied permission, etc.)
    if (error) {
      console.error('[Google OAuth Callback] OAuth error:', error);
      return NextResponse.redirect(
        new URL(`/oauth/google/error?error=${encodeURIComponent(error)}`, request.url)
      );
    }

    if (!code || !state) {
      console.error('[Google OAuth Callback] Missing code or state');
      return NextResponse.redirect(
        new URL('/oauth/google/error?error=missing_parameters', request.url)
      );
    }

    // 1. Decode and validate state
    let stateData: any;
    try {
      stateData = JSON.parse(Buffer.from(state, 'base64url').toString());
    } catch (err) {
      console.error('[Google OAuth Callback] Invalid state:', err);
      return NextResponse.redirect(
        new URL('/oauth/google/error?error=invalid_state', request.url)
      );
    }

    const { clerk_id } = stateData;
    if (!clerk_id) {
      console.error('[Google OAuth Callback] No clerk_id in state');
      return NextResponse.redirect(
        new URL('/oauth/google/error?error=invalid_state', request.url)
      );
    }

    console.log(`[Google OAuth Callback] Processing for user ${clerk_id}`);

    // 2. Get global Google OAuth credentials from environment
    const clientId = process.env.GOOGLE_CLIENT_ID;
    const clientSecret = process.env.GOOGLE_CLIENT_SECRET;

    if (!clientId || !clientSecret) {
      console.error('[Google OAuth Callback] Missing global OAuth credentials');
      return NextResponse.redirect(
        new URL('/oauth/google/error?error=credentials_not_found&hint=Global+OAuth+not+configured', request.url)
      );
    }

    // Initialize Supabase for saving refresh_token
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const supabaseKey = process.env.SUPABASE_SECRET_KEY;

    if (!supabaseUrl || !supabaseKey) {
      throw new Error('Supabase configuration missing');
    }

    const supabase = createClient(supabaseUrl, supabaseKey);

    // 3. Exchange authorization code for tokens
    const appUrl = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3004';
    const redirectUri = `${appUrl}/api/oauth/google/callback`;

    const tokenResponse = await fetch(GOOGLE_TOKEN_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        code,
        client_id: clientId,
        client_secret: clientSecret,
        redirect_uri: redirectUri,
        grant_type: 'authorization_code',
      }),
    });

    if (!tokenResponse.ok) {
      const errorData = await tokenResponse.json();
      console.error('[Google OAuth Callback] Token exchange failed:', errorData);
      return NextResponse.redirect(
        new URL(`/oauth/google/error?error=token_exchange_failed&details=${encodeURIComponent(errorData.error || 'unknown')}`, request.url)
      );
    }

    const tokens = await tokenResponse.json();

    // 4. Verify we got a refresh_token
    if (!tokens.refresh_token) {
      console.error('[Google OAuth Callback] No refresh_token received');
      return NextResponse.redirect(
        new URL('/oauth/google/error?error=no_refresh_token&hint=Try+revoking+access+and+reconnecting', request.url)
      );
    }

    console.log(`[Google OAuth Callback] Successfully received refresh_token for user ${clerk_id}`);

    // 5. Save refresh_token to Supabase user_secrets
    const { error: updateError } = await supabase
      .from('user_secrets')
      .update({
        google_refresh_token: tokens.refresh_token,
        // Optionally store access_token and expiry for immediate use
        // (will be refreshed automatically by agents)
      })
      .eq('clerk_id', clerk_id);

    if (updateError) {
      console.error('[Google OAuth Callback] Failed to save refresh_token:', updateError);
      return NextResponse.redirect(
        new URL('/oauth/google/error?error=save_failed', request.url)
      );
    }

    console.log(`[Google OAuth Callback] refresh_token saved successfully for user ${clerk_id}`);

    // 6. Redirect to success page
    return NextResponse.redirect(
      new URL('/oauth/google/success', request.url)
    );

  } catch (error: any) {
    console.error('[Google OAuth Callback] Unexpected error:', error);
    return NextResponse.redirect(
      new URL(`/oauth/google/error?error=${encodeURIComponent(error.message || 'unexpected_error')}`, request.url)
    );
  }
}
