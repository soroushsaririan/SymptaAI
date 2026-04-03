"""Analysis and agent run Pydantic schemas."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class AnalysisRequest(BaseModel):
    patient_id: uuid.UUID
    include_labs: bool = True
    include_records: bool = True
    additional_context: Optional[str] = None
    workflow_type: str = "full_analysis"


class AnalysisResponse(BaseModel):
    agent_run_id: uuid.UUID
    status: str
    message: str
    estimated_duration_seconds: int = 120


class AgentRunStatus(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    patient_id: uuid.UUID
    status: str
    current_step: Optional[str]
    steps_completed: list[str]
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    tokens_used: int
    created_at: datetime


class StreamEvent(BaseModel):
    """Server-sent event from the agent workflow."""
    event_type: str
    # Types: step_start, step_complete, step_error, workflow_complete, workflow_error
    agent_name: Optional[str] = None
    data: dict[str, Any] = {}
    timestamp: datetime
    run_id: str
