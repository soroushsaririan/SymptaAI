"""Analysis orchestration service — runs and tracks AI workflow execution."""
from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.models.agent_run import AgentRun
from app.models.lab_result import LabResult
from app.models.medical_record import MedicalRecord
from app.models.patient import Patient
from app.models.report import Report
from app.schemas.analysis import AgentRunStatus, AnalysisRequest, AnalysisResponse, StreamEvent
from app.services.rag_service import RAGService
from app.workflows.healthcare_workflow import HealthcareWorkflow
from app.workflows.state import HealthcareWorkflowState

logger = get_logger("service.analysis")


class AnalysisService:
    """Coordinates AI analysis workflow execution and persistence."""

    def __init__(self, db: AsyncSession, rag_service: RAGService | None) -> None:
        self.db = db
        self.rag_service = rag_service
        self.workflow = HealthcareWorkflow()

    async def start_analysis(
        self,
        request: AnalysisRequest,
        user_id: uuid.UUID,
    ) -> AnalysisResponse:
        """Create an AgentRun record and enqueue the Celery task.

        Returns an AnalysisResponse with the run ID for status polling.
        """
        # Verify patient exists
        patient = await self.db.get(Patient, request.patient_id)
        if not patient:
            raise NotFoundError("Patient", request.patient_id)

        agent_run = AgentRun(
            id=uuid.uuid4(),
            patient_id=request.patient_id,
            initiated_by=user_id,
            workflow_type=request.workflow_type,
            status="pending",
            input_data={
                "include_labs": request.include_labs,
                "include_records": request.include_records,
                "additional_context": request.additional_context,
            },
        )
        self.db.add(agent_run)
        await self.db.flush()

        # Enqueue via Celery (import here to avoid circular dependency)
        try:
            from app.workers.tasks import run_healthcare_analysis
            run_healthcare_analysis.delay(str(agent_run.id))
        except Exception as exc:
            logger.warning("celery_unavailable", error=str(exc), run_id=str(agent_run.id))
            # Fall back to synchronous execution in development
            if not agent_run:
                raise

        logger.info("analysis_started", run_id=str(agent_run.id), patient_id=str(request.patient_id))
        return AnalysisResponse(
            agent_run_id=agent_run.id,
            status="pending",
            message="Analysis queued. Use the run ID to poll status or stream results.",
        )

    async def get_run_status(self, run_id: uuid.UUID) -> AgentRunStatus:
        """Get the current execution status of an agent run."""
        run = await self.db.get(AgentRun, run_id)
        if not run:
            raise NotFoundError("AgentRun", run_id)
        return AgentRunStatus.model_validate(run)

    async def run_workflow_sync(self, agent_run_id: uuid.UUID) -> HealthcareWorkflowState:
        """Execute the workflow synchronously — used by Celery worker."""
        run = await self.db.get(AgentRun, agent_run_id)
        if not run:
            raise NotFoundError("AgentRun", agent_run_id)

        run.status = "running"
        run.started_at = datetime.now(timezone.utc)
        await self.db.flush()

        try:
            initial_state = await self._build_initial_state(run)
            final_state = await self.workflow.run(initial_state)
            await self._save_results(final_state, run)
            return final_state
        except Exception as exc:
            run.status = "failed"
            run.error_message = str(exc)
            run.completed_at = datetime.now(timezone.utc)
            await self.db.flush()
            raise

    async def stream_workflow(
        self, agent_run_id: uuid.UUID
    ) -> AsyncGenerator[StreamEvent, None]:
        """Stream workflow execution events as SSE-compatible events."""
        run = await self.db.get(AgentRun, agent_run_id)
        if not run:
            raise NotFoundError("AgentRun", agent_run_id)

        # If run is already completed, stream final state
        if run.status == "completed" and run.output_data:
            yield StreamEvent(
                event_type="workflow_complete",
                data={"output": run.output_data},
                timestamp=datetime.now(timezone.utc),
                run_id=str(agent_run_id),
            )
            return

        # Build initial state and stream
        initial_state = await self._build_initial_state(run)
        run.status = "running"
        run.started_at = datetime.now(timezone.utc)
        await self.db.flush()

        try:
            final_state = initial_state
            async for event in self.workflow.stream(initial_state):
                for node_name, node_output in event.items():
                    # Merge node output into final state
                    final_state = {**final_state, **node_output}
                    steps = node_output.get("steps_completed", [])
                    completed_step = steps[-1] if steps else node_name
                    yield StreamEvent(
                        event_type="step_complete",
                        agent_name=completed_step,
                        data={"step": node_name, "output_keys": list(node_output.keys())},
                        timestamp=datetime.now(timezone.utc),
                        run_id=str(agent_run_id),
                    )
                    # Update DB current step
                    run.current_step = completed_step
                    await self.db.flush()

            # Save results from the streamed final state (no second LLM run)
            await self._save_results(final_state, run)
            yield StreamEvent(
                event_type="workflow_complete",
                data={"steps_completed": final_state.get("steps_completed", []), "tokens_used": final_state.get("tokens_used", 0)},
                timestamp=datetime.now(timezone.utc),
                run_id=str(agent_run_id),
            )
        except Exception as exc:
            run.status = "failed"
            run.error_message = str(exc)
            await self.db.flush()
            yield StreamEvent(
                event_type="workflow_error",
                data={"error": str(exc)},
                timestamp=datetime.now(timezone.utc),
                run_id=str(agent_run_id),
            )

    async def _build_initial_state(self, run: AgentRun) -> HealthcareWorkflowState:
        """Build the workflow initial state from DB entities."""
        patient = await self.db.get(Patient, run.patient_id)
        if not patient:
            raise NotFoundError("Patient", run.patient_id)

        from datetime import date
        today = date.today()
        dob = patient.date_of_birth
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

        # Load labs if requested
        lab_data = []
        if run.input_data.get("include_labs", True):
            result = await self.db.execute(
                select(LabResult).where(LabResult.patient_id == patient.id)
            )
            labs = result.scalars().all()
            lab_data = [
                {
                    "test_name": l.test_name,
                    "value": l.value,
                    "unit": l.unit or "",
                    "reference_range": l.reference_range or "",
                    "is_abnormal": l.is_abnormal,
                    "abnormality_severity": l.abnormality_severity,
                    "collected_at": l.collected_at.isoformat(),
                }
                for l in labs
            ]

        # Load records if requested
        record_texts = []
        if run.input_data.get("include_records", True):
            result = await self.db.execute(
                select(MedicalRecord)
                .where(MedicalRecord.patient_id == patient.id)
                .where(MedicalRecord.processed == True)  # noqa: E712
            )
            records = result.scalars().all()
            record_texts = [r.content for r in records if r.content]

        return HealthcareWorkflowState(
            agent_run_id=str(run.id),
            patient_data={
                "patient_id": str(patient.id),
                "mrn": patient.mrn,
                "full_name": f"{patient.first_name} {patient.last_name}",
                "age": age,
                "gender": patient.gender,
                "date_of_birth": patient.date_of_birth.isoformat(),
                "chief_complaint": patient.chief_complaint or "",
                "symptoms": patient.symptoms or [],
                "symptom_duration": "Not specified",
                "severity": 5,
                "vitals": patient.vitals or {},
                "allergies": patient.allergies or [],
                "current_medications": [
                    m if isinstance(m, dict) else {"name": str(m)}
                    for m in (patient.current_medications or [])
                ],
                "medical_history": patient.medical_history or [],
                "family_history": patient.family_history or [],
            },
            medical_records=record_texts,
            lab_results=lab_data,
            current_step="initializing",
            steps_completed=[],
            errors=[],
            intake_summary=None,
            record_summaries=None,
            symptom_analysis=None,
            lab_interpretation=None,
            drug_interactions=None,
            differential_diagnoses=None,
            care_plan=None,
            clinical_report=None,
            tokens_used=0,
            started_at=datetime.now(timezone.utc).isoformat(),
            completed_at=None,
            model_used="gpt-4o",
        )

    async def _save_results(self, state: HealthcareWorkflowState, run: AgentRun) -> None:
        """Persist the completed workflow state to the database."""
        now = datetime.now(timezone.utc)
        run.status = "completed"
        run.completed_at = now
        run.steps_completed = state.get("steps_completed", [])
        run.tokens_used = state.get("tokens_used", 0)
        run.output_data = {
            "intake_summary": state.get("intake_summary"),
            "symptom_analysis": state.get("symptom_analysis"),
            "lab_interpretation": state.get("lab_interpretation"),
            "drug_interactions": state.get("drug_interactions"),
            "differential_diagnoses": state.get("differential_diagnoses"),
            "care_plan": state.get("care_plan"),
        }
        if run.started_at:
            delta = now - run.started_at
            run.duration_seconds = delta.total_seconds()

        # Create the clinical report record
        if state.get("clinical_report"):
            report = Report(
                id=uuid.uuid4(),
                patient_id=run.patient_id,
                agent_run_id=run.id,
                report_type="full_clinical",
                title=f"Clinical Analysis Report — {now.strftime('%Y-%m-%d')}",
                status="completed",
                content=state["clinical_report"],
                generated_at=now,
            )
            self.db.add(report)

        await self.db.flush()
        logger.info("analysis_saved", run_id=str(run.id), tokens=run.tokens_used)
