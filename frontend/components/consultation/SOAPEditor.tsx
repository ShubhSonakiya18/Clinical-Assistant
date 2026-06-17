"use client";

import { useState, useEffect, useRef } from "react";
import type { GeneratedNote } from "@/lib/types";
import { AlertTriangle } from "lucide-react";

interface Props {
  note: GeneratedNote;
  onApprove: (
    fields: { subjective: string; objective: string; assessment: string; plan: string },
    editTimeSeconds: number
  ) => void;
  onRegenerate: () => void;
  approving?: boolean;
}

const SECTIONS = [
  { key: "subjective" as const, label: "S — Subjective", hint: "Chief complaint & history of present illness" },
  { key: "objective" as const, label: "O — Objective", hint: "Examination findings & vitals" },
  { key: "assessment" as const, label: "A — Assessment", hint: "Diagnosis / clinical impression" },
  { key: "plan" as const, label: "P — Plan", hint: "Management plan, medications, follow-up" },
];

export default function SOAPEditor({ note, onApprove, onRegenerate, approving }: Props) {
  const [fields, setFields] = useState({
    subjective: note.subjective ?? "",
    objective: note.objective ?? "",
    assessment: note.assessment ?? "",
    plan: note.plan ?? "",
  });

  const startTimeRef = useRef(Date.now());

  // Sync if note changes (after regeneration)
  useEffect(() => {
    setFields({
      subjective: note.subjective ?? "",
      objective: note.objective ?? "",
      assessment: note.assessment ?? "",
      plan: note.plan ?? "",
    });
    startTimeRef.current = Date.now();
  }, [note.id]);

  function handleApprove() {
    const editTime = Math.round((Date.now() - startTimeRef.current) / 1000);
    onApprove(fields, editTime);
  }

  return (
    <div className="space-y-4">
      {note.missing_information.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 flex gap-2">
          <AlertTriangle size={16} className="text-amber-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-amber-800">Missing from recording:</p>
            <p className="text-xs text-amber-600 mt-0.5">{note.missing_information.join(", ")}</p>
          </div>
        </div>
      )}

      {SECTIONS.map(({ key, label, hint }) => (
        <div key={key} className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
            <div>
              <span className="text-sm font-semibold text-blue-700">{label}</span>
              <span className="text-xs text-gray-400 ml-2">{hint}</span>
            </div>
          </div>
          <textarea
            value={fields[key]}
            onChange={(e) => setFields((f) => ({ ...f, [key]: e.target.value }))}
            rows={4}
            className="w-full px-4 py-3 text-sm text-gray-800 resize-y focus:outline-none focus:ring-2 focus:ring-blue-200 font-mono leading-relaxed"
            placeholder={`Not documented.`}
          />
        </div>
      ))}

      <div className="flex gap-3 pt-2">
        <button
          onClick={handleApprove}
          disabled={approving}
          className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white font-medium py-2.5 rounded-lg text-sm transition-colors"
        >
          {approving ? "Approving..." : "Approve & Save"}
        </button>
        <button
          onClick={onRegenerate}
          disabled={approving}
          className="px-4 py-2.5 border border-gray-300 hover:bg-gray-50 text-gray-600 rounded-lg text-sm transition-colors"
        >
          Regenerate
        </button>
      </div>

      <p className="text-xs text-gray-400 text-center">
        Approved notes are locked and immutable. Review carefully before approving.
      </p>
    </div>
  );
}
