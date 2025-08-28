import { ThreadData } from "../types";
import { GenericInterruptValue } from "./generic-interrupt-value";

// InterruptDetailsView component
export function InterruptDetailsView({
  threadData,
}: {
  threadData: ThreadData<any>;
}) {
  return (
    <div className="flex flex-col gap-4 h-full w-full">
      {threadData.thread.interrupts &&
      Object.entries(threadData.thread.interrupts).length > 0 ? (
        Object.entries(threadData.thread.interrupts).map(
          ([interruptId, values]) => (
            <GenericInterruptValue
              key={interruptId}
              interrupt={values?.[values?.length - 1]?.value}
              id={interruptId}
            />
          )
        )
      ) : (
        <div className="text-gray-500 text-sm">No interrupt data available</div>
      )}
    </div>
  );
}
