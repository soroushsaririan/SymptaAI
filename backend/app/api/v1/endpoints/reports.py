"""Report viewing, reviewing, and export endpoints."""
from __future__ import annotations

import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ClinicalStaff, CurrentUser
from app.db.session import get_db
from app.schemas.report import PhysicianNotesRequest, ReportListResponse, ReportResponse
from app.services.audit_service import AuditService
from app.services.report_service import ReportService

router = APIRouter()


@router.get("", response_model=ReportListResponse)
async def list_reports(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    patient_id: Optional[uuid.UUID] = Query(default=None),
    report_type: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ReportListResponse:
    """List reports with optional filters."""
    service = ReportService(db)
    reports, total = await service.list_reports(patient_id, report_type, limit, offset)
    return ReportListResponse(
        items=[ReportResponse.model_validate(r) for r in reports],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReportResponse:
    """Get full report content by ID."""
    service = ReportService(db)
    report = await service.get_report(report_id)
    audit = AuditService(db)
    await audit.log("read", "report", report_id, current_user.id, phi_accessed=True)
    return ReportResponse.model_validate(report)


@router.post("/{report_id}/review", response_model=ReportResponse)
async def add_physician_notes(
    report_id: uuid.UUID,
    data: PhysicianNotesRequest,
    current_user: ClinicalStaff,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReportResponse:
    """Physician adds review notes to a report."""
    service = ReportService(db)
    report = await service.add_physician_notes(report_id, data.notes, current_user.id)
    return ReportResponse.model_validate(report)


@router.get("/{report_id}/export")
async def export_report_pdf(
    report_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    """Export report as a physician-ready PDF document."""
    service = ReportService(db)
    pdf_bytes = await service.export_pdf(report_id)
    audit = AuditService(db)
    await audit.log("export", "report", report_id, current_user.id, phi_accessed=True)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="report-{report_id}.pdf"'},
    )


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: uuid.UUID,
    current_user: ClinicalStaff,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a report."""
    service = ReportService(db)
    await service.delete_report(report_id)
    audit = AuditService(db)
    await audit.log("delete", "report", report_id, current_user.id)
