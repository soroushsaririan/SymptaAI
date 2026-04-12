"""Lab result model."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class LabResult(Base):
    __tablename__ = "lab_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True
    )
    test_name: Mapped[str] = mapped_column(String(255), nullable=False)
    test_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    value: Mapped[str] = mapped_column(String(100), nullable=False)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference_range: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_abnormal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    abnormality_severity: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # mild, moderate, critical
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ordering_physician: Mapped[str | None] = mapped_column(String(255), nullable=True)
    interpretation: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    patient = relationship("Patient", back_populates="lab_results")

    def __repr__(self) -> str:
        return f"<LabResult id={self.id} test={self.test_name} value={self.value}>"
