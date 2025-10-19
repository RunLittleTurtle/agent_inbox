import { validate } from "uuid";
import { getApiKey } from "@/lib/api-key";
import { Thread } from "@langchain/langgraph-sdk";
import { useQueryState } from "nuqs";
import {
  createContext,
  useContext,
  ReactNode,
  useCallback,
  useState,
  Dispatch,
  SetStateAction,
} from "react";
import { createClient } from "./client";
import { useAuth } from "@clerk/nextjs";

interface ThreadContextType {
  getThreads: () => Promise<Thread[]>;
  threads: Thread[];
  setThreads: Dispatch<SetStateAction<Thread[]>>;
  threadsLoading: boolean;
  setThreadsLoading: Dispatch<SetStateAction<boolean>>;
}

const ThreadContext = createContext<ThreadContextType | undefined>(undefined);

function getThreadSearchMetadata(
  assistantId: string,
): { graph_id: string } | { assistant_id: string } {
  if (validate(assistantId)) {
    return { assistant_id: assistantId };
  } else {
    return { graph_id: assistantId };
  }
}

// Helper function to get API URL from current domain (2025 Next.js pattern)
// Works with any production domain: chat.mekanize.app, agent-chat-ui-2.vercel.app, localhost
function getApiUrl(): string {
  if (typeof window === "undefined") return "";
  return `${window.location.origin}/api`;
}

export function ThreadProvider({ children }: { children: ReactNode }) {
  // Get environment variables as fallbacks
  const envApiUrl: string | undefined = process.env.NEXT_PUBLIC_API_URL;
  const envAssistantId: string | undefined = process.env.NEXT_PUBLIC_ASSISTANT_ID;

  const [apiUrl] = useQueryState("apiUrl", {
    defaultValue: envApiUrl || getApiUrl() || "",
  });
  const [assistantId] = useQueryState("assistantId", {
    defaultValue: envAssistantId || "",
  });
  const [threads, setThreads] = useState<Thread[]>([]);
  const [threadsLoading, setThreadsLoading] = useState(false);
  const { getToken } = useAuth(); // Clerk JWT token for LangGraph custom auth

  const getThreads = useCallback(async (): Promise<Thread[]> => {
    if (!apiUrl || !assistantId) return [];

    // Get Clerk JWT token for LangGraph custom auth (2025)
    const clerkToken = await getToken();

    const client = createClient(apiUrl, getApiKey() ?? undefined, clerkToken);

    const threads = await client.threads.search({
      metadata: {
        ...getThreadSearchMetadata(assistantId),
      },
      limit: 100,
    });

    return threads;
  }, [apiUrl, assistantId, getToken]);

  const value = {
    getThreads,
    threads,
    setThreads,
    threadsLoading,
    setThreadsLoading,
  };

  return (
    <ThreadContext.Provider value={value}>{children}</ThreadContext.Provider>
  );
}

export function useThreads() {
  const context = useContext(ThreadContext);
  if (context === undefined) {
    throw new Error("useThreads must be used within a ThreadProvider");
  }
  return context;
}
