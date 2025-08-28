import { Client } from "@langchain/langgraph-sdk";

export const createClient = ({
  deploymentUrl,
  langchainApiKey,
}: {
  deploymentUrl: string;
  langchainApiKey: string | undefined;
}) => {
  return new Client({
    apiUrl: deploymentUrl,
    defaultHeaders: {
      ...(langchainApiKey && { "x-api-key": langchainApiKey }),
    },
  });
};
