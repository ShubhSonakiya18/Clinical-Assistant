"use client";

import { useEffect, useState, useCallback } from "react";
import { consultations } from "@/lib/api";
import type { ConsultationStatus } from "@/lib/types";
import { Loader2, AlertCircle } from "lucide-react";

interface Props {
  consultationId: string;
  onReady: () => void;
  onFailed: (error: string) => void;
}

const STEPS: { statuses: ConsultationStatus[]; label: string }[] = [
  { statuses: ["uploading", "uploaded"], label: "Uploading audio" },
  { statuses: ["transcribing", "transcribed"], label: "Transcribing consultation" },
  { statuses: ["generating"], label: "Generating clinical note" },
];

export default function ProcessingScreen({ consultationId, onReady, onFailed }: Props) {
  const [status, setStatus] = useState<ConsultationStatus>("uploaded");
  const [error, setError] = useState<string | null>(null);

  const poll = useCallback(async () => {
    try {
      const data = await consultations.getStatus(consultationId);
      setStatus(data.status);

      if (data.status === "generated") {
        onReady();
        return;
      }
      if (data.status === "failed") {
        const msg = data.error_message ?? "Processing failed. Please try again.";
        setError(msg);
        onFailed(msg);
        return;
      }
      // Keep polling
      setTimeout(poll, 2000);
    } catch {
      setTimeout(poll, 3000);
    }
  }, [consultationId, onReady, onFailed]);

  useEffect(() => {
    const t = setTimeout(poll, 1000);
    return () => clearTimeout(t);
  }, [poll]);

  if (error) {
    return (
      <div className="flex flex-col items-center gap-3 py-10">
        <AlertCircle size={32} className="text-red-400" />
        <p className="text-red-600 font-medium text-sm">{error}</p>
      </div>
    );
  }

  const activeStepIndex = STEPS.findIndex((s) => s.statuses.includes(status));

  return (
    <div className="flex flex-col items-center gap-6 py-10">
      <Loader2 size={36} className="animate-spin text-blue-500" />
      <div className="w-full max-w-xs space-y-3">
        {STEPS.map((step, i) => {
          const done = activeStepIndex > i;
          const active = activeStepIndex === i;
          return (
            <div key={step.label} className="flex items-center gap-3">
              <div className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 ${
                done ? "bg-green-500 text-white" :
                active ? "bg-blue-500 text-white" :
                "bg-gray-100 text-gray-400"
              }`}>
                {done ? "✓" : i + 1}
              </div>
              <span className={`text-sm ${active ? "text-gray-900 font-medium" : done ? "text-gray-400 line-through" : "text-gray-300"}`}>
                {step.label}
              </span>
              {active && <Loader2 size={12} className="animate-spin text-blue-400" />}
            </div>
          );
        })}
      </div>
      <p className="text-xs text-gray-400">Usually takes 15–25 seconds</p>
    </div>
  );
}
