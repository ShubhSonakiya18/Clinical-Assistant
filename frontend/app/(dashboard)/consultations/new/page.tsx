"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { consultations } from "@/lib/api";
import { ApiError } from "@/lib/api";
import AudioRecorder from "@/components/consultation/AudioRecorder";
import ProcessingScreen from "@/components/consultation/ProcessingScreen";

const schema = z.object({
  patient_name: z.string().min(1, "Patient name is required"),
  patient_age: z.coerce.number().int().positive().optional().or(z.literal("")),
  patient_sex: z.enum(["M", "F", "Other", ""]).optional(),
});
type FormData = z.infer<typeof schema>;

type Stage = "form" | "recording" | "processing" | "done";

export default function NewConsultationPage() {
  const router = useRouter();
  const [stage, setStage] = useState<Stage>("form");
  const [consultationId, setConsultationId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    getValues,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  async function onFormSubmit() {
    setStage("recording");
  }

  async function handleRecordingComplete(blob: Blob) {
    setError(null);
    try {
      const values = getValues();
      // 1. Create consultation record
      const c = await consultations.create({
        patient_name: values.patient_name,
        patient_age: values.patient_age ? Number(values.patient_age) : undefined,
        patient_sex: values.patient_sex || undefined,
      });
      setConsultationId(c.id);

      // 2. Get presigned upload URL
      const { upload_url } = await consultations.getUploadUrl(c.id);

      // 3. Upload audio directly to R2
      await consultations.uploadAudio(upload_url, blob);

      // 4. Tell backend to start processing
      await consultations.process(c.id);

      setStage("processing");
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : "Something went wrong. Please try again.";
      if (msg.includes("quota")) {
        setError("You've used all your free consultations this month. Please upgrade to Pro.");
      } else {
        setError(msg);
      }
      setStage("form");
    }
  }

  function handleProcessingReady() {
    if (consultationId) {
      router.push(`/consultations/${consultationId}`);
    }
  }

  return (
    <div className="p-8 max-w-xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">New Consultation</h1>
        <p className="text-gray-500 text-sm mt-1">Record consultation audio to generate a clinical note</p>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-6">
        {stage === "form" && (
          <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Patient name <span className="text-red-500">*</span>
              </label>
              <input
                {...register("patient_name")}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Full name"
              />
              {errors.patient_name && (
                <p className="text-red-500 text-xs mt-1">{errors.patient_name.message}</p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Age</label>
                <input
                  {...register("patient_age")}
                  type="number"
                  min="0"
                  max="120"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g. 45"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Sex</label>
                <select
                  {...register("patient_sex")}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                >
                  <option value="">—</option>
                  <option value="M">Male</option>
                  <option value="F">Female</option>
                  <option value="Other">Other</option>
                </select>
              </div>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg px-3 py-2 text-sm text-red-600">
                {error}
              </div>
            )}

            <button
              type="submit"
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 rounded-lg text-sm transition-colors"
            >
              Continue to Recording
            </button>
          </form>
        )}

        {stage === "recording" && (
          <div>
            <div className="mb-4 bg-blue-50 border border-blue-100 rounded-lg px-4 py-3">
              <p className="text-sm text-blue-800 font-medium">{getValues("patient_name")}</p>
              {getValues("patient_age") && (
                <p className="text-xs text-blue-500">
                  {getValues("patient_age")} yrs {getValues("patient_sex") && `/ ${getValues("patient_sex")}`}
                </p>
              )}
            </div>
            <AudioRecorder onRecordingComplete={handleRecordingComplete} />
          </div>
        )}

        {stage === "processing" && consultationId && (
          <ProcessingScreen
            consultationId={consultationId}
            onReady={handleProcessingReady}
            onFailed={(msg) => {
              setError(msg);
              setStage("form");
            }}
          />
        )}
      </div>
    </div>
  );
}
