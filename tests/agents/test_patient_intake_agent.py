"""Tests for the Patient Intake agent."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestPatientIntakeAgent:
    """Test the PatientIntakeAgent in isolation."""

    @pytest.fixture
    def mock_state(self):
        return {
            "agent_run_id": "test-run-uuid",
            "patient_data": {"id": "test-patient-uuid"},
            "steps_completed": [],
            "errors": [],
            "tokens_used": 0,
            "lab_results": [
                {
                    "test_name": "HbA1c",
                    "value": "8.5",
                    "unit": "%",
                    "reference_range": "< 5.7",
                    "is_abnormal": True,
                }
            ],
            "medical_records": [],
            "intake_summary": None,
            "record_summaries": [],
            "symptom_analysis": None,
            "lab_interpretation": None,
            "drug_interactions": None,
            "differential_diagnoses": None,
            "care_plan": None,
            "clinical_report": None,
            "current_step": None,
            "started_at": None,
            "completed_at": None,
            "model_used": "gpt-4o",
        }

    @pytest.fixture
    def mock_patient(self):
        patient = MagicMock()
        patient.id = "test-patient-uuid"
        patient.first_name = "Jane"
        patient.last_name = "Doe"
        patient.date_of_birth.isoformat.return_value = "1985-03-15"
        patient.gender = "female"
        patient.mrn = "MRN-2024-000001"
        patient.chief_complaint = "Fatigue and frequent urination"
        patient.symptoms = ["fatigue", "polyuria", "polydipsia"]
        patient.allergies = ["Penicillin"]
        patient.current_medications = [
            MagicMock(name="Metformin", dose="500mg", frequency="twice daily")
        ]
        patient.medical_history = [{"condition": "Type 2 Diabetes"}]
        patient.vitals = None
        return patient

    def test_agent_instantiation(self):
        """Agent should instantiate without requiring a real DB or LLM."""
        with patch("app.agents.base.ChatOpenAI"):
            from app.agents.patient_intake import PatientIntakeAgent
            agent = PatientIntakeAgent()
            assert agent is not None

    @pytest.mark.asyncio
    async def test_agent_safe_run_returns_dict(self, mock_state, mock_patient):
        """safe_run() should always return a dict, never raise."""
        with patch("app.agents.base.ChatOpenAI"):
            from app.agents.patient_intake import PatientIntakeAgent
            agent = PatientIntakeAgent()
            agent._invoke_with_retry = AsyncMock(
                return_value=MagicMock(content="Patient intake summary complete.")
            )
            result = await agent.safe_run(mock_state)
            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_agent_error_isolation(self, mock_state):
        """If the LLM call fails, safe_run() should return error state, not raise."""
        with patch("app.agents.base.ChatOpenAI"):
            from app.agents.patient_intake import PatientIntakeAgent
            agent = PatientIntakeAgent()
            agent._invoke_with_retry = AsyncMock(side_effect=Exception("LLM connection timeout"))

            result = await agent.safe_run(mock_state)
            assert isinstance(result, dict)
            # Should contain error info (not propagate the exception)
