import { auth } from "@clerk/nextjs/server";
import { NextRequest, NextResponse } from "next/server";

export const runtime = "edge";

const LANGGRAPH_API_URL = process.env.LANGGRAPH_API_URL ?? "remove-me";
const LANGSMITH_API_KEY = process.env.LANGSMITH_API_KEY ?? "remove-me";

async function handleRequest(request: NextRequest) {
  try {
    // Get Clerk token
    const { getToken } = await auth();
    const clerkToken = await getToken();

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

    // Get request body if present
    let body: string | undefined;
    if (request.method !== "GET" && request.method !== "HEAD") {
      body = await request.text();
    }

    // Forward request to LangGraph Platform
    const response = await fetch(targetUrl, {
      method: request.method,
      headers,
      body,
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
