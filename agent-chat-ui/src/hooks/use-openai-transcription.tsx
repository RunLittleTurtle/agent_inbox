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

  // Check if OpenAI API key is available
  const getOpenAIKey = useCallback((): string | null => {
    // Check multiple possible env var names
    return (
      process.env.NEXT_PUBLIC_OPENAI_API_KEY ||
      process.env.OPENAI_API_KEY ||
      null
    );
  }, []);

  // Convert audio blob to format suitable for OpenAI API
  const prepareAudioForAPI = useCallback(
    async (audioBlob: Blob): Promise<File> => {
      // Convert to a File object with proper name and type
      const audioFile = new File([audioBlob], "audio.webm", {
        type: audioBlob.type || "audio/webm",
      });
      return audioFile;
    },
    [],
  );

  // Transcribe using OpenAI API
  const transcribe = useCallback(
    async (audioBlob: Blob): Promise<TranscriptionResult | null> => {
      const apiKey = getOpenAIKey();

      if (!apiKey) {
        setState((prev) => ({
          ...prev,
          error:
            "OpenAI API key not found. Please set NEXT_PUBLIC_OPENAI_API_KEY or OPENAI_API_KEY in your environment.",
        }));
        return null;
      }

      if (!audioBlob || audioBlob.size === 0) {
        setState((prev) => ({ ...prev, error: "No audio data provided" }));
        return null;
      }

      setState((prev) => ({ ...prev, isLoading: true, error: null }));

      try {
        // Prepare audio file for API
        const audioFile = await prepareAudioForAPI(audioBlob);

        // Create FormData for the API request
        const formData = new FormData();
        formData.append("file", audioFile);
        formData.append("model", "whisper-1"); // OpenAI currently uses whisper-1, not v3-turbo yet
        // Note: Omitting language parameter enables auto-detection (French/English)
        formData.append("response_format", "json");

        // Make API request to OpenAI
        const response = await fetch(
          "https://api.openai.com/v1/audio/transcriptions",
          {
            method: "POST",
            headers: {
              Authorization: `Bearer ${apiKey}`,
            },
            body: formData,
          },
        );

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(
            errorData.error?.message ||
              `OpenAI API error: ${response.status} ${response.statusText}`,
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
    [getOpenAIKey, prepareAudioForAPI],
  );

  return {
    ...state,
    transcribe,
    isModelReady: !!getOpenAIKey(), // Ready if API key is available
  };
}
