import { clerkMiddleware } from "@clerk/nextjs/server";

export default clerkMiddleware(async (auth, req) => {
  // Bypass Clerk auth for LangGraph SDK internal endpoints
  // Note: LangGraph Platform auth.py handles authentication and owner filtering
  const pathname = req.nextUrl.pathname;

  // Skip Clerk auth for ALL LangGraph SDK internal endpoints:
  // - /api/threads/{id}/history - State history endpoint
  // - /api/threads/{id}/runs/stream - Streaming runs endpoint
  // - /api/threads/{id}/state - State management endpoint
  // - /api/threads - Thread management
  // - /api/assistants/* - Assistant endpoints
  const isLangGraphEndpoint =
    pathname.match(/^\/api\/threads\/[^/]+\/(history|runs\/stream|state)$/) ||
    pathname.match(/^\/api\/threads$/) ||
    pathname.match(/^\/api\/assistants/);

  if (isLangGraphEndpoint) {
    // Skip Clerk auth - LangGraph Platform will validate JWT and enforce ownership
    return;
  }

  // Protect all other routes
  await auth.protect();
});

export const config = {
  matcher: [
    // Skip Next.js internals and all static files, unless found in search params
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    // Always run for API routes
    "/(api|trpc)(.*)",
  ],
};
