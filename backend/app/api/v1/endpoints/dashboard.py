"""Dashboard stats endpoint."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.db.session import get_db
from app.models.agent_run import AgentRun
from app.models.lab_result import LabResult
from app.models.patient import Patient
from app.models.report import Report

router = APIRouter()


class DashboardStats(BaseModel):
    total_patients: int
    active_analyses: int
    total_reports: int
    critical_labs: int


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DashboardStats:
    """Return aggregate counts for the dashboard overview cards."""

    total_patients = (await db.execute(
        select(func.count()).select_from(Patient).where(Patient.is_deleted == False)  # noqa: E712
    )).scalar_one()

    active_analyses = (await db.execute(
        select(func.count()).select_from(AgentRun)
        .where(AgentRun.status.in_(["pending", "running"]))
    )).scalar_one()

    total_reports = (await db.execute(
        select(func.count()).select_from(Report)
    )).scalar_one()

    critical_labs = (await db.execute(
        select(func.count()).select_from(LabResult)
        .where(LabResult.abnormality_severity == "critical")
    )).scalar_one()

    return DashboardStats(
        total_patients=total_patients,
        active_analyses=active_analyses,
        total_reports=total_reports,
        critical_labs=critical_labs,
    )
