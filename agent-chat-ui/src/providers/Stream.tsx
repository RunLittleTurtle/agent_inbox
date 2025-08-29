import React, {
  createContext,
  useContext,
  ReactNode,
  useState,
  useEffect,
} from "react";
import { useStream } from "@langchain/langgraph-sdk/react";
import { type Message } from "@langchain/langgraph-sdk";
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

// Enhanced streaming event types
export interface StreamEvent {
  event_type: 'node_update' | 'token' | 'custom' | 'error' | 'raw';
  data: Record<string, any>;
  timestamp: string;
  node?: string;
  metadata?: Record<string, any>;
}

export interface WorkflowProgress {
  currentNode: string;
  completedNodes: string[];
  totalNodes: number;
  progress: number;
  status: 'running' | 'complete' | 'error' | 'waiting';
}

export interface TokenStreamData {
  content: string;
  isComplete: boolean;
  metadata?: Record<string, any>;
}

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

type StreamContextType = ReturnType<typeof useTypedStream>;
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
  
  // Enhanced state for streaming
  const [streamEvents, setStreamEvents] = useState<StreamEvent[]>([]);
  const [workflowProgress, setWorkflowProgress] = useState<WorkflowProgress>({
    currentNode: '',
    completedNodes: [],
    totalNodes: 0,
    progress: 0,
    status: 'waiting'
  });
  const [tokenStream, setTokenStream] = useState<TokenStreamData>({
    content: '',
    isComplete: false
  });
  
  const streamValue = useTypedStream({
    apiUrl,
    apiKey: apiKey ?? undefined,
    assistantId,
    threadId: threadId ?? null,
    onUpdateEvent: (data: any) => {
      console.log('🔄 UPDATE EVENT:', data);
      const timestamp = new Date().toISOString();
      const eventData = {
        timestamp,
        event_type: 'update',
        data: data
      };
      setStreamEvents(prev => [...prev.slice(-50), eventData as unknown as StreamEvent]);
      
      // Check if this update contains messages (indicates completion)
      if (data && data.messages && Array.isArray(data.messages) && data.messages.length > 0) {
        console.log('🏁 COMPLETION DETECTED - Messages found in update:', data.messages);
        setWorkflowProgress(prev => ({
          ...prev,
          status: 'complete'
        }));
      }
    },
    onMetadataEvent: (data: any) => {
      console.log('📊 METADATA EVENT:', data);
      const timestamp = new Date().toISOString();
      const eventData = {
        timestamp,
        event_type: 'metadata',
        data: data
      };
      setStreamEvents(prev => [...prev.slice(-50), eventData as unknown as StreamEvent]);
    },
    onCustomEvent: (event: any, options: any) => {
      console.log('🔥 CUSTOM EVENT RECEIVED:', typeof event, event);
      
      if (isUIMessage(event) || isRemoveUIMessage(event)) {
        options.mutate((prev: any) => {
          const ui = uiMessageReducer(prev.ui ?? [], event);
          return { ...prev, ui };
        });
      }
      
      // Capture any custom streaming events
      if (event && typeof event === 'object') {
        const eventData = {
          timestamp: new Date().toISOString(),
          event_type: 'custom_stream',
          data: event
        };
        setStreamEvents(prev => [...prev.slice(-50), eventData as unknown as StreamEvent]);
        console.log('🔥 ADDED CUSTOM EVENT TO STATE:', eventData);
      }
    },
    onThreadId: (id) => {
      setThreadId(id);
      // Reset streaming state for new thread
      setStreamEvents([]);
      setWorkflowProgress({
        currentNode: '',
        completedNodes: [],
        totalNodes: 0,
        progress: 0,
        status: 'waiting'
      });
      setTokenStream({
        content: '',
        isComplete: false
      });
      
      sleep().then(() => getThreads().then(setThreads).catch(console.error));
    },
  });

  // Process node updates for workflow progress
  const processNodeUpdate = (event: StreamEvent) => {
    setWorkflowProgress(prev => {
      const newCompleted = [...prev.completedNodes];
      if (event.node && !newCompleted.includes(event.node)) {
        newCompleted.push(event.node);
      }
      
      return {
        ...prev,
        currentNode: event.node || prev.currentNode,
        completedNodes: newCompleted,
        totalNodes: Math.max(prev.totalNodes, newCompleted.length + 1),
        progress: (newCompleted.length / Math.max(prev.totalNodes, newCompleted.length + 1)) * 100,
        status: 'running'
      };
    });
  };

  // Process token streaming
  const processTokenStream = (event: StreamEvent) => {
    const content = event.data.content || '';
    setTokenStream(prev => ({
      content: prev.content + content,
      isComplete: event.data.isComplete || false,
      metadata: event.metadata
    }));
  };

  // Process custom events
  const processCustomEvent = (event: StreamEvent) => {
    // Handle custom workflow events
    if (event.data.event === 'node_complete') {
      setWorkflowProgress(prev => ({
        ...prev,
        status: 'complete'
      }));
    }
  };
  
  // Enhanced stream value with additional state
  const enhancedStreamValue = {
    ...streamValue,
    streamEvents,
    workflowProgress,
    tokenStream
  };

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
    <StreamContext.Provider value={enhancedStreamValue}>
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

  // Use URL params with env var fallbacks
  const [apiUrl, setApiUrl] = useQueryState("apiUrl", {
    defaultValue: envApiUrl || "",
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

  // Determine final values to use, prioritizing URL params then env vars
  const finalApiUrl = apiUrl || envApiUrl;
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
