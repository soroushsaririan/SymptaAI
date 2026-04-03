"""Shared LangGraph state types for the healthcare workflow."""
from __future__ import annotations

import operator
from typing import Annotated, Any, Optional, TypedDict


class PatientData(TypedDict):
    patient_id: str
    mrn: str
    full_name: str
    age: int
    gender: str
    date_of_birth: str
    chief_complaint: str
    symptoms: list[str]
    symptom_duration: str
    severity: int  # 1-10
    vitals: dict[str, Any]
    allergies: list[str]
    current_medications: list[dict[str, Any]]
    medical_history: list[dict[str, Any]]
    family_history: list[str]


class LabData(TypedDict):
    test_name: str
    value: str
    unit: str
    reference_range: str
    is_abnormal: bool
    abnormality_severity: Optional[str]
    collected_at: str


class DrugInteraction(TypedDict):
    drug1: str
    drug2: str
    severity: str  # minor, moderate, major, contraindicated
    description: str
    recommendation: str


class DifferentialDiagnosis(TypedDict):
    condition: str
    likelihood: str  # high, medium, low
    reasoning: str
    supporting_findings: list[str]
    against_findings: list[str]
    icd_code: Optional[str]
    urgency: str  # emergency, urgent, routine


class CarePlanItem(TypedDict):
    priority: str  # immediate, short_term, long_term
    action: str
    rationale: str
    timeframe: str
    responsible_party: Optional[str]


class HealthcareWorkflowState(TypedDict):
    """Shared state object that flows through all workflow nodes.

    Uses operator.add for list fields so concurrent updates are merged
    rather than overwritten.
    """
    # ── Input ─────────────────────────────────────────────────────────────
    agent_run_id: str
    patient_data: PatientData
    medical_records: list[str]       # raw text of each clinical note
    lab_results: list[LabData]

    # ── Processing ────────────────────────────────────────────────────────
    current_step: str
    steps_completed: Annotated[list[str], operator.add]
    errors: Annotated[list[str], operator.add]

    # ── Agent outputs ─────────────────────────────────────────────────────
    intake_summary: Optional[dict[str, Any]]
    record_summaries: Optional[list[dict[str, Any]]]
    symptom_analysis: Optional[dict[str, Any]]
    lab_interpretation: Optional[dict[str, Any]]
    drug_interactions: Optional[list[DrugInteraction]]
    differential_diagnoses: Optional[list[DifferentialDiagnosis]]
    care_plan: Optional[list[CarePlanItem]]
    clinical_report: Optional[dict[str, Any]]

    # ── Metadata ──────────────────────────────────────────────────────────
    tokens_used: Annotated[int, operator.add]
    started_at: str
    completed_at: Optional[str]
    model_used: str
