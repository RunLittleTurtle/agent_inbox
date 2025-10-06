import { auth } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

/**
 * GET /api/config/deployment-urls
 * Returns available LangGraph deployment URLs from global config
 * Used to populate dropdown in "Add Inbox" dialog
 */
export async function GET() {
  try {
    const { userId } = await auth();

    if (!userId) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    // Read deployment URLs from environment variables (set in global config)
    const agentInboxUrl =
      process.env.AGENT_INBOX_DEPLOYMENT_URL ||
      "https://multi-agent-app-1d1e061875eb5640a47e3bb201edb076.us.langgraph.app";

    const executiveUrl =
      process.env.EXECUTIVE_DEPLOYMENT_URL ||
      "https://multi-agent-app-1d1e061875eb5640a47e3bb201edb076.us.langgraph.app";

    // Return available deployment URLs
    const deploymentUrls = [
      {
        label: "Production (Multi-Agent)",
        value: agentInboxUrl,
        description: "Primary LangGraph deployment for agent inbox",
      },
      {
        label: "Production (Executive)",
        value: executiveUrl,
        description: "LangGraph deployment for executive assistant",
      },
      {
        label: "Custom",
        value: "",
        description: "Enter a custom LangGraph deployment URL",
      },
    ];

    return NextResponse.json({
      success: true,
      deploymentUrls,
      defaultUrl: agentInboxUrl,
    });
  } catch (error) {
    console.error("Error in GET /api/config/deployment-urls:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
