"use client";

import React from 'react';
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { Settings, Globe, Bot, Calendar, FileText, User, Briefcase } from "lucide-react";
import { cn } from "@/lib/utils";

interface Agent {
  id: string;
  path: string;
  config: {
    CONFIG_INFO: {
      name: string;
      description: string;
      config_type: string;
    };
  };
}

interface ConfigSidebarProps {
  agents: Agent[];
  selectedAgent: string | null;
  onAgentSelect: (agentId: string) => void;
  onMainMenuSelect: () => void;
  showMainMenu: boolean;
}

const getAgentIcon = (agentId: string, configType: string) => {
  if (configType === 'env_file') return <Globe className="w-4 h-4" />;

  switch (agentId) {
    case 'calendar_agent':
      return <Calendar className="w-4 h-4" />;
    case 'drive_react_agent':
      return <FileText className="w-4 h-4" />;
    case 'job_search_agent':
      return <Briefcase className="w-4 h-4" />;
    case 'executive-ai-assistant':
      return <User className="w-4 h-4" />;
    default:
      return <Bot className="w-4 h-4" />;
  }
};

const getDisplayName = (agent: Agent) => {
  const name = agent.config.CONFIG_INFO.name;
  if (name.includes('{') && name.includes('}')) {
    // Handle template placeholders
    return agent.id.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  }
  return name;
};

export function ConfigSidebar({
  agents,
  selectedAgent,
  onAgentSelect,
  onMainMenuSelect,
  showMainMenu,
}: ConfigSidebarProps) {
  return (
    <div className="w-72 h-full bg-[#F9FAFB] border-r border-gray-200">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <Settings className="w-5 h-5 text-gray-600" />
          <h2 className="font-semibold text-gray-800">Configuration</h2>
        </div>
      </div>

      <div className="flex flex-col h-full">
        <div className="flex-1 overflow-y-auto p-4">
          <div className="space-y-1">
            <button
              onClick={onMainMenuSelect}
              className={cn(
                "w-full flex items-center gap-3 px-3 py-3 text-sm rounded-md transition-colors",
                showMainMenu
                  ? "bg-blue-50 text-blue-700 border border-blue-200"
                  : "text-gray-600 hover:bg-gray-100"
              )}
            >
              <Globe className="w-4 h-4 flex-shrink-0" />
              <span className="font-medium">Global Environment</span>
            </button>

            {agents
              .filter((agent) => agent.config.CONFIG_INFO.config_type !== 'env_file')
              .map((agent) => {
                const displayName = getDisplayName(agent);
                const isSelected = selectedAgent === agent.id;

                return (
                  <button
                    key={agent.id}
                    onClick={() => onAgentSelect(agent.id)}
                    className={cn(
                      "w-full flex items-center gap-3 px-3 py-3 text-sm rounded-md transition-colors",
                      isSelected
                        ? "bg-blue-50 text-blue-700 border border-blue-200"
                        : "text-gray-600 hover:bg-gray-100"
                    )}
                  >
                    {getAgentIcon(agent.id, agent.config.CONFIG_INFO.config_type)}
                    <div className="flex-1 text-left min-w-0">
                      <div className="font-medium truncate">{displayName}</div>
                      {agent.config.CONFIG_INFO.description && (
                        <div className="text-xs text-gray-500 line-clamp-2 leading-tight mt-0.5">
                          {agent.config.CONFIG_INFO.description}
                        </div>
                      )}
                    </div>
                  </button>
                );
              })}
          </div>
        </div>

        <div className="p-4 border-t border-gray-200">
          <div className="text-xs text-gray-500">
            Configuration changes are saved automatically
          </div>
        </div>
      </div>
    </div>
  );
}