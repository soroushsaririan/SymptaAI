"""
Unit test conftest — sets environment variables only.
Does NOT import the FastAPI app, so heavy dependencies (langchain,
chromadb, openai) are never needed for pure unit tests.
"""
import os

# Must be set before any app module is imported
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-at-least-32-chars-long-ok")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("APP_ENV", "test")
