import { useState, useRef, useCallback } from "react";

// Define simplified types for Whisper pipeline
type WhisperPipeline = (audio: any, options?: any) => Promise<{ text: string }>;

export interface TranscriptionState {
  isLoading: boolean;
  isModelLoading: boolean;
  error: string | null;
  progress: number;
}

export interface TranscriptionResult {
  text: string;
  language?: string;
  confidence?: number;
}

export interface UseWhisperTranscriptionReturn extends TranscriptionState {
  transcribe: (audioBlob: Blob) => Promise<TranscriptionResult | null>;
  isModelReady: boolean;
}

export function useWhisperTranscription(): UseWhisperTranscriptionReturn {
  const [state, setState] = useState<TranscriptionState>({
    isLoading: false,
    isModelLoading: false,
    error: null,
    progress: 0,
  });

  const modelRef = useRef<WhisperPipeline | null>(null);
  const isModelReadyRef = useRef(false);

  // Convert audio blob to the format expected by Whisper
  const convertAudioBlobToArray = useCallback(
    async (blob: Blob): Promise<Float32Array> => {
      try {
        // Convert blob to array buffer
        const arrayBuffer = await blob.arrayBuffer();

        // Create audio context
        const audioContext = new AudioContext({ sampleRate: 16000 });

        // Decode audio data
        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

        // Get the first channel (mono)
        const float32Array = audioBuffer.getChannelData(0);

        // Close audio context to free resources
        await audioContext.close();

        return float32Array;
      } catch (error) {
        console.error("Error converting audio blob:", error);
        throw new Error("Failed to process audio data");
      }
    },
    [],
  );

  // Load the Whisper model
  const loadModel = useCallback(async () => {
    if (modelRef.current || isModelReadyRef.current) {
      return modelRef.current;
    }

    setState((prev) => ({
      ...prev,
      isModelLoading: true,
      error: null,
      progress: 0,
    }));

    try {
      // Dynamic import to avoid loading transformers until needed
      const { pipeline } = await import("@huggingface/transformers");

      // Load Whisper Large v3 Turbo model
      const transcriber = (await pipeline(
        "automatic-speech-recognition",
        "openai/whisper-large-v3-turbo",
        {
          dtype: {
            encoder_model: "fp32",
            decoder_model_merged: "q4", // Quantized for better performance
          },
          device: "webgpu", // Use WebGPU if available, fallback to CPU
          progress_callback: (progress: any) => {
            if (progress.status === "downloading") {
              const percent = Math.round(
                (progress.loaded / progress.total) * 100,
              );
              setState((prev) => ({ ...prev, progress: percent }));
            }
          },
        },
      )) as any;

      modelRef.current = transcriber;
      isModelReadyRef.current = true;

      setState((prev) => ({
        ...prev,
        isModelLoading: false,
        progress: 100,
      }));

      return transcriber;
    } catch (error) {
      console.error("Error loading Whisper model:", error);
      setState((prev) => ({
        ...prev,
        isModelLoading: false,
        error:
          error instanceof Error
            ? error.message
            : "Failed to load speech recognition model",
        progress: 0,
      }));
      return null;
    }
  }, []);

  // Transcribe audio blob
  const transcribe = useCallback(
    async (audioBlob: Blob): Promise<TranscriptionResult | null> => {
      if (!audioBlob || audioBlob.size === 0) {
        setState((prev) => ({ ...prev, error: "No audio data provided" }));
        return null;
      }

      setState((prev) => ({ ...prev, isLoading: true, error: null }));

      try {
        // Load model if not already loaded
        const model = await loadModel();
        if (!model) {
          throw new Error("Failed to load speech recognition model");
        }

        // Convert audio blob to Float32Array
        const audioArray = await convertAudioBlobToArray(audioBlob);

        // Transcribe with language detection
        const result = await model(audioArray, {
          task: "transcribe",
          language: "auto", // Auto-detect language (supports French and English)
          return_timestamps: false,
          chunk_length_s: 30,
          stride_length_s: 5,
        });

        setState((prev) => ({ ...prev, isLoading: false }));

        return {
          text: result.text?.trim() || "",
          language: result.language,
          confidence: result.confidence,
        };
      } catch (error) {
        console.error("Error during transcription:", error);
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error:
            error instanceof Error ? error.message : "Transcription failed",
        }));
        return null;
      }
    },
    [loadModel, convertAudioBlobToArray],
  );

  return {
    ...state,
    transcribe,
    isModelReady: isModelReadyRef.current,
  };
}
