"use client";

import React from 'react';
import Link from 'next/link';
import { ArrowLeft, RefreshCw, Save, AlertCircle } from 'lucide-react';
import { ConfigSidebarStandalone } from '@/components/config/ConfigSidebarStandalone';
import { EnhancedConfigForm } from '@/components/config/EnhancedConfigForm';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useToast } from '@/hooks/use-toast';

interface Agent {
  id: string;
  path: string;
  config: {
    CONFIG_INFO: {
      name: string;
      description: string;
      config_type: string;
      config_path: string;
    };
    CONFIG_SECTIONS: Array<{
      key: string;
      label: string;
      description: string;
      fields: Array<{
        key: string;
        label: string;
        type: string;
        envVar?: string;
        default?: any;
        description?: string;
        placeholder?: string;
        required?: boolean;
        options?: string[];
        validation?: any;
        note?: string;
        warning?: string;
      }>;
    }>;
  };
}

export default function ConfigPage() {
  const [agents, setAgents] = React.useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent] = React.useState<string | null>(null);
  const [showMainMenu, setShowMainMenu] = React.useState(true);
  const [configValues, setConfigValues] = React.useState<Record<string, any>>({});
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [pendingChanges, setPendingChanges] = React.useState<Record<string, any>>({});

  const { toast } = useToast();

  // Simple retry helper following Next.js best practices
  const fetchWithRetry = async (url: string, retries = 2): Promise<Response> => {
    for (let i = 0; i <= retries; i++) {
      try {
        const response = await fetch(url);
        if (response.ok) return response;

        // Don't retry on 4xx errors (client errors)
        if (response.status >= 400 && response.status < 500) {
          throw new Error(`Client error: ${response.status}`);
        }

        // Retry on 5xx errors (server errors)
        if (i < retries) {
          await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1))); // exponential backoff
          continue;
        }

        throw new Error(`Server error: ${response.status}`);
      } catch (err) {
        if (i === retries) throw err;
        await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
      }
    }
    throw new Error('Max retries exceeded');
  };

  // Load config values for specific agent
  const loadAgentValues = React.useCallback(async (agentId: string | null) => {
    try {
      const url = agentId
        ? `/api/config/values?agentId=${agentId}`
        : '/api/config/values';

      const response = await fetchWithRetry(url);
      const data = await response.json();

      setConfigValues(data.values);
    } catch (error) {
      console.error('Error loading agent values:', error);
    }
  }, []);

  // Load agents and initial config data
  React.useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);

        console.log('[ConfigPage] Starting to load configuration...');

        // Load agents first
        console.log('[ConfigPage] Fetching agents from /api/config/agents');
        const agentsResponse = await fetchWithRetry('/api/config/agents');
        const agentsData = await agentsResponse.json();

        console.log('[ConfigPage] Loaded', agentsData.agents?.length || 0, 'agents');
        setAgents(agentsData.agents);

        // Load values for the current selection
        const agentId = showMainMenu ? null : selectedAgent;
        console.log('[ConfigPage] Loading values for agentId:', agentId);
        await loadAgentValues(agentId);

        console.log('[ConfigPage] Configuration loaded successfully');
      } catch (err) {
        console.error('[ConfigPage] Error loading configuration:', err);
        setError(err instanceof Error ? err.message : 'Failed to load configuration');
      } finally {
        console.log('[ConfigPage] Setting loading to false');
        setLoading(false);
      }
    };

    loadData();
  }, []);

  // Reload values when agent selection changes
  React.useEffect(() => {
    if (!loading) {
      const agentId = showMainMenu ? null : selectedAgent;
      loadAgentValues(agentId);
    }
  }, [selectedAgent, showMainMenu, loadAgentValues]);

  const handleValueChange = async (sectionKey: string, fieldKey: string, value: any, envVar?: string) => {
    const changeKey = `${sectionKey}.${fieldKey}`;

    // Update local state immediately for responsive UI
    setPendingChanges(prev => ({
      ...prev,
      [changeKey]: { sectionKey, fieldKey, value, envVar }
    }));

    // Update nested structure for immediate UI feedback (always)
    setConfigValues(prev => ({
      ...prev,
      [sectionKey]: {
        ...(prev[sectionKey] || {}),
        [fieldKey]: value
      },
      // Also update flat envVar structure if provided (for backward compatibility)
      ...(envVar ? { [envVar]: value } : {})
    }));

    try {
      // Send update to server
      const response = await fetch('/api/config/update', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          agentId: selectedAgent || 'global',
          configPath: selectedAgent ? agents.find(a => a.id === selectedAgent)?.path : 'ui_config.py',
          sectionKey,
          fieldKey,
          value,
          envVar,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to update configuration');
      }

      // Remove from pending changes on success
      setPendingChanges(prev => {
        const updated = { ...prev };
        delete updated[changeKey];
        return updated;
      });

      toast({
        title: "Configuration Updated",
        description: `${fieldKey} has been updated successfully.`,
      });

      // Don't reload values immediately after update to avoid race conditions
      // The optimistic update (lines 145-164) already updated local state
      // Values will be reloaded when user switches agents or explicitly refreshes

    } catch (error) {
      console.error('Error updating configuration:', error);

      toast({
        variant: "destructive",
        title: "Update Failed",
        description: `Failed to update ${fieldKey}. Please try again.`,
      });

      // Revert local change on error - reload from server is more reliable
      const agentId = showMainMenu ? null : selectedAgent;
      await loadAgentValues(agentId);

      // Remove from pending changes
      setPendingChanges(prev => {
        const updated = { ...prev };
        delete updated[changeKey];
        return updated;
      });
    }
  };

  const handleRefresh = () => {
    window.location.reload();
  };

  const getCurrentConfig = () => {
    if (showMainMenu) {
      // Find the global config agent
      const globalAgent = agents.find(agent => agent.config.CONFIG_INFO.config_type === 'env_file');
      return globalAgent ? globalAgent.config.CONFIG_SECTIONS : [];
    }

    if (selectedAgent) {
      const agent = agents.find(a => a.id === selectedAgent);
      return agent ? agent.config.CONFIG_SECTIONS : [];
    }

    return [];
  };

  const getCurrentAgentInfo = () => {
    if (showMainMenu) {
      const globalAgent = agents.find(agent => agent.config.CONFIG_INFO.config_type === 'env_file');
      return globalAgent?.config.CONFIG_INFO || {
        name: 'Global Environment',
        description: 'System-wide configuration and API keys',
        config_type: 'env_file',
        config_path: '.env'
      };
    }

    if (selectedAgent) {
      const agent = agents.find(a => a.id === selectedAgent);
      return agent?.config.CONFIG_INFO || null;
    }

    return null;
  };

  const handleAgentSelect = (agentId: string) => {
    setSelectedAgent(agentId);
    setShowMainMenu(false);
  };

  const handleMainMenuSelect = () => {
    setSelectedAgent(null);
    setShowMainMenu(true);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <RefreshCw className="w-8 h-8 animate-spin" />
      </div>
    );
  }

  return (
    <>
      <div className="flex h-screen bg-gray-50">
        <ConfigSidebarStandalone
          agents={agents}
          selectedAgent={selectedAgent}
          onAgentSelect={handleAgentSelect}
          onMainMenuSelect={handleMainMenuSelect}
          showMainMenu={showMainMenu}
        />

        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Header */}
          <div className="bg-white border-b border-gray-200 p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <Link href="http://localhost:3000" className="flex items-center gap-2 text-gray-600 hover:text-gray-800">
                  <ArrowLeft className="w-4 h-4" />
                  <span>Back to Inbox</span>
                </Link>

                <div className="h-6 w-px bg-gray-300" />

                <div>
                  <h1 className="text-xl font-semibold text-gray-800">
                    {getCurrentAgentInfo()?.name || 'Configuration'}
                  </h1>
                  {getCurrentAgentInfo()?.description && (
                    <p className="text-sm text-gray-600">
                      {getCurrentAgentInfo()?.description}
                    </p>
                  )}
                </div>
              </div>

              <Button
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                className="flex items-center gap-2"
              >
                <RefreshCw className="w-4 h-4" />
                Refresh
              </Button>
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6">
            {error && (
              <Alert variant="destructive" className="mb-6">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {Object.keys(pendingChanges).length > 0 && (
              <Alert className="mb-6">
                <Save className="h-4 w-4" />
                <AlertDescription>
                  {Object.keys(pendingChanges).length} change{Object.keys(pendingChanges).length > 1 ? 's' : ''} pending...
                </AlertDescription>
              </Alert>
            )}

            <EnhancedConfigForm
              sections={getCurrentConfig()}
              values={configValues}
              onValueChange={handleValueChange}
            />
          </div>
        </div>

      </div>
    </>
  );
}
