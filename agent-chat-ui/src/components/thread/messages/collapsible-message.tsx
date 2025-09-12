import { useState } from "react";
import { ChevronRight, ChevronDown } from "lucide-react";
import { MarkdownText } from "../markdown-text";

interface CollapsibleMessageProps {
  content: string;
  agentName: string;
  children?: React.ReactNode;
  shouldCollapse: boolean;
}

export function CollapsibleMessage({
  content,
  agentName,
  children,
  shouldCollapse,
}: CollapsibleMessageProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // If not collapsible, render normally
  if (!shouldCollapse) {
    return (
      <div className="py-1">
        <MarkdownText>{content}</MarkdownText>
        {children}
      </div>
    );
  }

  // Render as collapsible grey box
  return (
    <div className="mb-2">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex w-full items-center justify-between rounded bg-gray-100 px-3 py-2 text-sm text-gray-600 hover:bg-gray-150 focus:outline-none focus:ring-1 focus:ring-gray-300"
      >
        <div className="flex items-center gap-2">
          <span className="font-medium">{agentName}</span>
          <span className="text-xs opacity-60">
            {content.length > 50 ? content.substring(0, 50) + "..." : content}
          </span>
        </div>
        {isExpanded ? (
          <ChevronDown className="h-4 w-4" />
        ) : (
          <ChevronRight className="h-4 w-4" />
        )}
      </button>

      {isExpanded && (
        <div className="mt-1 rounded border border-gray-200 bg-white p-3 text-sm">
          <MarkdownText>{content}</MarkdownText>
          {children}
        </div>
      )}
    </div>
  );
}

// Helper function to get display name for agents
export function getAgentDisplayName(messageName: string): string {
  if (!messageName) return "Agent";

  const nameMapping: Record<string, string> = {
    "calendar_agent": "Calendar Agent",
    "email_agent": "Email Agent",
    "job_search_agent": "Job Search Agent",
    "multi_agent_supervisor": "Assistant",
    "supervisor": "Assistant",
  };

  return nameMapping[messageName] || messageName.replace(/_/g, " ");
}
