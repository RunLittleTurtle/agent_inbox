import { Client } from "@langchain/langgraph-sdk";

export const createClient = ({
  deploymentUrl,
  langchainApiKey,
  clerkToken,
}: {
  deploymentUrl: string;
  langchainApiKey: string | undefined;
  clerkToken?: string | null;
}) => {
  return new Client({
    apiUrl: deploymentUrl,
    defaultHeaders: {
      ...(langchainApiKey && { "x-api-key": langchainApiKey }),
      // Add Clerk JWT for custom auth (2025 LangGraph Platform feature)
      ...(clerkToken && { Authorization: `Bearer ${clerkToken}` }),
    },
  });
};
