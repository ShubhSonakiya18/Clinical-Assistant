"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { consultations as consultationsApi } from "@/lib/api";
import type { Consultation } from "@/lib/types";
import { formatDateTime, statusLabel } from "@/lib/utils";
import SOAPEditor from "@/components/consultation/SOAPEditor";
import ProcessingScreen from "@/components/consultation/ProcessingScreen";
import {
  ArrowLeft, Download, Share2, CheckCircle, FileText, Mic
} from "lucide-react";

export default function ConsultationDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [consultation, setConsultation] = useState<Consultation | null>(null);
  const [loading, setLoading] = useState(true);
  const [approving, setApproving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchConsultation = useCallback(async () => {
    try {
      const data = await consultationsApi.get(id);
      setConsultation(data);
    } catch {
      setError("Failed to load consultation.");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { fetchConsultation(); }, [fetchConsultation]);

  async function handleApprove(
    fields: { subjective: string; objective: string; assessment: string; plan: string },
    editTimeSeconds: number
  ) {
    if (!consultation?.generated_note) return;
    setApproving(true);
    try {
      await consultationsApi.approve(id, {
        ...fields,
        edit_time_seconds: editTimeSeconds,
        generated_note_id: consultation.generated_note.id,
      });
      await fetchConsultation();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Approval failed");
    } finally {
      setApproving(false);
    }
  }

  async function handleRegenerate() {
    try {
      await consultationsApi.regenerate(id);
      setConsultation((c) => c ? { ...c, status: "transcribed" } : c);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Regeneration failed");
    }
  }

  function handleDownloadPdf() {
    const url = consultationsApi.getPdfUrl(id);
    const token = typeof window !== "undefined" ? localStorage.getItem("ca_access_token") : null;
    // Open in new tab — browser will use the Bearer token via the cookie-less approach
    // For MVP: fetch and trigger download
    fetch(url, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
      .then((r) => r.blob())
      .then((blob) => {
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = `clinical_note_${id.slice(0, 8)}.pdf`;
        a.click();
      });
  }

  function handleWhatsApp() {
    const pdfUrl = consultationsApi.getPdfUrl(id);
    window.open(`https://wa.me/?text=${encodeURIComponent(`Clinical note: ${pdfUrl}`)}`, "_blank");
  }

  if (loading) {
    return (
      <div className="p-8">
        <div className="animate-pulse space-y-4 max-w-2xl mx-auto">
          <div className="h-8 bg-gray-100 rounded w-1/2" />
          <div className="h-40 bg-gray-100 rounded-xl" />
          <div className="h-40 bg-gray-100 rounded-xl" />
        </div>
      </div>
    );
  }

  if (!consultation) {
    return (
      <div className="p-8 text-center text-gray-500">
        {error ?? "Consultation not found."}
      </div>
    );
  }

  const isProcessing = ["uploading", "uploaded", "transcribing", "transcribed", "generating"].includes(
    consultation.status
  );

  return (
    <div className="p-8 max-w-2xl mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <button
            onClick={() => router.push("/dashboard")}
            className="flex items-center gap-1 text-gray-400 hover:text-gray-600 text-sm mb-3"
          >
            <ArrowLeft size={15} /> Back
          </button>
          <h1 className="text-xl font-bold text-gray-900">{consultation.patient_name}</h1>
          <p className="text-sm text-gray-400 mt-0.5">
            {consultation.patient_age && `${consultation.patient_age}y`}
            {consultation.patient_sex && ` · ${consultation.patient_sex}`}
            {" · "}{formatDateTime(consultation.created_at)}
          </p>
        </div>
        <span className="text-xs font-medium px-3 py-1 rounded-full bg-gray-100 text-gray-600">
          {statusLabel(consultation.status)}
        </span>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm text-red-600 mb-4">
          {error}
        </div>
      )}

      {/* Processing state */}
      {isProcessing && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 mb-4">
          <ProcessingScreen
            consultationId={id}
            onReady={() => fetchConsultation()}
            onFailed={(msg) => setError(msg)}
          />
        </div>
      )}

      {/* Transcript */}
      {consultation.transcript && (
        <details className="bg-white rounded-xl border border-gray-200 mb-4 overflow-hidden">
          <summary className="px-5 py-3 cursor-pointer text-sm font-medium text-gray-700 flex items-center gap-2 hover:bg-gray-50">
            <Mic size={15} />
            View transcript
          </summary>
          <div className="px-5 pb-4">
            <p className="text-xs text-gray-400 mb-2">
              Provider: {consultation.transcript.transcription_provider ?? "unknown"} ·
              {consultation.transcript.processing_time_ms && ` ${consultation.transcript.processing_time_ms}ms`}
            </p>
            <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap font-mono bg-gray-50 rounded-lg p-3">
              {consultation.transcript.raw_text}
            </p>
          </div>
        </details>
      )}

      {/* SOAP Editor */}
      {consultation.status === "generated" && consultation.generated_note && (
        <div>
          <div className="flex items-center gap-2 mb-3">
            <FileText size={16} className="text-blue-500" />
            <h2 className="text-sm font-semibold text-gray-700">Clinical Note — Review & Approve</h2>
          </div>
          <SOAPEditor
            note={consultation.generated_note}
            onApprove={handleApprove}
            onRegenerate={handleRegenerate}
            approving={approving}
          />
        </div>
      )}

      {/* Approved note */}
      {consultation.status === "approved" && consultation.approved_note && (
        <div className="space-y-4">
          <div className="flex items-center gap-2 bg-green-50 border border-green-200 rounded-lg px-4 py-2.5">
            <CheckCircle size={16} className="text-green-600" />
            <p className="text-sm text-green-700 font-medium">
              Approved on {formatDateTime(consultation.approved_note.approved_at)}
              {consultation.approved_note.was_edited && " · Edited before approval"}
            </p>
          </div>

          {[
            { label: "S — Subjective", value: consultation.approved_note.subjective },
            { label: "O — Objective", value: consultation.approved_note.objective },
            { label: "A — Assessment", value: consultation.approved_note.assessment },
            { label: "P — Plan", value: consultation.approved_note.plan },
          ].map(({ label, value }) => (
            <div key={label} className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <div className="px-5 py-3 border-b border-gray-100">
                <span className="text-sm font-semibold text-blue-700">{label}</span>
              </div>
              <p className="px-5 py-4 text-sm text-gray-800 whitespace-pre-wrap leading-relaxed font-mono">
                {value || "Not documented."}
              </p>
            </div>
          ))}

          <div className="flex gap-3">
            <button
              onClick={handleDownloadPdf}
              className="flex items-center gap-2 flex-1 justify-center border border-gray-300 hover:bg-gray-50 text-gray-700 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors"
            >
              <Download size={15} />
              Download PDF
            </button>
            <button
              onClick={handleWhatsApp}
              className="flex items-center gap-2 flex-1 justify-center bg-green-500 hover:bg-green-600 text-white px-4 py-2.5 rounded-lg text-sm font-medium transition-colors"
            >
              <Share2 size={15} />
              Share via WhatsApp
            </button>
          </div>
        </div>
      )}

      {/* Failed state */}
      {consultation.status === "failed" && (
        <div className="bg-white rounded-xl border border-red-200 p-6 text-center">
          <p className="text-red-600 font-medium mb-1">Processing failed</p>
          <p className="text-gray-400 text-sm mb-4">
            {consultation.error_message ?? "An unexpected error occurred."}
          </p>
          <button
            onClick={handleRegenerate}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700"
          >
            Try Again
          </button>
        </div>
      )}
    </div>
  );
}
