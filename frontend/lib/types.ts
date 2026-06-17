export interface User {
  id: string;
  email: string;
  full_name: string;
  phone: string | null;
  is_active: boolean;
  created_at: string;
}

export interface Doctor {
  id: string;
  specialization: string;
  clinic_name: string | null;
  preferred_language: string;
  subscription_tier: "free" | "pro";
  consultations_this_month: number;
  free_quota: number;
}

export interface Patient {
  id: string;
  name: string;
  age: number | null;
  sex: string | null;
  phone: string | null;
  created_at: string;
}

export interface Transcript {
  raw_text: string;
  detected_language: string | null;
  processing_time_ms: number | null;
}

export interface GeneratedNote {
  id: string;
  subjective: string | null;
  objective: string | null;
  assessment: string | null;
  plan: string | null;
  missing_information: string[];
  ai_model: string;
  generation_time_ms: number | null;
  created_at: string;
}

export interface ApprovedNote {
  id: string;
  subjective: string | null;
  objective: string | null;
  assessment: string | null;
  plan: string | null;
  was_edited: boolean;
  edit_time_seconds: number | null;
  fields_edited: string[];
  approved_at: string;
  pdf_storage_key: string | null;
}

export type ConsultationStatus =
  | "created"
  | "uploading"
  | "uploaded"
  | "transcribing"
  | "transcribed"
  | "generating"
  | "generated"
  | "approved"
  | "failed";

export interface Consultation {
  id: string;
  patient_name: string;
  patient_age: number | null;
  patient_sex: string | null;
  consultation_date: string;
  status: ConsultationStatus;
  error_message: string | null;
  chief_complaint: string | null;
  transcript: Transcript | null;
  generated_note: GeneratedNote | null;
  approved_note: ApprovedNote | null;
  created_at: string;
}

export interface ConsultationListItem {
  id: string;
  patient_name: string;
  patient_age: number | null;
  consultation_date: string;
  status: ConsultationStatus;
  chief_complaint: string | null;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface MeResponse {
  user: User;
  doctor: Doctor;
}
