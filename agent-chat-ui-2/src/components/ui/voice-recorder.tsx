import React, { useCallback, useEffect, useState } from "react";
import { Button } from "./button";
import {
  Mic,
  MicOff,
  Square,
  Loader2,
  AlertCircle,
  Check,
  Download,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAudioRecorder } from "@/hooks/use-audio-recorder";
import { useSpeechTranscription } from "@/hooks/use-speech-transcription";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "./tooltip";

// Configuration URL (same as sidebar configuration button)
const CONFIG_URL = "http://localhost:3004";

export interface VoiceRecorderProps {
  onTranscription: (text: string) => void;
  onError?: (error: string) => void;
  className?: string;
  disabled?: boolean;
}

export function VoiceRecorder({
  onTranscription,
  onError,
  className,
  disabled = false,
}: VoiceRecorderProps) {
  const {
    isRecording,
    isProcessing: isRecordingProcessing,
    audioLevel,
    duration,
    error: recordingError,
    isSupported,
    startRecording,
    stopRecording,
    cancelRecording,
  } = useAudioRecorder();

  const {
    isLoading: isTranscribing,
    isModelLoading,
    error: transcriptionError,
    progress: modelLoadProgress,
    transcribe,
    isModelReady,
  } = useSpeechTranscription();

  const [recordingState, setRecordingState] = useState<
    "idle" | "recording" | "processing" | "transcribing"
  >("idle");

  // Handle recording button click
  const handleRecordingToggle = useCallback(async () => {
    if (disabled) return;

    if (isRecording) {
      // Stop recording and start transcription
      setRecordingState("processing");
      const audioBlob = await stopRecording();

      if (audioBlob) {
        setRecordingState("transcribing");
        const result = await transcribe(audioBlob);

        if (result?.text) {
          onTranscription(result.text);
          setRecordingState("idle");
        } else {
          setRecordingState("idle");
        }
      } else {
        setRecordingState("idle");
      }
    } else {
      // Start recording
      setRecordingState("recording");
      await startRecording();
    }
  }, [
    disabled,
    isRecording,
    stopRecording,
    startRecording,
    transcribe,
    onTranscription,
  ]);

  // Handle cancel recording
  const handleCancel = useCallback(() => {
    cancelRecording();
    setRecordingState("idle");
  }, [cancelRecording]);

  // Handle errors
  useEffect(() => {
    const error = recordingError || transcriptionError;
    if (error && onError) {
      onError(error);
    }
  }, [recordingError, transcriptionError, onError]);

  // Format duration for display
  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  // Generate waveform visualization
  const WaveformVisualizer = () => {
    if (!isRecording) return null;

    const bars = Array.from({ length: 20 }, (_, i) => {
      const height = Math.max(2, audioLevel * 24 + Math.random() * 4);
      return (
        <div
          key={i}
          className="bg-primary w-0.5 rounded-full transition-all duration-75 ease-out"
          style={{ height: `${height}px` }}
        />
      );
    });

    return <div className="flex h-6 items-center gap-0.5">{bars}</div>;
  };

  // Don't render if not supported
  if (!isSupported) {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              disabled
              className={cn("p-2", className)}
            >
              <MicOff className="text-muted-foreground h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            Voice recording not supported in this browser
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  // Show model loading state
  if (isModelLoading) {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              disabled
              className={cn("p-2", className)}
            >
              <div className="flex items-center gap-2">
                <Download className="h-4 w-4 animate-pulse" />
                <span className="text-xs">{modelLoadProgress}%</span>
              </div>
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            <div className="flex flex-col gap-1">
              <span>Downloading browser model... {modelLoadProgress}%</span>
              <span className="text-xs text-muted-foreground">~450MB, persists in cache</span>
              <a
                href={CONFIG_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-400 hover:text-blue-300 underline text-xs"
              >
                Switch to API mode →
              </a>
            </div>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  // Recording state
  if (recordingState === "recording") {
    return (
      <div className="flex items-center gap-3 rounded-lg border border-red-200 bg-red-50 p-2">
        <Button
          onClick={handleRecordingToggle}
          variant="destructive"
          size="sm"
          className="animate-pulse p-2"
        >
          <Square className="h-4 w-4" />
        </Button>

        <WaveformVisualizer />

        <span className="font-mono text-sm text-red-600">
          {formatDuration(duration)}
        </span>

        <Button
          onClick={handleCancel}
          variant="ghost"
          size="sm"
          className="p-1 text-red-600 hover:text-red-800"
        >
          <AlertCircle className="h-3 w-3" />
        </Button>
      </div>
    );
  }

  // Processing states
  if (recordingState === "processing" || recordingState === "transcribing") {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              disabled
              className={cn("p-2", className)}
            >
              <Loader2 className="h-4 w-4 animate-spin" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            {recordingState === "processing"
              ? "Processing audio..."
              : "Transcribing speech..."}
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  // Default idle state
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            onClick={handleRecordingToggle}
            variant="ghost"
            size="sm"
            disabled={disabled || !isModelReady}
            className={cn(
              "hover:bg-primary/10 p-2 transition-colors",
              !isModelReady && "opacity-50",
              className,
            )}
          >
            <Mic className="h-4 w-4" />
          </Button>
        </TooltipTrigger>
        <TooltipContent>
          {transcriptionError === 'API_KEY_MISSING'
            ? (<div className="flex flex-col gap-1">
                <span>OpenAI API key not configured</span>
                <a
                  href={CONFIG_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-400 hover:text-blue-300 underline text-sm"
                >
                  Configure now →
                </a>
              </div>)
            : 'Voice recording - French/English supported'}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
