import { useState, useRef, useCallback, useEffect } from "react";

export interface AudioRecorderState {
  isRecording: boolean;
  isProcessing: boolean;
  audioLevel: number;
  duration: number;
  error: string | null;
}

export interface AudioRecorderActions {
  startRecording: () => Promise<void>;
  stopRecording: () => Promise<Blob | null>;
  cancelRecording: () => void;
}

export interface UseAudioRecorderReturn
  extends AudioRecorderState,
    AudioRecorderActions {
  isSupported: boolean;
}

export function useAudioRecorder(): UseAudioRecorderReturn {
  const [state, setState] = useState<AudioRecorderState>({
    isRecording: false,
    isProcessing: false,
    audioLevel: 0,
    duration: 0,
    error: null,
  });

  const [isSupported, setIsSupported] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const animationFrameRef = useRef<number | null>(null);
  const startTimeRef = useRef<number | null>(null);
  const isRecordingRef = useRef(false);

  // Check if audio recording is supported (client-side only to prevent hydration mismatch)
  useEffect(() => {
    const checkSupport = () => {
      const supported = !!(
        typeof navigator !== "undefined" &&
        navigator.mediaDevices &&
        typeof navigator.mediaDevices.getUserMedia === "function" &&
        typeof window !== "undefined" &&
        window.MediaRecorder &&
        window.AudioContext
      );
      setIsSupported(supported);
    };

    checkSupport();
  }, []);

  // Update audio level and duration
  const updateAudioVisualization = useCallback(() => {
    if (!analyserRef.current || !isRecordingRef.current) {
      console.log(
        "🎤 [Visualization] Skipping - analyser:",
        !!analyserRef.current,
        "recording:",
        isRecordingRef.current,
      );
      return;
    }

    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
    analyserRef.current.getByteFrequencyData(dataArray);

    // Calculate average volume level (0-1)
    const average =
      dataArray.reduce((sum, value) => sum + value, 0) / dataArray.length;
    const normalizedLevel = average / 255;

    // Update duration
    const currentTime = Date.now();
    const duration = startTimeRef.current
      ? (currentTime - startTimeRef.current) / 1000
      : 0;

    // Log audio level for debugging
    if (Math.random() < 0.1) {
      // Log 10% of the time to avoid spam
      console.log(
        "🎤 [Visualization] Audio level:",
        normalizedLevel.toFixed(3),
        "duration:",
        duration.toFixed(1) + "s",
      );
    }

    setState((prev) => ({
      ...prev,
      audioLevel: normalizedLevel,
      duration,
    }));

    if (isRecordingRef.current) {
      animationFrameRef.current = requestAnimationFrame(
        updateAudioVisualization,
      );
    }
  }, []);

  // Start recording
  const startRecording = useCallback(async () => {
    console.log("🎤 [Audio Recorder] Starting recording...");
    console.log("🎤 [Audio Recorder] isSupported:", isSupported);

    if (!isSupported) {
      console.error("🎤 [Audio Recorder] Browser not supported");
      setState((prev) => ({
        ...prev,
        error: "Audio recording is not supported in this browser",
      }));
      return;
    }

    try {
      console.log("🎤 [Audio Recorder] Setting processing state...");
      setState((prev) => ({ ...prev, error: null, isProcessing: true }));

      console.log("🎤 [Audio Recorder] Requesting microphone permission...");
      // Get user media
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000, // Whisper prefers 16kHz
        },
      });

      console.log("🎤 [Audio Recorder] Microphone access granted!", stream);

      streamRef.current = stream;

      // Create audio context for visualization
      console.log("🎤 [Audio Recorder] Creating audio context...");
      const audioContext = new AudioContext({ sampleRate: 16000 });
      audioContextRef.current = audioContext;
      console.log(
        "🎤 [Audio Recorder] Audio context created:",
        audioContext.state,
      );

      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 256;
      analyser.smoothingTimeConstant = 0.8;

      source.connect(analyser);
      analyserRef.current = analyser;
      console.log("🎤 [Audio Recorder] Audio analysis setup complete");

      // Create media recorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
          ? "audio/webm;codecs=opus"
          : "audio/webm",
      });

      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      console.log("🎤 [Audio Recorder] Starting media recorder...");
      mediaRecorder.start(100); // Collect data every 100ms
      startTimeRef.current = Date.now();

      console.log("🎤 [Audio Recorder] Setting recording state to true...");
      isRecordingRef.current = true;
      setState((prev) => ({
        ...prev,
        isRecording: true,
        isProcessing: false,
        duration: 0,
        audioLevel: 0,
      }));

      // Start visualization loop
      console.log("🎤 [Audio Recorder] Starting visualization loop...");
      updateAudioVisualization();
    } catch (error) {
      console.error("Error starting recording:", error);
      setState((prev) => ({
        ...prev,
        error:
          error instanceof Error ? error.message : "Failed to start recording",
        isProcessing: false,
      }));
    }
  }, [isSupported, updateAudioVisualization]);

  // Stop recording
  const stopRecording = useCallback(async (): Promise<Blob | null> => {
    if (!mediaRecorderRef.current || !isRecordingRef.current) {
      return null;
    }

    return new Promise((resolve) => {
      const mediaRecorder = mediaRecorderRef.current!;

      setState((prev) => ({ ...prev, isProcessing: true }));

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(chunksRef.current, {
          type: mediaRecorder.mimeType || "audio/webm",
        });

        // Cleanup
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((track) => track.stop());
          streamRef.current = null;
        }

        if (audioContextRef.current) {
          audioContextRef.current.close();
          audioContextRef.current = null;
        }

        if (animationFrameRef.current) {
          cancelAnimationFrame(animationFrameRef.current);
          animationFrameRef.current = null;
        }

        isRecordingRef.current = false;
        setState((prev) => ({
          ...prev,
          isRecording: false,
          isProcessing: false,
          audioLevel: 0,
          duration: 0,
        }));

        resolve(audioBlob);
      };

      mediaRecorder.stop();
    });
  }, []);

  // Cancel recording
  const cancelRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecordingRef.current) {
      mediaRecorderRef.current.stop();
      chunksRef.current = [];
    }

    // Cleanup
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }

    isRecordingRef.current = false;
    setState((prev) => ({
      ...prev,
      isRecording: false,
      isProcessing: false,
      audioLevel: 0,
      duration: 0,
    }));
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cancelRecording();
    };
  }, [cancelRecording]);

  return {
    ...state,
    isSupported,
    startRecording,
    stopRecording,
    cancelRecording,
  };
}
