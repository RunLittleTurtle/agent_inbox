import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, ChevronUp, Check, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useStreamContext } from "@/providers/Stream";

function isComplexValue(value: any): boolean {
  return Array.isArray(value) || (typeof value === "object" && value !== null);
}

function isUrl(value: any): boolean {
  if (typeof value !== "string") return false;
  try {
    new URL(value);
    return value.startsWith("http://") || value.startsWith("https://");
  } catch {
    return false;
  }
}

function parseInterruptText(text: string): { [key: string]: string } | null {
  if (typeof text !== "string" || text.length < 30) return null;

  const parsed: { [key: string]: string } = {};

  // Parse the exact format: "🗓️ Booking approval required: Planning voyage Start: 2025-09-05T14:00:00-04:00 End: 2025-09-05T15:00:00-04:00 Location: None Description: Réunion pour planifier un voyage Approve (yes), modify, or reject?"

  // Extract main request type (everything before the first colon after emoji)
  const requestMatch = text.match(/^[^\w]*([^:]+):\s*(.+)/);
  if (requestMatch) {
    parsed["Request Type"] = requestMatch[1].trim();
    const remainingText = requestMatch[2];

    // Extract event details (everything before "Start:")
    const eventMatch = remainingText.match(/^([^S]+?)(?=\s+Start:)/);
    if (eventMatch) {
      parsed["Event"] = eventMatch[1].trim();
    }

    // Extract start time
    const startMatch = remainingText.match(/Start:\s*([\d-T:+]+)/);
    if (startMatch) {
      parsed["Start Time"] = formatDateTime(startMatch[1]);
    }

    // Extract end time
    const endMatch = remainingText.match(/End:\s*([\d-T:+]+)/);
    if (endMatch) {
      parsed["End Time"] = formatDateTime(endMatch[1]);
    }

    // Extract location (only if not "None")
    const locationMatch = remainingText.match(
      /Location:\s*([^\s]+(?:\s+[^\s]+)*?)(?:\s+Description:|$)/,
    );
    if (locationMatch) {
      const location = locationMatch[1].trim();
      if (location && location !== "None") {
        parsed["Location"] = location;
      }
    }

    // Extract description
    const descMatch = remainingText.match(
      /Description:\s*([^A]+?)(?:\s+Approve|$)/,
    );
    if (descMatch) {
      const desc = descMatch[1].trim();
      if (desc) {
        parsed["Description"] = desc;
      }
    }

    // Extract approval prompt
    const approveMatch = remainingText.match(/(Approve\s*\([^)]+\)[^?]*\?)/);
    if (approveMatch) {
      parsed["Action Required"] = approveMatch[1].trim();
    }
  }

  return Object.keys(parsed).length > 2 ? parsed : null;
}

function formatDateTime(dateTimeStr: string): string {
  try {
    const date = new Date(dateTimeStr);
    if (!isNaN(date.getTime())) {
      return date.toLocaleString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        timeZoneName: "short",
      });
    }
  } catch (e) {
    // Return original if parsing fails
  }
  return dateTimeStr;
}

function renderInterruptStateItem(value: any, key?: string): React.ReactNode {
  if (value === null || value === undefined) {
    return <span className="text-gray-400 italic">null</span>;
  }

  if (isComplexValue(value)) {
    return (
      <code className="rounded bg-gray-50 px-2 py-1 font-mono text-sm whitespace-pre-wrap">
        {JSON.stringify(value, null, 2)}
      </code>
    );
  } else if (isUrl(value)) {
    return (
      <a
        href={value}
        target="_blank"
        rel="noopener noreferrer"
        className="break-all text-blue-600 underline hover:text-blue-800"
      >
        {value}
      </a>
    );
  } else {
    const stringValue = String(value);

    // Try to parse structured text for better display
    if (key === "value" && stringValue.length > 30) {
      // Always organize the data by splitting on key patterns
      const parts = stringValue.split(
        /(?=\s(?:Start|End|Location|Description|Approve)(?:\s|:))/i,
      );

      if (parts.length > 1) {
        return (
          <div className="space-y-3 rounded-lg border border-gray-200 bg-white p-4">
            {parts.map((part, idx) => {
              const trimmed = part.trim();
              if (!trimmed) return null;

              // Check if this part has a field pattern (word followed by colon)
              const colonMatch = trimmed.match(/^([^:]+?):\s*(.+)$/);
              if (colonMatch) {
                const fieldName = colonMatch[1].replace(/^[^\w\s]*/, "").trim(); // Remove emoji
                let fieldValue = colonMatch[2].trim();

                // Clean up field values
                if (
                  fieldValue.includes(" Start:") ||
                  fieldValue.includes(" End:") ||
                  fieldValue.includes(" Location:") ||
                  fieldValue.includes(" Description:")
                ) {
                  fieldValue = fieldValue
                    .split(/\s(?:Start|End|Location|Description):/)[0]
                    .trim();
                }

                // Format dates if detected
                if (
                  fieldName.toLowerCase().includes("start") ||
                  fieldName.toLowerCase().includes("end")
                ) {
                  fieldValue = formatDateTime(fieldValue);
                }

                return (
                  <div
                    key={idx}
                    className="border-l-4 border-blue-500 bg-blue-50 py-2 pl-4"
                  >
                    <div className="mb-1 text-xs font-bold tracking-wider text-blue-800 uppercase">
                      {fieldName}
                    </div>
                    <div className="text-sm leading-relaxed font-medium text-gray-900">
                      {fieldValue}
                    </div>
                  </div>
                );
              } else {
                // For text without colon, treat as general content
                return (
                  <div
                    key={idx}
                    className="rounded border-l-4 border-gray-300 bg-gray-50 p-3 text-sm text-gray-700"
                  >
                    {trimmed}
                  </div>
                );
              }
            })}
          </div>
        );
      }
    }

    // Default rendering for other cases
    return (
      <span className="text-sm break-words text-gray-800">{stringValue}</span>
    );
  }
}

