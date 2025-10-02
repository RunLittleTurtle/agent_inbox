"use client";

import React from 'react';
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Info, AlertTriangle, User, Shield, CheckCircle, XCircle, Save, RefreshCw } from "lucide-react";
import { extractCurrentValue } from '@/lib/config-utils';

interface IdentityField {
  key: string;
  label: string;
  type: 'text' | 'textarea' | 'select';
  description?: string;
  placeholder?: string;
  required?: boolean;
  readonly?: boolean;
  options?: string[];
  rows?: number;
  note?: string;
  warning?: string;
  default?: any;
  envVar?: string;
}

interface AgentIdentityCardProps {
  title: string;
  description: string;
  fields: IdentityField[];
  values: Record<string, any>;
  onValueChange: (fieldKey: string, value: any, envVar?: string) => void;
  sectionKey: string;
  onSave: () => Promise<void>;
  isDirty: boolean;
  isSaving: boolean;
}

export function AgentIdentityCard({
  title,
  description,
  fields,
  values,
  onValueChange,
  sectionKey,
  onSave,
  isDirty,
  isSaving
}: AgentIdentityCardProps) {
  const getCurrentValue = (field: IdentityField) => {
    const rawValue = values[sectionKey]?.[field.key];
    if (rawValue !== undefined) {
      const extracted = extractCurrentValue(rawValue);
      // Ensure we never return null for text inputs/textareas
      return extracted ?? field.default ?? '';
    }
    return field.default ?? '';
  };

  const handleFieldChange = (field: IdentityField, value: any) => {
    onValueChange(field.key, value, field.envVar);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'disabled':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Shield className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'text-green-700 bg-green-50 border-green-200';
      case 'disabled':
        return 'text-red-700 bg-red-50 border-red-200';
      default:
        return 'text-gray-700 bg-gray-50 border-gray-200';
    }
  };

  // Check if this is a status field to determine card styling
  const statusField = fields.find(f => f.key.includes('status'));
  const currentStatus = statusField ? getCurrentValue(statusField) : null;

  return (
    <Card className="bg-gray-50 border-gray-200 transition-colors">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg flex items-center gap-2">
              <User className="h-5 w-5 text-gray-600" />
              {title}
              {currentStatus && (
                <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(currentStatus)}`}>
                  {getStatusIcon(currentStatus)}
                  {currentStatus}
                </div>
              )}
            </CardTitle>
            {description && (
              <CardDescription className="text-gray-700">
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

          return (
            <div key={field.key} className="space-y-3">
              <div className="space-y-2">
                <Label htmlFor={fieldId} className="flex items-center gap-2 text-gray-900 font-medium">
                  {field.label}
                  {field.required && <span className="text-red-500">*</span>}
                </Label>

                {field.type === 'textarea' ? (
                  <Textarea
                    id={fieldId}
                    value={currentValue}
                    onChange={(e) => !field.readonly && handleFieldChange(field, e.target.value)}
                    placeholder={field.placeholder}
                    rows={field.rows || 3}
                    className={`${
                      field.readonly
                        ? 'bg-gray-100 text-gray-600 border-gray-200'
                        : 'bg-white border-gray-300 focus:border-gray-400 focus:ring-gray-400'
                    } transition-colors`}
                    readOnly={field.readonly}
                  />
                ) : field.type === 'select' ? (
                  <Select
                    value={currentValue}
                    onValueChange={(value) => !field.readonly && handleFieldChange(field, value)}
                    disabled={field.readonly}
                  >
                    <SelectTrigger className="bg-white border-gray-300 focus:border-gray-400 focus:ring-gray-400">
                      <SelectValue placeholder={field.placeholder} />
                    </SelectTrigger>
                    <SelectContent>
                      {field.options?.map((option) => (
                        <SelectItem key={option} value={option}>
                          <div className="flex items-center gap-2">
                            {field.key.includes('status') && getStatusIcon(option)}
                            <span className="capitalize">{option}</span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                ) : (
                  <Input
                    id={fieldId}
                    type="text"
                    value={currentValue}
                    onChange={(e) => !field.readonly && handleFieldChange(field, e.target.value)}
                    placeholder={field.placeholder}
                    className={`${
                      field.readonly
                        ? 'bg-gray-100 text-gray-600 border-gray-200'
                        : 'bg-white border-gray-300 focus:border-gray-400 focus:ring-gray-400'
                    } transition-colors`}
                    readOnly={field.readonly}
                  />
                )}
              </div>

              {field.description && (
                <div className="flex items-start gap-2 text-sm text-gray-700 bg-gray-100/50 p-3 rounded-md">
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