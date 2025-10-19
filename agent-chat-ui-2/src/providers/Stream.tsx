import React, {
  createContext,
  useContext,
  ReactNode,
  useEffect,
  useRef,
  useCallback,
} from "react";
import { useStream } from "@langchain/langgraph-sdk/react";
import { type Message, Client } from "@langchain/langgraph-sdk";
import {
  uiMessageReducer,
  isUIMessage,
  isRemoveUIMessage,
  type UIMessage,
  type RemoveUIMessage,
} from "@langchain/langgraph-sdk/react-ui";
import { useQueryState } from "nuqs";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { LangGraphLogoSVG } from "@/components/icons/langgraph";
import { Label } from "@/components/ui/label";
import { ArrowRight } from "lucide-react";
import { PasswordInput } from "@/components/ui/password-input";
import { getApiKey } from "@/lib/api-key";
import { useThreads } from "./Thread";
import { toast } from "sonner";

export type StateType = { messages: Message[]; ui?: UIMessage[] };

const useTypedStream = useStream<
  StateType,
  {
    UpdateType: {
      messages?: Message[] | Message | string;
      ui?: (UIMessage | RemoveUIMessage)[] | UIMessage | RemoveUIMessage;
      context?: Record<string, unknown>;
    };
    CustomEventType: UIMessage | RemoveUIMessage;
  }
>;

type StreamContextType = ReturnType<typeof useTypedStream> & {
  cancelRun: () => Promise<void>;
  fetchHistoryOnDemand: (threadId: string) => Promise<any>;
};
const StreamContext = createContext<StreamContextType | undefined>(undefined);

async function sleep(ms = 4000) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function checkGraphStatus(
  apiUrl: string,
  apiKey: string | null,
): Promise<boolean> {
  try {
    const res = await fetch(`${apiUrl}/info`, {
      ...(apiKey && {
        headers: {
          "X-Api-Key": apiKey,
        },
      }),
    });

    return res.ok;
  } catch (e) {
    console.error(e);
    return false;
  }
}

