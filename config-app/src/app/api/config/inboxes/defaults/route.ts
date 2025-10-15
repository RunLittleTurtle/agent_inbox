import { auth } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";
import { createServerSupabaseClient } from "@/lib/supabase-client";

// Default inboxes configuration (same as parent route)
const DEFAULT_INBOXES = [
  {
    inbox_name: "Agent Inbox",
    graph_id: "agent",
    deployment_url: "https://multi-agent-app-1d1e061875eb5640a47e3bb201edb076.us.langgraph.app",
    is_default: true,
    selected: true, // First inbox is selected by default
  },
  {
    inbox_name: "Executive Main",
    graph_id: "executive_main",
    deployment_url: "https://multi-agent-app-1d1e061875eb5640a47e3bb201edb076.us.langgraph.app",
    is_default: true,
    selected: false,
  },
];

/**
 * POST /api/config/inboxes/defaults
 * Create default inboxes for a user (manual action via button)
 * Only creates defaults that don't already exist
 */
export async function POST() {
  try {
    const { userId, sessionClaims } = await auth();

    if (!userId) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const email = (sessionClaims?.email as string) || null;
    const supabase = createServerSupabaseClient(userId);

    // Check which defaults already exist
    const { data: existingInboxes, error: fetchError } = await supabase
      .from("user_inboxes")
      .select("graph_id")
      .eq("clerk_id", userId)
      .in("graph_id", DEFAULT_INBOXES.map(inbox => inbox.graph_id));

    if (fetchError) {
      console.error("Error checking existing inboxes:", fetchError);
      return NextResponse.json(
        { error: "Failed to check existing inboxes" },
        { status: 500 }
      );
    }

    const existingGraphIds = new Set(
      existingInboxes?.map(inbox => inbox.graph_id) || []
    );

    // Filter out defaults that already exist
    const inboxesToCreate = DEFAULT_INBOXES
      .filter(inbox => !existingGraphIds.has(inbox.graph_id))
      .map(inbox => ({
        clerk_id: userId,
        email,
        ...inbox,
      }));

    if (inboxesToCreate.length === 0) {
      return NextResponse.json({
        success: true,
        message: "All default inboxes already exist",
        created: [],
      });
    }

    // Create missing defaults
    const { data: createdInboxes, error: createError } = await supabase
      .from("user_inboxes")
      .insert(inboxesToCreate)
      .select();

    if (createError) {
      console.error("Error creating default inboxes:", createError);
      return NextResponse.json(
        { error: "Failed to create default inboxes" },
        { status: 500 }
      );
    }

    console.log(
      `[Defaults Created] User ${userId} created ${createdInboxes.length} default inboxes`
    );

    return NextResponse.json({
      success: true,
      message: `Created ${createdInboxes.length} default inbox(es)`,
      created: createdInboxes,
    });
  } catch (error) {
    console.error("Error in POST /api/config/inboxes/defaults:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
