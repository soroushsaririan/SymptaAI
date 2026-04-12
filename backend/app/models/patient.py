"""Patient model — core PHI entity."""
from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    mrn: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    address: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    emergency_contact: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    insurance_info: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    allergies: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    current_medications: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    medical_history: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    family_history: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    # Intake fields (populated during clinical intake)
    chief_complaint: Mapped[str | None] = mapped_column(Text, nullable=True)
    symptoms: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    vitals: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    intake_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    creator = relationship("User", back_populates="patients", foreign_keys=[created_by])
    medical_records = relationship("MedicalRecord", back_populates="patient")
    lab_results = relationship("LabResult", back_populates="patient")
    reports = relationship("Report", back_populates="patient")
    agent_runs = relationship("AgentRun", back_populates="patient")

    def __repr__(self) -> str:
        return f"<Patient id={self.id} mrn={self.mrn} name={self.last_name}, {self.first_name}>"
