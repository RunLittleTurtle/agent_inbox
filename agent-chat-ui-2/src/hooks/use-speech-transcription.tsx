import { useOpenAITranscription } from './use-openai-transcription';

export type { TranscriptionResult, TranscriptionState } from './use-openai-transcription';

/**
 * Speech transcription hook - uses OpenAI Whisper API
 *
 * Configure OPENAI_API_KEY in root .env file
 *
 * @returns Transcription hook with API-based transcription
 */
export function useSpeechTranscription() {
  return useOpenAITranscription();
}
