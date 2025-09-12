import { Message } from "@langchain/langgraph-sdk";
import { useStreamContext } from "@/providers/Stream";

/**
 * Determines if this is the final supervisor response that should be prominently displayed
 * This is the last message from multi_agent_supervisor before workflow ends
 */
export function isFinalSupervisorResponse(message: Message): boolean {
  const thread = useStreamContext();

  // Check if message is from multi_agent_supervisor
  const isFromSupervisor = message.name === 'multi_agent_supervisor' ||
                          message.name === 'supervisor';

  if (!isFromSupervisor) return false;

  // Check if this is the last AI message (indicating workflow completion)
  const lastAIMessage = thread.messages
    .filter(m => m.type === 'ai')
    .pop();

  const isLastAIMessage = lastAIMessage?.id === message.id;

  // Check if workflow appears to be complete (no more streaming)
  const isWorkflowComplete = !thread.isLoading &&
                            thread.streamingActivity?.agents.size === 0;

  return isLastAIMessage && isWorkflowComplete;
}

/**
 * Alternative approach: Check if this supervisor message is followed by workflow end
 * We look for patterns that indicate the workflow is ending after this message
 */
export function isFinalSupervisorResponseAlt(message: Message, messages: Message[]): boolean {
  // Find current message index
  const currentIndex = messages.findIndex(m => m.id === message.id);
  if (currentIndex === -1) return false;

  // Check if message is from supervisor
  const isFromSupervisor = message.name === 'multi_agent_supervisor' ||
                          message.name === 'supervisor';

  if (!isFromSupervisor) return false;

  // Check if this is one of the last few messages and no more agent activity follows
  const remainingMessages = messages.slice(currentIndex + 1);
  const hasMoreAgentActivity = remainingMessages.some(m =>
    m.type === 'ai' &&
    (m.name === 'calendar_agent' || m.name === 'email_agent' || m.name === 'job_search_agent')
  );

  // If no more agent activity follows, this is likely the final response
  return !hasMoreAgentActivity;
}

/**
 * Check if message should be treated as intermediate (collapsible)
 */
export function isIntermediateMessage(message: Message): boolean {
  // Individual agents are always intermediate
  const individualAgents = ['calendar_agent', 'email_agent', 'job_search_agent'];

  if (individualAgents.includes(message.name || '')) {
    return true;
  }

  // Supervisor messages are final unless proven intermediate
  if (message.name === 'multi_agent_supervisor' || message.name === 'supervisor') {
    return false;
  }

  // Default: treat as intermediate if we're unsure
  return true;
}
