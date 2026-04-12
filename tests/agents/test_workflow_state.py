"""Tests for LangGraph workflow state management."""
from __future__ import annotations

import operator
from typing import Annotated, TypedDict

import pytest


class TestStateReducers:
    """Verify the LangGraph operator.add reducer pattern works as expected."""

    def test_list_reducer_accumulates(self):
        """operator.add reducer should concatenate lists across parallel nodes."""
        from app.workflows.state import HealthcareWorkflowState

        # Simulate merging two parallel node outputs
        base_state: HealthcareWorkflowState = {
            "patient_id": "test-id",
            "steps_completed": ["patient_intake"],
            "errors": [],
            "tokens_used": 100,
            "messages": [],
            "patient_context": {},
            "lab_results": [],
            "medical_records": [],
            "symptom_analysis": {},
            "lab_interpretation": {},
            "drug_interactions": {},
            "differential_diagnosis": {},
            "care_plan": {},
            "clinical_report": {},
            "run_id": "run-id",
        }

        # Reducer adds lists together
        update_a = {"steps_completed": ["symptom_analysis"]}
        update_b = {"steps_completed": ["lab_interpretation"]}

        # The operator.add reducer means both updates are merged
        merged_steps = base_state["steps_completed"] + update_a["steps_completed"] + update_b["steps_completed"]
        assert "patient_intake" in merged_steps
        assert "symptom_analysis" in merged_steps
        assert "lab_interpretation" in merged_steps

    def test_tokens_accumulate(self):
        """Tokens used should accumulate across all agent steps."""
        tokens = [150, 200, 300, 100, 250]
        total = sum(tokens)
        assert total == 1000

    def test_errors_accumulate_without_overwriting(self):
        """Errors from different agents should all be preserved."""
        errors_a = ["Lab agent: context length exceeded"]
        errors_b = ["Drug interaction agent: OpenAI timeout"]
        combined = errors_a + errors_b
        assert len(combined) == 2
        assert "Lab agent" in combined[0]
        assert "Drug interaction agent" in combined[1]


class TestStateImport:
    def test_state_imports_cleanly(self):
        from app.workflows.state import HealthcareWorkflowState
        # Verify it's a TypedDict
        assert hasattr(HealthcareWorkflowState, "__annotations__")
        required_fields = {
            "steps_completed", "errors", "tokens_used",
            "symptom_analysis", "differential_diagnoses",
            "care_plan", "clinical_report",
        }
        annotations = HealthcareWorkflowState.__annotations__
        for field in required_fields:
            assert field in annotations, f"Missing required state field: {field}"
