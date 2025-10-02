"use client";

import React from 'react';
import { CardSelector } from './cards/CardSelector';

interface ConfigField {
  key: string;
  label: string;
  type: string;
  envVar?: string;
  default?: any;
  description?: string;
  placeholder?: string;
  required?: boolean;
  readonly?: boolean;
  showCopyButton?: boolean;
  options?: string[];
  validation?: any;
  note?: string;
  warning?: string;
  rows?: number;
}

interface ConfigSection {
  key: string;
  label: string;
  description: string;
  fields: ConfigField[];
  card_style?: string;
}

interface EnhancedConfigFormProps {
  sections: ConfigSection[];
  values: Record<string, any>;
  onValueChange: (sectionKey: string, fieldKey: string, value: any, envVar?: string) => void;
  agentId?: string;
  onReset?: (sectionKey: string, fieldKey: string) => Promise<void>;
  onSaveSection: (sectionKey: string) => Promise<void>;
  dirtySections: Set<string>;
  savingSection: string | null;
}

export function EnhancedConfigForm({ sections, values, onValueChange, agentId, onReset, onSaveSection, dirtySections, savingSection }: EnhancedConfigFormProps) {
  // Define card order for consistent organization across all agents
  const getCardOrder = (sectionKey: string): number => {
    const key = sectionKey.toLowerCase();

    // 1. Agent Identity (if exists)
    if (key.includes('agent_identity') ||
        (key.includes('identity') && !key.includes('user'))) return 1;

    // 2. User Identity & Preferences
    if (key.includes('user_identity') || key.includes('user_preferences')) return 2;

    // 3. LLM sections (grouped)
    if (key.includes('llm')) return 3;

    // 4. Prompt sections (grouped)
    if (key.includes('prompt') || key.includes('triage') || key.includes('email_preferences')) return 4;

    // 5. Credentials sections (grouped)
    if (key.includes('api') || key.includes('credentials') || key.includes('ai_models') ||
        key.includes('langgraph_system') || key.includes('google_workspace')) return 5;

    // 6. Integration sections
    if (key.includes('mcp') || key.includes('integration')) return 6;

    // 7. Specialized/other sections
    return 7;
  };

  // Get category name and color for each order
  const getCategoryInfo = (order: number): { name: string; color: string } => {
    switch (order) {
      case 1: return { name: "Agent Identity", color: "text-gray-400" };
      case 2: return { name: "User Identity & Preferences", color: "text-gray-400" };
      case 3: return { name: "AI Models", color: "text-blue-400" };
      case 4: return { name: "Prompts & Instructions", color: "text-orange-400" };
      case 5: return { name: "Credentials & API Keys", color: "text-yellow-500" };
      case 6: return { name: "Integrations & Services", color: "text-green-400" };
      case 7: return { name: "Specialized Configuration", color: "text-gray-400" };
      default: return { name: "Other", color: "text-gray-400" };
    }
  };

  // Sort sections according to the defined order
  const sortedSections = [...sections].sort((a, b) => {
    const orderA = getCardOrder(a.key);
    const orderB = getCardOrder(b.key);

    // If same order, maintain original relative position
    if (orderA === orderB) {
      return sections.indexOf(a) - sections.indexOf(b);
    }

    return orderA - orderB;
  });

  // Group sections by category for headers
  const groupedSections: { category: { name: string; color: string }; sections: ConfigSection[] }[] = [];
  let currentCategory: number | null = null;

  sortedSections.forEach((section) => {
    const order = getCardOrder(section.key);
    if (order !== currentCategory) {
      currentCategory = order;
      groupedSections.push({
        category: getCategoryInfo(order),
        sections: [section]
      });
    } else {
      groupedSections[groupedSections.length - 1].sections.push(section);
    }
  });

  return (
    <div className="space-y-8">
      {groupedSections.map((group, groupIndex) => (
        <div key={`group-${groupIndex}`} className="space-y-4">
          {/* Category Header */}
          <div className="flex items-center">
            <h3 className={`text-sm font-medium ${group.category.color} uppercase tracking-wide`}>
              {group.category.name}
            </h3>
            <div className={`flex-1 h-px bg-current opacity-20 ml-4`}></div>
          </div>

          {/* Category Cards */}
          <div className="space-y-4">
            {group.sections.map((section) => (
              <CardSelector
                key={section.key}
                section={section}
                values={values}
                onValueChange={onValueChange}
                agentId={agentId}
                onReset={onReset}
                onSaveSection={onSaveSection}
                isDirty={dirtySections.has(section.key)}
                isSaving={savingSection === section.key}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}