"""Medical record upload and processing service."""
from __future__ import annotations

import os
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.models.medical_record import MedicalRecord

settings = get_settings()
logger = get_logger("service.record")

ALLOWED_TYPES = {"application/pdf", "text/plain", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}


class RecordService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def upload_record(
        self,
        patient_id: uuid.UUID,
        file: UploadFile,
        record_type: str,
        title: str,
        uploaded_by: uuid.UUID,
    ) -> MedicalRecord:
        """Save file to disk (or S3) and create a MedicalRecord entry."""
        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)

        record_id = uuid.uuid4()
        suffix = Path(file.filename or "file.txt").suffix.lower()
        file_path = upload_dir / f"{record_id}{suffix}"

        content_bytes = await file.read()
        if len(content_bytes) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
            from app.core.exceptions import ValidationError
            raise ValidationError(f"File exceeds maximum size of {settings.MAX_FILE_SIZE_MB}MB")

        with open(file_path, "wb") as f:
            f.write(content_bytes)

        text_content = await self.extract_text(str(file_path), suffix)

        record = MedicalRecord(
            id=record_id,
            patient_id=patient_id,
            record_type=record_type,
            title=title,
            content=text_content,
            file_url=str(file_path),
            file_type=suffix.lstrip("."),
            file_size_bytes=len(content_bytes),
            uploaded_by=uploaded_by,
            processed=False,
        )
        self.db.add(record)
        await self.db.flush()
        logger.info("record_uploaded", record_id=str(record_id), patient_id=str(patient_id))
        return record

    async def extract_text(self, file_path: str, file_type: str) -> str:
        """Extract plain text from PDF, DOCX, or TXT files."""
        try:
            if file_type in (".pdf",):
                from pypdf import PdfReader
                reader = PdfReader(file_path)
                return "\n\n".join(page.extract_text() or "" for page in reader.pages)
            elif file_type in (".docx",):
                import docx
                doc = docx.Document(file_path)
                return "\n".join(para.text for para in doc.paragraphs if para.text.strip())
            else:  # .txt and others
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read()
        except Exception as exc:
            logger.warning("text_extraction_failed", file=file_path, error=str(exc))
            return ""

    async def process_record(self, record_id: uuid.UUID) -> MedicalRecord:
        """Trigger AI processing for a record via Celery."""
        record = await self.get_record(record_id)
        try:
            from app.workers.tasks import process_medical_record
            process_medical_record.delay(str(record_id))
        except Exception as exc:
            logger.warning("celery_unavailable_for_record", error=str(exc))
        return record

    async def list_records(
        self, patient_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> list[MedicalRecord]:
        result = await self.db.execute(
            select(MedicalRecord)
            .where(MedicalRecord.patient_id == patient_id)
            .order_by(MedicalRecord.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_record(self, record_id: uuid.UUID) -> MedicalRecord:
        record = await self.db.get(MedicalRecord, record_id)
        if not record:
            raise NotFoundError("MedicalRecord", record_id)
        return record

    async def delete_record(self, record_id: uuid.UUID) -> None:
        record = await self.get_record(record_id)
        if record.file_url and os.path.exists(record.file_url):
            os.remove(record.file_url)
        await self.db.delete(record)
        await self.db.flush()
