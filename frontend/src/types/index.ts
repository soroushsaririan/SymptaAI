export interface User {
  id: string;
  email: string;
  full_name: string;
  role: "physician" | "nurse" | "admin" | "viewer";
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface Patient {
  id: string;
  mrn: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  gender: string;
  email?: string;
  phone?: string;
  address?: string | Record<string, string>;
  insurance_id?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  allergies: string[];
  current_medications: Medication[];
  medical_history: string[] | MedicalHistoryItem[];
  family_history: string[];
  chief_complaint?: string;
  symptoms: string[];
  vitals?: Vitals;
  intake_completed: boolean;
  created_at: string;
  updated_at: string;
}

export interface Medication {
  name: string;
  dose: string;
  frequency: string;
  route?: string;
  indication?: string;
}

export interface MedicalHistoryItem {
  condition: string;
  diagnosed_date?: string;
  status?: string;
}

export interface Vitals {
  blood_pressure?: string;
  blood_pressure_systolic?: number;
  blood_pressure_diastolic?: number;
  heart_rate?: number | string;
  temperature?: number | string;
  temperature_celsius?: number;
  respiratory_rate?: number | string;
  oxygen_saturation?: number | string;
  weight_kg?: number | string;
  height_cm?: number | string;
}

export interface MedicalRecord {
  id: string;
  patient_id: string;
  record_type: string;
  title?: string;
  chief_complaint?: string;
  summary?: string;
  provider_name?: string;
  content?: string;
  structured_summary?: Record<string, unknown>;
  file_url?: string;
  file_type?: string;
  processed: boolean;
  created_at: string;
}

export interface LabResult {
  id: string;
  patient_id: string;
  test_name: string;
  test_code?: string;
  value: string;
  unit?: string;
  reference_range?: string;
  is_abnormal: boolean;
  abnormal_flag?: string | null;
  abnormality_severity?: "mild" | "moderate" | "critical";
  collected_at: string;
  ordering_physician?: string;
  interpretation?: string;
  created_at: string;
}

export interface AgentRun {
  id: string;
  patient_id: string;
  report_id?: string;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  current_step?: string;
  steps_completed: string[];
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
  tokens_used: number;
  created_at: string;
}

/** SSE event payload from the analysis stream endpoint */
export interface StreamEvent {
  type?: string;
  event_type?: string;
  agent?: string;
  agent_name?: string;
  thought?: string;
  token?: string;
  error?: string;
  tokens_used?: number;
  run_id?: string;
  data?: Record<string, unknown>;
  timestamp?: string;
}

export interface DifferentialDiagnosis {
  /** Primary name as used in report viewer */
  diagnosis?: string;
  /** Backend may use condition */
  condition?: string;
  probability?: number;
  likelihood?: "high" | "medium" | "low";
  reasoning?: string;
  supporting_findings?: string[];
  against_findings?: string[];
  icd10_code?: string;
  icd_code?: string;
  urgency?: "emergency" | "urgent" | "routine";
}

export interface DrugInteraction {
  drug1: string;
  drug2: string;
  severity: "minor" | "moderate" | "major" | "contraindicated";
  description: string;
  recommendation?: string;
}

export interface CarePlanItem {
  priority: "immediate" | "urgent" | "routine" | "preventive" | "short_term" | "long_term";
  category?: string;
  action: string;
  rationale?: string;
  timeframe?: string;
  responsible_party?: string;
}

export interface ClinicalReportContent {
  patient_summary?: Record<string, unknown>;
  chief_complaint?: string;
  executive_summary?: string;
  symptom_analysis?: {
    primary_symptoms?: string[];
    red_flags?: string[];
    severity?: string;
    [key: string]: unknown;
  };
  lab_interpretation?: unknown[];
  drug_interactions?: DrugInteraction[];
  differential_diagnoses?: DifferentialDiagnosis[];
  care_plan?: CarePlanItem[];
  physician_summary?: string;
  key_recommendations?: string[];
  generated_at?: string;
  model_used?: string;
  disclaimer?: string;
}

export interface Report {
  id: string;
  patient_id: string;
  agent_run_id?: string;
  report_type: string;
  title: string;
  status: "generating" | "completed" | "failed";
  content?: ClinicalReportContent;
  physician_notes?: string;
  reviewed_by?: string;
  reviewed_at?: string;
  generated_at?: string;
  created_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface Token {
  access_token: string;
  token_type: string;
  expires_in: number;
}
