import { getAccessToken, getRefreshToken, setTokens, clearTokens } from "./auth";
import type {
  TokenResponse, MeResponse, Patient, Consultation,
  ConsultationListItem, ConsultationStatus,
} from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  retry = true,
): Promise<T> {
  const token = getAccessToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE}${path}`, { ...options, headers });

  if (res.status === 401 && retry) {
    const refreshed = await tryRefresh();
    if (refreshed) return request<T>(path, options, false);
    clearTokens();
    window.location.href = "/login";
    throw new ApiError(401, "Session expired");
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, body.detail ?? res.statusText);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

async function tryRefresh(): Promise<boolean> {
  const rt = getRefreshToken();
  if (!rt) return false;
  try {
    const res = await fetch(`${BASE}/api/v1/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: rt }),
    });
    if (!res.ok) return false;
    const data: TokenResponse = await res.json();
    setTokens(data.access_token, data.refresh_token);
    return true;
  } catch {
    return false;
  }
}

// ── Auth ─────────────────────────────────────────────────────────────────────

export const auth = {
  register: (body: {
    email: string; password: string; full_name: string;
    phone?: string; clinic_name?: string; specialization?: string;
  }) => request<TokenResponse>("/api/v1/auth/register", {
    method: "POST", body: JSON.stringify(body),
  }),

  login: (email: string, password: string) =>
    request<TokenResponse>("/api/v1/auth/login", {
      method: "POST", body: JSON.stringify({ email, password }),
    }),

  logout: (refresh_token: string) =>
    request<void>("/api/v1/auth/logout", {
      method: "POST", body: JSON.stringify({ refresh_token }),
    }),

  me: () => request<MeResponse>("/api/v1/auth/me"),
};

// ── Patients ──────────────────────────────────────────────────────────────────

export const patients = {
  list: (q?: string) =>
    request<Patient[]>(`/api/v1/patients${q ? `?q=${encodeURIComponent(q)}` : ""}`),

  create: (body: { name: string; age?: number; sex?: string; phone?: string }) =>
    request<Patient>("/api/v1/patients", { method: "POST", body: JSON.stringify(body) }),

  get: (id: string) => request<Patient>(`/api/v1/patients/${id}`),
};

// ── Consultations ─────────────────────────────────────────────────────────────

export const consultations = {
  list: (skip = 0, limit = 20) =>
    request<ConsultationListItem[]>(`/api/v1/consultations?skip=${skip}&limit=${limit}`),

  create: (body: {
    patient_name: string; patient_age?: number;
    patient_sex?: string; patient_id?: string;
  }) => request<Consultation>("/api/v1/consultations", {
    method: "POST", body: JSON.stringify(body),
  }),

  get: (id: string) => request<Consultation>(`/api/v1/consultations/${id}`),

  getStatus: (id: string) =>
    request<{ id: string; status: ConsultationStatus; error_message: string | null }>(
      `/api/v1/consultations/${id}/status`
    ),

  getUploadUrl: (id: string) =>
    request<{ upload_url: string; storage_key: string; consultation_id: string }>(
      `/api/v1/consultations/${id}/upload-url`,
      { method: "POST" }
    ),

  uploadAudio: async (uploadUrl: string, blob: Blob): Promise<void> => {
    const res = await fetch(uploadUrl, {
      method: "PUT",
      body: blob,
      headers: { "Content-Type": "audio/webm" },
    });
    if (!res.ok) throw new ApiError(res.status, "Audio upload failed");
  },

  process: (id: string) =>
    request<{ message: string }>(`/api/v1/consultations/${id}/process`, { method: "POST" }),

  approve: (id: string, body: {
    subjective: string; objective: string; assessment: string; plan: string;
    edit_time_seconds?: number; generated_note_id: string;
  }) => request<Consultation["approved_note"]>(`/api/v1/consultations/${id}/approve`, {
    method: "PUT", body: JSON.stringify(body),
  }),

  regenerate: (id: string) =>
    request<{ message: string }>(`/api/v1/consultations/${id}/regenerate`, { method: "POST" }),

  getPdfUrl: (id: string) => `${BASE}/api/v1/consultations/${id}/pdf`,
};

export { ApiError };
