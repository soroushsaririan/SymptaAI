"""Shared FastAPI dependencies."""
from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.middleware.auth_middleware import (
    get_current_active_user,
    get_current_user,
    require_roles,
)
from app.models.patient import Patient
from app.models.report import Report
from app.models.user import User
from app.services.rag_service import RAGService

# Re-export auth dependencies for use in route files
CurrentUser = Annotated[User, Depends(get_current_active_user)]
AdminOnly = Annotated[User, Depends(require_roles("admin"))]
ClinicalStaff = Annotated[User, Depends(require_roles("physician", "nurse", "admin"))]

# Singleton RAG service (initialized at startup)
_rag_service: RAGService | None = None


def set_rag_service(rag: RAGService) -> None:
    global _rag_service
    _rag_service = rag


async def get_rag_service() -> RAGService | None:
    if _rag_service is None or not _rag_service.is_initialized:
        return None
    return _rag_service


async def get_patient_or_404(
    patient_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Patient:
    """Dependency: load Patient or raise 404."""
    patient = await db.get(Patient, patient_id)
    if not patient or patient.is_deleted:
        raise NotFoundError("Patient", patient_id)
    return patient


async def get_report_or_404(
    report_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Report:
    """Dependency: load Report or raise 404."""
    report = await db.get(Report, report_id)
    if not report:
        raise NotFoundError("Report", report_id)
    return report
