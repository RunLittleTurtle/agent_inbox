/**
 * OAuth Initiation Endpoint
 * Starts the OAuth 2.1 flow for MCP server authentication
 */

import { auth } from '@clerk/nextjs/server';
import { NextRequest, NextResponse } from 'next/server';
import {
  generatePKCE,
  generateState,
  inferProvider,
  getDefaultScopes,
  discoverOAuthMetadata,
  registerClient
} from '@/lib/oauth-utils';
import { storeOAuthState } from '@/lib/redis-client';

export async function POST(req: NextRequest) {
  try {
    // 1. Authenticate user with Clerk
    const { userId } = await auth();

    if (!userId) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    // 2. Parse request body
    const { agent_id, mcp_url, provider } = await req.json();

    if (!agent_id || !mcp_url) {
      return NextResponse.json(
        { error: 'Missing required fields: agent_id, mcp_url' },
        { status: 400 }
      );
    }

    // 3. Infer provider if not specified
    const inferredProvider = provider || inferProvider(mcp_url);

    // 4. Discover OAuth endpoints from MCP server
    const metadata = await discoverOAuthMetadata(mcp_url);

    // 5. Dynamic client registration (if registration endpoint exists)
    let client_id = process.env.MCP_CLIENT_ID;

    if (metadata.registration_endpoint && !client_id) {
      const appUrl = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3004';
      const callback_url = `${appUrl}/api/mcp/oauth/callback`;

      const registration = await registerClient(metadata.registration_endpoint, {
        client_name: `Agent Inbox - ${agent_id}`,
        redirect_uris: [callback_url],
        grant_types: ['authorization_code', 'refresh_token'],
        response_types: ['code'],
        token_endpoint_auth_method: 'none' // Public client with PKCE
      });

      client_id = registration.client_id;

      console.log(`[OAuth] Registered client: ${client_id}`);
    }

    if (!client_id) {
      return NextResponse.json(
        { error: 'No client_id available. Set MCP_CLIENT_ID in .env or enable dynamic registration' },
        { status: 500 }
      );
    }

    // 6. Generate PKCE parameters
    const { code_verifier, code_challenge, code_challenge_method } = generatePKCE();

    // 7. Generate state for CSRF protection
    const state = generateState();

    // 8. Store PKCE state in Redis (10 min TTL)
    await storeOAuthState(state, {
      code_verifier,
      clerk_id: userId,
      agent_id,
      mcp_url,
      provider: inferredProvider
    });

    // 9. Build authorization URL
    const appUrl = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3004';
    const callback_url = `${appUrl}/api/mcp/oauth/callback`;
    const scopes = getDefaultScopes(inferredProvider);

    const authUrl = new URL(metadata.authorization_endpoint);
    authUrl.searchParams.set('client_id', client_id);
    authUrl.searchParams.set('redirect_uri', callback_url);
    authUrl.searchParams.set('response_type', 'code');
    authUrl.searchParams.set('code_challenge', code_challenge);
    authUrl.searchParams.set('code_challenge_method', code_challenge_method);
    authUrl.searchParams.set('resource', mcp_url); // Required by RFC 8707
    authUrl.searchParams.set('state', state);
    authUrl.searchParams.set('scope', scopes);

    console.log(`[OAuth] Initiated flow for ${agent_id} (${inferredProvider})`);

    return NextResponse.json({
      authUrl: authUrl.toString(),
      provider: inferredProvider,
      state
    });

  } catch (error: any) {
    console.error('[OAuth Initiate] Error:', error);

    return NextResponse.json(
      {
        error: 'OAuth initiation failed',
        message: error.message
      },
      { status: 500 }
    );
  }
}
