"""Celery background tasks for async analysis processing."""
from __future__ import annotations

import asyncio
import uuid

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "healthcare_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    broker_connection_retry=False,
    broker_connection_max_retries=0,
)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "tasks.run_healthcare_analysis": {"queue": "analysis"},
        "tasks.process_medical_record": {"queue": "records"},
        "tasks.generate_report": {"queue": "reports"},
    },
)


def _get_db_and_rag():
    """Create sync DB session and RAG service for use in Celery tasks."""
    from app.db.session import AsyncSessionLocal
    from app.services.rag_service import RAGService
    rag = RAGService()
    return AsyncSessionLocal, rag


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="tasks.run_healthcare_analysis",
    soft_time_limit=300,
    time_limit=360,
)
def run_healthcare_analysis(self, agent_run_id: str) -> dict:
    """Run the full healthcare analysis workflow for a given agent run.

    This task executes the LangGraph workflow synchronously within the
    Celery worker process, updating the AgentRun record throughout.
    """
    async def _run():
        AsyncSessionLocal, rag_service = _get_db_and_rag()
        async with AsyncSessionLocal() as db:
            await rag_service.initialize()
            from app.services.analysis_service import AnalysisService
            service = AnalysisService(db=db, rag_service=rag_service)
            state = await service.run_workflow_sync(uuid.UUID(agent_run_id))
            return {"status": "completed", "steps": state.get("steps_completed", [])}

    try:
        return asyncio.run(_run())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries * 30)


@celery_app.task(
    name="tasks.process_medical_record",
    max_retries=2,
    default_retry_delay=30,
)
def process_medical_record(record_id: str) -> dict:
    """Process and AI-summarize an uploaded medical record."""
    async def _run():
        from app.db.session import AsyncSessionLocal
        from app.models.medical_record import MedicalRecord
        from app.services.rag_service import RAGService

        async with AsyncSessionLocal() as db:
            record = await db.get(MedicalRecord, uuid.UUID(record_id))
            if not record or not record.content:
                return {"status": "skipped", "reason": "No content to process"}

            # Use a simple summarization chain
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(model=settings.OPENAI_MODEL, api_key=settings.OPENAI_API_KEY, temperature=0)
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a medical transcriptionist. Summarize this clinical document into structured JSON with keys: diagnoses, treatments, outcomes, key_findings, follow_up."),
                ("human", "{content}"),
            ])
            chain = prompt | llm
            response = await chain.ainvoke({"content": record.content[:4000]})
            record.structured_summary = {"summary": response.content}
            record.processed = True
            await db.commit()
            return {"status": "completed", "record_id": record_id}

    return asyncio.run(_run())


@celery_app.task(
    name="tasks.generate_report",
    max_retries=2,
)
def generate_report(agent_run_id: str, report_type: str = "full_clinical") -> dict:
    """Generate a specific report type from a completed analysis run."""
    async def _run():
        from app.db.session import AsyncSessionLocal
        from app.models.agent_run import AgentRun

        async with AsyncSessionLocal() as db:
            run = await db.get(AgentRun, uuid.UUID(agent_run_id))
            if not run or run.status != "completed":
                return {"status": "skipped", "reason": "Run not completed"}
            return {"status": "completed", "report_type": report_type}

    return asyncio.run(_run())
