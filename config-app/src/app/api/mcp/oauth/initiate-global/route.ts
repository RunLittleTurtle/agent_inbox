/**
 * Initiate Global MCP OAuth Flow (user_secrets)
 * Similar to per-agent OAuth but stores tokens globally
 */

import { NextRequest, NextResponse } from 'next/server';
import { generatePKCE, generateState, inferProvider, getDefaultScopes, discoverOAuthMetadata } from '@/lib/oauth-utils';
import { createClient } from '@supabase/supabase-js';
import { auth } from '@clerk/nextjs/server';

// Supabase client with service role key (bypasses RLS for server operations)
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SECRET_KEY!
);

export async function POST(request: NextRequest) {
  try {
    // 1. Get authenticated user from Clerk
    const { userId } = await auth();
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // 2. Parse request body
    const body = await request.json();
    const { mcp_url } = body;

    if (!mcp_url) {
      return NextResponse.json({ error: 'mcp_url required' }, { status: 400 });
    }

    console.log(`[Global OAuth Init] Starting for user ${userId}, MCP URL: ${mcp_url}`);

    // 3. Generate PKCE parameters (RFC 7636)
    const pkceParams = generatePKCE();
    console.log('[Global OAuth Init] Generated PKCE params');

    // 4. Generate state for CSRF protection
    const state = generateState();

    // 5. Infer provider from MCP URL
    const provider = inferProvider(mcp_url);
    console.log(`[Global OAuth Init] Detected provider: ${provider}`);

    // 6. Discover OAuth metadata from MCP server
    const metadata = await discoverOAuthMetadata(mcp_url);
    console.log('[Global OAuth Init] Discovered OAuth metadata:', metadata.authorization_endpoint);

    // 7. Get client_id from environment
    const client_id = process.env.MCP_CLIENT_ID;
    if (!client_id) {
      throw new Error('MCP_CLIENT_ID not configured');
    }

    // 8. Build callback URL (global endpoint)
    const callback_url = `${process.env.NEXT_PUBLIC_APP_URL}/api/mcp/oauth/callback-global`;

    // 9. Store PKCE state in Supabase for later verification
    // We'll store this temporarily in a global_oauth_states table or session
    const { error: stateError } = await supabase
      .from('oauth_states')
      .upsert({
        state,
        clerk_id: userId,
        code_verifier: pkceParams.code_verifier,
        mcp_url,
        provider,
        is_global: true, // Mark as global OAuth (not agent-specific)
        created_at: new Date().toISOString(),
        expires_at: new Date(Date.now() + 10 * 60 * 1000).toISOString() // 10 min expiry
      });

    if (stateError) {
      console.error('[Global OAuth Init] Error storing state:', stateError);
      throw stateError;
    }

    // 10. Get default scopes for provider
    const scopes = getDefaultScopes(provider);

    // 11. Build authorization URL
    const authUrl = new URL(metadata.authorization_endpoint);
    authUrl.searchParams.set('client_id', client_id);
    authUrl.searchParams.set('redirect_uri', callback_url);
    authUrl.searchParams.set('response_type', 'code');
    authUrl.searchParams.set('state', state);
    authUrl.searchParams.set('code_challenge', pkceParams.code_challenge);
    authUrl.searchParams.set('code_challenge_method', 'S256');
    authUrl.searchParams.set('scope', scopes);
    authUrl.searchParams.set('resource', mcp_url);

    console.log('[Global OAuth Init] Authorization URL generated');

    return NextResponse.json({
      authUrl: authUrl.toString(),
      state,
      provider
    });

  } catch (error: any) {
    console.error('[Global OAuth Init] Error:', error);
    return NextResponse.json(
      { error: error.message || 'OAuth initiation failed' },
      { status: 500 }
    );
  }
}
