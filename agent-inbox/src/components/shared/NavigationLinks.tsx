"use client";

import React from "react";

interface NavigationLink {
  name: string;
  url: string;
  key: string;
}

export function NavigationLinks() {
  const links: NavigationLink[] = [
    {
      name: "Chat",
      url: process.env.NEXT_PUBLIC_CHAT_URL || "https://agent-chat-ui-2.vercel.app",
      key: "chat",
    },
    {
      name: "Inbox",
      url: process.env.NEXT_PUBLIC_INBOX_URL || "https://agent-inbox-2.vercel.app",
      key: "inbox",
    },
    {
      name: "Config",
      url: process.env.NEXT_PUBLIC_CONFIG_URL || "https://config-app.vercel.app",
      key: "config",
    },
  ];

  // Detect current app based on URL patterns
  const getCurrentApp = () => {
    if (typeof window === "undefined") return null;

    const hostname = window.location.hostname;

    if (hostname.includes("agent-chat") || hostname.includes("agentchat")) {
      return "chat";
    }
    if (hostname.includes("agent-inbox")) {
      return "inbox";
    }
    if (hostname.includes("config")) {
      return "config";
    }

    return null;
  };

  const currentApp = getCurrentApp();

  // Filter out current app
  const filteredLinks = links.filter((link) => link.key !== currentApp);

  if (filteredLinks.length === 0) {
    return null;
  }

  return (
    <nav className="flex items-center gap-2">
      {filteredLinks.map((link) => (
        <a
          key={link.key}
          href={link.url}
          target="_blank"
          rel="noopener noreferrer"
          className="px-3 py-1.5 text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
        >
          {link.name}
        </a>
      ))}
    </nav>
  );
}
