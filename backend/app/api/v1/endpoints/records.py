"""Medical records upload and management endpoints."""
from __future__ import annotations

import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ClinicalStaff, CurrentUser
from app.db.session import get_db
from app.schemas.report import ReportResponse
from app.services.record_service import RecordService
from app.core.exceptions import NotFoundError
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class MedicalRecordResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    patient_id: uuid.UUID
    record_type: str
    title: str
    content: Optional[str]
    structured_summary: Optional[dict]
    file_url: Optional[str]
    file_type: Optional[str]
    file_size_bytes: Optional[int]
    processed: bool
    processing_error: Optional[str]
    created_at: datetime


@router.post("/upload", response_model=MedicalRecordResponse, status_code=status.HTTP_201_CREATED)
async def upload_record(
    current_user: ClinicalStaff,
    db: Annotated[AsyncSession, Depends(get_db)],
    file: UploadFile = File(...),
    patient_id: uuid.UUID = Form(...),
    record_type: str = Form(default="clinical_note"),
    title: str = Form(...),
) -> MedicalRecordResponse:
    """Upload a medical record file (PDF, DOCX, or TXT)."""
    service = RecordService(db)
    record = await service.upload_record(
        patient_id=patient_id,
        file=file,
        record_type=record_type,
        title=title,
        uploaded_by=current_user.id,
    )
    return MedicalRecordResponse.model_validate(record)


class PaginatedRecordsResponse(BaseModel):
    items: list[MedicalRecordResponse]
    total: int
    limit: int
    offset: int


@router.get("", response_model=PaginatedRecordsResponse)
async def list_records(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    patient_id: Optional[uuid.UUID] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> PaginatedRecordsResponse:
    """List medical records, optionally filtered by patient."""
    if not patient_id:
        return PaginatedRecordsResponse(items=[], total=0, limit=limit, offset=offset)
    service = RecordService(db)
    records = await service.list_records(patient_id, limit=limit, offset=offset)
    items = [MedicalRecordResponse.model_validate(r) for r in records]
    return PaginatedRecordsResponse(items=items, total=len(items), limit=limit, offset=offset)


@router.get("/{record_id}", response_model=MedicalRecordResponse)
async def get_record(
    record_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MedicalRecordResponse:
    service = RecordService(db)
    record = await service.get_record(record_id)
    return MedicalRecordResponse.model_validate(record)


@router.post("/{record_id}/process", response_model=MedicalRecordResponse)
async def process_record(
    record_id: uuid.UUID,
    current_user: ClinicalStaff,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MedicalRecordResponse:
    """Trigger AI summarization of an uploaded record."""
    service = RecordService(db)
    record = await service.process_record(record_id)
    return MedicalRecordResponse.model_validate(record)


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_record(
    record_id: uuid.UUID,
    current_user: ClinicalStaff,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    service = RecordService(db)
    await service.delete_record(record_id)
