# MCP OAuth 2.1 Implementation Findings

## Rube MCP Server (https://rube.app/mcp)

### Discovery Process ✅

1. **Initial Request** (No Auth):
   ```bash
   GET https://rube.app/mcp
   Response: 401 Unauthorized
   WWW-Authenticate: Bearer error="invalid_token",
                     error_description="No authorization provided",
                     resource_metadata="https://rube.app/.well-known/oauth-protected-resource"
   ```

2. **Protected Resource Metadata**:
   ```bash
   GET https://rube.app/.well-known/oauth-protected-resource
   ```
   ```json
   {
     "resource": "https://rube.app/mcp",
     "authorization_servers": ["https://rube.app"],
     "jwks_uri": "https://rube.app/api/auth/mcp/jwks",
     "bearer_methods_supported": ["header", "body"],
     "resource_documentation": "https://rube.app/docs",
     "resource_registration": "https://rube.app/api/auth/mcp/auth"
   }
   ```

3. **Authorization Server Metadata**:
   ```bash
   GET https://rube.app/.well-known/oauth-authorization-server
   ```
   ```json
   {
     "issuer": "https://login.composio.dev",
     "authorization_endpoint": "https://rube.app/api/auth/mcp/authorize",
     "token_endpoint": "https://rube.app/api/auth/mcp/token",
     "registration_endpoint": "https://rube.app/api/auth/mcp/register",
     "jwks_uri": "https://rube.app/api/auth/mcp/jwks",
     "introspection_endpoint": "https://login.composio.dev/oauth2/introspection",
     "code_challenge_methods_supported": ["S256"],
     "grant_types_supported": ["authorization_code", "refresh_token"],
     "response_types_supported": ["code"],
     "response_modes_supported": ["query"],
     "scopes_supported": ["email", "offline_access", "openid", "profile"],
     "token_endpoint_auth_methods_supported": ["none", "client_secret_post", "client_secret_basic"]
   }
   ```

### OAuth Flow Implementation

#### 1. Dynamic Client Registration (Optional)
```typescript
POST https://rube.app/api/auth/mcp/register
Content-Type: application/json

{
  "client_name": "Agent Inbox Config App",
  "redirect_uris": ["https://config.mekanize.app/api/mcp/oauth/callback"],
  "grant_types": ["authorization_code", "refresh_token"],
  "response_types": ["code"],
  "token_endpoint_auth_method": "none"  // Public client (PKCE only)
}
```

Response:
```json
{
  "client_id": "generated_client_id",
  "client_secret": null,  // Not needed for PKCE
  "redirect_uris": [...],
  "grant_types": [...]
}
```

#### 2. Authorization Request (with PKCE)
```typescript
// Generate PKCE
const code_verifier = generateRandomString(128);
const code_challenge = base64url(sha256(code_verifier));

// Build authorization URL
const authUrl = new URL("https://rube.app/api/auth/mcp/authorize");
authUrl.searchParams.set("client_id", client_id);
authUrl.searchParams.set("redirect_uri", callback_url);
authUrl.searchParams.set("response_type", "code");
authUrl.searchParams.set("code_challenge", code_challenge);
authUrl.searchParams.set("code_challenge_method", "S256");
authUrl.searchParams.set("resource", "https://rube.app/mcp");  // REQUIRED (RFC 8707)
authUrl.searchParams.set("state", random_state);
authUrl.searchParams.set("scope", "openid email profile offline_access");
```

#### 3. Token Exchange
```typescript
POST https://rube.app/api/auth/mcp/token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code
&code={authorization_code}
&redirect_uri={callback_url}
&code_verifier={code_verifier}
&client_id={client_id}
&resource=https://rube.app/mcp  // REQUIRED
```

Response:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "openid email profile offline_access"
}
```

#### 4. Using the Access Token
```bash
GET https://rube.app/mcp
Authorization: Bearer {access_token}
```

#### 5. Token Refresh
```typescript
POST https://rube.app/api/auth/mcp/token
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token
&refresh_token={refresh_token}
&client_id={client_id}
&resource=https://rube.app/mcp
```

### Security Requirements ✅

- [x] HTTPS for all endpoints
- [x] PKCE (S256) required
- [x] Resource parameter (RFC 8707) required
- [x] State parameter for CSRF protection
- [x] Short-lived access tokens
- [x] Refresh token support

### Implementation Notes

1. **Public Client**: Use `token_endpoint_auth_method: "none"` with PKCE
2. **Resource Parameter**: Always include `resource=https://rube.app/mcp` in:
   - Authorization request
   - Token request
   - Refresh token request
3. **State Storage**: Use Redis/Upstash to store PKCE state (10 min TTL)
4. **Token Storage**: Encrypt tokens (AES-256-GCM) before storing in Supabase

### Next Steps

1. ✅ Test dynamic client registration
2. Generate ENCRYPTION_KEY for token encryption
3. Implement OAuth initiation endpoint
4. Implement OAuth callback endpoint
5. Update MCPConfigCard UI with "Connect Apps" button
6. Store encrypted tokens in Supabase `agent_configs.config_data.mcp_integration`

## Pipedream v2 MCP (https://mcp.pipedream.net/v2)

TODO: Test OAuth discovery for Pipedream v2
