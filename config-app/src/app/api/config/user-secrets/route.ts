/**
 * GET /api/config/user-secrets
 * POST /api/config/user-secrets
 *
 * Modern 2025 API routes for user configuration with Clerk + Supabase.
 * Replaces the old .env file-based configuration system.
 *
 * Architecture:
 * - Clerk: Authentication & JWT tokens
 * - Supabase: Data storage with RLS
 * - Lazy creation: user_secrets row created on first access
 */

import { auth } from "@clerk/nextjs/server";
import { NextResponse, NextRequest } from "next/server";
import {
  createServerSupabaseClient,
  getOrCreateUserSecrets,
  maskApiKey,
} from "@/lib/supabase-client";

/**
 * GET - Retrieve user's configuration (secrets masked)
 */
export async function GET() {
  try {
    const { userId } = await auth();

    if (!userId) {
      return NextResponse.json(
        { error: "Unauthorized - Please sign in" },
        { status: 401 }
      );
    }

    const supabase = createServerSupabaseClient(userId);
    const secrets = await getOrCreateUserSecrets(supabase, userId);

    if (!secrets) {
      return NextResponse.json(
        { error: "Failed to load configuration" },
        { status: 500 }
      );
    }

    // Return masked secrets
    return NextResponse.json({
      success: true,
      data: {
        // AI Model Keys (masked for security)
        openai_api_key: maskApiKey(secrets.openai_api_key),
        anthropic_api_key: maskApiKey(secrets.anthropic_api_key),
        google_api_key: maskApiKey(secrets.google_api_key),

        // LangSmith
        langsmith_api_key: maskApiKey(secrets.langsmith_api_key),

        // Google OAuth
        google_client_id: maskApiKey(secrets.google_client_id),
        google_client_secret: maskApiKey(secrets.google_client_secret),
        google_refresh_token: maskApiKey(secrets.google_refresh_token),

        // MCP Tokens
        rube_token: maskApiKey(secrets.rube_token),
        composio_token: maskApiKey(secrets.composio_token),
        pipedream_token: maskApiKey(secrets.pipedream_token),

        // User Preferences (not masked)
        timezone: secrets.timezone,
        preferred_model: secrets.preferred_model,
        temperature: secrets.temperature,
      },
    });
  } catch (error) {
    console.error("Error in GET /api/config/user-secrets:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

/**
 * POST - Update user's configuration
 *
 * Body: { field: string, value: string }
 * Example: { field: "openai_api_key", value: "sk-proj-..." }
 */
export async function POST(request: NextRequest) {
  try {
    const { userId } = await auth();

    if (!userId) {
      return NextResponse.json(
        { error: "Unauthorized - Please sign in" },
        { status: 401 }
      );
    }

    const body = await request.json();
    const { field, value } = body;

    if (!field || value === undefined) {
      return NextResponse.json(
        { error: "Missing required fields: field, value" },
        { status: 400 }
      );
    }

    // Validate allowed fields
    const allowedFields = [
      "openai_api_key",
      "anthropic_api_key",
      "google_api_key",
      "langsmith_api_key",
      "google_client_id",
      "google_client_secret",
      "google_refresh_token",
      "rube_token",
      "composio_token",
      "pipedream_token",
      "timezone",
      "preferred_model",
      "temperature",
    ];

    if (!allowedFields.includes(field)) {
      return NextResponse.json(
        { error: `Invalid field: ${field}` },
        { status: 400 }
      );
    }

    // TODO: Add API key validation here
    // For now, just save the value

    const supabase = createServerSupabaseClient(userId);

    // Use UPSERT pattern (lazy creation)
    const { data, error } = await supabase
      .from("user_secrets")
      .upsert(
        {
          clerk_id: userId,
          [field]: value,
          updated_at: new Date().toISOString(),
        },
        {
          onConflict: "clerk_id",
        }
      )
      .select()
      .single();

    if (error) {
      console.error("Error updating user_secrets:", error);
      return NextResponse.json(
        { error: "Failed to update configuration" },
        { status: 500 }
      );
    }

    return NextResponse.json({
      success: true,
      message: `${field} updated successfully`,
    });
  } catch (error) {
    console.error("Error in POST /api/config/user-secrets:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
