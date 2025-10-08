import { auth } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";
import { createServerSupabaseClient } from "@/lib/supabase-client";

/**
 * DELETE /api/config/inboxes/[id]
 * Remove a custom inbox from Supabase
 * Prevents deletion of default inboxes
 */
export async function DELETE(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { userId } = await auth();

    if (!userId) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const { id } = await params;

    if (!id) {
      return NextResponse.json(
        { error: "Missing inbox ID" },
        { status: 400 }
      );
    }

    const supabase = createServerSupabaseClient(userId);

    // Fetch the inbox to check if it exists and belongs to user
    const { data: inbox, error: fetchError } = await supabase
      .from("user_inboxes")
      .select("*")
      .eq("id", id)
      .eq("clerk_id", userId)
      .single();

    if (fetchError || !inbox) {
      console.error("Error fetching inbox for deletion:", fetchError);
      return NextResponse.json({ error: "Inbox not found" }, { status: 404 });
    }

    // Allow deletion of any inbox (including defaults)
    // User can restore defaults with "Add Default Inboxes" button

    // Delete the inbox
    const { error: deleteError } = await supabase
      .from("user_inboxes")
      .delete()
      .eq("id", id)
      .eq("clerk_id", userId);

    if (deleteError) {
      console.error("Error deleting inbox:", deleteError);
      return NextResponse.json(
        { error: "Failed to delete inbox" },
        { status: 500 }
      );
    }

    // If deleted inbox was selected, select the first remaining inbox
    if (inbox.selected) {
      const { data: remainingInboxes } = await supabase
        .from("user_inboxes")
        .select("*")
        .eq("clerk_id", userId)
        .order("created_at", { ascending: true })
        .limit(1);

      if (remainingInboxes && remainingInboxes.length > 0) {
        await supabase
          .from("user_inboxes")
          .update({ selected: true })
          .eq("id", remainingInboxes[0].id);
      }
    }

    console.log(`[Inbox Deleted] User ${userId} removed inbox: ${inbox.graph_id}`);

    return NextResponse.json({
      success: true,
      message: "Inbox deleted successfully",
    });
  } catch (error) {
    console.error("Error in DELETE /api/config/inboxes/[id]:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
