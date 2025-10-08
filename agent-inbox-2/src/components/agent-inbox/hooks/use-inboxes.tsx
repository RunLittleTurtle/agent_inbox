import { useToast } from "@/hooks/use-toast";
import { useQueryParams } from "./use-query-params";
import {
  AGENT_INBOX_PARAM,
  OFFSET_PARAM,
  LIMIT_PARAM,
  INBOX_PARAM,
} from "../constants";
import { useState, useCallback, useEffect, useRef } from "react";
import { AgentInbox } from "../types";
import { useRouter } from "next/navigation";
import { logger } from "../utils/logger";

/**
 * Hook for managing agent inboxes
 *
 * NOW POWERED BY SUPABASE (was localStorage)
 *
 * Provides functionality to:
 * - Load agent inboxes from Supabase (auto-creates defaults on first load)
 * - Add new agent inboxes
 * - Delete agent inboxes
 * - Change the selected agent inbox
 * - Update an existing agent inbox
 *
 * @returns {Object} Object containing agent inboxes and methods to manage them
 */
export function useInboxes() {
  const { getSearchParam, updateQueryParams } = useQueryParams();
  const router = useRouter();
  const { toast } = useToast();
  const [agentInboxes, setAgentInboxes] = useState<AgentInbox[]>([]);
  const initialLoadComplete = useRef(false);

  /**
   * Load initial inboxes on mount from Supabase
   * Auto-creates default inboxes (Agent, Executive Main) if none exist
   */
  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }
    const initializeInboxes = async () => {
      try {
        logger.log("Loading inboxes from Supabase (with auto-creation)");
        getAgentInboxes();
      } catch (e) {
        logger.error("Error during initial inbox loading", e);
        // Attempt normal load as fallback
        getAgentInboxes();
      }
    };
    initializeInboxes();
    // Run only once on mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /**
   * Load agent inboxes from Supabase and set up proper selection state
   * Auto-creates default inboxes on first request
   */
  const getAgentInboxes = useCallback(
    async () => {
      if (typeof window === "undefined") {
        return;
      }

      try {
        // Fetch inboxes from Supabase (auto-creates defaults if needed)
        const response = await fetch(`${process.env.NEXT_PUBLIC_CONFIG_URL || 'http://localhost:8000'}/api/config/inboxes`, {
          method: "GET",
          credentials: "include",
        });

        if (!response.ok) {
          logger.error("Failed to fetch inboxes from Supabase:", response.statusText);
          setAgentInboxes([]);
          return;
        }

        const data = await response.json();
        logger.log("Fetched inboxes from Supabase:", data);

        const currentInboxes: AgentInbox[] = data.inboxes || [];

        if (!currentInboxes.length) {
          logger.log("No inboxes returned from Supabase");
          setAgentInboxes([]);
          return;
        }

        // Map Supabase inboxes to AgentInbox format
        const formattedInboxes: AgentInbox[] = currentInboxes.map((inbox: any) => ({
          id: inbox.id,
          graphId: inbox.graph_id,
          deploymentUrl: inbox.deployment_url,
          name: inbox.inbox_name,
          selected: inbox.selected,
          tenantId: inbox.tenant_id,
          createdAt: inbox.created_at,
        }));

        const agentInboxSearchParam = getSearchParam(AGENT_INBOX_PARAM);
        logger.log("Agent inbox search param for selection:", agentInboxSearchParam);

        // If there is no agent inbox search param, use the selected inbox from Supabase
        if (!agentInboxSearchParam) {
          const selectedInbox = formattedInboxes.find((inbox) => inbox.selected);
          const inboxToSelect = selectedInbox || formattedInboxes[0];

          updateQueryParams(
            [AGENT_INBOX_PARAM, OFFSET_PARAM, LIMIT_PARAM, INBOX_PARAM],
            [inboxToSelect.id, "0", "10", "interrupted"]
          );
          setAgentInboxes(formattedInboxes);

          // Mark initial load as complete
          if (!initialLoadComplete.current) {
            initialLoadComplete.current = true;
          }

          return;
        }

        // Param exists: Find inbox by param ID
        const selectedByParam = formattedInboxes.find(
          (inbox) => inbox.id === agentInboxSearchParam
        );

        if (selectedByParam) {
          logger.log("Found inbox by search param:", selectedByParam.id);
          setAgentInboxes(formattedInboxes);
        } else {
          // Param exists but inbox not found: Select first
          const firstInbox = formattedInboxes[0];
          logger.log("Inbox for search param not found, selecting first inbox:", firstInbox.id);
          updateQueryParams(AGENT_INBOX_PARAM, firstInbox.id);
          setAgentInboxes(formattedInboxes);
        }

        // Mark initial load as complete
        if (!initialLoadComplete.current) {
          initialLoadComplete.current = true;
        }
      } catch (error) {
        logger.error("Error fetching inboxes from Supabase:", error);
        setAgentInboxes([]);
      }
    },
    [getSearchParam, updateQueryParams]
  );

  /**
   * Add a new agent inbox via Supabase API
   * @param {AgentInbox} agentInbox - The agent inbox to add
   */
  const addAgentInbox = useCallback(
    async (agentInbox: AgentInbox) => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_CONFIG_URL || 'http://localhost:8000'}/api/config/inboxes`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          credentials: "include",
          body: JSON.stringify({
            inbox_name: agentInbox.name || agentInbox.graphId,
            graph_id: agentInbox.graphId,
            deployment_url: agentInbox.deploymentUrl,
            tenant_id: agentInbox.tenantId || null,
          }),
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.error || "Failed to add inbox");
        }

        const data = await response.json();
        logger.log("Inbox added successfully:", data);

        toast({
          title: "Success",
          description: "Agent inbox added successfully",
          duration: 3000,
        });

        // Reload inboxes from Supabase
        await getAgentInboxes();

        // Update URL to show the new inbox
        updateQueryParams(AGENT_INBOX_PARAM, data.inbox.id);

        router.refresh();
      } catch (error) {
        logger.error("Error adding agent inbox", error);
        toast({
          title: "Error",
          description: error instanceof Error ? error.message : "Failed to add agent inbox",
          variant: "destructive",
          duration: 3000,
        });
      }
    },
    [updateQueryParams, router, toast, getAgentInboxes]
  );

  /**
   * Delete an agent inbox by ID via Supabase API
   * @param {string} id - The ID of the agent inbox to delete
   */
  const deleteAgentInbox = useCallback(
    async (id: string) => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_CONFIG_URL || 'http://localhost:8000'}/api/config/inboxes/${id}`, {
          method: "DELETE",
          credentials: "include",
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.error || "Failed to delete inbox");
        }

        logger.log("Inbox deleted successfully:", id);

        toast({
          title: "Success",
          description: "Agent inbox deleted successfully",
          duration: 3000,
        });

        // Reload inboxes from Supabase (will auto-select first if needed)
        await getAgentInboxes();

        router.refresh();
      } catch (error) {
        logger.error("Error deleting agent inbox", error);
        toast({
          title: "Error",
          description: error instanceof Error ? error.message : "Failed to delete agent inbox",
          variant: "destructive",
          duration: 3000,
        });
      }
    },
    [router, toast, getAgentInboxes]
  );

  /**
   * Change the selected agent inbox via Supabase API
   * @param {string} id - The ID of the agent inbox to select
   * @param {boolean} replaceAll - Whether to replace all query parameters
   */
  const changeAgentInbox = useCallback(
    async (id: string, replaceAll?: boolean) => {
      try {
        // Optimistic update to UI
        setAgentInboxes((prevInboxes) =>
          prevInboxes.map((inbox) => ({
            ...inbox,
            selected: inbox.id === id,
          }))
        );

        // Update selection in Supabase
        const response = await fetch(`${process.env.NEXT_PUBLIC_CONFIG_URL || 'http://localhost:8000'}/api/config/inboxes`, {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
          },
          credentials: "include",
          body: JSON.stringify({ inbox_id: id }),
        });

        if (!response.ok) {
          throw new Error("Failed to update inbox selection");
        }

        logger.log("Inbox selection updated successfully:", id);

        // Reload inboxes to get fresh state from server
        await getAgentInboxes();

        // Update URL parameters (smooth transition, no reload)
        updateQueryParams(
          [AGENT_INBOX_PARAM, OFFSET_PARAM, LIMIT_PARAM, INBOX_PARAM],
          [id, "0", "10", "interrupted"]
        );

        // Refresh UI if replaceAll flag is set
        if (replaceAll) {
          router.refresh();
        }
      } catch (error) {
        logger.error("Error changing selected inbox", error);
        // Revert optimistic update on error
        await getAgentInboxes();
      }
    },
    [updateQueryParams, getAgentInboxes]
  );

  /**
   * Update an existing agent inbox via Supabase API
   * @param {AgentInbox} updatedInbox - The updated agent inbox
   */
  const updateAgentInbox = useCallback(
    async (updatedInbox: AgentInbox) => {
      try {
        // Note: For now, we'll just reload after any update
        // Full update endpoint can be added if needed
        logger.log("Updating inbox, reloading from Supabase:", updatedInbox.id);

        await getAgentInboxes();
        router.refresh();
      } catch (error) {
        logger.error("Error updating agent inbox", error);
        toast({
          title: "Error",
          description: "Failed to update agent inbox. Please try again.",
          variant: "destructive",
          duration: 3000,
        });
      }
    },
    [router, toast, getAgentInboxes]
  );

  /**
   * Create default inboxes via Supabase API
   * Called when user clicks "Add Default Inboxes" button
   */
  const createDefaultInboxes = useCallback(
    async () => {
      try {
        const configUrl = process.env.NEXT_PUBLIC_CONFIG_URL || 'http://localhost:8000';
        const endpoint = `${configUrl}/api/config/inboxes/defaults`;

        logger.log("Creating default inboxes at:", endpoint);

        const response = await fetch(endpoint, {
          method: "POST",
          credentials: "include",
        });

        logger.log("Create defaults response status:", response.status);

        if (!response.ok) {
          const errorText = await response.text();
          logger.error("Create defaults failed with response:", errorText);

          let errorMessage = "Failed to create default inboxes";
          try {
            const errorJson = JSON.parse(errorText);
            errorMessage = errorJson.error || errorMessage;
          } catch (_e) {
            // Not JSON, use the text
            errorMessage = errorText || errorMessage;
          }

          throw new Error(errorMessage);
        }

        const data = await response.json();
        logger.log("Default inboxes created successfully:", data);

        toast({
          title: "Success",
          description: data.message || "Default inboxes created successfully",
          duration: 3000,
        });

        // Reload inboxes from Supabase
        await getAgentInboxes();

        router.refresh();
      } catch (error) {
        logger.error("Error creating default inboxes:", error);

        // More descriptive error message
        let errorMessage = "Failed to create default inboxes";
        if (error instanceof TypeError && error.message.includes("fetch")) {
          errorMessage = "Unable to reach config server. Please check your connection.";
        } else if (error instanceof Error) {
          errorMessage = error.message;
        }

        toast({
          title: "Error",
          description: errorMessage,
          variant: "destructive",
          duration: 5000,
        });
      }
    },
    [toast, getAgentInboxes, router]
  );

  return {
    agentInboxes,
    getAgentInboxes,
    addAgentInbox,
    deleteAgentInbox,
    changeAgentInbox,
    updateAgentInbox,
    createDefaultInboxes,
  };
}
