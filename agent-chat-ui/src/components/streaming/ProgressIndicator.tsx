import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Activity, Loader2 } from 'lucide-react';
import { useStreamContext } from '@/providers/Stream';

const WORKFLOW_STEPS = [
  'analyzing_email',
  'coordinating_agents',
  'processing_request',
  'response_synthesized',
  'awaiting_review'
];

export function ProgressIndicator() {
  const streamContext = useStreamContext();
  
  // Calculate progress from streaming messages
  const progress = React.useMemo(() => {
    if (!streamContext?.messages) return { current: 0, total: WORKFLOW_STEPS.length, percentage: 0 };
    
    // Find progress indicators in messages
    let currentStep = 0;
    streamContext.messages.forEach((message) => {
      if (message.type === 'ai' && typeof message.content === 'string') {
        WORKFLOW_STEPS.forEach((step, index) => {
          const contentStr = String(message.content);
          if (contentStr.includes(step) || contentStr.includes(step.replace('_', ' '))) {
            currentStep = Math.max(currentStep, index + 1);
          }
        });
      }
    });
    
    const percentage = (currentStep / WORKFLOW_STEPS.length) * 100;
    
    return {
      current: currentStep,
      total: WORKFLOW_STEPS.length,
      percentage,
      currentStatus: currentStep > 0 ? WORKFLOW_STEPS[currentStep - 1] : null
    };
  }, [streamContext?.messages]);

  if (!streamContext?.isLoading && progress.percentage === 0) {
    return null;
  }

  return (
    <Card className="w-full">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-sm font-medium">
          <Activity className="h-4 w-4 text-blue-500" />
          Workflow Progress
          {streamContext?.isLoading && (
            <Loader2 className="h-3 w-3 animate-spin text-blue-500" />
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex justify-between text-sm">
          <span className="font-medium">
            Step {progress.current} of {progress.total}
          </span>
          <span className="text-muted-foreground">
            {Math.round(progress.percentage)}%
          </span>
        </div>
        <div className="w-full bg-secondary rounded-full h-2">
          <div 
            className="bg-primary h-2 rounded-full transition-all duration-300"
            style={{ width: `${progress.percentage}%` }}
          />
        </div>
        {progress.currentStatus && (
          <p className="text-xs text-muted-foreground capitalize">
            {progress.currentStatus.replace('_', ' ')}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
