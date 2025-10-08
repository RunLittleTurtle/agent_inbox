import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

// Define public routes (none for this app - everything requires auth)
const isPublicRoute = createRouteMatcher([]);

// Allowed origins for CORS
const ALLOWED_ORIGINS = [
  "https://inbox.mekanize.app",
  "https://mekanize.app",
  "https://agent-inbox-three.vercel.app",
  "https://agent-inbox-samuelaudette1-9269s-projects.vercel.app",
  "https://agent-inbox-2-samuelaudette1-9269s-projects.vercel.app",
  // Allow all Vercel preview deployments for development
  process.env.NODE_ENV === "development" ? "http://localhost:3000" : null,
].filter(Boolean) as string[];

export default clerkMiddleware(async (auth, req) => {
  const origin = req.headers.get("origin");
  const isAllowedOrigin = origin && (ALLOWED_ORIGINS.includes(origin) || origin.includes("vercel.app"));

  // Handle preflight requests - BYPASS AUTH
  if (req.method === "OPTIONS") {
    const response = NextResponse.json({}, { status: 200 });

    if (isAllowedOrigin) {
      response.headers.set("Access-Control-Allow-Origin", origin);
      response.headers.set("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS");
      response.headers.set("Access-Control-Allow-Headers", "Content-Type, Authorization");
      response.headers.set("Access-Control-Allow-Credentials", "true");
      response.headers.set("Access-Control-Max-Age", "86400");
    }

    return response;
  }

  // For actual requests: Add CORS, then check auth
  try {
    // Protect all routes by default
    if (!isPublicRoute(req)) {
      await auth.protect();
    }

    // Success - add CORS and continue
    const response = NextResponse.next();

    if (isAllowedOrigin) {
      response.headers.set("Access-Control-Allow-Origin", origin);
      response.headers.set("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS");
      response.headers.set("Access-Control-Allow-Headers", "Content-Type, Authorization");
      response.headers.set("Access-Control-Allow-Credentials", "true");
    }

    return response;
  } catch (error) {
    // Auth failed - still add CORS to error response
    const errorResponse = NextResponse.json(
      { error: "Unauthorized" },
      { status: 401 }
    );

    if (isAllowedOrigin) {
      errorResponse.headers.set("Access-Control-Allow-Origin", origin);
      errorResponse.headers.set("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS");
      errorResponse.headers.set("Access-Control-Allow-Headers", "Content-Type, Authorization");
      errorResponse.headers.set("Access-Control-Allow-Credentials", "true");
    }

    return errorResponse;
  }
});

export const config = {
  matcher: [
    // Skip Next.js internals and all static files, unless found in search params
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    // Always run for API routes
    "/(api|trpc)(.*)",
  ],
};
