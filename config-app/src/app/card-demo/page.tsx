"use client";

import React, { useState } from 'react';
import { EnhancedConfigForm } from '@/components/config/EnhancedConfigForm';

// Sample configurations to test different card types
const SAMPLE_CONFIGS = [
  {
    key: 'agent_identity',
    label: 'Agent Identity',
    description: 'Agent identification and status',
    fields: [
      {
        key: 'agent_display_name',
        label: 'Display Name',
        type: 'text',
        default: 'Demo Agent',
        description: 'Human-readable agent name',
        required: true
      },
      {
        key: 'agent_description',
        label: 'Description',
        type: 'textarea',
        default: 'A demonstration agent for testing card components',
        description: 'Brief description of agent capabilities',
        required: true
      },
      {
        key: 'agent_status',
        label: 'Status',
        type: 'select',
        default: 'active',
        description: 'Enable or disable this agent',
        options: ['active', 'disabled'],
        required: true
      }
    ]
  },
  {
    key: 'llm_triage',
    label: 'Email Triage Model',
    description: 'AI model for categorizing incoming emails',
    fields: [
      {
        key: 'triage_model',
        label: 'Model',
        type: 'select',
        default: 'claude-3-5-haiku-20241022',
        description: 'Model for email categorization',
        options: [
          'claude-sonnet-4-20250514',
          'claude-3-5-haiku-20241022',
          'gpt-4o',
          'gpt-5'
        ],
        required: true
      },
      {
        key: 'triage_temperature',
        label: 'Temperature',
        type: 'number',
        default: 0.1,
        description: 'Model creativity level',
        validation: { min: 0.0, max: 1.0, step: 0.1 }
      }
    ]
  },
  {
    key: 'mcp_integration',
    label: 'MCP Server Configuration',
    description: 'API connection settings for external services',
    fields: [
      {
        key: 'mcp_server_url',
        label: 'MCP Server URL',
        type: 'text',
        description: 'The MCP server URL',
        placeholder: 'https://mcp.pipedream.net/xxx/google_gmail',
        required: false
      },
      {
        key: 'mcp_env_var',
        label: 'Environment Variable',
        type: 'text',
        readonly: true,
        default: 'DEMO_MCP_SERVER',
        description: 'Environment variable name (read-only)'
      }
    ]
  },
  {
    key: 'triage_prompts',
    label: 'Triage Prompts',
    description: 'AI-powered email classification rules',
    card_style: 'orange',
    fields: [
      {
        key: 'triage_no',
        label: 'Ignore Rules',
        type: 'textarea',
        description: 'Define criteria for emails to ignore',
        placeholder: '- Automated emails from services that are spam\n- Cold outreach from vendors\n- Newsletter subscriptions',
        rows: 8,
        required: false
      },
      {
        key: 'triage_email',
        label: 'Action Required Rules',
        type: 'textarea',
        description: 'Define criteria for emails requiring response',
        placeholder: '- Direct questions from clients\n- Meeting requests requiring response\n- Legal matters',
        rows: 8,
        required: false
      }
    ]
  }
];

export default function CardDemoPage() {
  const [values, setValues] = useState<Record<string, any>>({
    agent_identity: {
      agent_display_name: 'Demo Agent',
      agent_description: 'A demonstration agent for testing card components',
      agent_status: 'active'
    },
    llm_triage: {
      triage_model: 'claude-3-5-haiku-20241022',
      triage_temperature: 0.1
    },
    mcp_integration: {
      mcp_server_url: 'https://mcp.pipedream.net/demo/service',
      mcp_env_var: 'DEMO_MCP_SERVER'
    },
    triage_prompts: {
      triage_no: '- Automated emails from services that are spam\n- Cold outreach from vendors',
      triage_email: '- Direct questions from clients\n- Meeting requests requiring response'
    }
  });

  const [dirtySections, setDirtySections] = useState<Set<string>>(new Set());
  const [savingSection, setSavingSection] = useState<string | null>(null);

  const handleValueChange = (sectionKey: string, fieldKey: string, value: any, envVar?: string) => {
    console.log('Value changed:', { sectionKey, fieldKey, value, envVar });

    setValues(prev => ({
      ...prev,
      [sectionKey]: {
        ...prev[sectionKey],
        [fieldKey]: value
      }
    }));

    // Mark section as dirty
    setDirtySections(prev => new Set(prev).add(sectionKey));
  };

  const handleSaveSection = async (sectionKey: string) => {
    setSavingSection(sectionKey);
    try {
      // Simulate save operation
      await new Promise(resolve => setTimeout(resolve, 1000));
      console.log('Saved section:', sectionKey, values[sectionKey]);

      // Clear dirty flag
      setDirtySections(prev => {
        const next = new Set(prev);
        next.delete(sectionKey);
        return next;
      });
    } finally {
      setSavingSection(null);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Configuration Card Components Demo
          </h1>
          <p className="text-gray-600">
            Showcasing specialized card components: AgentIdentityCard, LLMCard, MCPConfigCard, and PromptCard
          </p>
        </div>

        {/* TODO(human): Add a section here that demonstrates how the CardSelector automatically
            detects and renders the appropriate card type for each configuration section.

            You could add:
            1. A visual indicator showing which card type was selected for each section
            2. A toggle to switch between the new EnhancedConfigForm and the original ConfigForm
            3. Debug information showing the detection logic results
            4. Additional test cases with edge cases that might confuse the detection logic

            The goal is to prove that our intelligent card selection is working correctly
            and makes the configuration interface more intuitive and specialized. */}

        <EnhancedConfigForm
          sections={SAMPLE_CONFIGS}
          values={values}
          onValueChange={handleValueChange}
          onSaveSection={handleSaveSection}
          dirtySections={dirtySections}
          savingSection={savingSection}
        />

        <div className="mt-8 p-4 bg-white rounded-lg border">
          <h3 className="text-lg font-semibold mb-2">Current Values (Debug)</h3>
          <pre className="text-sm bg-gray-100 p-3 rounded overflow-auto">
            {JSON.stringify(values, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  );
}