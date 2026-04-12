"""Report Pydantic schemas."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class DrugInteraction(BaseModel):
    drug1: str
    drug2: str
    severity: str  # minor, moderate, major, contraindicated
    description: str
    recommendation: str


class DifferentialDiagnosis(BaseModel):
    condition: str
    likelihood: str  # high, medium, low
    reasoning: str
    supporting_findings: list[str] = Field(default_factory=list)
    against_findings: list[str] = Field(default_factory=list)
    icd_code: Optional[str] = None
    urgency: str = "routine"  # emergency, urgent, routine
    recommended_workup: list[str] = Field(default_factory=list)


class CarePlanItem(BaseModel):
    priority: str  # immediate, short_term, long_term
    action: str
    rationale: str
    timeframe: str
    responsible_party: Optional[str] = None


class LabInterpretationItem(BaseModel):
    test_name: str
    value: str
    unit: Optional[str]
    reference_range: Optional[str]
    status: str  # normal, abnormal, critical
    clinical_significance: str
    interpretation: str


class ClinicalReportContent(BaseModel):
    patient_summary: dict[str, Any]
    chief_complaint: str
    symptom_analysis: dict[str, Any]
    lab_interpretation: list[LabInterpretationItem] = Field(default_factory=list)
    drug_interactions: list[DrugInteraction] = Field(default_factory=list)
    differential_diagnoses: list[DifferentialDiagnosis] = Field(default_factory=list)
    care_plan: list[CarePlanItem] = Field(default_factory=list)
    physician_summary: str
    executive_summary: str
    cannot_miss_diagnoses: list[str] = Field(default_factory=list)
    generated_at: datetime
    model_used: str = "gpt-4o"
    disclaimer: str = (
        "IMPORTANT: This AI-generated report is intended as a clinical decision support tool "
        "only. It does not replace the judgment of a qualified healthcare professional. All "
        "findings, diagnoses, and recommendations must be reviewed and validated by a licensed "
        "physician before any clinical action is taken. This report is not a substitute for "
        "professional medical advice, diagnosis, or treatment."
    )


class ReportResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    patient_id: uuid.UUID
    agent_run_id: Optional[uuid.UUID]
    report_type: str
    title: str
    status: str
    content: Optional[dict[str, Any]]
    physician_notes: Optional[str]
    reviewed_by: Optional[uuid.UUID]
    reviewed_at: Optional[datetime]
    generated_at: Optional[datetime]
    created_at: datetime


class ReportListResponse(BaseModel):
    items: list[ReportResponse]
    total: int
    limit: int
    offset: int


class PhysicianNotesRequest(BaseModel):
    notes: str = Field(min_length=1, max_length=5000)
