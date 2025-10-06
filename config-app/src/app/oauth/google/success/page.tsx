"use client";

import React from 'react';
import { CheckCircle } from 'lucide-react';

export default function GoogleOAuthSuccess() {
  React.useEffect(() => {
    // Notify parent window that OAuth completed successfully
    if (window.opener) {
      window.opener.postMessage(
        { type: 'google_oauth_complete', success: true },
        window.location.origin
      );

      // Close window after a short delay
      setTimeout(() => {
        window.close();
      }, 1500);
    }
  }, []);

  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-green-50 to-blue-50">
      <div className="bg-white p-8 rounded-lg shadow-lg max-w-md text-center">
        <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          Connected Successfully!
        </h1>
        <p className="text-gray-600">
          Your Google Workspace is now connected. This window will close automatically...
        </p>
      </div>
    </div>
  );
}
