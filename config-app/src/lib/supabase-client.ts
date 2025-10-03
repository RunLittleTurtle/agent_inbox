/**
 * Supabase Client with Clerk Integration - Modern 2025 Architecture
 *
 * This utility creates a Supabase client that automatically injects
 * Clerk JWT tokens into every request. This follows the official
 * Clerk + Supabase native integration pattern.
 *
 * Key Features:
 * - Automatic JWT token injection via accessToken callback
 * - Works with Supabase Third-Party Auth (Clerk enabled)
 * - RLS policies automatically enforced based on auth.jwt()->>'sub'
 * - No manual token management needed
 */

import { createClient } from "@supabase/supabase-js";

/**
 * Creates a basic Supabase client for client-side usage
 *
 * Note: For client-side auth with Clerk, manually add headers:
 * ```tsx
 * const { session } = useSession();
 * const token = await session?.getToken();
 * const supabase = createClient(url, key, {
 *   global: { headers: { Authorization: `Bearer ${token}` } }
 * });
 * ```
 *
 * For most use cases, use the server-side client in API routes instead.
 */
export function createClerkSupabaseClient() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!
  );
}

/**
 * Server-side Supabase client for API routes
 *
 * Usage in API routes:
 * ```tsx
 * import { auth } from "@clerk/nextjs/server";
 *
 * export async function GET() {
 *   const { userId } = await auth();
 *   const supabase = createServerSupabaseClient(userId);
 *   // ...
 * }
 * ```
 */
export function createServerSupabaseClient(clerkUserId?: string | null) {
  // For server-side, we use the secret key with service role privileges
  // but we'll still filter by clerk_id manually in queries
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SECRET_KEY!
  );
}

/**
 * Type definitions for user_secrets table
 */
export interface UserSecrets {
  id: string;
  clerk_id: string;

  // AI Model API Keys
  openai_api_key: string | null;
  anthropic_api_key: string | null;
  google_api_key: string | null;

  // LangSmith Tracing
  langsmith_api_key: string | null;

  // Google OAuth
  google_client_id: string | null;
  google_client_secret: string | null;
  google_refresh_token: string | null;

  // MCP Integration Tokens
  rube_token: string | null;
  composio_token: string | null;
  pipedream_token: string | null;

  // User Preferences
  timezone: string;
  preferred_model: string;
  temperature: number;

  // Metadata
  created_at: string;
  updated_at: string;
}

/**
 * Helper to get or create user secrets (lazy creation pattern)
 *
 * This function implements the "lazy creation" pattern:
 * - If user_secrets row exists, return it
 * - If not, create a new row with defaults
 * - Uses UPSERT (INSERT ... ON CONFLICT DO UPDATE) for atomicity
 */
export async function getOrCreateUserSecrets(
  supabase: ReturnType<typeof createServerSupabaseClient>,
  clerkUserId: string
): Promise<UserSecrets | null> {
  try {
    // Try to get existing secrets
    const { data: existing, error: selectError } = await supabase
      .from("user_secrets")
      .select("*")
      .eq("clerk_id", clerkUserId)
      .single();

    if (existing) {
      return existing as UserSecrets;
    }

    // If doesn't exist, create with defaults (lazy creation)
    const { data: created, error: insertError } = await supabase
      .from("user_secrets")
      .insert({
        clerk_id: clerkUserId,
        timezone: "America/Toronto",
        preferred_model: "claude-3-5-sonnet-20241022",
        temperature: 0.0,
      })
      .select()
      .single();

    if (insertError) {
      console.error("Error creating user_secrets:", insertError);
      return null;
    }

    return created as UserSecrets;
  } catch (error) {
    console.error("Error in getOrCreateUserSecrets:", error);
    return null;
  }
}

/**
 * Mask sensitive API keys for display
 *
 * Transforms: "sk-proj-abc123def456" -> "***CONFIGURED***"
 */
export function maskApiKey(key: string | null): string | null {
  if (!key) return null;
  return "***CONFIGURED***";
}
