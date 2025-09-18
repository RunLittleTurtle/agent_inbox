import { StateView } from "./components/state-view";
import { ThreadActionsView } from "./components/thread-actions-view";
import { useThreadsContext } from "./contexts/ThreadContext";
import { ThreadData } from "./types";
import React from "react";
import { cn } from "@/lib/utils";
import { useQueryParams } from "./hooks/use-query-params";
import { IMPROPER_SCHEMA, VIEW_STATE_THREAD_QUERY_PARAM } from "./constants";
import { logger } from "./utils/logger";

export function ThreadView<
  ThreadValues extends Record<string, any> = Record<string, any>,
>({ threadId }: { threadId: string }) {
  const { updateQueryParams } = useQueryParams();
  const { threadData: threads, loading } = useThreadsContext<ThreadValues>();
  const [threadData, setThreadData] =
    React.useState<ThreadData<ThreadValues>>();
  const [showDescription, setShowDescription] = React.useState(true);
  const [showState, setShowState] = React.useState(false);

  // Create interrupt actions if we have an interrupted thread
  const isInterrupted = threadData?.status === "interrupted";

  // Show side panel for all thread types
  const showSidePanel = showDescription || showState;

  // Derive thread title
  const threadTitle = React.useMemo(() => {
    if (
      threadData?.interrupts?.[0]?.action_request?.action &&
      threadData.interrupts[0].action_request.action !== IMPROPER_SCHEMA
    ) {
      return threadData.interrupts[0].action_request.action;
    }
    return `Thread: ${threadData?.thread.thread_id.slice(0, 6)}...`;
  }, [threadData]);

  // Scroll to top when thread view is mounted
  React.useEffect(() => {
    if (typeof window !== "undefined") {
      window.scrollTo(0, 0);
    }
  }, []);

  React.useEffect(() => {
    try {
      if (typeof window === "undefined") return;
      if (!threadId || !threads.length || loading) return;
      const selectedThread = threads.find(
        (t) => t.thread.thread_id === threadId
      );
      if (selectedThread) {
        setThreadData(selectedThread);
        // Default to description first, state if no description
        if (
          selectedThread.status === "interrupted" &&
          selectedThread.interrupts?.[0]?.description
        ) {
          setShowDescription(true);
          setShowState(false);
        } else {
          setShowState(true);
          setShowDescription(false);
        }
      } else {
        // Route the user back to the inbox view.
        updateQueryParams(VIEW_STATE_THREAD_QUERY_PARAM);
      }
    } catch (e) {
      logger.error("Error updating query params & setting thread data", e);
    }
  }, [threads, loading, threadId]);

  const handleShowSidePanel = (
    showState: boolean,
    showDescription: boolean
  ) => {
    if (showState && showDescription) {
      logger.error("Cannot show both state and description");
      return;
    }
    if (showState) {
      setShowDescription(false);
      setShowState(true);
    } else if (showDescription) {
      setShowState(false);
      setShowDescription(true);
    } else {
      setShowState(false);
      setShowDescription(false);
    }
  };

  if (!threadData) {
    return null;
  }

  return (
    <div className="flex flex-col lg:flex-row w-full h-full">
      <div
        className={cn(
          "flex overflow-y-auto",
          showSidePanel ? "lg:min-w-1/2 lg:max-w-2xl w-full" : "w-full"
        )}
      >
        <ThreadActionsView<ThreadValues>
          threadData={threadData}
          isInterrupted={isInterrupted}
          threadTitle={threadTitle}
          showState={showState}
          showDescription={showDescription}
          handleShowSidePanel={handleShowSidePanel}
          setThreadData={setThreadData}
        />
      </div>
      <div
        className={cn(
          showSidePanel ? "flex" : "hidden",
          "overflow-y-auto lg:max-w-1/2 w-full"
        )}
      >
        <StateView
          handleShowSidePanel={handleShowSidePanel}
          threadData={threadData}
          view={showState ? "state" : "description"}
        />
      </div>
    </div>
  );
}
