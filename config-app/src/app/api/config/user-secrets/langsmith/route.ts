/**
 * GET /api/config/user-secrets/langsmith
 *
 * Returns the UNMASKED LangSmith API key for the authenticated user.
 * This endpoint is specifically for auto-populating localStorage on client mount.
 *
 * Security:
 * - Protected by Clerk authentication
 * - Supabase RLS ensures users can only access their own keys
 * - Used only for localStorage persistence across browser sessions
 */

import { auth } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";
import { createServerSupabaseClient } from "@/lib/supabase-client";

/**
 * GET - Retrieve user's LangSmith API key (unmasked)
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

    // Fetch the user's secrets
    const { data: secrets, error } = await supabase
      .from("user_secrets")
      .select("langsmith_api_key")
      .eq("clerk_id", userId)
      .single();

    if (error) {
      console.error("Error fetching LangSmith API key:", error);
      return NextResponse.json(
        { error: "Failed to fetch LangSmith API key" },
        { status: 500 }
      );
    }

    // Return unmasked key (or null if not set)
    return NextResponse.json({
      success: true,
      langsmith_api_key: secrets?.langsmith_api_key || null,
    });
  } catch (error) {
    console.error("Error in GET /api/config/user-secrets/langsmith:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
