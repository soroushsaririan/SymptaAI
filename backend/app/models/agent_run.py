"""Agent run model — tracks workflow execution."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True
    )
    initiated_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    workflow_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="full_analysis"
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    # Statuses: pending, running, completed, failed, cancelled
    current_step: Mapped[str | None] = mapped_column(String(100), nullable=True)
    steps_completed: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    input_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    output_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    tokens_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    patient = relationship("Patient", back_populates="agent_runs")
    initiator = relationship("User", back_populates="agent_runs", foreign_keys=[initiated_by])
    report = relationship("Report", back_populates="agent_run", foreign_keys="Report.agent_run_id")

    def __repr__(self) -> str:
        return f"<AgentRun id={self.id} status={self.status} patient={self.patient_id}>"
