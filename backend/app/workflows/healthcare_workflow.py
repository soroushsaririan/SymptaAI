"""LangGraph healthcare workflow orchestration."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from langgraph.graph import END, StateGraph

from app.agents.care_plan import CarePlanAgent
from app.agents.clinical_report import ClinicalReportAgent
from app.agents.differential_diagnosis import DifferentialDiagnosisAgent
from app.agents.drug_interaction import DrugInteractionAgent
from app.agents.lab_interpretation import LabInterpretationAgent
from app.agents.medical_record_summarizer import MedicalRecordSummarizerAgent
from app.agents.patient_intake import PatientIntakeAgent
from app.agents.symptom_analysis import SymptomAnalysisAgent
from app.core.logging import get_logger
from app.workflows.state import HealthcareWorkflowState

logger = get_logger("workflow.healthcare")


class HealthcareWorkflow:
    """Orchestrates the full multi-agent healthcare analysis pipeline.

    Flow:
        patient_intake
            → [medical_record_summarizer, symptom_analysis] (parallel)
            → merge
            → lab_interpretation
            → drug_interaction
            → differential_diagnosis
            → care_plan
            → clinical_report
            → END
    """

    def __init__(self) -> None:
        self.intake_agent = PatientIntakeAgent()
        self.record_agent = MedicalRecordSummarizerAgent()
        self.symptom_agent = SymptomAnalysisAgent()
        self.lab_agent = LabInterpretationAgent()
        self.drug_agent = DrugInteractionAgent()
        self.dx_agent = DifferentialDiagnosisAgent()
        self.care_agent = CarePlanAgent()
        self.report_agent = ClinicalReportAgent()
        self.graph = self._build_graph()

    # ── Node implementations ───────────────────────────────────────────────

    async def _node_intake(self, state: HealthcareWorkflowState) -> dict[str, Any]:
        logger.info("workflow_step", step="patient_intake", run_id=state["agent_run_id"])
        state["current_step"] = "patient_intake"
        return await self.intake_agent.safe_run(state)

    async def _node_record_summarizer(self, state: HealthcareWorkflowState) -> dict[str, Any]:
        logger.info("workflow_step", step="medical_record_summarizer", run_id=state["agent_run_id"])
        state["current_step"] = "medical_record_summarizer"
        return await self.record_agent.safe_run(state)

    async def _node_symptom_analysis(self, state: HealthcareWorkflowState) -> dict[str, Any]:
        logger.info("workflow_step", step="symptom_analysis", run_id=state["agent_run_id"])
        state["current_step"] = "symptom_analysis"
        return await self.symptom_agent.safe_run(state)

    async def _node_lab_interpretation(self, state: HealthcareWorkflowState) -> dict[str, Any]:
        logger.info("workflow_step", step="lab_interpretation", run_id=state["agent_run_id"])
        state["current_step"] = "lab_interpretation"
        return await self.lab_agent.safe_run(state)

    async def _node_drug_interaction(self, state: HealthcareWorkflowState) -> dict[str, Any]:
        logger.info("workflow_step", step="drug_interaction", run_id=state["agent_run_id"])
        state["current_step"] = "drug_interaction"
        return await self.drug_agent.safe_run(state)

    async def _node_differential_diagnosis(self, state: HealthcareWorkflowState) -> dict[str, Any]:
        logger.info("workflow_step", step="differential_diagnosis", run_id=state["agent_run_id"])
        state["current_step"] = "differential_diagnosis"
        return await self.dx_agent.safe_run(state)

    async def _node_care_plan(self, state: HealthcareWorkflowState) -> dict[str, Any]:
        logger.info("workflow_step", step="care_plan", run_id=state["agent_run_id"])
        state["current_step"] = "care_plan"
        return await self.care_agent.safe_run(state)

    async def _node_clinical_report(self, state: HealthcareWorkflowState) -> dict[str, Any]:
        logger.info("workflow_step", step="clinical_report", run_id=state["agent_run_id"])
        state["current_step"] = "clinical_report"
        result = await self.report_agent.safe_run(state)
        result["completed_at"] = datetime.now(timezone.utc).isoformat()
        return result

    def _should_continue(self, state: HealthcareWorkflowState) -> str:
        """Conditional edge: abort workflow if critical errors accumulated."""
        errors = state.get("errors", [])
        # Allow up to 2 non-critical errors before aborting
        critical_keywords = ["authentication", "rate limit", "quota"]
        critical_errors = [
            e for e in errors
            if any(kw in e.lower() for kw in critical_keywords)
        ]
        if critical_errors:
            logger.error("workflow_critical_error", errors=critical_errors)
            return "end"
        return "continue"

    # ── Graph construction ─────────────────────────────────────────────────

    def _build_graph(self) -> Any:
        graph = StateGraph(HealthcareWorkflowState)

        # Register all nodes
        graph.add_node("patient_intake", self._node_intake)
        graph.add_node("medical_record_summarizer", self._node_record_summarizer)
        graph.add_node("symptom_analysis", self._node_symptom_analysis)
        graph.add_node("lab_interpretation", self._node_lab_interpretation)
        graph.add_node("drug_interaction", self._node_drug_interaction)
        graph.add_node("differential_diagnosis", self._node_differential_diagnosis)
        graph.add_node("care_plan", self._node_care_plan)
        graph.add_node("clinical_report", self._node_clinical_report)

        # Entry point
        graph.set_entry_point("patient_intake")

        # Sequential flow with guard after intake
        graph.add_conditional_edges(
            "patient_intake",
            self._should_continue,
            {"continue": "symptom_analysis", "end": END},
        )
        graph.add_edge("symptom_analysis", "medical_record_summarizer")
        graph.add_edge("medical_record_summarizer", "lab_interpretation")
        graph.add_edge("lab_interpretation", "drug_interaction")
        graph.add_edge("drug_interaction", "differential_diagnosis")
        graph.add_edge("differential_diagnosis", "care_plan")
        graph.add_edge("care_plan", "clinical_report")
        graph.add_edge("clinical_report", END)

        return graph.compile()

    # ── Public interface ───────────────────────────────────────────────────

    async def run(self, initial_state: HealthcareWorkflowState) -> HealthcareWorkflowState:
        """Execute the full workflow and return the final state."""
        logger.info(
            "workflow_started",
            run_id=initial_state["agent_run_id"],
            patient_id=initial_state["patient_data"]["patient_id"],
        )
        config = {"recursion_limit": 50}
        final_state = await self.graph.ainvoke(initial_state, config=config)
        logger.info(
            "workflow_completed",
            run_id=initial_state["agent_run_id"],
            steps=final_state.get("steps_completed", []),
            tokens=final_state.get("tokens_used", 0),
        )
        return final_state

    async def stream(self, initial_state: HealthcareWorkflowState):
        """Stream workflow events as they occur."""
        config = {"recursion_limit": 50}
        async for event in self.graph.astream(initial_state, config=config):
            yield event
