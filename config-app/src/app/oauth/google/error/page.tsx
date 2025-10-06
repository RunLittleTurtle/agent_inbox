"use client";

import React, { Suspense } from 'react';
import { XCircle, AlertTriangle } from 'lucide-react';
import { useSearchParams } from 'next/navigation';
import { Button } from '@/components/ui/button';

const ERROR_MESSAGES: Record<string, string> = {
  'access_denied': 'You denied permission. Please try again and grant access to Gmail and Calendar.',
  'missing_parameters': 'OAuth callback received incomplete data.',
  'invalid_state': 'Security verification failed. Please try connecting again.',
  'credentials_not_found': 'Your Google OAuth credentials were not found. Please add them in config-app first.',
  'token_exchange_failed': 'Failed to exchange authorization code for tokens.',
  'no_refresh_token': 'Did not receive a refresh token. Try revoking access in Google account settings and reconnecting.',
  'save_failed': 'Failed to save credentials. Please try again.',
  'unexpected_error': 'An unexpected error occurred.',
};

function ErrorContent() {
  const searchParams = useSearchParams();
  const error = searchParams.get('error') || 'unexpected_error';
  const details = searchParams.get('details');
  const hint = searchParams.get('hint');

  const errorMessage = ERROR_MESSAGES[error] || ERROR_MESSAGES['unexpected_error'];

  React.useEffect(() => {
    // Notify parent window that OAuth failed
    if (window.opener) {
      window.opener.postMessage(
        { type: 'google_oauth_error', error: errorMessage },
        window.location.origin
      );
    }
  }, [errorMessage]);

  const handleClose = () => {
    window.close();
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-red-50 to-orange-50">
      <div className="bg-white p-8 rounded-lg shadow-lg max-w-md">
        <div className="text-center mb-6">
          <XCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Connection Failed
          </h1>
        </div>

        <div className="space-y-4">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800 text-sm">
              {errorMessage}
            </p>
          </div>

          {details && (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <p className="text-gray-600 text-xs font-mono">
                Details: {details}
              </p>
            </div>
          )}

          {hint && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 flex gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
              <p className="text-amber-800 text-sm">
                {decodeURIComponent(hint)}
              </p>
            </div>
          )}

          <div className="pt-4">
            <Button
              onClick={handleClose}
              className="w-full"
              variant="outline"
            >
              Close Window
            </Button>
          </div>

          <p className="text-center text-xs text-gray-500">
            Error code: <code className="bg-gray-100 px-1 rounded">{error}</code>
          </p>
        </div>
      </div>
    </div>
  );
}

export default function GoogleOAuthError() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-500">Loading...</div>
      </div>
    }>
      <ErrorContent />
    </Suspense>
  );
}
