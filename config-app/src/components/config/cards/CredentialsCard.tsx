"use client";

import React from 'react';
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Info, AlertTriangle, Key, Eye, EyeOff, Copy, Check, Shield, Save, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { extractCurrentValue, maskCredential } from '@/lib/config-utils';

interface CredentialField {
  key: string;
  label: string;
  type: 'text' | 'password';
  description?: string;
  placeholder?: string;
  required?: boolean;
  readonly?: boolean;
  note?: string;
  warning?: string;
  default?: any;
  showCopyButton?: boolean;
  envVar?: string;
}

interface CredentialsCardProps {
  title: string;
  description: string;
  fields: CredentialField[];
  values: Record<string, any>;
  onValueChange: (fieldKey: string, value: any, envVar?: string) => void;
  sectionKey: string;
  agentId?: string;
  onReset?: (sectionKey: string, fieldKey: string) => Promise<void>;
  onSave: () => Promise<void>;
  isDirty: boolean;
  isSaving: boolean;
}

export function CredentialsCard({
  title,
  description,
  fields,
  values,
  onValueChange,
  sectionKey,
  onSave,
  isDirty,
  isSaving
}: CredentialsCardProps) {
  const [showPasswords, setShowPasswords] = React.useState<Record<string, boolean>>({});
  const [copiedFields, setCopiedFields] = React.useState<Record<string, boolean>>({});
  const [focusedFields, setFocusedFields] = React.useState<Record<string, boolean>>({});

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

  const getCurrentValue = (field: CredentialField) => {
    const rawValue = values[sectionKey]?.[field.key];
    if (rawValue !== undefined && rawValue !== null) {
      const extracted = extractCurrentValue(rawValue);
      // Ensure we never return null - always return string
      return extracted ?? '';
    }
    return field.default || '';
  };

  const handleFieldChange = (field: CredentialField, value: string) => {
    onValueChange(field.key, value, field.envVar);
  };

  const getSecurityIcon = (field: CredentialField) => {
    if (field.type === 'password' || field.key.toLowerCase().includes('secret') || field.key.toLowerCase().includes('token')) {
      return <Shield className="h-4 w-4 text-yellow-600" />;
    }
    return <Key className="h-4 w-4 text-yellow-600" />;
  };

  const getDisplayValue = (field: CredentialField, fieldId: string) => {
    const currentValue = getCurrentValue(field);

    // Ensure we never return null - convert to empty string
    const safeValue = currentValue ?? '';

    // Show real value if:
    // 1. Field is focused (user is editing)
    // 2. Password visibility is toggled on
    // 3. Field is not password type
    // 4. Value is empty
    if (focusedFields[fieldId] || showPasswords[fieldId] || field.type !== 'password' || !safeValue) {
      return safeValue;
    }

    // Otherwise, show masked value for password fields
    return maskCredential(safeValue);
  };

  return (
    <Card className="bg-yellow-50 border-yellow-200">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg flex items-center gap-2">
              <Key className="h-5 w-5 text-yellow-600" />
              {title}
            </CardTitle>
            {description && (
              <CardDescription className="text-yellow-700">
                {description}
              </CardDescription>
            )}
          </div>
          <Button
            onClick={onSave}
            disabled={!isDirty || isSaving}
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
        {fields.map((field) => {
          const fieldId = `${sectionKey}-${field.key}`;
          const currentValue = getCurrentValue(field);
          const displayValue = getDisplayValue(field, fieldId);

          return (
            <div key={field.key} className="space-y-3">
              <div className="space-y-2">
                <Label htmlFor={fieldId} className="flex items-center gap-2 text-yellow-900 font-medium">
                  {getSecurityIcon(field)}
                  {field.label}
                  {field.required && <span className="text-red-500">*</span>}
                </Label>

                <div className="relative">
                  <Input
                    id={fieldId}
                    type={field.type === 'password' && !showPasswords[fieldId] && !focusedFields[fieldId] ? "password" : "text"}
                    value={displayValue}
                    onChange={(e) => !field.readonly && handleFieldChange(field, e.target.value)}
                    onFocus={() => setFocusedFields(prev => ({ ...prev, [fieldId]: true }))}
                    onBlur={() => setFocusedFields(prev => ({ ...prev, [fieldId]: false }))}
                    placeholder={field.placeholder}
                    className={`${field.showCopyButton || field.type === 'password' ? 'pr-20' : 'pr-10'} ${
                      field.readonly
                        ? 'bg-yellow-100 text-yellow-700 border-yellow-200'
                        : 'bg-white border-yellow-300 focus:border-yellow-400 focus:ring-yellow-400'
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
                          <Copy className="h-3 w-3 text-yellow-600" />
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
                          <EyeOff className="h-3 w-3 text-yellow-600" />
                        ) : (
                          <Eye className="h-3 w-3 text-yellow-600" />
                        )}
                      </Button>
                    )}
                  </div>
                </div>
              </div>

              {field.description && (
                <div className="flex items-start gap-2 text-sm text-yellow-700 bg-yellow-100/50 p-3 rounded-md">
                  <Info className="h-4 w-4 mt-0.5 flex-shrink-0" />
                  <span>{field.description}</span>
                </div>
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