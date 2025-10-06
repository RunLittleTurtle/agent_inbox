"use client";

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Info, AlertTriangle, CheckCircle, Zap, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { extractCurrentValue } from '@/lib/config-utils';
import { useToast } from "@/hooks/use-toast";

interface GoogleWorkspaceCardProps {
  values: Record<string, any>;
  onValueChange: (fieldKey: string, value: any) => void;
  sectionKey: string;
  onSave: () => Promise<void>;
  isDirty: boolean;
  isSaving: boolean;
}

export function GoogleWorkspaceCard({
  values,
  onValueChange,
  sectionKey,
  onSave,
  isDirty,
  isSaving,
}: GoogleWorkspaceCardProps) {
  const { toast } = useToast();
  const [oauthStatus, setOauthStatus] = React.useState<'connected' | 'disconnected' | 'loading'>('disconnected');
  const [isConnecting, setIsConnecting] = React.useState(false);
  const [isCheckingStatus, setIsCheckingStatus] = React.useState(true);

  // Check if user has refresh_token (means they've connected)
  const loadOAuthStatus = React.useCallback(async () => {
    try {
      setIsCheckingStatus(true);
      // Check if refresh_token exists in values
      const refreshToken = values[sectionKey]?.google_refresh_token;
      const extracted = extractCurrentValue(refreshToken);

      if (extracted && extracted.length > 0) {
        setOauthStatus('connected');
      } else {
        setOauthStatus('disconnected');
      }
    } catch (error) {
      console.error('Failed to load OAuth status:', error);
      setOauthStatus('disconnected');
    } finally {
      setIsCheckingStatus(false);
    }
  }, [values, sectionKey]);

  // OAuth Connection Handler
  const handleConnectGoogle = async () => {
    setIsConnecting(true);

    try {
      // 1. Initiate OAuth flow
      const response = await fetch('/api/oauth/google/initiate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'OAuth initiation failed');
      }

      const { authUrl } = await response.json();

      // 2. Open OAuth popup
      const popup = window.open(
        authUrl,
        'Google OAuth',
        'width=600,height=700,left=100,top=100'
      );

      if (!popup) {
        toast({
          variant: "destructive",
          title: "Popup Blocked",
          description: "Please allow popups for this site"
        });
        setIsConnecting(false);
        return;
      }

      // 3. Listen for completion
      const handleMessage = (event: MessageEvent) => {
        if (event.data.type === 'google_oauth_complete') {
          popup?.close();
          window.removeEventListener('message', handleMessage);
          setIsConnecting(false);
          setOauthStatus('connected');
          toast({
            title: "Success!",
            description: "Google Workspace connected successfully!"
          });
          // Reload page to fetch updated values with refresh_token
          window.location.reload();
        } else if (event.data.type === 'google_oauth_error') {
          popup?.close();
          window.removeEventListener('message', handleMessage);
          setIsConnecting(false);
          toast({
            variant: "destructive",
            title: "Connection Failed",
            description: event.data.error
          });
        }
      };

      window.addEventListener('message', handleMessage);

    } catch (error: any) {
      setIsConnecting(false);
      toast({
        variant: "destructive",
        title: "Error",
        description: error.message
      });
    }
  };

  // Load OAuth status on mount and when values change
  React.useEffect(() => {
    loadOAuthStatus();
  }, [loadOAuthStatus]);

  return (
    <Card className="bg-amber-50 border-amber-200">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg flex items-center gap-2">
              <Zap className="h-5 w-5 text-amber-600" />
              Google Workspace Integration
            </CardTitle>
            <CardDescription className="text-amber-700">
              Connect your Google account to enable Gmail, Calendar, and other Google services
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* OAuth Connection Status */}
        <div className="space-y-3 pb-4 border-b border-amber-200">
          {oauthStatus === 'connected' ? (
            <Alert className="bg-green-100 border-green-300">
              <CheckCircle className="h-4 w-4 text-green-600" />
              <AlertDescription className="text-green-800">
                <div className="flex items-center justify-between">
                  <span>Connected to Google Workspace</span>
                  <Button
                    onClick={handleConnectGoogle}
                    variant="ghost"
                    size="sm"
                    disabled={isConnecting}
                    className="ml-4"
                  >
                    {isConnecting ? 'Connecting...' : 'Reconnect'}
                  </Button>
                </div>
              </AlertDescription>
            </Alert>
          ) : (
            <Alert className="bg-amber-100 border-amber-300">
              <AlertTriangle className="h-4 w-4 text-amber-600" />
              <AlertDescription className="text-amber-800">
                Click below to authorize access to your Gmail and Calendar
              </AlertDescription>
            </Alert>
          )}

          <Button
            onClick={handleConnectGoogle}
            disabled={isConnecting || isCheckingStatus}
            className="w-full bg-amber-600 hover:bg-amber-700"
          >
            {isConnecting ? (
              <>
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                Connecting...
              </>
            ) : (
              <>
                <Zap className="w-4 h-4 mr-2" />
                {oauthStatus === 'connected' ? 'Reconnect Google Account' : 'Connect Google Account'}
              </>
            )}
          </Button>
        </div>

        {/* Help Text */}
        <Alert className="bg-blue-50 border-blue-200">
          <Info className="h-4 w-4 text-blue-600" />
          <AlertDescription className="text-blue-800 text-sm">
            <strong>What permissions will be requested:</strong>
            <ul className="list-disc list-inside mt-2 space-y-1">
              <li><strong>Gmail</strong>: Read, send, and manage emails</li>
              <li><strong>Calendar</strong>: View and manage calendar events</li>
              <li><strong>Profile</strong>: Access your basic profile information</li>
            </ul>
            <p className="mt-3 text-xs">
              You may see an "unverified app" warning. This is normal for internal applications. Click "Advanced" → "Go to [app name]" to continue.
            </p>
          </AlertDescription>
        </Alert>
      </CardContent>
    </Card>
  );
}