export function GenericInterruptView({
  interrupt,
}: {
  interrupt: Record<string, any> | Record<string, any>[];
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const thread = useStreamContext();

  const contentStr = JSON.stringify(interrupt, null, 2);
  const contentLines = contentStr.split("\n");
  const shouldTruncate = contentLines.length > 4 || contentStr.length > 500;

  // Function to truncate long string values (but preserve URLs)
  const truncateValue = (value: any): any => {
    if (typeof value === "string" && value.length > 100) {
      // Don't truncate URLs so they remain clickable
      if (isUrl(value)) {
        return value;
      }
      return value.substring(0, 100) + "...";
    }

    if (Array.isArray(value) && !isExpanded) {
      return value.slice(0, 2).map(truncateValue);
    }

    if (isComplexValue(value) && !isExpanded) {
      const strValue = JSON.stringify(value, null, 2);
      if (strValue.length > 100) {
        // Return plain text for truncated content instead of a JSON object
        return `Truncated ${strValue.length} characters...`;
      }
    }

    return value;
  };

  // Process entries based on expanded state
  const processEntries = () => {
    if (Array.isArray(interrupt)) {
      return isExpanded ? interrupt : interrupt.slice(0, 5);
    } else if (typeof interrupt === "object" && interrupt !== null) {
      const entries = Object.entries(interrupt);
      if (!isExpanded && shouldTruncate) {
        // When collapsed, process each value to potentially truncate it
        return entries.map(([key, value]) => [key, truncateValue(value)]);
      }
      return entries;
    } else {
      // Handle primitive values (strings, numbers, etc.) - don't treat as arrays
      return [["value", interrupt]];
    }
  };

  const displayEntries = processEntries();

  // Check if this is an interrupt that allows actions
  const interruptObj = Array.isArray(interrupt) ? interrupt[0] : interrupt;

  // More flexible action detection - always show actions for human interrupts
  // This ensures users can always respond to interrupts requesting feedback
  const hasActions = true; // Show actions for all human interrupts

  // Action handlers
  const handleAccept = async () => {
    setIsSubmitting(true);
    try {
      thread.submit(
        {},
        {
          command: {
            resume: [
              {
                type: "accept",
                args: null,
              },
            ],
          },
        },
      );
    } catch (error) {
      console.error("Failed to accept:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReject = async () => {
    setIsSubmitting(true);
    try {
      thread.submit(
        {},
        {
          command: {
            resume: [
              {
                type: "ignore",
                args: "Rejected by user",
              },
            ],
          },
        },
      );
    } catch (error) {
      console.error("Failed to reject:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="overflow-hidden rounded-lg border border-gray-200">
      <div className="border-b border-gray-200 bg-gray-50 px-4 py-2">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h3 className="font-medium text-gray-900">Human Interrupt</h3>
        </div>
      </div>
      <motion.div
        className="min-w-full bg-gray-100"
        initial={false}
        animate={{ height: "auto" }}
        transition={{ duration: 0.3 }}
      >
        <div className="p-3">
          <AnimatePresence
            mode="wait"
            initial={false}
          >
            <motion.div
              key={isExpanded ? "expanded" : "collapsed"}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.2 }}
              style={{
                maxHeight: isExpanded ? "none" : "500px",
                overflow: "auto",
              }}
            >
              <table className="min-w-full divide-y divide-gray-200">
                <tbody className="divide-y divide-gray-200">
                  {displayEntries.map((item, argIdx) => {
                    const [key, value] = Array.isArray(interrupt)
                      ? [argIdx.toString(), item]
                      : (item as [string, any]);
                    return (
                      <tr key={argIdx}>
                        <td className="px-4 py-2 text-sm font-medium whitespace-nowrap text-gray-900">
                          {key}
                        </td>
                        <td className="px-4 py-2 text-sm text-gray-500">
                          {renderInterruptStateItem(value, key)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </motion.div>
          </AnimatePresence>
        </div>
        {(shouldTruncate ||
          (Array.isArray(interrupt) && interrupt.length > 5)) && (
          <motion.button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex w-full cursor-pointer items-center justify-center border-t-[1px] border-gray-200 py-2 text-gray-500 transition-all duration-200 ease-in-out hover:bg-gray-50 hover:text-gray-600"
            initial={{ scale: 1 }}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            {isExpanded ? <ChevronUp /> : <ChevronDown />}
          </motion.button>
        )}

        {/* Action Buttons for Interrupts */}
        {hasActions && (
          <div className="border-t border-gray-200 bg-white p-4">
            <div className="flex flex-wrap gap-2">
              <Button
                onClick={handleAccept}
                disabled={isSubmitting}
                className="bg-green-600 text-white hover:bg-green-700"
                size="sm"
              >
                <Check className="mr-1 h-4 w-4" />
                Accept
              </Button>

              <Button
                onClick={handleReject}
                disabled={isSubmitting}
                variant="destructive"
                size="sm"
              >
                <X className="mr-1 h-4 w-4" />
                Reject
              </Button>
            </div>
          </div>
        )}
      </motion.div>
    </div>
  );
}
