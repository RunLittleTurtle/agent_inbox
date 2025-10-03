"use client";

import React from 'react';
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Info, AlertTriangle, Cpu, Zap, Brain, DollarSign, Thermometer, RotateCcw, Save, RefreshCw } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import modelConstants from '../../../../config/model_constants.json';
import { extractCurrentValue, isFieldOverridden } from '@/lib/config-utils';

interface LLMField {
  key: string;
  label: string;
  type: 'select' | 'number';
  description?: string;
  required?: boolean;
  options?: string[];
  validation?: {
    min?: number;
    max?: number;
    step?: number;
  };
  default?: any;
  note?: string;
  warning?: string;
  envVar?: string;
}

interface LLMCardProps {
  title: string;
  description: string;
  fields: LLMField[];
  values: Record<string, any>;
  onValueChange: (fieldKey: string, value: any, envVar?: string) => void;
  sectionKey: string;
  context?: 'triage' | 'draft' | 'rewrite' | 'scheduling' | 'reflection' | 'general';
  agentId?: string;
  onReset?: (sectionKey: string, fieldKey: string) => Promise<void>;
  onSave: () => Promise<void>;
  isDirty: boolean;
  isSaving: boolean;
}

export function LLMCard({
  title,
  description,
  fields,
  values,
  onValueChange,
  sectionKey,
  context = 'general',
  agentId,
  onReset,
  onSave,
  isDirty,
  isSaving
}: LLMCardProps) {
  const { toast } = useToast();
  const getCurrentValue = (field: LLMField) => {
    const rawValue = values[sectionKey]?.[field.key];
    if (rawValue !== undefined) {
      // Extract current value (handles both old and new FastAPI format)
      const extracted = extractCurrentValue(rawValue);
      return extracted ?? field.default ?? '';
    }
    return field.default ?? '';
  };

  const isOverridden = (field: LLMField): boolean => {
    const rawValue = values[sectionKey]?.[field.key];
    return isFieldOverridden(rawValue);
  };

  const handleFieldChange = (field: LLMField, value: any) => {
    let processedValue = value;

    if (field.type === 'number') {
      processedValue = typeof value === 'string' ? parseFloat(value) || 0 : value;
    }

    onValueChange(field.key, processedValue, field.envVar);
  };

  const handleReset = async (field: LLMField) => {
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

  const getModelIcon = (model: unknown) => {
    // Type guard: ensure model is a string
    if (typeof model !== 'string') return <Cpu className="h-4 w-4 text-gray-500" />;

    if (model.includes('haiku')) return <Zap className="h-4 w-4 text-green-500" />;
    if (model.includes('sonnet')) return <Brain className="h-4 w-4 text-blue-500" />;
    if (model.includes('opus')) return <Cpu className="h-4 w-4 text-purple-500" />;
    if (model.includes('gpt-4o')) return <Brain className="h-4 w-4 text-emerald-500" />;
    if (model.includes('gpt-5')) return <DollarSign className="h-4 w-4 text-yellow-500" />;
    if (model.includes('o3')) return <Brain className="h-4 w-4 text-red-500" />;
    return <Cpu className="h-4 w-4 text-gray-500" />;
  };

  const getModelDescription = (model: unknown) => {
    // Type guard: ensure model is a string
    if (typeof model !== 'string') return 'AI language model';

    // Load descriptions from JSON (single source of truth)
    const descriptions: Record<string, string> = modelConstants.MODEL_DESCRIPTIONS as Record<string, string>;
    return descriptions[model] || 'AI language model';
  };

  const getTemperatureDescription = (temp: unknown) => {
    // Type guard: ensure temp is a number
    if (typeof temp !== 'number' && typeof temp !== 'string') return '';

    // Convert to string for lookup
    const tempStr = String(temp);

    // Load descriptions from JSON (single source of truth)
    const descriptions: Record<string, string> = (modelConstants as any).TEMPERATURE_DESCRIPTIONS as Record<string, string>;
    return descriptions[tempStr] || '';
  };

  const isTemperatureField = (field: LLMField) => {
    return field.key.toLowerCase().includes('temperature');
  };

  const getContextRecommendation = () => {
    const recommendations: Record<string, string> = {
      triage: 'Haiku recommended - simple classification task',
      draft: 'Sonnet-4 or GPT-4o recommended - good writing quality',
      rewrite: 'Opus-4 or Sonnet-4 recommended - style understanding',
      scheduling: 'GPT-4o or o3 recommended - calendar reasoning',
      reflection: 'o3 or Opus-4 recommended - analytical capabilities',
      general: 'Sonnet-4 recommended - balanced performance'
    };
    return recommendations[context];
  };

  // Get model constraints from JSON config
  const getModelConstraints = (modelName: string) => {
    const constraints = (modelConstants as any).MODEL_CONSTRAINTS;
    return constraints?.[modelName] || null;
  };

  // Find the currently selected model from fields
  const getSelectedModel = () => {
    const modelField = fields.find(f => f.type === 'select' && !isTemperatureField(f));
    if (!modelField) return null;
    return getCurrentValue(modelField);
  };

  const selectedModel = getSelectedModel();
  const modelConstraints = selectedModel ? getModelConstraints(selectedModel) : null;
  const temperatureSupported = modelConstraints?.supports_temperature !== false;

  return (
    <Card className="bg-blue-50 border-blue-200">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg flex items-center gap-2">
              <Brain className="h-5 w-5 text-blue-600" />
              {title}
            </CardTitle>
            {description && (
              <CardDescription className="text-blue-700">
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
                  <Label htmlFor={fieldId} className="flex items-center gap-2 text-blue-900 font-medium">
                    {field.label}
                    {field.required && <span className="text-red-500">*</span>}
                    {fieldOverridden && (
                      <Badge variant="secondary" className="ml-2 text-xs bg-amber-100 text-amber-800">
                        Overridden
                      </Badge>
                    )}
                  </Label>
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
                </div>

                {field.type === 'select' ? (
                  <Select
                    value={currentValue}
                    onValueChange={(value) => handleFieldChange(field, value)}
                    disabled={isTemperatureField(field) && !temperatureSupported}
                  >
                    <SelectTrigger className="bg-white border-blue-300 focus:border-blue-400 focus:ring-blue-400 disabled:opacity-50 disabled:cursor-not-allowed">
                      <SelectValue placeholder={isTemperatureField(field) ? "Select temperature" : "Select a model"} />
                    </SelectTrigger>
                    <SelectContent>
                      {field.options?.map((option) => (
                        <SelectItem key={option} value={option}>
                          <div className="flex items-center gap-2">
                            {isTemperatureField(field) ? (
                              <Thermometer className="h-4 w-4 text-orange-500" />
                            ) : (
                              getModelIcon(option)
                            )}
                            <span>{option}</span>
                            <span className="text-xs text-gray-500 ml-2">
                              {isTemperatureField(field)
                                ? getTemperatureDescription(option)
                                : getModelDescription(option)}
                            </span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                ) : (
                  <Input
                    id={fieldId}
                    type="number"
                    value={currentValue}
                    onChange={(e) => handleFieldChange(field, parseFloat(e.target.value) || 0)}
                    min={field.validation?.min}
                    max={field.validation?.max}
                    step={field.validation?.step}
                    className="bg-white border-blue-300 focus:border-blue-400 focus:ring-blue-400"
                    disabled={isTemperatureField(field) && !temperatureSupported}
                  />
                )}
              </div>

              {field.description && (
                <div className="flex items-start gap-2 text-sm text-blue-700 bg-blue-100/50 p-3 rounded-md">
                  <Info className="h-4 w-4 mt-0.5 flex-shrink-0" />
                  <span>{field.description}</span>
                </div>
              )}

              {field.note && (
                <Alert className="border-blue-300 bg-blue-100/30">
                  <Info className="h-4 w-4 text-blue-600" />
                  <AlertDescription className="text-blue-800">{field.note}</AlertDescription>
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