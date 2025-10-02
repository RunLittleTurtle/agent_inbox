import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

// Define public routes (none for this app - everything requires auth)
const isPublicRoute = createRouteMatcher([]);

export default clerkMiddleware(async (auth, req) => {
  // Protect all routes by default
  if (!isPublicRoute(req)) {
    await auth.protect();
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
