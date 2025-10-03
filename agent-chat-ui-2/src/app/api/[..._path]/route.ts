import { auth } from "@clerk/nextjs/server";
import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

export const runtime = "edge";

const LANGGRAPH_API_URL = process.env.LANGGRAPH_API_URL ?? "remove-me";
const LANGSMITH_API_KEY = process.env.LANGSMITH_API_KEY ?? "remove-me";
const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const SUPABASE_SECRET_KEY = process.env.SUPABASE_SECRET_KEY!;

async function handleRequest(request: NextRequest) {
  try {
    // Get Clerk user ID
    const { userId, getToken } = await auth();
    const clerkToken = await getToken();

    if (!userId) {
      return NextResponse.json(
        { error: "Unauthorized - No user ID" },
        { status: 401 }
      );
    }

    // Fetch user-specific API keys from Supabase
    const supabase = createClient(SUPABASE_URL, SUPABASE_SECRET_KEY);
    const { data: userSecrets, error: secretsError } = await supabase
      .from("user_secrets")
      .select("*")
      .eq("clerk_id", userId)
      .maybeSingle();

    if (secretsError) {
      console.error("Error fetching user secrets:", secretsError);
      return NextResponse.json(
        { error: "Failed to fetch user API keys. Please add your API keys in the config page." },
        { status: 403 }
      );
    }

    if (!userSecrets) {
      return NextResponse.json(
        { error: "No API keys found. Please add your OpenAI or Anthropic API keys in the config page." },
        { status: 403 }
      );
    }

    const openaiKey = userSecrets.openai_api_key;
    const anthropicKey = userSecrets.anthropic_api_key;

    if (!openaiKey && !anthropicKey) {
      return NextResponse.json(
        { error: "No API keys configured. Please add at least one API key (OpenAI or Anthropic) in the config page." },
        { status: 403 }
      );
    }

    // Extract path from URL
    const url = new URL(request.url);
    const pathSegments = url.pathname.replace("/api/", "");
    const targetUrl = `${LANGGRAPH_API_URL}/${pathSegments}${url.search}`;

    // Build headers
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };

    // Add LangSmith API key if available
    if (LANGSMITH_API_KEY && LANGSMITH_API_KEY !== "remove-me") {
      headers["x-api-key"] = LANGSMITH_API_KEY;
    }

    // Add Clerk JWT token for custom auth
    if (clerkToken) {
      headers["Authorization"] = `Bearer ${clerkToken}`;
    }

    // Get request body and inject user-specific API keys
    let modifiedBody: string | undefined;
    if (request.method !== "GET" && request.method !== "HEAD") {
      const originalBody = await request.text();
      let bodyObject: any = {};

      // Parse existing body if present
      if (originalBody) {
        try {
          bodyObject = JSON.parse(originalBody);
        } catch (e) {
          console.warn("Could not parse request body as JSON, creating new object");
        }
      }

      // Inject user-specific API keys into config.configurable
      if (!bodyObject.config) {
        bodyObject.config = {};
      }
      if (!bodyObject.config.configurable) {
        bodyObject.config.configurable = {};
      }

      // Add user-specific API keys to configurable
      bodyObject.config.configurable.openai_api_key = openaiKey;
      bodyObject.config.configurable.anthropic_api_key = anthropicKey;
      bodyObject.config.configurable.user_id = userId;

      modifiedBody = JSON.stringify(bodyObject);
    }

    // Forward request to LangGraph Platform with user-specific API keys
    const response = await fetch(targetUrl, {
      method: request.method,
      headers,
      body: modifiedBody,
    });

    // Return response
    const data = await response.text();
    return new NextResponse(data, {
      status: response.status,
      headers: {
        "Content-Type": response.headers.get("Content-Type") || "application/json",
      },
    });
  } catch (error) {
    console.error("Error in API passthrough:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

export const GET = handleRequest;
export const POST = handleRequest;
export const PUT = handleRequest;
export const PATCH = handleRequest;
export const DELETE = handleRequest;
export const OPTIONS = handleRequest;
