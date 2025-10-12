import { auth, clerkClient } from "@clerk/nextjs/server";
import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

export const runtime = "edge";

const LANGGRAPH_API_URL = process.env.LANGGRAPH_API_URL ?? "remove-me";
const LANGSMITH_API_KEY = process.env.LANGSMITH_API_KEY ?? "remove-me";
const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const SUPABASE_SECRET_KEY = process.env.SUPABASE_SECRET_KEY!;

async function handleRequest(request: NextRequest) {
  // Handle CORS preflight requests for production domains
  if (request.method === "OPTIONS") {
    return new NextResponse(null, {
      status: 204,
      headers: {
        "Access-Control-Allow-Origin": request.headers.get("origin") || "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization, x-api-key",
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Max-Age": "86400", // 24 hours
      },
    });
  }

  try {
    // Dual-mode authentication to support both regular requests and SDK requests
    let userId: string | null = null;
    let clerkToken: string | null = null;

    // Primary method: Get from Clerk auth context (when middleware runs)
    const authResult = await auth();
    userId = authResult?.userId || null;

    // Only try to get token if we have an auth result
    if (authResult?.getToken) {
      clerkToken = await authResult.getToken();
    }

    // Fallback method: Use authenticateRequest for SDK requests (when middleware is bypassed)
    if (!userId && request.headers.get("authorization")) {
      console.log("[API Route] No Clerk context, trying authenticateRequest for SDK request");

      const client = await clerkClient();

      // Build authorized parties list with proper type safety
      const authorizedParties: string[] = [
        'https://chat.mekanize.app',
        'https://agent-chat-ui-2.vercel.app',
        'http://localhost:3000',
        'http://localhost:3001',
      ];

      // Add NEXT_PUBLIC_APP_URL if it exists
      if (process.env.NEXT_PUBLIC_APP_URL) {
        authorizedParties.push(process.env.NEXT_PUBLIC_APP_URL);
      }

      const { isAuthenticated, toAuth } = await client.authenticateRequest(request, {
        // Security: Only accept requests from our known domains
        authorizedParties
      });

      if (isAuthenticated) {
        const authData = toAuth();
        userId = authData.userId;
        // Use the token from the Authorization header since we already have it
        clerkToken = request.headers.get("authorization")?.substring(7) || null;
        console.log("[API Route] Authenticated via authenticateRequest, userId:", userId);
      }
    }

    // Final check - if still no user ID, return unauthorized
    if (!userId) {
      console.error("[API Route] No user ID found via auth() or authenticateRequest()");
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

    // Stream response body directly without buffering (LangGraph 2025 best practice)
    // This enables real-time SSE streaming for supervisor + sub-agent tool calls
    return new NextResponse(response.body, {
      status: response.status,
      headers: {
        // Preserve original Content-Type from LangGraph Platform
        // - Streaming requests (/runs/stream) return text/event-stream
        // - Regular requests (/threads, /history) return application/json
        "Content-Type": response.headers.get("Content-Type") || "application/json",
        "Cache-Control": "no-cache, no-transform",
        "Connection": "keep-alive",
        // CORS headers for production domains
        "Access-Control-Allow-Origin": request.headers.get("origin") || "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization, x-api-key",
        "Access-Control-Allow-Credentials": "true",
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
