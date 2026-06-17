"use client";

import { useState, useRef, useCallback } from "react";
import { Mic, Square, Upload, Loader2 } from "lucide-react";

interface Props {
  onRecordingComplete: (blob: Blob) => void;
  disabled?: boolean;
}

type RecorderState = "idle" | "recording" | "stopped";

export default function AudioRecorder({ onRecordingComplete, disabled }: Props) {
  const [state, setState] = useState<RecorderState>("idle");
  const [seconds, setSeconds] = useState(0);
  const [fileMode, setFileMode] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
      mediaRecorderRef.current = recorder;
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        stream.getTracks().forEach((t) => t.stop());
        onRecordingComplete(blob);
        setState("stopped");
      };

      recorder.start(250);
      setState("recording");
      setSeconds(0);
      timerRef.current = setInterval(() => setSeconds((s) => s + 1), 1000);
    } catch {
      alert("Microphone access denied. Please allow microphone access and try again.");
    }
  }, [onRecordingComplete]);

  const stopRecording = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    mediaRecorderRef.current?.stop();
  }, []);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    onRecordingComplete(file);
    setState("stopped");
  }

  function formatTime(s: number) {
    const m = Math.floor(s / 60).toString().padStart(2, "0");
    const sec = (s % 60).toString().padStart(2, "0");
    return `${m}:${sec}`;
  }

  if (fileMode) {
    return (
      <div className="flex flex-col items-center gap-4 py-6">
        <input
          ref={fileInputRef}
          type="file"
          accept="audio/*"
          className="hidden"
          onChange={handleFileChange}
        />
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled}
          className="flex items-center gap-2 border-2 border-dashed border-gray-300 rounded-xl px-8 py-6 text-gray-500 hover:border-blue-400 hover:text-blue-500 transition-colors disabled:opacity-50"
        >
          <Upload size={20} />
          <span className="text-sm font-medium">Click to upload audio file</span>
        </button>
        <button
          onClick={() => setFileMode(false)}
          className="text-xs text-gray-400 hover:text-blue-500"
        >
          Switch to microphone recording
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center gap-4 py-6">
      {state === "idle" && (
        <>
          <button
            onClick={startRecording}
            disabled={disabled}
            className="w-20 h-20 rounded-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center text-white shadow-lg transition-all hover:scale-105 active:scale-95"
          >
            <Mic size={32} />
          </button>
          <p className="text-sm text-gray-500">Click to start recording</p>
          <button
            onClick={() => setFileMode(true)}
            className="text-xs text-gray-400 hover:text-blue-500"
          >
            Or upload a file instead
          </button>
        </>
      )}

      {state === "recording" && (
        <>
          <div className="relative">
            <div className="absolute inset-0 rounded-full bg-red-400 animate-ping opacity-30" />
            <button
              onClick={stopRecording}
              className="relative w-20 h-20 rounded-full bg-red-500 hover:bg-red-600 flex items-center justify-center text-white shadow-lg transition-all"
            >
              <Square size={28} />
            </button>
          </div>
          <p className="text-sm text-red-500 font-medium">Recording {formatTime(seconds)}</p>
          <p className="text-xs text-gray-400">Click to stop and generate note</p>
        </>
      )}

      {state === "stopped" && (
        <div className="flex items-center gap-2 text-green-600">
          <Loader2 size={18} className="animate-spin" />
          <span className="text-sm font-medium">Audio captured, processing...</span>
        </div>
      )}
    </div>
  );
}
