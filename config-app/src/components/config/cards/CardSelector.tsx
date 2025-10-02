"use client";

import React from 'react';
import { PromptCard, LLMCard, MCPConfigCard, AgentIdentityCard, CredentialsCard } from './index';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Info, AlertTriangle, Eye, EyeOff, Copy, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { extractCurrentValue, isFieldOverridden } from '@/lib/config-utils';

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

interface CardSelectorProps {
  section: ConfigSection;
  values: Record<string, any>;
  onValueChange: (sectionKey: string, fieldKey: string, value: any, envVar?: string) => void;
}

// Generic card component for fields that don't match specialized patterns
function GenericCard({ section, values, onValueChange }: {
  section: ConfigSection;
  values: Record<string, any>;
  onValueChange: (fieldKey: string, value: any, envVar?: string) => void;
}) {
  const [showPasswords, setShowPasswords] = React.useState<Record<string, boolean>>({});
  const [copiedFields, setCopiedFields] = React.useState<Record<string, boolean>>({});

  const togglePasswordVisibility = (fieldKey: string) => {
    setShowPasswords(prev => ({ ...prev, [fieldKey]: !prev[fieldKey] }));
  };

  const copyToClipboard = async (fieldId: string, value: string) => {
    try {
      await navigator.clipboard.writeText(value);
      setCopiedFields(prev => ({ ...prev, [fieldId]: true }));
      setTimeout(() => {
        setCopiedFields(prev => ({ ...prev, [fieldId]: false }));
      }, 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  const getCurrentValue = (field: ConfigField) => {
    // First check the nested section structure (e.g., values.ai_models.openai_api_key)
    let rawValue = values[section.key]?.[field.key];
    if (rawValue !== undefined) {
      // Extract current value (handles both old and new FastAPI format)
      return extractCurrentValue(rawValue);
    }
    // Fallback to flat envVar structure (e.g., values.OPENAI_API_KEY)
    if (field.envVar && values[field.envVar] !== undefined) {
      return extractCurrentValue(values[field.envVar]);
    }
    return field.default || '';
  };

  const isOverridden = (field: ConfigField): boolean => {
    const rawValue = values[section.key]?.[field.key];
    if (rawValue !== undefined) {
      return isFieldOverridden(rawValue);
    }
    if (field.envVar && values[field.envVar] !== undefined) {
      return isFieldOverridden(values[field.envVar]);
    }
    return false;
  };

  const handleFieldChange = (field: ConfigField, value: any) => {
    let processedValue = value;
    switch (field.type) {
      case 'number':
        processedValue = typeof value === 'string' ? parseFloat(value) || 0 : value;
        break;
      case 'boolean':
        processedValue = typeof value === 'string' ? value === 'true' : value;
        break;
      default:
        processedValue = String(value);
    }
    onValueChange(field.key, processedValue, field.envVar);
  };

  return (
    <Card className={section.card_style === 'orange' ? 'bg-orange-50 border-orange-200' : ''}>
      <CardHeader>
        <CardTitle className="text-lg">{section.label}</CardTitle>
        {section.description && (
          <CardDescription>{section.description}</CardDescription>
        )}
      </CardHeader>
      <CardContent className="space-y-4">
        {section.fields.map((field) => {
          const fieldId = `${section.key}-${field.key}`;
          const currentValue = getCurrentValue(field);

          return (
            <div key={field.key} className="space-y-2">
              <Label htmlFor={fieldId} className="flex items-center gap-2">
                {field.label}
                {field.required && <span className="text-red-500">*</span>}
              </Label>

              {field.type === 'password' ? (
                <div className="relative">
                  <Input
                    id={fieldId}
                    type={showPasswords[fieldId] ? "text" : "password"}
                    value={currentValue}
                    onChange={(e) => !field.readonly && handleFieldChange(field, e.target.value)}
                    placeholder={field.placeholder}
                    className={`${field.showCopyButton ? 'pr-20' : 'pr-10'} ${field.readonly ? 'bg-gray-50 text-gray-600' : ''}`}
                    readOnly={field.readonly}
                  />
                  <div className="absolute right-2 top-1/2 -translate-y-1/2 flex gap-1">
                    {field.showCopyButton && (
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0"
                        onClick={() => copyToClipboard(fieldId, currentValue)}
                      >
                        {copiedFields[fieldId] ? <Check className="h-3 w-3 text-green-600" /> : <Copy className="h-3 w-3" />}
                      </Button>
                    )}
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="h-6 w-6 p-0"
                      onClick={() => togglePasswordVisibility(fieldId)}
                    >
                      {showPasswords[fieldId] ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
                    </Button>
                  </div>
                </div>
              ) : field.type === 'textarea' ? (
                <Textarea
                  id={fieldId}
                  value={currentValue}
                  onChange={(e) => !field.readonly && handleFieldChange(field, e.target.value)}
                  placeholder={field.placeholder}
                  rows={field.rows || 8}
                  className={field.readonly ? 'bg-gray-50 text-gray-600' : ''}
                  readOnly={field.readonly}
                />
              ) : field.type === 'boolean' ? (
                <div className="flex items-center space-x-2">
                  <Switch
                    id={fieldId}
                    checked={currentValue === true || currentValue === 'true'}
                    onCheckedChange={(checked) => !field.readonly && handleFieldChange(field, checked)}
                    disabled={field.readonly}
                  />
                </div>
              ) : field.type === 'select' ? (
                <Select
                  value={currentValue}
                  onValueChange={(value) => !field.readonly && handleFieldChange(field, value)}
                  disabled={field.readonly}
                >
                  <SelectTrigger>
                    <SelectValue placeholder={field.placeholder} />
                  </SelectTrigger>
                  <SelectContent>
                    {field.options?.map((option) => (
                      <SelectItem key={option} value={option}>{option}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : field.type === 'number' ? (
                <Input
                  id={fieldId}
                  type="number"
                  value={currentValue}
                  onChange={(e) => !field.readonly && handleFieldChange(field, parseFloat(e.target.value) || 0)}
                  min={field.validation?.min}
                  max={field.validation?.max}
                  step={field.validation?.step}
                  className={field.readonly ? 'bg-gray-50 text-gray-600' : ''}
                  readOnly={field.readonly}
                />
              ) : (
                <div className="relative">
                  <Input
                    id={fieldId}
                    type="text"
                    value={currentValue}
                    onChange={(e) => !field.readonly && handleFieldChange(field, e.target.value)}
                    placeholder={field.placeholder}
                    className={`${field.showCopyButton ? 'pr-10' : ''} ${field.readonly ? 'bg-gray-50 text-gray-600' : ''}`}
                    readOnly={field.readonly}
                  />
                  {field.showCopyButton && (
                    <div className="absolute right-2 top-1/2 -translate-y-1/2 flex gap-1">
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0"
                        onClick={() => copyToClipboard(fieldId, currentValue)}
                      >
                        {copiedFields[fieldId] ? <Check className="h-3 w-3 text-green-600" /> : <Copy className="h-3 w-3" />}
                      </Button>
                    </div>
                  )}
                </div>
              )}

              {field.description && (
                <div className="flex items-start gap-2 text-sm text-gray-600">
                  <Info className="h-4 w-4 mt-0.5 flex-shrink-0" />
                  <span>{field.description}</span>
                </div>
              )}

              {field.note && (
                <Alert>
                  <Info className="h-4 w-4" />
                  <AlertDescription>{field.note}</AlertDescription>
                </Alert>
              )}

              {field.warning && (
                <Alert variant="destructive">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>{field.warning}</AlertDescription>
                </Alert>
              )}
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}

export function CardSelector({ section, values, onValueChange }: CardSelectorProps) {
  // Create a wrapper function that matches the expected signature for specialized cards
  const handleValueChange = (fieldKey: string, value: any, envVar?: string) => {
    onValueChange(section.key, fieldKey, value, envVar);
  };

  // Determine card type based on section characteristics (7-category system)
  const getCardType = (section: ConfigSection): 'identity' | 'user' | 'llm' | 'prompt' | 'credentials' | 'integration' | 'generic' => {
    const sectionKey = section.key.toLowerCase();
    const sectionLabel = section.label.toLowerCase();

    // SPECIAL CASE: Interface UIs should always use generic (white) cards
    // Check if this is from interface_uis_config.py by checking for characteristic patterns
    if (sectionKey.includes('agent_chat_ui') ||
        sectionKey.includes('agent_inbox_') ||
        sectionLabel.includes('agent chat ui') ||
        sectionLabel.includes('agent inbox')) {
      return 'generic';
    }

    // 1. Agent Identity (grey) - agent info & status - HIGHEST PRIORITY
    if (sectionKey === 'agent_identity' ||
        sectionKey.includes('agent_identity') ||
        (sectionKey.includes('identity') && !sectionKey.includes('user')) ||
        section.fields.some(field => field.key.includes('agent_name') || field.key.includes('agent_display_name') || field.key.includes('agent_description'))) {
      return 'identity';
    }

    // 2. User Identity & Preferences (grey) - user info & preferences
    if (sectionKey.includes('user_identity') ||
        sectionKey.includes('user_preferences') ||
        sectionLabel.includes('user identity') ||
        sectionLabel.includes('user preferences')) {
      return 'user';
    }

    // 3. Credentials (yellow) - API keys & sensitive data - MOVED UP BEFORE LLM CHECK
    if (sectionKey === 'ai_models' ||
        sectionKey.includes('api') ||
        sectionKey.includes('credentials') ||
        sectionKey.includes('ai_models') ||
        sectionKey.includes('langgraph_system') ||
        sectionKey.includes('google_workspace') ||
        sectionLabel.includes('api keys') ||
        sectionLabel.includes('keys') ||
        sectionLabel.includes('auth') ||
        section.fields.some(field => field.key.includes('api_key') || field.key.includes('token') || field.key.includes('secret') || field.type === 'password')) {
      return 'credentials';
    }

    // 4. LLM Models (blue) - AI model configurations (NOT for API keys)
    if (sectionKey.includes('llm') ||
        (sectionLabel.includes('model') && !sectionLabel.includes('api')) ||
        sectionLabel.includes('language') ||
        section.fields.some(field => field.key.includes('model') || field.key.includes('temperature'))) {
      return 'llm';
    }

    // 5. Prompts (orange) - prompt configurations
    if (section.card_style === 'orange' ||
        sectionKey.includes('prompt') ||
        sectionKey.includes('triage') ||
        sectionKey.includes('email_preferences') ||
        sectionLabel.includes('prompt') ||
        section.fields.every(field => field.type === 'textarea')) {
      return 'prompt';
    }

    // 6. Integration (green) - MCP/external integrations
    if (sectionKey.includes('mcp') ||
        sectionKey.includes('integration') ||
        sectionLabel.includes('mcp') ||
        sectionLabel.includes('integration') ||
        sectionLabel.includes('server') ||
        section.fields.some(field => field.key.includes('mcp') || field.envVar)) {
      return 'integration';
    }

    // 7. Generic/Specialized (white) - everything else
    return 'generic';
  };

  // Determine LLM context based on section key
  const getLLMContext = (sectionKey: string): 'triage' | 'draft' | 'rewrite' | 'scheduling' | 'reflection' | 'general' => {
    if (sectionKey.includes('triage')) return 'triage';
    if (sectionKey.includes('draft')) return 'draft';
    if (sectionKey.includes('rewrite')) return 'rewrite';
    if (sectionKey.includes('scheduling')) return 'scheduling';
    if (sectionKey.includes('reflection')) return 'reflection';
    return 'general';
  };

  const cardType = getCardType(section);

  switch (cardType) {
    case 'identity':
      return (
        <AgentIdentityCard
          title={section.label}
          description={section.description}
          fields={section.fields as any[]}
          values={values}
          onValueChange={handleValueChange}
          sectionKey={section.key}
        />
      );

    case 'user':
      return (
        <AgentIdentityCard
          title={section.label}
          description={section.description}
          fields={section.fields as any[]}
          values={values}
          onValueChange={handleValueChange}
          sectionKey={section.key}
        />
      );

    case 'llm':
      return (
        <LLMCard
          title={section.label}
          description={section.description}
          fields={section.fields as any[]}
          values={values}
          onValueChange={handleValueChange}
          sectionKey={section.key}
          context={getLLMContext(section.key)}
        />
      );

    case 'prompt':
      return (
        <PromptCard
          title={section.label}
          description={section.description}
          fields={section.fields as any[]}
          values={values}
          onValueChange={handleValueChange}
          sectionKey={section.key}
        />
      );

    case 'credentials':
      return (
        <CredentialsCard
          title={section.label}
          description={section.description}
          fields={section.fields as any[]}
          values={values}
          onValueChange={handleValueChange}
          sectionKey={section.key}
        />
      );

    case 'integration':
      return (
        <MCPConfigCard
          title={section.label}
          description={section.description}
          fields={section.fields as any[]}
          values={values}
          onValueChange={handleValueChange}
          sectionKey={section.key}
        />
      );

    default:
      // Fall back to the generic card implementation
      return <GenericCard section={section} values={values} onValueChange={handleValueChange} />;
  }
}