const StreamSession = ({
  children,
  apiKey,
  apiUrl,
  assistantId,
}: {
  children: ReactNode;
  apiKey: string | null;
  apiUrl: string;
  assistantId: string;
}) => {
  const [threadId, setThreadId] = useQueryState("threadId");
  const { getThreads, setThreads } = useThreads();

  // 2025 Pattern: NO frontend token management
  // Token authentication is handled entirely by Next.js API route
  // The API route fetches fresh Clerk tokens on EVERY request server-side
  // This prevents SSE stream disruption from frontend token refresh

  // Create LangGraph client for manual run cancellation
  const clientRef = useRef<Client | null>(null);
  const currentRunIdRef = useRef<string | null>(null);
  const currentThreadIdRef = useRef<string | null>(null);

  // Initialize client ONCE - no token dependency
  // Backend API route handles all auth
  useEffect(() => {
    if (apiUrl && !clientRef.current) {
      console.log("[Client] Initializing client (backend handles auth)");
      clientRef.current = new Client({
        apiUrl,
        apiKey: apiKey ?? undefined,
        // No Authorization header - backend adds it
      });
    }
  }, [apiUrl, apiKey]);

  const streamValue = useTypedStream({
    apiUrl,
    apiKey: apiKey ?? undefined,
    assistantId,
    threadId: threadId ?? null,
    fetchStateHistory: true,  // Required by SDK - 404 errors handled by onError callback below
    // No defaultHeaders - backend API route handles auth
    // This prevents stream disruption from token refresh
    onCustomEvent: (event, options) => {
      if (isUIMessage(event) || isRemoveUIMessage(event)) {
        options.mutate((prev) => {
          const ui = uiMessageReducer(prev.ui ?? [], event);
          return { ...prev, ui };
        });
      }
    },
    onThreadId: (id) => {
      setThreadId(id);
      // Refetch threads list when thread ID changes.
      sleep().then(() => getThreads().then(setThreads).catch(console.error));
    },
    onCreated: (run) => {
      // Capture run_id for manual cancellation
      // Always store new run metadata, replacing any previous run
      console.log("[Cancel Debug] onCreated fired:", {
        run_id: run.run_id,
        thread_id: run.thread_id,
        replacing_previous: !!currentRunIdRef.current
      });
      currentRunIdRef.current = run.run_id;
      currentThreadIdRef.current = run.thread_id;
    },
    onError: (error) => {
      console.error("[Stream Error]", error);

      // Handle different types of streaming errors
      if (error && typeof error === 'object' && 'message' in error && 'status' in error) {
        const err = error as { message?: string; status?: number };

        // Ignore 404 on legacy history endpoint - expected with fetchStateHistory:true
        if (err.message?.includes('/history') && err.status === 404) {
          console.log("[Stream] Ignoring legacy history 404 (expected behavior)");
          return; // Don't propagate this error
        }

        // Handle 404 on runs/stream endpoint - log for debugging
        if (err.status === 404 && err.message?.includes('/runs/stream')) {
          console.error("[Stream] API route not found for /runs/stream");
          console.error("[Stream] Error details:", {
            status: err.status,
            message: err.message,
            apiUrl,
            timestamp: new Date().toISOString()
          });
          toast.error("Connection Error", {
            description: "Stream connection failed. Please try again or check your network connection.",
            duration: 5000,
          });
          return;
        }

        // Handle 401/403 auth errors - backend token fetch failed
        if (err.status === 401 || err.status === 403) {
          console.error("[Stream] Authentication failed - backend token issue");
          console.error("[Stream] Auth error details:", {
            status: err.status,
            message: err.message,
            timestamp: new Date().toISOString()
          });
          toast.error("Authentication Error", {
            description: "Your session may have expired. Please refresh the page.",
            duration: 5000,
          });
          return;
        }

        // For other stream errors, log for debugging
        if (err.message?.includes('stream')) {
          console.warn("[Stream] Stream connection error:", {
            status: err.status,
            message: err.message,
            timestamp: new Date().toISOString()
          });
        }
      }
    },
    // NOTE: Don't clear run metadata in onFinish - it fires when the stream connection
    // closes, not when the run actually finishes. Clearing here would prevent cancellation
    // of long-running agents. Metadata is replaced when a new run starts (onCreated).
  });

  // Manual cancellation function using SDK client
  const cancelRun = useCallback(async () => {
    const runId = currentRunIdRef.current;
    const threadId = currentThreadIdRef.current;

    console.log("[Cancel Debug] cancelRun called:", {
      runId,
      threadId,
      hasClient: !!clientRef.current,
      apiUrl,
      hasApiKey: !!apiKey
    });

    if (runId && threadId && clientRef.current) {
      try {
        console.log("[Cancel Debug] Calling streamValue.stop()...");
        // Call built-in stop first (best effort)
        streamValue.stop();

        console.log("[Cancel Debug] Calling client.runs.cancel()...");
        // Then manually cancel via API to ensure it works in production
        await clientRef.current.runs.cancel(threadId, runId);

        console.log("[Cancel Debug] Cancel successful!");
        // Clear refs after successful cancellation
        currentRunIdRef.current = null;
        currentThreadIdRef.current = null;
      } catch (error) {
        console.error("[Cancel Debug] Failed to cancel run:", error);
        // Still call stop as fallback
        streamValue.stop();
      }
    } else {
      console.log("[Cancel Debug] Missing run metadata, using fallback stop()");
      // Fallback to built-in stop if we don't have run metadata
      streamValue.stop();
    }
  }, [streamValue, apiUrl, apiKey]);

  // On-demand history fetching for components that need full state
  // LangGraph 2025: Use GET /state/history instead of legacy polling
  const fetchHistoryOnDemand = useCallback(async (threadId: string) => {
    if (!clientRef.current) {
      console.warn("[History] Client not initialized");
      return null;
    }

    try {
      console.log("[History] Fetching state for thread:", threadId);
      // Use the correct endpoint with GET method
      const state = await clientRef.current.threads.getState(threadId);
      console.log("[History] State fetched successfully");
      return state;
    } catch (error) {
      console.error("[History] Failed to fetch state:", error);
      return null;
    }
  }, []);

  useEffect(() => {
    checkGraphStatus(apiUrl, apiKey).then((ok) => {
      if (!ok) {
        toast.error("Failed to connect to LangGraph server", {
          description: () => (
            <p>
              Please ensure your graph is running at <code>{apiUrl}</code> and
              your API key is correctly set (if connecting to a deployed graph).
            </p>
          ),
          duration: 10000,
          richColors: true,
          closeButton: true,
        });
      }
    });
  }, [apiKey, apiUrl]);

  return (
    <StreamContext.Provider value={{ ...streamValue, cancelRun, fetchHistoryOnDemand }}>
      {children}
    </StreamContext.Provider>
  );
};

// Default values for the form
const DEFAULT_API_URL = "http://localhost:2024";
const DEFAULT_ASSISTANT_ID = "agent";

