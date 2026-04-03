"""Patient CRUD and intake endpoints."""
from __future__ import annotations

import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ClinicalStaff, CurrentUser, require_roles
from app.db.session import get_db
from app.schemas.patient import (
    PatientCreate,
    PatientIntakeRequest,
    PatientListResponse,
    PatientResponse,
    PatientUpdate,
)
from app.services.audit_service import AuditService
from app.services.patient_service import PatientService

router = APIRouter()


@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    data: PatientCreate,
    current_user: ClinicalStaff,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PatientResponse:
    """Create a new patient record."""
    service = PatientService(db)
    patient = await service.create_patient(data, created_by=current_user.id)
    audit = AuditService(db)
    await audit.log("create", "patient", patient.id, current_user.id, phi_accessed=True)
    return PatientResponse.model_validate(patient)


@router.get("", response_model=PatientListResponse)
async def list_patients(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    q: Optional[str] = Query(default=None, description="Search by name or MRN"),
) -> PatientListResponse:
    """List all patients with optional search and pagination."""
    service = PatientService(db)
    patients, total = await service.list_patients(limit=limit, offset=offset, search=q)
    return PatientListResponse(
        items=[PatientResponse.model_validate(p) for p in patients],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PatientResponse:
    """Get patient detail by ID."""
    service = PatientService(db)
    patient = await service.get_patient(patient_id)
    # PHI access audit
    audit = AuditService(db)
    await audit.log("read", "patient", patient_id, current_user.id, phi_accessed=True)
    return PatientResponse.model_validate(patient)


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: uuid.UUID,
    data: PatientUpdate,
    current_user: ClinicalStaff,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PatientResponse:
    """Update patient information."""
    service = PatientService(db)
    patient = await service.update_patient(patient_id, data)
    audit = AuditService(db)
    await audit.log("update", "patient", patient_id, current_user.id, phi_accessed=True)
    return PatientResponse.model_validate(patient)


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(
    patient_id: uuid.UUID,
    current_user: Annotated[object, Depends(require_roles("admin"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Soft-delete a patient record (admin only)."""
    service = PatientService(db)
    await service.soft_delete(patient_id)
    audit = AuditService(db)
    await audit.log("delete", "patient", patient_id, current_user.id)  # type: ignore


@router.post("/{patient_id}/intake", response_model=PatientResponse)
async def submit_intake(
    patient_id: uuid.UUID,
    intake: PatientIntakeRequest,
    current_user: ClinicalStaff,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PatientResponse:
    """Submit clinical intake form for a patient."""
    service = PatientService(db)
    patient = await service.submit_intake(patient_id, intake)
    audit = AuditService(db)
    await audit.log("update", "patient_intake", patient_id, current_user.id, phi_accessed=True)
    return PatientResponse.model_validate(patient)


@router.get("/{patient_id}/summary")
async def get_patient_summary(
    patient_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Get comprehensive patient summary including stats."""
    service = PatientService(db)
    return await service.get_patient_summary(patient_id)
