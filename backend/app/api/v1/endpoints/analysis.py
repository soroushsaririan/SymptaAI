"""AI analysis workflow endpoints."""
from __future__ import annotations

import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ClinicalStaff, CurrentUser, get_rag_service
from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.models.agent_run import AgentRun
from app.schemas.analysis import AgentRunStatus, AnalysisRequest, AnalysisResponse
from app.services.analysis_service import AnalysisService
from app.services.rag_service import RAGService

router = APIRouter()


@router.post("/run", response_model=AgentRunStatus, status_code=status.HTTP_202_ACCEPTED)
async def run_analysis(
    request: AnalysisRequest,
    current_user: ClinicalStaff,
    db: Annotated[AsyncSession, Depends(get_db)],
    rag: Annotated[Optional[RAGService], Depends(get_rag_service)],
) -> AgentRunStatus:
    """Start a full AI analysis workflow for a patient.

    Returns the AgentRun record immediately. Poll /status or stream /stream for results.
    """
    service = AnalysisService(db=db, rag_service=rag)
    run = await service.start_analysis(request, user_id=current_user.id)
    # start_analysis may return AnalysisResponse or AgentRun — normalise to AgentRunStatus
    if hasattr(run, "agent_run_id"):
        agent_run = await db.get(AgentRun, run.agent_run_id)
        if not agent_run:
            raise NotFoundError("AgentRun", run.agent_run_id)
        return AgentRunStatus.model_validate(agent_run)
    return AgentRunStatus.model_validate(run)


@router.get("/{run_id}/status", response_model=AgentRunStatus)
async def get_run_status(
    run_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    rag: Annotated[Optional[RAGService], Depends(get_rag_service)],
) -> AgentRunStatus:
    """Poll the status of an agent run."""
    service = AnalysisService(db=db, rag_service=rag)
    return await service.get_run_status(run_id)


@router.get("/{run_id}/stream")
async def stream_analysis(
    run_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    rag: Annotated[Optional[RAGService], Depends(get_rag_service)],
    token: Optional[str] = None,
) -> StreamingResponse:
    """Stream agent workflow events as Server-Sent Events (SSE).

    Connect with EventSource in the browser to receive real-time updates.
    Each event is JSON-encoded with event_type, agent_name, data, timestamp.
    """
    from fastapi import HTTPException
    from app.core.security import verify_token
    from app.models.user import User

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        token_data = verify_token(token)
        user = await db.get(User, token_data.user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="Not authenticated")
    except Exception:
        raise HTTPException(status_code=401, detail="Not authenticated")

    service = AnalysisService(db=db, rag_service=rag)

    async def event_generator():
        async for event in service.stream_workflow(run_id):
            payload = event.model_dump_json()
            yield f"data: {payload}\n\n"
        yield "data: {\"event_type\": \"done\"}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{run_id}/cancel", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_analysis(
    run_id: uuid.UUID,
    current_user: ClinicalStaff,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Cancel a running analysis."""
    run = await db.get(AgentRun, run_id)
    if not run:
        raise NotFoundError("AgentRun", run_id)
    if run.status in ("completed", "failed"):
        return
    run.status = "cancelled"
    await db.flush()


@router.get("/history/{patient_id}", response_model=list[AgentRunStatus])
async def get_analysis_history(
    patient_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[AgentRunStatus]:
    """List all past analyses for a patient."""
    result = await db.execute(
        select(AgentRun)
        .where(AgentRun.patient_id == patient_id)
        .order_by(AgentRun.created_at.desc())
        .limit(20)
    )
    runs = result.scalars().all()
    return [AgentRunStatus.model_validate(r) for r in runs]
