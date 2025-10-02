"use client";

import React from 'react';
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Info, AlertTriangle, Link, Server, Eye, EyeOff, Copy, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { extractCurrentValue } from '@/lib/config-utils';

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
}

interface MCPConfigCardProps {
  title: string;
  description: string;
  fields: MCPField[];
  values: Record<string, any>;
  onValueChange: (fieldKey: string, value: any, envVar?: string) => void;
  sectionKey: string;
}

export function MCPConfigCard({
  title,
  description,
  fields,
  values,
  onValueChange,
  sectionKey
}: MCPConfigCardProps) {
  const [showPasswords, setShowPasswords] = React.useState<Record<string, boolean>>({});
  const [copiedFields, setCopiedFields] = React.useState<Record<string, boolean>>({});

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

  const getCurrentValue = (field: MCPField) => {
    // Handle environment variable fields (flat structure from API)
    if (field.envVar && values[field.envVar] !== undefined) {
      return extractCurrentValue(values[field.envVar]);
    }

    // Handle nested structure fields
    const rawValue = values[sectionKey]?.[field.key];
    if (rawValue !== undefined) {
      return extractCurrentValue(rawValue);
    }

    return field.default || '';
  };

  const handleFieldChange = (field: MCPField, value: string) => {
    onValueChange(field.key, value, field.envVar);
  };

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
        <CardTitle className="text-lg flex items-center gap-2">
          <Link className="h-5 w-5 text-green-600" />
          {title}
        </CardTitle>
        {description && (
          <CardDescription className="text-green-700">
            {description}
          </CardDescription>
        )}
        <Alert className="border-green-300 bg-green-100/50">
          <Info className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">
            <strong>MCP Integration:</strong> Configure external service connections through Model Context Protocol servers.
          </AlertDescription>
        </Alert>
      </CardHeader>
      <CardContent className="space-y-6">
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
                    type={field.type === 'password' && !showPasswords[fieldId] ? "password" : "text"}
                    value={currentValue}
                    onChange={(e) => !field.readonly && handleFieldChange(field, e.target.value)}
                    placeholder={field.placeholder}
                    className={`${field.showCopyButton || field.type === 'password' ? 'pr-20' : 'pr-10'} ${
                      field.readonly
                        ? 'bg-green-100 text-green-700 border-green-200'
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

              {field.note && (
                <Alert className="border-green-300 bg-green-100/30">
                  <Info className="h-4 w-4 text-green-600" />
                  <AlertDescription className="text-green-800">{field.note}</AlertDescription>
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