"""Lab results endpoints."""
from __future__ import annotations

import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ClinicalStaff, CurrentUser
from app.db.session import get_db
from app.models.lab_result import LabResult
from app.core.exceptions import NotFoundError
from datetime import datetime, timezone

router = APIRouter()


class LabCreate:
    pass  # Defined inline below


from pydantic import BaseModel


class LabCreateSchema(BaseModel):
    patient_id: uuid.UUID
    test_name: str
    test_code: Optional[str] = None
    value: str
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    is_abnormal: bool = False
    abnormality_severity: Optional[str] = None
    collected_at: datetime
    ordering_physician: Optional[str] = None
    raw_data: Optional[dict] = None


class LabResponseSchema(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    patient_id: uuid.UUID
    test_name: str
    test_code: Optional[str]
    value: str
    unit: Optional[str]
    reference_range: Optional[str]
    is_abnormal: bool
    abnormality_severity: Optional[str]
    collected_at: datetime
    ordering_physician: Optional[str]
    interpretation: Optional[str]
    created_at: datetime


@router.post("", response_model=LabResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_lab(
    data: LabCreateSchema,
    current_user: ClinicalStaff,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LabResult:
    lab = LabResult(**data.model_dump())
    db.add(lab)
    await db.flush()
    return lab


@router.post("/bulk", response_model=list[LabResponseSchema], status_code=status.HTTP_201_CREATED)
async def bulk_create_labs(
    data: list[LabCreateSchema],
    current_user: ClinicalStaff,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[LabResult]:
    labs = [LabResult(**item.model_dump()) for item in data]
    db.add_all(labs)
    await db.flush()
    return labs


class PaginatedLabsResponse(BaseModel):
    items: list[LabResponseSchema]
    total: int
    limit: int
    offset: int


@router.get("", response_model=PaginatedLabsResponse)
async def list_labs(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    patient_id: Optional[uuid.UUID] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> PaginatedLabsResponse:
    from sqlalchemy import func

    base_query = select(LabResult)
    if patient_id:
        base_query = base_query.where(LabResult.patient_id == patient_id)

    total_result = await db.execute(select(func.count()).select_from(base_query.subquery()))
    total = total_result.scalar_one()

    items_result = await db.execute(
        base_query.order_by(LabResult.collected_at.desc()).limit(limit).offset(offset)
    )
    items = list(items_result.scalars().all())
    return PaginatedLabsResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/patient/{patient_id}/critical", response_model=list[LabResponseSchema])
async def get_critical_labs(
    patient_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[LabResult]:
    """Get critical lab values for a patient."""
    result = await db.execute(
        select(LabResult)
        .where(LabResult.patient_id == patient_id)
        .where(LabResult.abnormality_severity == "critical")
        .order_by(LabResult.collected_at.desc())
    )
    return list(result.scalars().all())


@router.get("/{lab_id}", response_model=LabResponseSchema)
async def get_lab(
    lab_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LabResult:
    lab = await db.get(LabResult, lab_id)
    if not lab:
        raise NotFoundError("LabResult", lab_id)
    return lab


@router.delete("/{lab_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lab(
    lab_id: uuid.UUID,
    current_user: ClinicalStaff,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    lab = await db.get(LabResult, lab_id)
    if not lab:
        raise NotFoundError("LabResult", lab_id)
    await db.delete(lab)
    await db.flush()
