import { AIMessage, ToolMessage } from "@langchain/langgraph-sdk";

export function ToolCalls({
  toolCalls,
}: {
  toolCalls: AIMessage["tool_calls"];
}) {
  if (!toolCalls || toolCalls.length === 0) return null;

  return (
    <div className="space-y-1">
      {toolCalls.map((tc, idx) => {
        const args = tc.args as Record<string, any>;
        const hasArgs = Object.keys(args).length > 0;

        return (
          <div
            key={idx}
            className="rounded bg-gray-100 px-3 py-2 text-xs text-gray-600"
          >
            <div className="font-mono">
              <span className="font-medium">{tc.name}</span>
              {tc.id && (
                <span className="ml-2 opacity-60">{tc.id.slice(-8)}</span>
              )}
            </div>
            {hasArgs && (
              <div className="mt-1 font-mono opacity-80">
                {Object.entries(args)
                  .slice(0, 2)
                  .map(([key, value]) => (
                    <div key={key}>
                      {key}:{" "}
                      {typeof value === "string" && value.length > 30
                        ? value.substring(0, 30) + "..."
                        : String(value)}
                    </div>
                  ))}
                {Object.keys(args).length > 2 && (
                  <div className="opacity-60">
                    ...{Object.keys(args).length - 2} more
                  </div>
                )}
              </div>
            )}
            {!hasArgs && <div className="font-mono opacity-60">{"{}"}</div>}
          </div>
        );
      })}
    </div>
  );
}

export function ToolResult({ message }: { message: ToolMessage }) {
  const contentStr = String(message.content);
  const displayContent =
    contentStr.length > 100 ? contentStr.substring(0, 100) + "..." : contentStr;

  return (
    <div className="rounded bg-gray-100 px-3 py-2 text-xs text-gray-600">
      <div className="font-mono">
        <span className="font-medium">Tool Result: </span>
        {message.name && <span>{message.name}</span>}
        {message.tool_call_id && (
          <span className="ml-2 opacity-60">
            {message.tool_call_id.slice(-8)}
          </span>
        )}
      </div>
      <div className="mt-1 font-mono whitespace-pre-wrap opacity-80">
        {displayContent}
      </div>
    </div>
  );
}
