import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { MessageSquare, Loader2 } from 'lucide-react';
import { useStreamContext } from '@/providers/Stream';

export function TokenStream() {
  const streamContext = useStreamContext();
  const [displayText, setDisplayText] = React.useState<string>('');

  // Use actual streaming messages for token display
  React.useEffect(() => {
    if (streamContext?.messages && streamContext.messages.length > 0) {
      const lastMessage = streamContext.messages[streamContext.messages.length - 1];
      if (lastMessage?.type === 'ai') {
        const content = typeof lastMessage.content === 'string' ? lastMessage.content : '';
        setDisplayText(content);
      }
    }
  }, [streamContext?.messages]);

  // Only show during active streaming
  if (!streamContext?.isLoading) {
    return null;
  }

  return (
    <Card className="w-full">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-sm font-medium">
          <MessageSquare className="h-4 w-4 text-blue-500" />
          Live Response
          {streamContext?.isLoading && (
            <Loader2 className="h-3 w-3 animate-spin text-blue-500" />
          )}
          {!streamContext?.isLoading && displayText && (
            <Badge variant="outline" className="text-xs text-green-600">
              Complete
            </Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="bg-muted/50 rounded-lg p-3 text-sm">
          <div className="whitespace-pre-wrap">
            {displayText}
            {streamContext?.isLoading && (
              <span className="inline-block w-2 h-4 bg-primary animate-pulse ml-1" />
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
