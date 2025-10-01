import { Client } from "@langchain/langgraph-sdk";

export function createClient(
  apiUrl: string,
  apiKey: string | undefined,
  clerkToken?: string | null
) {
  return new Client({
    apiKey,
    apiUrl,
    defaultHeaders: {
      // Add Clerk JWT for custom auth (2025 LangGraph Platform feature)
      ...(clerkToken && { Authorization: `Bearer ${clerkToken}` }),
    },
  });
}
