"""Patient Pydantic schemas."""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class MedicationItem(BaseModel):
    name: str
    dose: str
    frequency: str
    route: str = "oral"
    indication: str | None = None


class VitalsData(BaseModel):
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    heart_rate: Optional[int] = None
    temperature_celsius: Optional[float] = None
    respiratory_rate: Optional[int] = None
    oxygen_saturation: Optional[float] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    bmi: Optional[float] = None


class PatientCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    date_of_birth: date
    gender: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[dict[str, Any]] = None
    emergency_contact: Optional[dict[str, Any]] = None
    insurance_info: Optional[dict[str, Any]] = None
    allergies: list[str] = Field(default_factory=list)
    current_medications: list[MedicationItem] = Field(default_factory=list)
    medical_history: list[dict[str, Any]] = Field(default_factory=list)
    family_history: list[str] = Field(default_factory=list)

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: str) -> str:
        allowed = {"male", "female", "non_binary", "other", "prefer_not_to_say"}
        if v.lower() not in allowed:
            raise ValueError(f"Gender must be one of: {', '.join(allowed)}")
        return v.lower()

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v: date) -> date:
        from datetime import date as date_type
        if v > date_type.today():
            raise ValueError("Date of birth cannot be in the future")
        return v


class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[dict[str, Any]] = None
    emergency_contact: Optional[dict[str, Any]] = None
    insurance_info: Optional[dict[str, Any]] = None
    allergies: Optional[list[str]] = None
    current_medications: Optional[list[MedicationItem]] = None
    medical_history: Optional[list[dict[str, Any]]] = None
    family_history: Optional[list[str]] = None


class PatientResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    mrn: str
    first_name: str
    last_name: str
    date_of_birth: date
    gender: str
    email: Optional[str]
    phone: Optional[str]
    allergies: list[Any]
    current_medications: list[Any]
    medical_history: list[Any]
    family_history: list[Any]
    chief_complaint: Optional[str]
    symptoms: list[Any]
    vitals: Optional[dict[str, Any]]
    intake_completed: bool
    created_at: datetime
    updated_at: datetime

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self) -> int:
        from datetime import date as date_type
        today = date_type.today()
        dob = self.date_of_birth
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


class PatientListResponse(BaseModel):
    items: list[PatientResponse]
    total: int
    limit: int
    offset: int


class PatientIntakeRequest(BaseModel):
    """Clinical intake form submitted at point of care."""
    chief_complaint: str = Field(min_length=1, max_length=500)
    symptoms: list[str] = Field(min_length=1)
    symptom_duration: str
    severity: int = Field(ge=1, le=10)
    vitals: Optional[VitalsData] = None
    additional_history: Optional[str] = None
    onset_description: Optional[str] = None
