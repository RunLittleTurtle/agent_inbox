/**
 * OAuth 2.1 Utilities for MCP OAuth Flow
 * Implements PKCE (RFC 7636) and state generation
 */

import crypto from 'crypto';

/**
 * Generate a cryptographically secure random string
 * @param length Length of the random string (default: 128 for code_verifier)
 */
export function generateRandomString(length: number = 128): string {
  const bytes = crypto.randomBytes(length);
  return base64UrlEncode(bytes);
}

/**
 * Base64 URL encode (RFC 4648)
 * Replaces '+' with '-', '/' with '_', and removes '=' padding
 */
export function base64UrlEncode(buffer: Buffer): string {
  return buffer
    .toString('base64')
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '');
}

/**
 * Generate PKCE parameters (RFC 7636)
 * Returns code_verifier and code_challenge for OAuth 2.1 flow
 */
export interface PKCEParams {
  code_verifier: string;
  code_challenge: string;
  code_challenge_method: 'S256';
}

export function generatePKCE(): PKCEParams {
  // Generate code_verifier (43-128 characters)
  const code_verifier = generateRandomString(64); // Results in ~86 chars after base64url

  // Generate code_challenge = BASE64URL(SHA256(code_verifier))
  const hash = crypto.createHash('sha256').update(code_verifier).digest();
  const code_challenge = base64UrlEncode(hash);

  return {
    code_verifier,
    code_challenge,
    code_challenge_method: 'S256'
  };
}

/**
 * Generate a random state parameter for CSRF protection
 */
export function generateState(): string {
  return generateRandomString(32); // Results in ~43 chars
}

/**
 * Infer MCP provider from URL
 */
export function inferProvider(mcpUrl: string): string {
  const url = mcpUrl.toLowerCase();

  if (url.includes('rube.app')) return 'rube';
  if (url.includes('pipedream')) return 'pipedream_v2';

  return 'generic';
}

/**
 * Get default scopes for MCP provider
 */
export function getDefaultScopes(provider: string): string {
  const scopeMap: Record<string, string> = {
    'rube': 'openid email profile offline_access',
    'pipedream_v2': 'openid email profile offline_access',
    'generic': 'openid email profile offline_access'
  };

  return scopeMap[provider] || scopeMap.generic;
}

/**
 * Discover OAuth endpoints from MCP server
 */
export interface OAuthMetadata {
  issuer: string;
  authorization_endpoint: string;
  token_endpoint: string;
  registration_endpoint?: string;
  jwks_uri?: string;
  scopes_supported?: string[];
  code_challenge_methods_supported?: string[];
}

export async function discoverOAuthMetadata(mcpUrl: string): Promise<OAuthMetadata> {
  // Step 1: Get protected resource metadata
  const resourceUrl = new URL(mcpUrl);
  const wellKnownUrl = `${resourceUrl.protocol}//${resourceUrl.host}/.well-known/oauth-protected-resource`;

  const resourceResponse = await fetch(wellKnownUrl);
  if (!resourceResponse.ok) {
    throw new Error(`Failed to fetch protected resource metadata: ${resourceResponse.statusText}`);
  }

  const resourceMetadata = await resourceResponse.json();
  const authServerUrl = resourceMetadata.authorization_servers?.[0];

  if (!authServerUrl) {
    throw new Error('No authorization server found in protected resource metadata');
  }

  // Step 2: Get authorization server metadata
  const authServerMetadataUrl = `${authServerUrl}/.well-known/oauth-authorization-server`;

  const authResponse = await fetch(authServerMetadataUrl);
  if (!authResponse.ok) {
    throw new Error(`Failed to fetch authorization server metadata: ${authResponse.statusText}`);
  }

  const metadata: OAuthMetadata = await authResponse.json();

  return metadata;
}

/**
 * Register dynamic OAuth client (RFC 7591)
 */
export interface ClientRegistrationRequest {
  client_name: string;
  redirect_uris: string[];
  grant_types: string[];
  response_types: string[];
  token_endpoint_auth_method: 'none'; // Public client with PKCE
}

export interface ClientRegistrationResponse {
  client_id: string;
  client_id_issued_at?: number;
  client_name: string;
  redirect_uris: string[];
  grant_types: string[];
  response_types: string[];
  token_endpoint_auth_method: string;
}

export async function registerClient(
  registrationEndpoint: string,
  request: ClientRegistrationRequest
): Promise<ClientRegistrationResponse> {
  const response = await fetch(registrationEndpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(request)
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Client registration failed: ${error}`);
  }

  return await response.json();
}
