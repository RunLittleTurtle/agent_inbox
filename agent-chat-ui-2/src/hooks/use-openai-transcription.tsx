import { useState, useCallback } from "react";
import {
  TranscriptionResult,
  TranscriptionState,
} from "./use-whisper-transcription";

export interface UseOpenAITranscriptionReturn extends TranscriptionState {
  transcribe: (audioBlob: Blob) => Promise<TranscriptionResult | null>;
  isModelReady: boolean;
}

export function useOpenAITranscription(): UseOpenAITranscriptionReturn {
  const [state, setState] = useState<TranscriptionState>({
    isLoading: false,
    isModelLoading: false,
    error: null,
    progress: 0,
  });

  // Check if API route is available (always true in browser environment)
  const isAPIAvailable = useCallback((): boolean => {
    return typeof window !== "undefined";
  }, []);

  // Transcribe using secure API route
  const transcribe = useCallback(
    async (audioBlob: Blob): Promise<TranscriptionResult | null> => {
      if (!audioBlob || audioBlob.size === 0) {
        setState((prev) => ({ ...prev, error: "No audio data provided" }));
        return null;
      }

      setState((prev) => ({ ...prev, isLoading: true, error: null }));

      try {
        // Prepare audio file
        const audioFile = new File([audioBlob], "audio.webm", {
          type: audioBlob.type || "audio/webm",
        });

        // Create FormData for the API request
        const formData = new FormData();
        formData.append("file", audioFile);

        // Call secure API route (API key handled server-side)
        const response = await fetch("/api/transcribe", {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(
            errorData.error || `Transcription API error: ${response.status}`,
          );
        }

        const result = await response.json();

        setState((prev) => ({ ...prev, isLoading: false }));

        return {
          text: result.text?.trim() || "",
          language: result.language,
          confidence: undefined, // OpenAI API doesn't return confidence scores
        };
      } catch (error) {
        console.error("Error during OpenAI transcription:", error);

        let errorMessage = "Transcription failed";
        if (error instanceof Error) {
          errorMessage = error.message;
        }

        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: errorMessage,
        }));
        return null;
      }
    },
    [],
  );

  return {
    ...state,
    transcribe,
    isModelReady: isAPIAvailable(), // Ready if in browser environment
  };
}