/**
 * Global MCP OAuth Callback (user_secrets)
 * Handles OAuth callback and stores tokens in user_secrets.mcp_universal
 */

import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';
import crypto from 'crypto';

// Supabase client with service role key
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SECRET_KEY!
);

// Encryption utilities (same as Python mcp_auth.py)
function getEncryptionKey(): Buffer {
  const keyHex = process.env.ENCRYPTION_KEY;
  if (!keyHex || keyHex.length !== 64) {
    throw new Error('ENCRYPTION_KEY must be 64 hex characters (32 bytes)');
  }
  return Buffer.from(keyHex, 'hex');
}

function encryptToken(text: string): string {
  const key = getEncryptionKey();
  const iv = crypto.randomBytes(16); // 16 bytes for GCM

  const cipher = crypto.createCipheriv('aes-256-gcm', key, iv);
  const encrypted = Buffer.concat([cipher.update(text, 'utf8'), cipher.final()]);
  const authTag = cipher.getAuthTag();

  // Format: iv:authTag:encrypted (all hex)
  return `${iv.toString('hex')}:${authTag.toString('hex')}:${encrypted.toString('hex')}`;
}

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const code = searchParams.get('code');
    const state = searchParams.get('state');
    const error = searchParams.get('error');

    // 1. Handle OAuth errors
    if (error) {
      console.error('[Global OAuth Callback] OAuth error:', error);
      return new NextResponse(
        `<html><body><script>window.opener.postMessage({type: 'mcp_oauth_error', error: '${error}'}, '*'); window.close();</script></body></html>`,
        { headers: { 'Content-Type': 'text/html' } }
      );
    }

    if (!code || !state) {
      return NextResponse.json({ error: 'Missing code or state' }, { status: 400 });
    }

    console.log('[Global OAuth Callback] Received code and state');

    // 2. Retrieve stored PKCE state
    const { data: storedState, error: stateError } = await supabase
      .from('oauth_states')
      .select('*')
      .eq('state', state)
      .eq('is_global', true)
      .single();

    if (stateError || !storedState) {
      console.error('[Global OAuth Callback] Invalid state:', stateError);
      return new NextResponse(
        `<html><body><script>window.opener.postMessage({type: 'mcp_oauth_error', error: 'Invalid state'}, '*'); window.close();</script></body></html>`,
        { headers: { 'Content-Type': 'text/html' } }
      );
    }

    const { clerk_id, code_verifier, mcp_url, provider } = storedState;

    console.log(`[Global OAuth Callback] Found state for user ${clerk_id}`);

    // 3. Discover token endpoint from MCP server
    const metadataUrl = `${mcp_url.split('/mcp')[0]}/.well-known/oauth-authorization-server`;
    const metadataResponse = await fetch(metadataUrl);
    if (!metadataResponse.ok) {
      throw new Error('Failed to fetch OAuth metadata');
    }
    const metadata = await metadataResponse.json();
    const tokenEndpoint = metadata.token_endpoint;

    // 4. Exchange authorization code for tokens (with PKCE)
    const callback_url = `${process.env.NEXT_PUBLIC_APP_URL}/api/mcp/oauth/callback-global`;
    const client_id = process.env.MCP_CLIENT_ID!;

    const tokenResponse = await fetch(tokenEndpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        grant_type: 'authorization_code',
        code,
        redirect_uri: callback_url,
        client_id,
        code_verifier,
        resource: mcp_url
      })
    });

    if (!tokenResponse.ok) {
      const errorText = await tokenResponse.text();
      console.error('[Global OAuth Callback] Token exchange failed:', errorText);
      throw new Error(`Token exchange failed: ${errorText}`);
    }

    const tokens = await tokenResponse.json();
    console.log('[Global OAuth Callback] Token exchange successful');

    // 5. Encrypt tokens
    const encryptedAccessToken = encryptToken(tokens.access_token);
    const encryptedRefreshToken = encryptToken(tokens.refresh_token);

    // 6. Calculate expiry
    const expiresAt = new Date(Date.now() + (tokens.expires_in || 3600) * 1000).toISOString();

    // 7. Store in user_secrets.mcp_universal (GLOBAL)
    const mcp_universal = {
      provider,
      mcp_server_url: mcp_url,
      oauth_tokens: {
        access_token: encryptedAccessToken,
        refresh_token: encryptedRefreshToken,
        expires_at: expiresAt,
        token_type: tokens.token_type || 'Bearer'
      }
    };

    const { error: updateError } = await supabase
      .from('user_secrets')
      .upsert({
        clerk_id,
        mcp_universal
      }, {
        onConflict: 'clerk_id'
      });

    if (updateError) {
      console.error('[Global OAuth Callback] Error saving tokens:', updateError);
      throw updateError;
    }

    console.log('[Global OAuth Callback] Tokens saved to user_secrets.mcp_universal');

    // 8. Clean up state
    await supabase.from('oauth_states').delete().eq('state', state);

    // 9. Return success to popup
    return new NextResponse(
      `<html><body><script>window.opener.postMessage({type: 'mcp_oauth_complete'}, '*'); window.close();</script></body></html>`,
      { headers: { 'Content-Type': 'text/html' } }
    );

  } catch (error: any) {
    console.error('[Global OAuth Callback] Error:', error);
    return new NextResponse(
      `<html><body><script>window.opener.postMessage({type: 'mcp_oauth_error', error: '${error.message}'}, '*'); window.close();</script></body></html>`,
      { headers: { 'Content-Type': 'text/html' } }
    );
  }
}
