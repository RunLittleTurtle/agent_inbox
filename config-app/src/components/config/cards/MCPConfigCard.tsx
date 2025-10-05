"use client";

import React from 'react';
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Info, AlertTriangle, Link, Server, Eye, EyeOff, Copy, Check, Save, RefreshCw, AlertCircle, CheckCircle, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { extractCurrentValue } from '@/lib/config-utils';
import { validateCredential, inferCredentialType, type ValidationResult, type CredentialType } from '@/lib/credential-validator';
import { useToast } from "@/hooks/use-toast";

interface MCPField {
  key: string;
  label: string;
  type: 'text' | 'password';
  description?: string;
  placeholder?: string;
  required?: boolean;
  readonly?: boolean;
  note?: string;
  warning?: string;
  envVar?: string;
  showCopyButton?: boolean;
  default?: any;
  validationType?: CredentialType; // Optional: specify validation type, otherwise auto-inferred
}

interface MCPConfigCardProps {
  title: string;
  description: string;
  fields: MCPField[];
  values: Record<string, any>;
  onValueChange: (fieldKey: string, value: any, envVar?: string) => void;
  sectionKey: string;
  onSave: () => Promise<void>;
  isDirty: boolean;
  isSaving: boolean;
  agentId?: string; // For OAuth flow
  isGlobal?: boolean; // True if this is global MCP (user_secrets), false for per-agent (agent_configs)
}

