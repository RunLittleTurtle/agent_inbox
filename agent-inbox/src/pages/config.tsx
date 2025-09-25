"use client";

import React from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { ArrowLeft, RefreshCw, Save, AlertCircle } from 'lucide-react';
import { ConfigSidebar } from '@/components/config/ConfigSidebar';
import { ConfigForm } from '@/components/config/ConfigForm';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Toaster } from '@/components/ui/toaster';
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

  // Load agents and config data
  React.useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Load agents
        const agentsResponse = await fetch('/api/config/agents');
        if (!agentsResponse.ok) {
          throw new Error('Failed to load agents');
        }
        const agentsData = await agentsResponse.json();
        setAgents(agentsData.agents);

        // Load current config values
        const valuesResponse = await fetch('/api/config/values');
        if (!valuesResponse.ok) {
          throw new Error('Failed to load configuration values');
        }
        const valuesData = await valuesResponse.json();
        setConfigValues(valuesData.values);

      } catch (err) {
        console.error('Error loading configuration:', err);
        setError(err instanceof Error ? err.message : 'Failed to load configuration');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  const handleValueChange = async (sectionKey: string, fieldKey: string, value: any, envVar?: string) => {
    const changeKey = `${sectionKey}.${fieldKey}`;

    // Update local state immediately for responsive UI
    setPendingChanges(prev => ({
      ...prev,
      [changeKey]: { sectionKey, fieldKey, value, envVar }
    }));

    if (envVar) {
      setConfigValues(prev => ({
        ...prev,
        [envVar]: value
      }));
    }

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

    } catch (error) {
      console.error('Error updating configuration:', error);

      toast({
        variant: "destructive",
        title: "Update Failed",
        description: `Failed to update ${fieldKey}. Please try again.`,
      });

      // Revert local change on error
      if (envVar) {
        setConfigValues(prev => ({
          ...prev,
          [envVar]: prev[envVar] // Revert to previous value
        }));
      }
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
      <Head>
        <title>Agent Configuration - Agent Inbox</title>
        <meta name="description" content="Configure agents and environment settings" />
      </Head>

      <div className="flex h-screen bg-gray-50">
        <ConfigSidebar
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
                <Link href="/" className="flex items-center gap-2 text-gray-600 hover:text-gray-800">
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

            <ConfigForm
              sections={getCurrentConfig()}
              values={configValues}
              onValueChange={handleValueChange}
            />
          </div>
        </div>

        <Toaster />
      </div>
    </>
  );
}