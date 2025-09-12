import { Message } from "@langchain/langgraph-sdk";

/**
 * Determines if this is the final supervisor response that should be prominently displayed.
 * Uses content patterns to identify complete user-facing responses from the supervisor.
 */
export function isFinalSupervisorResponse(
  message: Message,
  allMessages: Message[],
): boolean {
  // Must be from supervisor
  if (!message.name || !message.name.includes("supervisor")) {
    return false;
  }

  // Content-based detection for final responses
  const content =
    typeof message.content === "string"
      ? message.content
      : String(message.content);

  // Look for patterns that indicate a complete response to the user
  const finalResponsePatterns = [
    /has been successfully (created|scheduled|completed|done|processed)/i,
    /if you need any (more|further|additional) assistance/i,
    /feel free to ask/i,
    /is there anything else/i,
    /let me know if you need/i,
    /your (event|meeting|task|request) (has been|is|was)/i,
    /here are (all |your )/i, // For listing responses
    /i have (completed|finished|done)/i,
  ];

  const hasCompleteResponsePattern = finalResponsePatterns.some((pattern) =>
    pattern.test(content),
  );

  // Also check if this supervisor message comes after some agent activity
  // (indicating it's summarizing completed work)
  const currentIndex = allMessages.findIndex((m) => m.id === message.id);
  if (currentIndex === -1) return false;

  const recentMessages = allMessages.slice(
    Math.max(0, currentIndex - 10),
    currentIndex,
  );
  const hasRecentAgentActivity = recentMessages.some(
    (m) =>
      m.name &&
      (m.name.includes("calendar_agent") ||
        m.name.includes("email_agent") ||
        m.name.includes("job_search_agent")),
  );

  return hasCompleteResponsePattern || hasRecentAgentActivity;
}

/**
 * Determines if a message should be collapsed/minimized (not the main user-facing response)
 */
export function shouldCollapseMessage(
  message: Message,
  allMessages: Message[],
): boolean {
  // Individual agent messages should ALWAYS be collapsed
  const individualAgents = [
    "calendar_agent",
    "email_agent",
    "job_search_agent",
  ];
  if (
    message.name &&
    individualAgents.some((agent) => message.name?.includes(agent))
  ) {
    return true;
  }

  // Tool results should ALWAYS be collapsed
  if (message.type === "tool") {
    return true;
  }

  // Any message without a name should be collapsed (likely intermediate)
  if (!message.name) {
    return true;
  }

  // Supervisor messages: only show final ones prominently
  if (message.name.includes("supervisor")) {
    return !isFinalSupervisorResponse(message, allMessages);
  }

  // Default: collapse anything we're unsure about
  return true;
}
