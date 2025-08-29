import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Brain, Loader2, CheckCircle, Clock, MessageSquare, Wrench } from 'lucide-react';

// LangGraph streaming event types based on official documentation
// Reference: https://langchain-ai.github.io/langgraph/concepts/streaming/
interface LangGraphStreamEvent {
  event: 'on_chain_start' | 'on_chain_stream' | 'on_chain_end' | 'on_chat_model_stream' | 'on_tool_start' | 'on_tool_end';
  name: string; // Node name in LangGraph
  run_id: string;
  data?: {
    input?: any;
    output?: any;
    chunk?: string; // For streaming tokens
  };
  metadata?: {
    langgraph_step?: number;
    langgraph_node?: string;
    langgraph_triggers?: string[];
  };
}

// Update stream chunk from LangGraph astream() with mode
interface LangGraphUpdateChunk {
  [node_name: string]: {
    messages?: any[];
    [key: string]: any;
  };
}

// Message stream chunk for token streaming
interface LangGraphMessageChunk {
  content?: string;
  additional_kwargs?: Record<string, any>;
  tool_calls?: any[];
  id?: string;
}

interface AgentWorkflowProps {
  // Support different LangGraph streaming modes
  updateEvents?: LangGraphUpdateChunk[]; // For stream_mode="updates"
  messageChunks?: LangGraphMessageChunk[]; // For stream_mode="messages"
  streamEvents?: LangGraphStreamEvent[]; // For detailed event tracking
  isActive?: boolean;
  streamMode?: 'updates' | 'messages' | 'values' | 'custom' | 'debug';
}

export function AgentWorkflow({ 
  updateEvents = [], 
  messageChunks = [], 
  streamEvents = [],
  isActive = false,
  streamMode = 'updates'
}: AgentWorkflowProps) {
  const hasContent = updateEvents.length > 0 || messageChunks.length > 0 || streamEvents.length > 0;
  
  if (!hasContent && !isActive) {
    return null;
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'on_chain_start':
      case 'on_tool_start':
        return <Clock className="h-3 w-3 mt-0.5 text-blue-500 flex-shrink-0" />;
      case 'on_chain_stream':
      case 'on_chat_model_stream':
        return <Loader2 className="h-3 w-3 mt-0.5 animate-spin text-blue-500 flex-shrink-0" />;
      case 'on_chain_end':
      case 'on_tool_end':
        return <CheckCircle className="h-3 w-3 mt-0.5 text-green-500 flex-shrink-0" />;
      default:
        return <Clock className="h-3 w-3 mt-0.5 text-gray-400 flex-shrink-0" />;
    }
  };

  const renderUpdateEvents = () => {
    return updateEvents.map((update, index) => {
      const nodeNames = Object.keys(update);
      return nodeNames.map((nodeName) => (
        <div key={`update-${index}-${nodeName}`} className="flex items-start gap-2 text-sm">
          <CheckCircle className="h-3 w-3 mt-0.5 text-green-500 flex-shrink-0" />
          <div className="flex-1 space-y-1">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-xs">
                {nodeName}
              </Badge>
              <span className="text-xs text-muted-foreground">
                Updated
              </span>
            </div>
            {update[nodeName]?.messages && (
              <p className="text-xs text-muted-foreground">
                {update[nodeName]?.messages?.length || 0} message(s) processed
              </p>
            )}
          </div>
        </div>
      ));
    }).flat();
  };

  const renderMessageChunks = () => {
    return messageChunks.map((chunk, index) => (
      <div key={`message-${index}`} className="flex items-start gap-2 text-sm">
        <MessageSquare className="h-3 w-3 mt-0.5 text-green-500 flex-shrink-0" />
        <div className="flex-1 space-y-1">
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs">
              LLM Token
            </Badge>
            <span className="text-xs text-muted-foreground">
              Streaming
            </span>
          </div>
          {chunk.content && (
            <p className="text-xs text-muted-foreground font-mono">
              "{chunk.content}"
            </p>
          )}
          {chunk.tool_calls && chunk.tool_calls.length > 0 && (
            <p className="text-xs text-muted-foreground">
              {chunk.tool_calls.length} tool call(s)
            </p>
          )}
        </div>
      </div>
    ));
  };

  const renderStreamEvents = () => {
    return streamEvents.map((event) => (
      <div key={event.run_id} className="flex items-start gap-2 text-sm">
        {getStatusIcon(event.event)}
        <div className="flex-1 space-y-1">
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs">
              {event.metadata?.langgraph_node || event.name}
            </Badge>
            <span className="text-xs text-muted-foreground">
              {event.event.replace('on_', '').replace('_', ' ')}
            </span>
            {event.metadata?.langgraph_step && (
              <span className="text-xs text-gray-400">
                Step {event.metadata.langgraph_step}
              </span>
            )}
          </div>
          {event.data?.chunk && (
            <p className="text-xs text-muted-foreground font-mono">
              "{event.data.chunk}"
            </p>
          )}
          {event.data?.output && (
            <p className="text-xs text-muted-foreground">
              Output: {typeof event.data.output === 'string' ? event.data.output : 'Complex data'}
            </p>
          )}
        </div>
      </div>
    ));
  };

  return (
    <Card className="w-full">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-sm font-medium">
          <Brain className="h-4 w-4 text-blue-500" />
          LangGraph Workflow
          {isActive && (
            <Loader2 className="h-3 w-3 animate-spin text-blue-500" />
          )}
          <Badge variant="secondary" className="text-xs ml-auto">
            {streamMode}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 max-h-48 overflow-y-auto">
        {streamMode === 'updates' && renderUpdateEvents()}
        {streamMode === 'messages' && renderMessageChunks()}
        {(streamMode === 'debug' || streamMode === 'custom') && renderStreamEvents()}
        
        {!hasContent && isActive && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-3 w-3 animate-spin" />
            <span>Initializing LangGraph workflow...</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
