"use client";

import React, { useState } from 'react';
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Info, AlertTriangle, Maximize2, RotateCcw, Save, RefreshCw } from "lucide-react";
import { extractCurrentValue, isFieldOverridden } from '@/lib/config-utils';
import { useToast } from "@/hooks/use-toast";

interface PromptField {
  key: string;
  label: string;
  type: 'textarea';
  description?: string;
  placeholder?: string;
  required?: boolean;
  readonly?: boolean;
  rows?: number;
  note?: string;
  warning?: string;
  default?: any;
  envVar?: string;
}

interface PromptCardProps {
  title: string;
  description: string;
  fields: PromptField[];
  values: Record<string, any>;
  onValueChange: (fieldKey: string, value: any, envVar?: string) => void;
  sectionKey: string;
  agentId?: string;
  onReset?: (sectionKey: string, fieldKey: string) => Promise<void>;
  onSave: () => Promise<void>;
  isDirty: boolean;
  isSaving: boolean;
}

export function PromptCard({
  title,
  description,
  fields,
  values,
  onValueChange,
  sectionKey,
  agentId,
  onReset,
  onSave,
  isDirty,
  isSaving
}: PromptCardProps) {
  const { toast } = useToast();

  const getCurrentValue = (field: PromptField) => {
    const rawValue = values[sectionKey]?.[field.key];
    if (rawValue !== undefined) {
      const extracted = extractCurrentValue(rawValue);
      return extracted ?? field.default ?? '';
    }
    return field.default ?? '';
  };

  const isOverridden = (field: PromptField): boolean => {
    const rawValue = values[sectionKey]?.[field.key];
    return isFieldOverridden(rawValue);
  };

  const handleFieldChange = (field: PromptField, value: string) => {
    onValueChange(field.key, value, field.envVar);
  };

  const handleReset = async (field: PromptField) => {
    if (onReset && agentId) {
      try {
        await onReset(sectionKey, field.key);
        toast({
          title: "Reset successful",
          description: `${field.label} has been reset to default value.`,
        });
      } catch (error) {
        toast({
          title: "Reset failed",
          description: error instanceof Error ? error.message : "Failed to reset field",
          variant: "destructive",
        });
      }
    }
  };

  return (
    <Card className="bg-orange-50 border-orange-200">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg flex items-center gap-2">
              <div className="w-2 h-2 bg-orange-400 rounded-full"></div>
              {title}
            </CardTitle>
            {description && (
              <CardDescription className="text-orange-700">
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
          const fieldOverridden = isOverridden(field);

          return (
            <div key={field.key} className="space-y-3">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor={fieldId} className="flex items-center gap-2 text-orange-900 font-medium">
                    {field.label}
                    {field.required && <span className="text-red-500">*</span>}
                    {fieldOverridden && (
                      <Badge variant="secondary" className="ml-2 text-xs bg-amber-100 text-amber-800">
                        Overridden
                      </Badge>
                    )}
                  </Label>
                  <div className="flex items-center gap-2">
                    {onReset && agentId && (
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="h-7 px-2 text-xs text-amber-600 hover:text-amber-700 hover:bg-amber-50"
                        onClick={() => handleReset(field)}
                      >
                        <RotateCcw className="h-3 w-3 mr-1" />
                        Reset
                      </Button>
                    )}
                    <Dialog>
                    <DialogTrigger asChild>
                      <Button variant="ghost" size="sm" className="h-8 w-8 p-0 text-orange-600 hover:text-orange-700 hover:bg-orange-100">
                        <Maximize2 className="h-4 w-4" />
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
                      <DialogHeader>
                        <DialogTitle>{field.label}</DialogTitle>
                        {field.description && (
                          <DialogDescription>{field.description}</DialogDescription>
                        )}
                      </DialogHeader>
                      <div className="flex-1 overflow-auto">
                        <Textarea
                          value={currentValue}
                          onChange={(e) => !field.readonly && handleFieldChange(field, e.target.value)}
                          placeholder={field.placeholder}
                          rows={30}
                          className={`min-h-[600px] ${field.readonly ? 'bg-orange-50 text-orange-900' : 'bg-white'} font-mono text-sm`}
                          readOnly={field.readonly}
                        />
                      </div>
                    </DialogContent>
                  </Dialog>
                  </div>
                </div>
                <Textarea
                  id={fieldId}
                  value={currentValue}
                  onChange={(e) => !field.readonly && handleFieldChange(field, e.target.value)}
                  placeholder={field.placeholder}
                  rows={field.rows || Math.max(8, Math.min(25, (currentValue?.toString().split('\n').length || 8) + 2))}
                  className={`${field.readonly ? 'bg-orange-100 text-orange-700 border-orange-200' : 'bg-white border-orange-300 focus:border-orange-400 focus:ring-orange-400'} transition-colors`}
                  readOnly={field.readonly}
                />
              </div>

              {field.description && (
                <div className="flex items-start gap-2 text-sm text-orange-700 bg-orange-100/50 p-3 rounded-md">
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