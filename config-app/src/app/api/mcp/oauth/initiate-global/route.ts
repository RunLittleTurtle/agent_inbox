/**
 * Initiate Global MCP OAuth Flow (user_secrets)
 * Similar to per-agent OAuth but stores tokens globally
 */

import { NextRequest, NextResponse } from 'next/server';
import { generatePKCE, generateState, inferProvider, getDefaultScopes, discoverOAuthMetadata, registerClient } from '@/lib/oauth-utils';
import { storeOAuthState } from '@/lib/redis-client';
import { auth } from '@clerk/nextjs/server';

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

    // 7. Dynamic client registration (if registration endpoint exists)
    let client_id = process.env.MCP_CLIENT_ID;

    if (metadata.registration_endpoint && !client_id) {
      const appUrl = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3004';
      const callback_url = `${appUrl}/api/mcp/oauth/callback-global`;

      const registration = await registerClient(metadata.registration_endpoint, {
        client_name: `Agent Inbox - Global MCP`,
        redirect_uris: [callback_url],
        grant_types: ['authorization_code', 'refresh_token'],
        response_types: ['code'],
        token_endpoint_auth_method: 'none' // Public client with PKCE
      });

      client_id = registration.client_id;

      console.log(`[Global OAuth] Registered client: ${client_id}`);
    }

    if (!client_id) {
      throw new Error('No client_id available. Set MCP_CLIENT_ID in .env or enable dynamic registration');
    }

    // 8. Build callback URL (global endpoint)
    const callback_url = `${process.env.NEXT_PUBLIC_APP_URL}/api/mcp/oauth/callback-global`;

    // 9. Store PKCE state in Redis (10 min TTL) - SAME as multi-tool
    await storeOAuthState(state, {
      code_verifier: pkceParams.code_verifier,
      clerk_id: userId,
      mcp_url,
      provider,
      client_id,
      is_global: true // Mark as global OAuth (not agent-specific)
    });

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
