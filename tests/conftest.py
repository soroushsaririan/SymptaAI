"""
Shared pytest fixtures for SymptaAI test suite.
All async tests use pytest-asyncio with asyncio_mode = auto (set in pytest.ini).
"""
from __future__ import annotations

import asyncio
import os
import uuid
from collections.abc import AsyncGenerator
from datetime import date, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

# ---------------------------------------------------------------------------
# Force test environment BEFORE importing any app code
# ---------------------------------------------------------------------------
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-at-least-32-chars-long-ok")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("APP_ENV", "test")

from app.core.security import create_access_token, get_password_hash

# ---------------------------------------------------------------------------
# Database fixtures
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest_asyncio.fixture(scope="session")
async def engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create a test database engine (SQLite in-memory for speed)."""
    from app.db.session import Base

    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional database session, rolled back after each test."""
    from sqlalchemy.ext.asyncio import async_sessionmaker

    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        async with session.begin():
            yield session
            await session.rollback()


# ---------------------------------------------------------------------------
# FastAPI test client
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client wired to the FastAPI app with overridden DB session."""
    from app.db.session import get_db
    from main import app  # deferred — only needed for integration tests

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def test_user_data() -> dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "email": "testphysician@hospital.com",
        "full_name": "Dr. Test Physician",
        "role": "physician",
        "is_active": True,
        "is_verified": True,
    }


@pytest.fixture
def auth_token(test_user_data: dict[str, Any]) -> str:
    return create_access_token(
        data={
            "sub": test_user_data["id"],
            "email": test_user_data["email"],
            "role": test_user_data["role"],
        }
    )


@pytest.fixture
def auth_headers(auth_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth_token}"}


# ---------------------------------------------------------------------------
# Sample data factories
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_patient_data() -> dict[str, Any]:
    return {
        "first_name": "Jane",
        "last_name": "Doe",
        "date_of_birth": "1985-03-15",
        "gender": "female",
        "email": "jane.doe@example.com",
        "phone": "+1-555-0100",
        "allergies": ["Penicillin", "Sulfa drugs"],
        "current_medications": [
            {"name": "Metformin", "dose": "500mg", "frequency": "twice daily"},
            {"name": "Lisinopril", "dose": "10mg", "frequency": "once daily"},
        ],
        "medical_history": ["Type 2 Diabetes", "Hypertension"],
        "family_history": ["Coronary artery disease"],
    }


@pytest.fixture
def sample_lab_data() -> dict[str, Any]:
    return {
        "test_name": "Hemoglobin A1c",
        "test_code": "HBA1C",
        "value": "8.2",
        "unit": "%",
        "reference_range": "< 5.7",
        "is_abnormal": True,
        "abnormality_severity": "moderate",
        "collected_at": "2024-01-15T10:30:00Z",
        "ordering_physician": "Dr. Smith",
    }


@pytest.fixture
def mock_openai():
    """Mock OpenAI API calls to avoid incurring costs in tests."""
    with patch("langchain_openai.ChatOpenAI") as mock:
        mock_instance = MagicMock()
        mock_instance.invoke = AsyncMock(
            return_value=MagicMock(content="Mocked LLM response for testing")
        )
        mock_instance.astream = AsyncMock(return_value=iter([]))
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_rag_service():
    """Mock RAG service to avoid ChromaDB dependency in unit tests."""
    with patch("app.services.rag_service.RAGService") as mock:
        mock_instance = MagicMock()
        mock_instance.search = AsyncMock(
            return_value=[
                {
                    "content": "Normal HbA1c range is < 5.7%. Diabetic range > 6.5%.",
                    "source": "ADA 2024 Guidelines",
                    "relevance_score": 0.95,
                }
            ]
        )
        mock.return_value = mock_instance
        yield mock_instance
