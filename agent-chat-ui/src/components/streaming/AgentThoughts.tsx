import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Brain, Loader2, CheckCircle } from 'lucide-react';
import { useStreamContext } from '@/providers/Stream';

interface CustomEvent {
  event: string;
  node: string;
  data?: Record<string, any>;
  id: number;
  timestamp: string;
}

export function AgentThoughts() {
  const streamContext = useStreamContext();
  
  // Extract custom events from streaming data - check for ui in messages or direct UI events
  const customEvents = React.useMemo(() => {
    const events: CustomEvent[] = [];
    
    // Check messages for workflow progress
    if (streamContext?.messages) {
      streamContext.messages.forEach((message, idx) => {
        if (message.type === 'ai' && typeof message.content === 'string') {
          // Parse AI messages for workflow events
          if (message.content.includes('Status:') || message.content.includes('Processing:')) {
            events.push({
              id: idx,
              event: 'workflow_update',
              node: 'supervisor',
              data: { message: message.content },
              timestamp: new Date().toISOString()
            });
          }
        }
      });
    }
    
    return events;
  }, [streamContext?.messages]);

  if (customEvents.length === 0) {
    return null;
  }

  return (
    <Card className="w-full">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-sm font-medium">
          <Brain className="h-4 w-4 text-blue-500" />
          Agent Reasoning
          {streamContext?.isLoading && (
            <Loader2 className="h-3 w-3 animate-spin text-blue-500" />
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 max-h-48 overflow-y-auto">
        {customEvents.map((thought: CustomEvent) => (
          <div key={thought.id} className="flex items-start gap-2 text-sm">
            <CheckCircle className="h-3 w-3 mt-0.5 text-green-500 flex-shrink-0" />
            <div className="flex-1 space-y-1">
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-xs">
                  {thought.node}
                </Badge>
                <span className="text-xs text-muted-foreground">
                  {thought.event}
                </span>
              </div>
              {thought.data?.status && (
                <p className="text-muted-foreground text-xs">
                  {thought.data.status}
                </p>
              )}
              {thought.data?.message && (
                <p className="text-foreground text-xs">
                  {thought.data.message}
                </p>
              )}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
