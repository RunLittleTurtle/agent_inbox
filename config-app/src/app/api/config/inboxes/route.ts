import { auth } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";
import { createServerSupabaseClient } from "@/lib/supabase-client";

// Type for inbox stored in Supabase
interface UserInbox {
  id: string;
  clerk_id: string;
  email: string | null;
  inbox_name: string;
  graph_id: string;
  deployment_url: string;
  is_default: boolean;
  selected: boolean;
  tenant_id: string | null;
  created_at: string;
  updated_at: string;
}

// Default inboxes configuration
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
    graph_id: "executive-ai-assistant",
    deployment_url: "https://multi-agent-app-1d1e061875eb5640a47e3bb201edb076.us.langgraph.app",
    is_default: true,
    selected: false,
  },
];

/**
 * GET /api/config/inboxes
 * Fetch user's inboxes from Supabase
 * Auto-creates default inboxes on first request
 */
export async function GET() {
  try {
    const { userId, sessionClaims } = await auth();

    if (!userId) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    // Extract email from JWT for inbox tracking
    const email = (sessionClaims?.email as string) || null;

    const supabase = createServerSupabaseClient(userId);

    // Fetch existing inboxes
    const { data: existingInboxes, error: fetchError } = await supabase
      .from("user_inboxes")
      .select("*")
      .eq("clerk_id", userId)
      .order("created_at", { ascending: true });

    if (fetchError) {
      console.error("Error fetching user inboxes:", fetchError);
      return NextResponse.json(
        { error: "Failed to fetch inboxes" },
        { status: 500 }
      );
    }

    // If user has no inboxes, auto-create defaults
    if (!existingInboxes || existingInboxes.length === 0) {
      console.log(`[Auto-Create] Creating default inboxes for user ${userId}`);

      const inboxesToCreate = DEFAULT_INBOXES.map((inbox) => ({
        clerk_id: userId,
        email,
        ...inbox,
      }));

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

      console.log(`[Auto-Create] Created ${createdInboxes.length} default inboxes`);

      return NextResponse.json({
        success: true,
        inboxes: createdInboxes,
        isFirstTime: true,
      });
    }

    // Return existing inboxes
    return NextResponse.json({
      success: true,
      inboxes: existingInboxes,
      isFirstTime: false,
    });
  } catch (error) {
    console.error("Error in GET /api/config/inboxes:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

/**
 * POST /api/config/inboxes
 * Add a new custom inbox to Supabase
 */
export async function POST(request: Request) {
  try {
    const { userId, sessionClaims } = await auth();

    if (!userId) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const email = (sessionClaims?.email as string) || null;
    const body = await request.json();

    // Validate required fields
    const { inbox_name, graph_id, deployment_url, tenant_id } = body;

    if (!inbox_name || !graph_id || !deployment_url) {
      return NextResponse.json(
        { error: "Missing required fields: inbox_name, graph_id, deployment_url" },
        { status: 400 }
      );
    }

    const supabase = createServerSupabaseClient(userId);

    // Unselect all existing inboxes for this user
    await supabase
      .from("user_inboxes")
      .update({ selected: false })
      .eq("clerk_id", userId);

    // Create new inbox (selected by default)
    const newInbox = {
      clerk_id: userId,
      email,
      inbox_name,
      graph_id,
      deployment_url,
      tenant_id: tenant_id || null,
      is_default: false, // Custom inboxes are not defaults
      selected: true, // New inbox becomes selected
    };

    const { data: createdInbox, error: createError } = await supabase
      .from("user_inboxes")
      .insert([newInbox])
      .select()
      .single();

    if (createError) {
      console.error("Error creating inbox:", createError);

      // Check for unique constraint violation
      if (createError.code === "23505") {
        return NextResponse.json(
          { error: "Inbox with this graph_id already exists" },
          { status: 409 }
        );
      }

      return NextResponse.json(
        { error: "Failed to create inbox" },
        { status: 500 }
      );
    }

    console.log(`[Inbox Created] User ${userId} added inbox: ${graph_id}`);

    return NextResponse.json({
      success: true,
      inbox: createdInbox,
    });
  } catch (error) {
    console.error("Error in POST /api/config/inboxes:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

/**
 * PATCH /api/config/inboxes
 * Update selected inbox
 */
export async function PATCH(request: Request) {
  try {
    const { userId } = await auth();

    if (!userId) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const body = await request.json();
    const { inbox_id } = body;

    if (!inbox_id) {
      return NextResponse.json(
        { error: "Missing required field: inbox_id" },
        { status: 400 }
      );
    }

    const supabase = createServerSupabaseClient(userId);

    // Unselect all inboxes
    await supabase
      .from("user_inboxes")
      .update({ selected: false })
      .eq("clerk_id", userId);

    // Select the specified inbox
    const { data: updatedInbox, error: updateError } = await supabase
      .from("user_inboxes")
      .update({ selected: true })
      .eq("id", inbox_id)
      .eq("clerk_id", userId)
      .select()
      .single();

    if (updateError) {
      console.error("Error updating selected inbox:", updateError);
      return NextResponse.json(
        { error: "Failed to update inbox selection" },
        { status: 500 }
      );
    }

    if (!updatedInbox) {
      return NextResponse.json({ error: "Inbox not found" }, { status: 404 });
    }

    return NextResponse.json({
      success: true,
      inbox: updatedInbox,
    });
  } catch (error) {
    console.error("Error in PATCH /api/config/inboxes:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
