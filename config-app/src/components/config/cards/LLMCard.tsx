"use client";

import React from 'react';
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Info, AlertTriangle, Cpu, Zap, Brain, DollarSign, Thermometer } from "lucide-react";
import modelConstants from '../../../../../config/model_constants.json';

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
}

export function LLMCard({
  title,
  description,
  fields,
  values,
  onValueChange,
  sectionKey,
  context = 'general'
}: LLMCardProps) {
  const getCurrentValue = (field: LLMField) => {
    if (values[sectionKey]?.[field.key] !== undefined) {
      return values[sectionKey][field.key];
    }
    return field.default || '';
  };

  const handleFieldChange = (field: LLMField, value: any) => {
    let processedValue = value;

    if (field.type === 'number') {
      processedValue = typeof value === 'string' ? parseFloat(value) || 0 : value;
    }

    onValueChange(field.key, processedValue, field.envVar);
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
        <CardTitle className="text-lg flex items-center gap-2">
          <Brain className="h-5 w-5 text-blue-600" />
          {title}
        </CardTitle>
        {description && (
          <CardDescription className="text-blue-700">
            {description}
          </CardDescription>
        )}
        {context !== 'general' && (
          <Alert className="border-blue-300 bg-blue-100/50">
            <Info className="h-4 w-4 text-blue-600" />
            <AlertDescription className="text-blue-800">
              <strong>Recommendation:</strong> {getContextRecommendation()}
            </AlertDescription>
          </Alert>
        )}
      </CardHeader>
      <CardContent className="space-y-6">
        {fields.map((field) => {
          const fieldId = `${sectionKey}-${field.key}`;
          const currentValue = getCurrentValue(field);

          return (
            <div key={field.key} className="space-y-3">
              <div className="space-y-2">
                <Label htmlFor={fieldId} className="flex items-center gap-2 text-blue-900 font-medium">
                  {field.label}
                  {field.required && <span className="text-red-500">*</span>}
                </Label>

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