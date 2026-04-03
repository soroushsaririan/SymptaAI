import axios, { AxiosError } from "axios";
import Cookies from "js-cookie";
import type {
  Patient, Report, LabResult, AgentRun, Token, User,
  MedicalRecord, PaginatedResponse,
} from "@/types";

const TOKEN_KEY = "sympta_token";

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1",
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = Cookies.get(TOKEN_KEY);
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      Cookies.remove(TOKEN_KEY);
      if (typeof window !== "undefined") window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

// Auth
export const authApi = {
  login: async (email: string, password: string): Promise<Token> => {
    const form = new FormData();
    form.append("username", email);
    form.append("password", password);
    const { data } = await api.post<Token>("/auth/token", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  },
  register: async (email: string, password: string, full_name: string, role: string): Promise<Token> => {
    const { data } = await api.post<Token>("/auth/register", { email, password, full_name, role });
    return data;
  },
  me: async (): Promise<User> => {
    const { data } = await api.get<User>("/auth/me");
    return data;
  },
};

// Patients
export const patientsApi = {
  list: async (params?: { limit?: number; offset?: number; q?: string }): Promise<PaginatedResponse<Patient>> => {
    const { data } = await api.get<PaginatedResponse<Patient>>("/patients", { params });
    return data;
  },
  get: async (id: string): Promise<Patient> => {
    const { data } = await api.get<Patient>(`/patients/${id}`);
    return data;
  },
  create: async (payload: unknown): Promise<Patient> => {
    const { data } = await api.post<Patient>("/patients", payload);
    return data;
  },
  update: async (id: string, payload: unknown): Promise<Patient> => {
    const { data } = await api.put<Patient>(`/patients/${id}`, payload);
    return data;
  },
  intake: async (id: string, payload: unknown): Promise<Patient> => {
    const { data } = await api.post<Patient>(`/patients/${id}/intake`, payload);
    return data;
  },
  summary: async (id: string): Promise<unknown> => {
    const { data } = await api.get(`/patients/${id}/summary`);
    return data;
  },
};

// Analysis
export const analysisApi = {
  start: async (payload: { patient_id: string; analysis_type?: string; include_labs?: boolean; include_records?: boolean }): Promise<AgentRun> => {
    const { data } = await api.post<AgentRun>("/analysis/run", payload);
    return data;
  },
  get: async (runId: string): Promise<AgentRun> => {
    const { data } = await api.get<AgentRun>(`/analysis/${runId}/status`);
    return data;
  },
  history: async (patientId: string): Promise<AgentRun[]> => {
    const { data } = await api.get<AgentRun[]>(`/analysis/history/${patientId}`);
    return data;
  },
  streamUrl: (runId: string): string => {
    const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
    const token = Cookies.get(TOKEN_KEY) || "";
    return `${base}/analysis/${runId}/stream?token=${encodeURIComponent(token)}`;
  },
};

// Reports
export const reportsApi = {
  list: async (params?: { patient_id?: string; report_type?: string; limit?: number; offset?: number }): Promise<PaginatedResponse<Report>> => {
    const { data } = await api.get<PaginatedResponse<Report>>("/reports", { params });
    return data;
  },
  get: async (id: string): Promise<Report> => {
    const { data } = await api.get<Report>(`/reports/${id}`);
    return data;
  },
  addNotes: async (id: string, notes: string): Promise<Report> => {
    const { data } = await api.post<Report>(`/reports/${id}/review`, { notes });
    return data;
  },
  exportPdf: async (id: string): Promise<Blob> => {
    const { data } = await api.get(`/reports/${id}/export`, { responseType: "blob" });
    return data;
  },
  exportPdfUrl: (id: string): string =>
    `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/reports/${id}/export`,
};

// Labs
export const labsApi = {
  list: async (patientId?: string, params?: { limit?: number; offset?: number }): Promise<PaginatedResponse<LabResult>> => {
    const { data } = await api.get<PaginatedResponse<LabResult>>("/labs", { params: { ...(patientId ? { patient_id: patientId } : {}), ...params } });
    return data;
  },
  critical: async (patientId: string): Promise<LabResult[]> => {
    const { data } = await api.get<LabResult[]>(`/labs/patient/${patientId}/critical`);
    return data;
  },
  create: async (payload: unknown): Promise<LabResult> => {
    const { data } = await api.post<LabResult>("/labs", payload);
    return data;
  },
};

// Records
export const recordsApi = {
  list: async (patientId: string, params?: { limit?: number; offset?: number }): Promise<PaginatedResponse<MedicalRecord>> => {
    const { data } = await api.get<PaginatedResponse<MedicalRecord>>("/records", { params: { patient_id: patientId, ...params } });
    return data;
  },
  upload: async (formData: FormData): Promise<MedicalRecord> => {
    const { data } = await api.post<MedicalRecord>("/records/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  },
};

export { TOKEN_KEY };
