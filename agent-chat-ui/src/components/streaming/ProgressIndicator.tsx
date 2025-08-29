import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Activity, Loader2, CheckCircle2, Clock, AlertCircle } from 'lucide-react';
import { useStreamContext } from '@/providers/Stream';

export function ProgressIndicator() {
  const streamContext = useStreamContext();
  
  // Get enhanced workflow progress from context
  const workflowProgress = (streamContext as any)?.workflowProgress;
  const streamEvents = (streamContext as any)?.streamEvents || [];
  
  // Parse actual LangGraph streaming events  
  const progress = React.useMemo(() => {
    console.log('🔍 PROGRESS CALCULATION - Stream Events:', streamEvents.length, streamEvents);
    
    const executionSteps: any[] = [];
    let status = 'waiting';
    let dynamicMessage = 'Waiting to start...';
    
    // Process LangGraph streaming events from get_stream_writer()
    if (streamEvents.length > 0) {
      status = 'running';
      console.log('🔍 Processing', streamEvents.length, 'stream events');
      
      streamEvents.forEach((event: any, index: number) => {
        const data = event.data || event;
        
        // Parse React SDK event types
        if (event.event_type === 'update') {
          // Node updates from onUpdateEvent
          if (data && typeof data === 'object') {
            const nodeNames = Object.keys(data).filter(key => key !== 'messages');
            if (nodeNames.length > 0) {
              const nodeName = nodeNames[0];
              const nodeData = data[nodeName];
              
              executionSteps.push({
                id: `update_${nodeName}_${index}`,
                name: `Executing: ${nodeName}`,
                status: 'running',
                timestamp: event.timestamp,
                type: 'node',
                node: nodeName,
                raw_data: nodeData
              });
              dynamicMessage = `Processing ${nodeName}`;
            }
            
            // Check for messages (indicates completion)
            if (data.messages && Array.isArray(data.messages)) {
              data.messages.forEach((msg: any, msgIdx: number) => {
                executionSteps.push({
                  id: `message_${index}_${msgIdx}`,
                  name: `${msg.type === 'ai' ? 'AI Response' : 'Message'}`,
                  status: 'complete',
                  timestamp: event.timestamp,
                  type: 'message',
                  message_type: msg.type,
                  content: msg.content
                });
              });
              
              // Mark all previous running steps as complete
              executionSteps.forEach(step => {
                if (step.status === 'running') {
                  step.status = 'complete';
                }
              });
              
              status = 'complete';
              dynamicMessage = 'Execution completed';
            }
          }
        }
        
        else if (event.event_type === 'metadata') {
          // Metadata events from onMetadataEvent
          if (data && data.run_id) {
            executionSteps.push({
              id: `meta_${index}`,
              name: 'Run Started',
              status: 'running',
              timestamp: event.timestamp,
              type: 'metadata',
              run_id: data.run_id
            });
            dynamicMessage = 'LangGraph execution started';
          }
        }
        
        else if (event.event_type === 'custom_stream') {
          // Custom events from onCustomEvent
          if (data && data.event) {
            const eventName = data.event;
            executionSteps.push({
              id: `custom_${eventName}_${index}`,
              name: `${eventName}`,
              status: data.event === 'node_complete' ? 'complete' : 'running',
              timestamp: event.timestamp,
              type: 'custom',
              event: eventName
            });
            dynamicMessage = data.data?.message || `Custom event: ${eventName}`;
          }
        }
        
        // Legacy custom events from get_stream_writer() 
        else if (data.event === 'node_start') {
          executionSteps.push({
            id: `start_${data.node}_${index}`,
            name: `Starting: ${data.node}`,
            status: 'running',
            timestamp: data.data?.timestamp || event.timestamp,
            type: 'node',
            message: data.data?.message,
            node: data.node
          });
          dynamicMessage = data.data?.message || `Starting ${data.node}`;
        }
        
        else if (data.event === 'processing') {
          executionSteps.push({
            id: `proc_${data.node}_${index}`,
            name: `Processing: ${data.node}`,
            status: 'running',
            timestamp: data.data?.timestamp || event.timestamp,
            type: 'processing',
            message: data.data?.message,
            step: data.data?.step
          });
          dynamicMessage = data.data?.message || `Processing in ${data.node}`;
        }
        
        else if (data.event === 'tool_execution') {
          executionSteps.push({
            id: `tool_${data.node}_${index}`,
            name: `Tool: ${data.data?.tool}`,
            status: 'running',
            timestamp: data.data?.timestamp || event.timestamp,
            type: 'tool',
            tool: data.data?.tool,
            node: data.node
          });
          dynamicMessage = `Executing ${data.data?.tool} in ${data.node}`;
        }
        
        else if (data.event === 'intent_detected') {
          executionSteps.push({
            id: `intent_${data.node}_${index}`,
            name: `Intent: ${data.data?.intent}`,
            status: 'complete',
            timestamp: data.data?.timestamp || event.timestamp,
            type: 'analysis',
            intent: data.data?.intent,
            confidence: data.data?.confidence,
            reasoning: data.data?.reasoning
          });
          dynamicMessage = `Detected intent: ${data.data?.intent}`;
        }
        
        else if (data.event === 'node_complete') {
          executionSteps.push({
            id: `complete_${data.node}_${index}`,
            name: `Completed: ${data.node}`,
            status: 'complete',
            timestamp: data.data?.timestamp || event.timestamp,
            type: 'node',
            message: data.data?.message,
            next_step: data.data?.next_step
          });
          dynamicMessage = data.data?.message || `Completed ${data.node}`;
        }
        
        else if (data.event === 'human_review_ready') {
          executionSteps.push({
            id: `review_${index}`,
            name: 'Ready for human review',
            status: 'complete',
            timestamp: data.data?.timestamp || event.timestamp,
            type: 'review',
            message: data.data?.message
          });
          dynamicMessage = 'Ready for Agent Inbox review';
        }
        
        else if (data.event === 'error') {
          executionSteps.push({
            id: `error_${data.node}_${index}`,
            name: `Error in ${data.node}`,
            status: 'error',
            timestamp: data.data?.timestamp || event.timestamp,
            type: 'error',
            message: data.data?.message
          });
          dynamicMessage = `Error: ${data.data?.message}`;
        }
      });
    }
    
    // Determine overall completion status first
    const completedSteps = executionSteps.filter(step => step.status === 'complete').length;
    const totalSteps = executionSteps.length;
    const progressPercentage = totalSteps > 0 ? Math.round((completedSteps / totalSteps) * 100) : 0;
    
    // Check for AI message completion or explicit completion
    const hasAIResponse = executionSteps.some(step => step.type === 'message' && step.message_type === 'ai');
    const hasNodeComplete = executionSteps.some(step => step.event === 'node_complete');
    const workflowComplete = (streamContext as any)?.workflowProgress?.status === 'complete';
    
    if (hasAIResponse || hasNodeComplete || workflowComplete || (completedSteps > 0 && completedSteps === totalSteps && totalSteps > 0)) {
      status = 'complete';
      dynamicMessage = 'LangGraph execution completed';
    } else if (streamContext?.isLoading || executionSteps.some(step => step.status === 'running')) {
      status = 'running';
      if (executionSteps.length === 0) {
        dynamicMessage = 'Initializing LangGraph workflow...';
      }
    }
    
    return {
      current: executionSteps.filter(s => s.status === 'complete').length,
      total: executionSteps.length,
      percentage: streamContext?.isLoading ? 
        Math.min(95, Math.round((executionSteps.filter(s => s.status === 'complete').length / executionSteps.length) * 100)) : 100,
      currentStatus: dynamicMessage,
      status,
      dynamicMessage,
      steps: executionSteps,
      currentStepIndex: executionSteps.length - 1
    };
  }, [streamEvents, streamContext?.isLoading]);

  // Get recent events for display
  const recentEvents = React.useMemo(() => {
    return streamEvents.slice(-3).reverse(); // Show last 3 events
  }, [streamEvents]);

  // Always show when streaming or when we have messages
  if (!streamContext?.isLoading && streamContext?.messages?.length === 0) {
    return null;
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <Loader2 className="h-3 w-3 animate-spin text-blue-500" />;
      case 'complete':
        return <CheckCircle2 className="h-3 w-3 text-green-500" />;
      case 'error':
        return <AlertCircle className="h-3 w-3 text-red-500" />;
      default:
        return <Clock className="h-3 w-3 text-gray-500" />;
    }
  };

  return (
    <Card className="w-full">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-sm font-medium">
          {getStatusIcon(progress.status)}
          <Activity className="h-4 w-4 text-primary" />
          Agent Workflow
          <Badge variant={progress.status === 'complete' ? 'default' : 'secondary'} className="text-xs">
            {Math.round(progress.percentage)}%
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Dynamic Status Message */}
          <div className="bg-muted/50 rounded-lg p-3">
            <div className="flex items-center gap-2">
              {progress.status === 'running' && (
                <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
              )}
              <span className="text-sm font-medium text-foreground">
                {(progress as any).dynamicMessage}
              </span>
            </div>
          </div>
          
          {/* Progress Bar */}
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-primary h-2 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${progress.percentage}%` }}
            />
          </div>
          
          {/* Real LangGraph Execution Steps */}
          <div className="space-y-2">
            {((progress as any).steps || []).map((step: any, index: number) => (
              <div key={step.id} className="flex items-start gap-3 text-sm">
                <div className="flex items-center justify-center w-6 h-6 rounded-full border-2 transition-all mt-0.5">
                  {step.status === 'complete' && (
                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                  )}
                  {step.status === 'running' && (
                    <Loader2 className="h-3 w-3 animate-spin text-blue-500" />
                  )}
                  {step.status === 'interrupted' && (
                    <AlertCircle className="h-4 w-4 text-yellow-500" />
                  )}
                  {step.status === 'pending' && (
                    <div className="w-2 h-2 rounded-full bg-gray-300" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className={`font-medium ${
                    step.status === 'running' ? 'text-foreground' : 
                    step.status === 'complete' ? 'text-muted-foreground' : 
                    'text-muted-foreground/60'
                  }`}>
                    {step.name}
                  </div>
                  {step.type === 'tool' && step.args && (
                    <div className="text-xs text-muted-foreground mt-1 font-mono bg-muted/50 rounded px-2 py-1">
                      {JSON.stringify(step.args, null, 0)}
                    </div>
                  )}
                  {step.timestamp && (
                    <div className="text-xs text-muted-foreground/60 mt-1">
                      {new Date(step.timestamp).toLocaleTimeString()}
                    </div>
                  )}
                </div>
                {step.status === 'complete' && (
                  <Badge variant="default" className="text-xs">
                    Complete
                  </Badge>
                )}
                {step.status === 'running' && (
                  <Badge variant="outline" className="text-xs">
                    Active
                  </Badge>
                )}
                <Badge variant="secondary" className="text-xs">
                  {step.type}
                </Badge>
              </div>
            ))}
            
            {/* Show raw events for debugging */}
            {streamEvents.length > 0 && (
              <div className="mt-4 pt-3 border-t border-border/50">
                <div className="text-xs font-medium text-muted-foreground mb-2">
                  Raw Events ({streamEvents.length}):
                </div>
                <div className="space-y-1 max-h-32 overflow-y-auto">
                  {streamEvents.slice(-5).map((event: any, index: number) => (
                    <div key={index} className="text-xs text-muted-foreground font-mono bg-muted/30 rounded px-2 py-1">
                      {JSON.stringify(event.data || event, null, 0).slice(0, 100)}...
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