export function MCPConfigCard({
  title,
  description,
  fields,
  values,
  onValueChange,
  sectionKey,
  onSave,
  isDirty,
  isSaving,
  agentId,
  isGlobal = false
}: MCPConfigCardProps) {
  const { toast } = useToast();
  const [showPasswords, setShowPasswords] = React.useState<Record<string, boolean>>({});
  const [copiedFields, setCopiedFields] = React.useState<Record<string, boolean>>({});
  const [focusedFields, setFocusedFields] = React.useState<Record<string, boolean>>({});
  const [validationResults, setValidationResults] = React.useState<Record<string, ValidationResult>>({});
  const [oauthStatus, setOauthStatus] = React.useState<'connected' | 'disconnected' | 'loading'>('disconnected');
  const [connectedApps, setConnectedApps] = React.useState<string[]>([]);
  const [isConnecting, setIsConnecting] = React.useState(false);

  const togglePasswordVisibility = (fieldKey: string) => {
    setShowPasswords(prev => ({
      ...prev,
      [fieldKey]: !prev[fieldKey]
    }));
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

  // OAuth Connection Handler
  const handleConnectMCP = async () => {
    const mcpUrlField = fields.find(f => f.key === 'mcp_server_url');
    if (!mcpUrlField) {
      toast({ variant: "destructive", title: "Error", description: "MCP server URL field not found" });
      return;
    }

    const mcp_url = getCurrentValue(mcpUrlField);
    if (!mcp_url) {
      toast({ variant: "destructive", title: "Error", description: "Please enter MCP server URL first" });
      return;
    }

    // For per-agent OAuth, require agentId
    if (!isGlobal && !agentId) {
      toast({ variant: "destructive", title: "Error", description: "Agent ID not found" });
      return;
    }

    setIsConnecting(true);

    try {
      // 1. Initiate OAuth flow (global or per-agent)
      const endpoint = isGlobal ? '/api/mcp/oauth/initiate-global' : '/api/mcp/oauth/initiate';
      const requestBody = isGlobal
        ? { mcp_url }
        : { agent_id: agentId, mcp_url };

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'OAuth initiation failed');
      }

      const { authUrl } = await response.json();

      // 2. Open OAuth popup
      const popup = window.open(
        authUrl,
        'MCP OAuth',
        'width=600,height=700,left=100,top=100'
      );

      if (!popup) {
        toast({ variant: "destructive", title: "Popup Blocked", description: "Please allow popups for this site" });
        setIsConnecting(false);
        return;
      }

      // 3. Listen for completion
      const handleMessage = (event: MessageEvent) => {
        if (event.data.type === 'mcp_oauth_complete') {
          popup?.close();
          window.removeEventListener('message', handleMessage);
          setIsConnecting(false);
          setOauthStatus('connected');
          toast({ title: "Success", description: "Apps connected successfully!" });
          // Reload OAuth status
          loadOAuthStatus();
        } else if (event.data.type === 'mcp_oauth_error') {
          popup?.close();
          window.removeEventListener('message', handleMessage);
          setIsConnecting(false);
          toast({ variant: "destructive", title: "Connection Failed", description: event.data.error });
        }
      };

      window.addEventListener('message', handleMessage);

    } catch (error: any) {
      setIsConnecting(false);
      toast({ variant: "destructive", title: "Error", description: error.message });
    }
  };

  // Load OAuth connection status
  const loadOAuthStatus = async () => {
    try {
      if (isGlobal) {
        // Global OAuth: check values.mcp_universal (from user_secrets)
        const mcp_universal = values.mcp_universal;
        if (mcp_universal?.oauth_tokens?.access_token) {
          setOauthStatus('connected');
          setConnectedApps([mcp_universal.provider || 'MCP Server']);
        } else {
          setOauthStatus('disconnected');
        }
      } else {
        // Per-agent OAuth: check values[sectionKey].oauth_tokens (from agent_configs)
        if (!agentId) return;

        const mcpIntegration = values[sectionKey]?.oauth_tokens;
        if (mcpIntegration && mcpIntegration.access_token) {
          setOauthStatus('connected');
          setConnectedApps(['Rube MCP']);
        } else {
          setOauthStatus('disconnected');
        }
      }
    } catch (error) {
      console.error('Failed to load OAuth status:', error);
    }
  };

  // Load OAuth status on mount
  React.useEffect(() => {
    loadOAuthStatus();
  }, [values]);

  const getCurrentValue = (field: MCPField) => {
    // Handle environment variable fields (flat structure from API)
    if (field.envVar && values[field.envVar] !== undefined) {
      const extracted = extractCurrentValue(values[field.envVar]);
      return extracted ?? field.default ?? '';
    }

    // Handle nested structure fields
    const rawValue = values[sectionKey]?.[field.key];
    if (rawValue !== undefined) {
      const extracted = extractCurrentValue(rawValue);
      return extracted ?? field.default ?? '';
    }

    return field.default ?? '';
  };

  const handleFieldChange = (field: MCPField, value: string) => {
    onValueChange(field.key, value, field.envVar);
  };

  const handleFieldBlur = (field: MCPField, fieldId: string, value: string) => {
    // Only validate non-empty values
    if (value && !field.readonly) {
      const validationType = field.validationType || inferCredentialType(field.key);
      const result = validateCredential(value, validationType);

      setValidationResults(prev => ({
        ...prev,
        [fieldId]: result
      }));
    }

    // Clear focused state
    setFocusedFields(prev => ({ ...prev, [fieldId]: false }));
  };

  // Check if there are any validation errors
  const hasValidationErrors = Object.values(validationResults).some(result => !result.isValid);

  const getFieldIcon = (field: MCPField) => {
    if (field.key.toLowerCase().includes('url') || field.key.toLowerCase().includes('server')) {
      return <Server className="h-4 w-4 text-green-500" />;
    }
    if (field.key.toLowerCase().includes('env')) {
      return <Link className="h-4 w-4 text-green-500" />;
    }
    return <Server className="h-4 w-4 text-green-500" />;
  };

  return (
    <Card className="bg-green-50 border-green-200">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg flex items-center gap-2">
              <Link className="h-5 w-5 text-green-600" />
              {title}
            </CardTitle>
            {description && (
              <CardDescription className="text-green-700">
                {description}
              </CardDescription>
            )}
          </div>
          <Button
            onClick={onSave}
            disabled={!isDirty || isSaving || hasValidationErrors}
            size="sm"
            className="ml-4"
          >
            {isSaving ? (
              <>
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="w-4 h-4 mr-2" />
                Save
              </>
            )}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* OAuth Connection Status */}
        {sectionKey === 'mcp_integration' && agentId && (
          <div className="space-y-3 pb-4 border-b border-green-200">
            {oauthStatus === 'connected' ? (
              <Alert className="bg-green-100 border-green-300">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <AlertDescription className="text-green-800">
                  <div className="flex items-center justify-between">
                    <span>Connected to {connectedApps.join(', ')}</span>
                    <Button
                      onClick={handleConnectMCP}
                      variant="ghost"
                      size="sm"
                      disabled={isConnecting}
                      className="ml-4"
                    >
                      {isConnecting ? 'Connecting...' : 'Reconnect'}
                    </Button>
                  </div>
                </AlertDescription>
              </Alert>
            ) : (
              <Alert className="bg-amber-50 border-amber-300">
                <AlertTriangle className="h-4 w-4 text-amber-600" />
                <AlertDescription className="text-amber-800">
                  OAuth required. Click below to connect your apps.
                </AlertDescription>
              </Alert>
            )}

            <Button
              onClick={handleConnectMCP}
              disabled={isConnecting || !getCurrentValue(fields.find(f => f.key === 'mcp_server_url') || fields[0])}
              className="w-full bg-green-600 hover:bg-green-700"
            >
              {isConnecting ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  Connecting...
                </>
              ) : (
                <>
                  <Zap className="w-4 h-4 mr-2" />
                  {oauthStatus === 'connected' ? 'Reconnect Apps' : 'Connect Apps'}
                </>
              )}
            </Button>
          </div>
        )}

        {fields.map((field) => {
          const fieldId = `${sectionKey}-${field.key}`;
          const currentValue = getCurrentValue(field);

          return (
            <div key={field.key} className="space-y-3">
              <div className="space-y-2">
                <Label htmlFor={fieldId} className="flex items-center gap-2 text-green-900 font-medium">
                  {getFieldIcon(field)}
                  {field.label}
                  {field.required && <span className="text-red-500">*</span>}
                  {field.envVar && (
                    <span className="text-xs bg-green-200 text-green-700 px-2 py-0.5 rounded">
                      {field.envVar}
                    </span>
                  )}
                </Label>

                <div className="relative">
                  <Input
                    id={fieldId}
                    type={field.type === 'password' && !showPasswords[fieldId] && !focusedFields[fieldId] ? "password" : "text"}
                    value={currentValue}
                    onChange={(e) => !field.readonly && handleFieldChange(field, e.target.value)}
                    onFocus={() => setFocusedFields(prev => ({ ...prev, [fieldId]: true }))}
                    onBlur={() => handleFieldBlur(field, fieldId, getCurrentValue(field))}
                    placeholder={field.placeholder}
                    className={`${field.showCopyButton || field.type === 'password' ? 'pr-20' : 'pr-10'} ${
                      field.readonly
                        ? 'bg-green-100 text-green-700 border-green-200'
                        : validationResults[fieldId] && !validationResults[fieldId].isValid
                        ? 'bg-white border-red-400 focus:border-red-500 focus:ring-red-400'
                        : 'bg-white border-green-300 focus:border-green-400 focus:ring-green-400'
                    } transition-colors font-mono text-sm`}
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
                        title="Copy to clipboard"
                      >
                        {copiedFields[fieldId] ? (
                          <Check className="h-3 w-3 text-green-600" />
                        ) : (
                          <Copy className="h-3 w-3 text-green-600" />
                        )}
                      </Button>
                    )}

                    {field.type === 'password' && (
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0"
                        onClick={() => togglePasswordVisibility(fieldId)}
                      >
                        {showPasswords[fieldId] ? (
                          <EyeOff className="h-3 w-3 text-green-600" />
                        ) : (
                          <Eye className="h-3 w-3 text-green-600" />
                        )}
                      </Button>
                    )}
                  </div>
                </div>
              </div>

              {field.description && (
                <div className="flex items-start gap-2 text-sm text-green-700 bg-green-100/50 p-3 rounded-md">
                  <Info className="h-4 w-4 mt-0.5 flex-shrink-0" />
                  <span>{field.description}</span>
                </div>
              )}

              {/* Validation Error */}
              {validationResults[fieldId] && !validationResults[fieldId].isValid && (
                <Alert variant="destructive" className="bg-red-50 border-red-300">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription className="text-red-800">
                    {validationResults[fieldId].error}
                  </AlertDescription>
                </Alert>
              )}

              {/* Validation Warning */}
              {validationResults[fieldId] && validationResults[fieldId].isValid && validationResults[fieldId].warning && (
                <Alert className="bg-amber-50 border-amber-300">
                  <AlertTriangle className="h-4 w-4 text-amber-600" />
                  <AlertDescription className="text-amber-800">
                    {validationResults[fieldId].warning}
                  </AlertDescription>
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