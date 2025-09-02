import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, ChevronUp, Check, X, Edit } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
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

function renderInterruptStateItem(value: any): React.ReactNode {
  if (isComplexValue(value)) {
    return (
      <code className="rounded bg-gray-50 px-2 py-1 font-mono text-sm">
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
    return String(value);
  }
}

export function GenericInterruptView({
  interrupt,
}: {
  interrupt: Record<string, any> | Record<string, any>[];
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showModifyInput, setShowModifyInput] = useState(false);
  const [modifyText, setModifyText] = useState("");
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
    } else {
      const entries = Object.entries(interrupt);
      if (!isExpanded && shouldTruncate) {
        // When collapsed, process each value to potentially truncate it
        return entries.map(([key, value]) => [key, truncateValue(value)]);
      }
      return entries;
    }
  };

  const displayEntries = processEntries();

  // Check if this is an interrupt that allows actions
  const interruptObj = Array.isArray(interrupt) ? interrupt[0] : interrupt;
  const hasActions = interruptObj && 
    typeof interruptObj === "object" && 
    "config" in interruptObj &&
    typeof interruptObj.config === "object";

  // Action handlers
  const handleAccept = async () => {
    setIsSubmitting(true);
    try {
      thread.submit({}, {
        command: {
          resume: [{
            type: "accept",
            args: null
          }]
        }
      });
    } catch (error) {
      console.error("Failed to accept:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReject = async () => {
    setIsSubmitting(true);
    try {
      thread.submit({}, {
        command: {
          resume: [{
            type: "ignore",
            args: "Rejected by user"
          }]
        }
      });
    } catch (error) {
      console.error("Failed to reject:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleModify = async () => {
    if (!modifyText.trim()) return;
    
    setIsSubmitting(true);
    try {
      thread.submit({}, {
        command: {
          resume: [{
            type: "response",
            args: modifyText
          }]
        }
      });
      setShowModifyInput(false);
      setModifyText("");
    } catch (error) {
      console.error("Failed to modify:", error);
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
                          {renderInterruptStateItem(value)}
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
          <div className="border-t border-gray-200 bg-white p-4 space-y-3">
            {/* Modify Input */}
            {showModifyInput && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                className="space-y-2"
              >
                <Textarea
                  placeholder="Provide feedback or describe changes..."
                  value={modifyText}
                  onChange={(e) => setModifyText(e.target.value)}
                  className="min-h-[80px] resize-none"
                />
              </motion.div>
            )}

            {/* Action Buttons */}
            <div className="flex flex-wrap gap-2">
              <Button 
                onClick={handleAccept}
                disabled={isSubmitting}
                className="bg-green-600 hover:bg-green-700 text-white"
                size="sm"
              >
                <Check className="h-4 w-4 mr-1" />
                Accept
              </Button>
              
              <Button 
                onClick={handleReject}
                disabled={isSubmitting}
                variant="destructive"
                size="sm"
              >
                <X className="h-4 w-4 mr-1" />
                Reject
              </Button>
              
              {!showModifyInput ? (
                <Button 
                  onClick={() => setShowModifyInput(true)}
                  disabled={isSubmitting}
                  variant="outline"
                  size="sm"
                >
                  <Edit className="h-4 w-4 mr-1" />
                  Modify
                </Button>
              ) : (
                <div className="flex gap-2">
                  <Button 
                    onClick={handleModify}
                    disabled={isSubmitting || !modifyText.trim()}
                    className="bg-blue-600 hover:bg-blue-700 text-white"
                    size="sm"
                  >
                    Submit Feedback
                  </Button>
                  <Button 
                    onClick={() => {
                      setShowModifyInput(false);
                      setModifyText("");
                    }}
                    disabled={isSubmitting}
                    variant="outline"
                    size="sm"
                  >
                    Cancel
                  </Button>
                </div>
              )}
            </div>
          </div>
        )}
      </motion.div>
    </div>
  );
}