export const StreamProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  // Get environment variables
  const envApiUrl: string | undefined = process.env.NEXT_PUBLIC_API_URL;
  const envAssistantId: string | undefined =
    process.env.NEXT_PUBLIC_ASSISTANT_ID;

  // Helper function to get API URL from current domain (2025 Next.js pattern)
  // Works with any production domain: chat.mekanize.app, agent-chat-ui-2.vercel.app, localhost
  const getApiUrl = () => {
    if (typeof window === "undefined") return "";
    return `${window.location.origin}/api`;
  };

  // Use URL params with env var fallbacks, prioritize dynamic URL over hardcoded env
  const [apiUrl, setApiUrl] = useQueryState("apiUrl", {
    defaultValue: envApiUrl || getApiUrl() || "",
  });
  const [assistantId, setAssistantId] = useQueryState("assistantId", {
    defaultValue: envAssistantId || "",
  });

  // For API key, use localStorage with env var fallback
  const [apiKey, _setApiKey] = useState(() => {
    const storedKey = getApiKey();
    return storedKey || "";
  });

  const setApiKey = (key: string) => {
    window.localStorage.setItem("lg:chat:apiKey", key);
    _setApiKey(key);
  };

  // Determine final values to use, prioritizing URL params then dynamic URL then env vars
  const finalApiUrl = apiUrl || getApiUrl() || envApiUrl;
  const finalAssistantId = assistantId || envAssistantId;

  // Show the form if we: don't have an API URL, or don't have an assistant ID
  if (!finalApiUrl || !finalAssistantId) {
    return (
      <div className="flex min-h-screen w-full items-center justify-center p-4">
        <div className="animate-in fade-in-0 zoom-in-95 bg-background flex max-w-3xl flex-col rounded-lg border shadow-lg">
          <div className="mt-14 flex flex-col gap-2 border-b p-6">
            <div className="flex flex-col items-start gap-2">
              <LangGraphLogoSVG className="h-7" />
              <h1 className="text-xl font-semibold tracking-tight">
                Agent Chat
              </h1>
            </div>
            <p className="text-muted-foreground">
              Welcome to Agent Chat! Before you get started, you need to enter
              the URL of the deployment and the assistant / graph ID.
            </p>
          </div>
          <form
            onSubmit={(e) => {
              e.preventDefault();

              const form = e.target as HTMLFormElement;
              const formData = new FormData(form);
              const apiUrl = formData.get("apiUrl") as string;
              const assistantId = formData.get("assistantId") as string;
              const apiKey = formData.get("apiKey") as string;

              setApiUrl(apiUrl);
              setApiKey(apiKey);
              setAssistantId(assistantId);

              form.reset();
            }}
            className="bg-muted/50 flex flex-col gap-6 p-6"
          >
            <div className="flex flex-col gap-2">
              <Label htmlFor="apiUrl">
                Deployment URL<span className="text-rose-500">*</span>
              </Label>
              <p className="text-muted-foreground text-sm">
                This is the URL of your LangGraph deployment. Can be a local, or
                production deployment.
              </p>
              <Input
                id="apiUrl"
                name="apiUrl"
                className="bg-background"
                defaultValue={apiUrl || DEFAULT_API_URL}
                required
              />
            </div>

            <div className="flex flex-col gap-2">
              <Label htmlFor="assistantId">
                Assistant / Graph ID<span className="text-rose-500">*</span>
              </Label>
              <p className="text-muted-foreground text-sm">
                This is the ID of the graph (can be the graph name), or
                assistant to fetch threads from, and invoke when actions are
                taken.
              </p>
              <Input
                id="assistantId"
                name="assistantId"
                className="bg-background"
                defaultValue={assistantId || DEFAULT_ASSISTANT_ID}
                required
              />
            </div>

            <div className="flex flex-col gap-2">
              <Label htmlFor="apiKey">LangSmith API Key</Label>
              <p className="text-muted-foreground text-sm">
                This is <strong>NOT</strong> required if using a local LangGraph
                server. This value is stored in your browser's local storage and
                is only used to authenticate requests sent to your LangGraph
                server.
              </p>
              <PasswordInput
                id="apiKey"
                name="apiKey"
                defaultValue={apiKey ?? ""}
                className="bg-background"
                placeholder="lsv2_pt_..."
              />
            </div>

            <div className="mt-2 flex justify-end">
              <Button
                type="submit"
                size="lg"
              >
                Continue
                <ArrowRight className="size-5" />
              </Button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  return (
    <StreamSession
      apiKey={apiKey}
      apiUrl={apiUrl}
      assistantId={assistantId}
    >
      {children}
    </StreamSession>
  );
};

// Create a custom hook to use the context
export const useStreamContext = (): StreamContextType => {
  const context = useContext(StreamContext);
  if (context === undefined) {
    throw new Error("useStreamContext must be used within a StreamProvider");
  }
  return context;
};

export default StreamContext;
