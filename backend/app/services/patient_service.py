"""Patient business logic service."""
from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.core.logging import get_logger
from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientIntakeRequest, PatientUpdate

logger = get_logger("service.patient")


class PatientService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_patient(self, data: PatientCreate, created_by: uuid.UUID) -> Patient:
        """Create a new patient record with auto-generated MRN."""
        mrn = await self.generate_mrn()
        # Check email uniqueness if provided
        if data.email:
            existing = await self.db.execute(
                select(Patient).where(Patient.email == data.email, Patient.is_deleted == False)  # noqa: E712
            )
            if existing.scalar_one_or_none():
                raise ConflictError(f"A patient with email {data.email} already exists")

        meds = [m.model_dump() for m in data.current_medications] if data.current_medications else []

        patient = Patient(
            mrn=mrn,
            first_name=data.first_name,
            last_name=data.last_name,
            date_of_birth=data.date_of_birth,
            gender=data.gender,
            email=data.email,
            phone=data.phone,
            address=data.address,
            emergency_contact=data.emergency_contact,
            insurance_info=data.insurance_info,
            allergies=data.allergies,
            current_medications=meds,
            medical_history=data.medical_history,
            family_history=data.family_history,
            created_by=created_by,
        )
        self.db.add(patient)
        await self.db.flush()
        logger.info("patient_created", patient_id=str(patient.id), mrn=mrn)
        return patient

    async def get_patient(self, patient_id: uuid.UUID) -> Patient:
        """Get a patient by ID, raising NotFoundError if missing."""
        patient = await self.db.get(Patient, patient_id)
        if not patient or patient.is_deleted:
            raise NotFoundError("Patient", patient_id)
        return patient

    async def get_by_mrn(self, mrn: str) -> Patient | None:
        """Lookup patient by medical record number."""
        result = await self.db.execute(
            select(Patient).where(Patient.mrn == mrn, Patient.is_deleted == False)  # noqa: E712
        )
        return result.scalar_one_or_none()

    async def list_patients(
        self,
        limit: int = 20,
        offset: int = 0,
        search: str | None = None,
    ) -> tuple[list[Patient], int]:
        """List patients with optional name/MRN search and pagination."""
        query = select(Patient).where(Patient.is_deleted == False)  # noqa: E712

        if search:
            like = f"%{search}%"
            query = query.where(
                or_(
                    Patient.first_name.ilike(like),
                    Patient.last_name.ilike(like),
                    Patient.mrn.ilike(like),
                    Patient.email.ilike(like),
                )
            )

        count_q = select(func.count()).select_from(query.subquery())
        count_result = await self.db.execute(count_q)
        total = count_result.scalar_one()

        query = query.order_by(Patient.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        patients = list(result.scalars().all())
        return patients, total

    async def update_patient(self, patient_id: uuid.UUID, data: PatientUpdate) -> Patient:
        """Partially update patient fields."""
        patient = await self.get_patient(patient_id)
        update_data = data.model_dump(exclude_none=True)
        if "current_medications" in update_data:
            update_data["current_medications"] = [
                m.model_dump() if hasattr(m, "model_dump") else m
                for m in update_data["current_medications"]
            ]
        for field, value in update_data.items():
            setattr(patient, field, value)
        await self.db.flush()
        return patient

    async def submit_intake(
        self, patient_id: uuid.UUID, intake: PatientIntakeRequest
    ) -> Patient:
        """Update patient with clinical intake data."""
        patient = await self.get_patient(patient_id)
        patient.chief_complaint = intake.chief_complaint
        patient.symptoms = intake.symptoms
        patient.intake_completed = True
        if intake.vitals:
            patient.vitals = intake.vitals.model_dump(exclude_none=True)
        await self.db.flush()
        logger.info("intake_submitted", patient_id=str(patient_id))
        return patient

    async def soft_delete(self, patient_id: uuid.UUID) -> None:
        """Soft-delete a patient record (HIPAA-safe — retains audit trail)."""
        patient = await self.get_patient(patient_id)
        patient.is_deleted = True
        await self.db.flush()

    async def get_patient_summary(self, patient_id: uuid.UUID) -> dict:
        """Return a comprehensive summary dict for the patient."""
        from sqlalchemy.orm import selectinload
        result = await self.db.execute(
            select(Patient)
            .where(Patient.id == patient_id)
            .options(
                selectinload(Patient.lab_results),
                selectinload(Patient.agent_runs),
                selectinload(Patient.reports),
            )
        )
        patient = result.scalar_one_or_none()
        if not patient or patient.is_deleted:
            raise NotFoundError("Patient", patient_id)

        today = date.today()
        dob = patient.date_of_birth
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

        return {
            "patient": {
                "id": str(patient.id),
                "mrn": patient.mrn,
                "full_name": f"{patient.first_name} {patient.last_name}",
                "age": age,
                "gender": patient.gender,
                "dob": patient.date_of_birth.isoformat(),
            },
            "stats": {
                "total_labs": len(patient.lab_results),
                "critical_labs": sum(1 for l in patient.lab_results if l.abnormality_severity == "critical"),
                "total_analyses": len(patient.agent_runs),
                "total_reports": len(patient.reports),
                "last_analysis": (
                    max((r.created_at for r in patient.agent_runs), default=None)
                ),
            },
            "intake_completed": patient.intake_completed,
            "chief_complaint": patient.chief_complaint,
            "allergies": patient.allergies,
            "medications_count": len(patient.current_medications),
        }

    async def generate_mrn(self) -> str:
        """Generate a unique MRN in format MRN-YYYYMMDD-XXXXX."""
        import random
        today_str = datetime.utcnow().strftime("%Y%m%d")
        for _ in range(10):
            suffix = str(random.randint(10000, 99999))
            mrn = f"MRN-{today_str}-{suffix}"
            existing = await self.get_by_mrn(mrn)
            if not existing:
                return mrn
        raise RuntimeError("Failed to generate unique MRN after 10 attempts")
