"use client";

import "./globals.css";
import { Inter } from "next/font/google";
import { Toaster } from "@/components/ui/toaster";
import { ThreadsProvider } from "@/components/agent-inbox/contexts/ThreadContext";
import React from "react";
import { SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar, AppSidebarTrigger } from "@/components/app-sidebar";
import { BreadCrumb } from "@/components/agent-inbox/components/breadcrumb";
import { cn } from "@/lib/utils";
import { ClerkProvider, SignedIn, SignedOut, SignInButton, UserButton } from "@clerk/nextjs";
import { NavigationLinks } from "@/components/shared/NavigationLinks";

const inter = Inter({
  subsets: ["latin"],
  preload: true,
  display: "swap",
});

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider>
      <html lang="en">
        <body className={inter.className}>
          <Toaster />
          <React.Suspense fallback={<div>Loading (layout)...</div>}>
            <ThreadsProvider>
              <SidebarProvider>
                <AppSidebar />
                <main className="flex flex-row w-full min-h-full pt-6 pl-6 gap-6">
                  <AppSidebarTrigger isOutside={true} />
                  <div className="flex flex-col gap-6 w-full min-h-full">
                    <div className="flex items-center justify-between pl-5">
                      <BreadCrumb />
                      <div className="pr-6 flex items-center gap-4">
                        <NavigationLinks />
                        <SignedOut>
                          <SignInButton mode="modal">
                            <button className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm">
                              Sign In
                            </button>
                          </SignInButton>
                        </SignedOut>
                        <SignedIn>
                          <UserButton afterSignOutUrl="/" />
                        </SignedIn>
                      </div>
                    </div>
                    <div
                      className={cn(
                        "h-full bg-white rounded-tl-[58px]",
                        "overflow-x-auto scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100"
                      )}
                    >
                      {children}
                    </div>
                  </div>
                </main>
              </SidebarProvider>
            </ThreadsProvider>
          </React.Suspense>
        </body>
      </html>
    </ClerkProvider>
  );
}
