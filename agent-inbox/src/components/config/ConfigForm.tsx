"use client";

import React from 'react';
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Info, AlertTriangle, Eye, EyeOff } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ConfigField {
  key: string;
  label: string;
  type: string;
  envVar?: string;
  default?: any;
  description?: string;
  placeholder?: string;
  required?: boolean;
  options?: string[];
  validation?: any;
  note?: string;
  warning?: string;
}

interface ConfigSection {
  key: string;
  label: string;
  description: string;
  fields: ConfigField[];
}

interface ConfigFormProps {
  sections: ConfigSection[];
  values: Record<string, any>;
  onValueChange: (sectionKey: string, fieldKey: string, value: any, envVar?: string) => void;
}

export function ConfigForm({ sections, values, onValueChange }: ConfigFormProps) {
  const [showPasswords, setShowPasswords] = React.useState<Record<string, boolean>>({});

  const togglePasswordVisibility = (fieldKey: string) => {
    setShowPasswords(prev => ({
      ...prev,
      [fieldKey]: !prev[fieldKey]
    }));
  };

  const getCurrentValue = (field: ConfigField) => {
    if (field.envVar) {
      return values[field.envVar] || field.default || '';
    }
    return field.default || '';
  };

  const handleFieldChange = (section: ConfigSection, field: ConfigField, value: any) => {
    // TODO(human) - Implement the field change handler logic
    // This function should handle different field types and call onValueChange appropriately
    // Consider these field types: text, password, boolean, select, number, textarea
    // Handle validation and type conversion before calling onValueChange

    onValueChange(section.key, field.key, value, field.envVar);
  };

  const renderField = (section: ConfigSection, field: ConfigField) => {
    const currentValue = getCurrentValue(field);
    const fieldId = `${section.key}-${field.key}`;

    switch (field.type) {
      case 'password':
        return (
          <div className="space-y-2">
            <Label htmlFor={fieldId} className="flex items-center gap-2">
              {field.label}
              {field.required && <span className="text-red-500">*</span>}
            </Label>
            <div className="relative">
              <Input
                id={fieldId}
                type={showPasswords[fieldId] ? "text" : "password"}
                value={currentValue}
                onChange={(e) => handleFieldChange(section, field, e.target.value)}
                placeholder={field.placeholder}
                className="pr-10"
              />
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="absolute right-2 top-1/2 -translate-y-1/2 h-6 w-6 p-0"
                onClick={() => togglePasswordVisibility(fieldId)}
              >
                {showPasswords[fieldId] ? (
                  <EyeOff className="h-3 w-3" />
                ) : (
                  <Eye className="h-3 w-3" />
                )}
              </Button>
            </div>
          </div>
        );

      case 'textarea':
        return (
          <div className="space-y-2">
            <Label htmlFor={fieldId} className="flex items-center gap-2">
              {field.label}
              {field.required && <span className="text-red-500">*</span>}
            </Label>
            <Textarea
              id={fieldId}
              value={currentValue}
              onChange={(e) => handleFieldChange(section, field, e.target.value)}
              placeholder={field.placeholder}
              rows={3}
            />
          </div>
        );

      case 'boolean':
        return (
          <div className="flex items-center space-x-2">
            <Switch
              id={fieldId}
              checked={currentValue === true || currentValue === 'true'}
              onCheckedChange={(checked) => handleFieldChange(section, field, checked)}
            />
            <Label htmlFor={fieldId} className="flex items-center gap-2">
              {field.label}
              {field.required && <span className="text-red-500">*</span>}
            </Label>
          </div>
        );

      case 'select':
        return (
          <div className="space-y-2">
            <Label htmlFor={fieldId} className="flex items-center gap-2">
              {field.label}
              {field.required && <span className="text-red-500">*</span>}
            </Label>
            <Select
              value={currentValue}
              onValueChange={(value) => handleFieldChange(section, field, value)}
            >
              <SelectTrigger>
                <SelectValue placeholder={field.placeholder} />
              </SelectTrigger>
              <SelectContent>
                {field.options?.map((option) => (
                  <SelectItem key={option} value={option}>
                    {option}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        );

      case 'number':
        return (
          <div className="space-y-2">
            <Label htmlFor={fieldId} className="flex items-center gap-2">
              {field.label}
              {field.required && <span className="text-red-500">*</span>}
            </Label>
            <Input
              id={fieldId}
              type="number"
              value={currentValue}
              onChange={(e) => handleFieldChange(section, field, parseFloat(e.target.value) || 0)}
              placeholder={field.placeholder}
              min={field.validation?.min}
              max={field.validation?.max}
              step={field.validation?.step}
            />
          </div>
        );

      default: // text
        return (
          <div className="space-y-2">
            <Label htmlFor={fieldId} className="flex items-center gap-2">
              {field.label}
              {field.required && <span className="text-red-500">*</span>}
            </Label>
            <Input
              id={fieldId}
              type="text"
              value={currentValue}
              onChange={(e) => handleFieldChange(section, field, e.target.value)}
              placeholder={field.placeholder}
            />
          </div>
        );
    }
  };

  return (
    <div className="space-y-6">
      {sections.map((section) => (
        <Card key={section.key}>
          <CardHeader>
            <CardTitle className="text-lg">{section.label}</CardTitle>
            {section.description && (
              <CardDescription>{section.description}</CardDescription>
            )}
          </CardHeader>
          <CardContent className="space-y-4">
            {section.fields.map((field) => (
              <div key={field.key} className="space-y-2">
                {renderField(section, field)}

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
            ))}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}