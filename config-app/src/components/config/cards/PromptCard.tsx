"use client";

import React, { useState } from 'react';
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Info, AlertTriangle, Maximize2 } from "lucide-react";
import { extractCurrentValue } from '@/lib/config-utils';

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
}

export function PromptCard({
  title,
  description,
  fields,
  values,
  onValueChange,
  sectionKey
}: PromptCardProps) {
  const getCurrentValue = (field: PromptField) => {
    const rawValue = values[sectionKey]?.[field.key];
    if (rawValue !== undefined) {
      return extractCurrentValue(rawValue);
    }
    return field.default || '';
  };

  const handleFieldChange = (field: PromptField, value: string) => {
    onValueChange(field.key, value, field.envVar);
  };

  return (
    <Card className="bg-orange-50 border-orange-200">
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <div className="w-2 h-2 bg-orange-400 rounded-full"></div>
          {title}
        </CardTitle>
        {description && (
          <CardDescription className="text-orange-700">
            {description}
          </CardDescription>
        )}
      </CardHeader>
      <CardContent className="space-y-6">
        {fields.map((field) => {
          const fieldId = `${sectionKey}-${field.key}`;
          const currentValue = getCurrentValue(field);

          return (
            <div key={field.key} className="space-y-3">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor={fieldId} className="flex items-center gap-2 text-orange-900 font-medium">
                    {field.label}
                    {field.required && <span className="text-red-500">*</span>}
                  </Label>
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

              {field.note && (
                <Alert className="border-orange-300 bg-orange-100/30">
                  <Info className="h-4 w-4 text-orange-600" />
                  <AlertDescription className="text-orange-800">{field.note}</AlertDescription>
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