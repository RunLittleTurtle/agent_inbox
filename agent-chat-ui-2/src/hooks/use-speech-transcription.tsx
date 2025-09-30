import { useState, useCallback, useEffect } from 'react';
import { useWhisperTranscription } from './use-whisper-transcription';
import { useOpenAITranscription } from './use-openai-transcription';

export type TranscriptionMode = 'browser' | 'openai' | 'auto';

export interface TranscriptionResult {
  text: string;
  language?: string;
  confidence?: number;
  mode?: 'browser' | 'openai';
}

export interface TranscriptionState {
  isLoading: boolean;
  isModelLoading: boolean;
  error: string | null;
  progress: number;
  currentMode: 'browser' | 'openai' | null;
}

export interface UseSpeechTranscriptionOptions {
  mode?: TranscriptionMode;
  preferOpenAI?: boolean;
}

export interface UseSpeechTranscriptionReturn extends TranscriptionState {
  transcribe: (audioBlob: Blob) => Promise<TranscriptionResult | null>;
  isModelReady: boolean;
  availableModes: ('browser' | 'openai')[];
  switchMode: (mode: TranscriptionMode) => void;
}

export function useSpeechTranscription(
  options: UseSpeechTranscriptionOptions = {}
): UseSpeechTranscriptionReturn {
  const { mode = 'auto', preferOpenAI = false } = options;

  const [selectedMode, setSelectedMode] = useState<TranscriptionMode>(mode);
  const [currentMode, setCurrentMode] = useState<'browser' | 'openai' | null>(null);

  // Initialize both hooks
  const browserTranscription = useWhisperTranscription();
  const openaiTranscription = useOpenAITranscription();

  // Determine available modes
  const availableModes: ('browser' | 'openai')[] = [];
  if (typeof window !== 'undefined') {
    availableModes.push('browser'); // Browser-based is always available on client
  }
  if (openaiTranscription.isModelReady) {
    availableModes.push('openai');
  }

  // Auto-select mode based on availability and preferences (OpenAI API first)
  useEffect(() => {
    if (selectedMode === 'auto') {
      // Prioritize OpenAI API regardless of preferOpenAI flag
      if (availableModes.includes('openai')) {
        setCurrentMode('openai');
      } else if (availableModes.includes('browser')) {
        setCurrentMode('browser');
      } else {
        setCurrentMode(null);
      }
    } else if (selectedMode === 'browser' && availableModes.includes('browser')) {
      setCurrentMode('browser');
    } else if (selectedMode === 'openai' && availableModes.includes('openai')) {
      setCurrentMode('openai');
    } else {
      setCurrentMode(null);
    }
  }, [selectedMode, availableModes, preferOpenAI]);

  // Get current active transcription hook
  const getActiveHook = useCallback(() => {
    switch (currentMode) {
      case 'browser':
        return browserTranscription;
      case 'openai':
        return openaiTranscription;
      default:
        return null;
    }
  }, [currentMode, browserTranscription, openaiTranscription]);

  // Switch transcription mode
  const switchMode = useCallback((newMode: TranscriptionMode) => {
    setSelectedMode(newMode);
  }, []);

  // Unified transcribe function
  const transcribe = useCallback(async (audioBlob: Blob): Promise<TranscriptionResult | null> => {
    const activeHook = getActiveHook();

    if (!activeHook) {
      return null;
    }

    const result = await activeHook.transcribe(audioBlob);

    if (result) {
      return {
        ...result,
        mode: currentMode || undefined,
      };
    }

    return null;
  }, [getActiveHook, currentMode]);

  // Combine state from active hook
  const activeHook = getActiveHook();
  const combinedState: TranscriptionState = {
    isLoading: activeHook?.isLoading || false,
    isModelLoading: activeHook?.isModelLoading || false,
    error: activeHook?.error || null,
    progress: activeHook?.progress || 0,
    currentMode,
  };

  return {
    ...combinedState,
    transcribe,
    isModelReady: activeHook?.isModelReady || false,
    availableModes,
    switchMode,
  };
}