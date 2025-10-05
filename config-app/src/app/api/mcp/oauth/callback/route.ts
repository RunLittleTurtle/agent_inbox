/**
 * OAuth Callback Endpoint
 * Handles the OAuth 2.1 callback and token exchange
 */

import { NextRequest, NextResponse } from 'next/server';
import { getOAuthState, deleteOAuthState } from '@/lib/redis-client';
import { discoverOAuthMetadata } from '@/lib/oauth-utils';
import { encrypt } from '@/lib/encryption';
import { createClient } from '@supabase/supabase-js';

export async function GET(req: NextRequest) {
  try {
    // 1. Extract code and state from query parameters
    const { searchParams } = new URL(req.url);
    const code = searchParams.get('code');
    const state = searchParams.get('state');
    const error = searchParams.get('error');
    const errorDescription = searchParams.get('error_description');

    // Check for OAuth error
    if (error) {
      console.error(`[OAuth Callback] Error: ${error} - ${errorDescription}`);
      return new NextResponse(renderErrorPage(errorDescription || error), {
        headers: { 'Content-Type': 'text/html' }
      });
    }

    if (!code || !state) {
      return new NextResponse(renderErrorPage('Missing code or state parameter'), {
        headers: { 'Content-Type': 'text/html' }
      });
    }

    // 2. Retrieve and validate state from Redis
    const sessionData = await getOAuthState(state);

    if (!sessionData) {
      return new NextResponse(renderErrorPage('Invalid or expired state. Please try again.'), {
        headers: { 'Content-Type': 'text/html' }
      });
    }

    const { code_verifier, clerk_id, agent_id, mcp_url, provider, client_id } = sessionData;

    // 3. Discover token endpoint
    const metadata = await discoverOAuthMetadata(mcp_url);

    // 4. Exchange authorization code for tokens
    const appUrl = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3004';
    const callback_url = `${appUrl}/api/mcp/oauth/callback`;

    if (!client_id) {
      return new NextResponse(renderErrorPage('No client_id available'), {
        headers: { 'Content-Type': 'text/html' }
      });
    }

    const tokenResponse = await fetch(metadata.token_endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: new URLSearchParams({
        grant_type: 'authorization_code',
        code,
        redirect_uri: callback_url,
        code_verifier,
        client_id,
        resource: mcp_url // Required by RFC 8707
      })
    });

    if (!tokenResponse.ok) {
      const errorText = await tokenResponse.text();
      console.error('[OAuth Callback] Token exchange failed:', errorText);
      return new NextResponse(renderErrorPage('Token exchange failed'), {
        headers: { 'Content-Type': 'text/html' }
      });
    }

    const tokens = await tokenResponse.json();

    // 5. Encrypt tokens before storing
    const encryptedAccessToken = encrypt(tokens.access_token);
    const encryptedRefreshToken = tokens.refresh_token
      ? encrypt(tokens.refresh_token)
      : null;

    // 6. Calculate token expiration
    const expiresAt = new Date(Date.now() + (tokens.expires_in * 1000));

    // 7. Store encrypted tokens in Supabase agent_configs
    const supabase = createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.SUPABASE_SECRET_KEY!
    );

    // Get existing config (if any)
    const { data: existingConfig } = await supabase
      .from('agent_configs')
      .select('config_data')
      .eq('clerk_id', clerk_id)
      .eq('agent_id', agent_id)
      .single();

    // Build updated config_data with mcp_integration
    const updatedConfigData = {
      ...(existingConfig?.config_data || {}),
      mcp_integration: {
        mcp_server_url: mcp_url,
        auth_type: 'oauth',
        oauth_tokens: {
          access_token: encryptedAccessToken,
          refresh_token: encryptedRefreshToken,
          token_type: tokens.token_type || 'Bearer',
          expires_at: expiresAt.toISOString(),
          scopes: tokens.scope?.split(' ') || []
        },
        provider_metadata: {
          provider,
          connected_at: new Date().toISOString(),
          issuer: metadata.issuer
        }
      }
    };

    // Upsert agent config
    await supabase
      .from('agent_configs')
      .upsert({
        clerk_id,
        agent_id,
        agent_name: agent_id.replace('_agent', ''),
        config_data: updatedConfigData
      }, {
        onConflict: 'clerk_id,agent_id'
      });

    // 8. Clean up state from Redis
    await deleteOAuthState(state);

    console.log(`[OAuth] Successfully connected ${agent_id} to ${provider}`);

    // 9. Return success page that closes popup
    return new NextResponse(renderSuccessPage(), {
      headers: { 'Content-Type': 'text/html' }
    });

  } catch (error: any) {
    console.error('[OAuth Callback] Error:', error);

    return new NextResponse(renderErrorPage(error.message), {
      headers: { 'Content-Type': 'text/html' }
    });
  }
}

/**
 * Render success page that closes popup and notifies parent window
 */
function renderSuccessPage(): string {
  return `
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Apps Connected</title>
        <style>
          body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
          }
          .container {
            text-align: center;
            padding: 2rem;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 1rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
          }
          h1 {
            font-size: 2rem;
            margin-bottom: 1rem;
          }
          p {
            font-size: 1.1rem;
            opacity: 0.9;
          }
          .checkmark {
            font-size: 4rem;
            margin-bottom: 1rem;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="checkmark">✓</div>
          <h1>Apps Connected Successfully!</h1>
          <p>You can close this window now.</p>
        </div>
        <script>
          if (window.opener) {
            window.opener.postMessage({ type: 'mcp_oauth_complete' }, '*');
            setTimeout(() => window.close(), 1500);
          }
        </script>
      </body>
    </html>
  `;
}

/**
 * Render error page that notifies parent window
 */
function renderErrorPage(error: string): string {
  return `
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Connection Failed</title>
        <style>
          body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
          }
          .container {
            text-align: center;
            padding: 2rem;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 1rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            max-width: 500px;
          }
          h1 {
            font-size: 2rem;
            margin-bottom: 1rem;
          }
          p {
            font-size: 1rem;
            opacity: 0.9;
            word-wrap: break-word;
          }
          .error-icon {
            font-size: 4rem;
            margin-bottom: 1rem;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="error-icon">✗</div>
          <h1>Connection Failed</h1>
          <p>${error}</p>
          <p style="margin-top: 1rem; font-size: 0.9rem;">This window will close automatically.</p>
        </div>
        <script>
          if (window.opener) {
            window.opener.postMessage({
              type: 'mcp_oauth_error',
              error: '${error.replace(/'/g, "\\'")}'
            }, '*');
            setTimeout(() => window.close(), 3000);
          }
        </script>
      </body>
    </html>
  `;
}
