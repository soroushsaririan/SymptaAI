"""Import all models so Alembic can discover them for migrations."""
from app.db.session import Base  # noqa: F401

# Import all models — order matters for FK resolution
from app.models.user import User  # noqa: F401
from app.models.patient import Patient  # noqa: F401
from app.models.medical_record import MedicalRecord  # noqa: F401
from app.models.lab_result import LabResult  # noqa: F401
from app.models.agent_run import AgentRun  # noqa: F401
from app.models.report import Report  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
