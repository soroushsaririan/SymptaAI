"""SymptaAI FastAPI application entry point."""
from __future__ import annotations

import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import redis.asyncio as aioredis
import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.v1.router import api_router
from app.api.deps import set_rag_service
import app.models  # noqa: F401 — ensure all ORM models are registered
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import LoggingMiddleware, configure_logging, get_logger
from app.db.session import engine
from app.middleware.rate_limit import RateLimitMiddleware
from app.services.rag_service import RAGService

settings = get_settings()
logger = get_logger("main")

_rag_service: RAGService | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    # ── Startup ────────────────────────────────────────────────────────
    configure_logging()
    logger.info("starting_up", app=settings.APP_NAME, version=settings.APP_VERSION, env=settings.ENVIRONMENT)

    # Verify DB connectivity
    try:
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        logger.info("database_connected")
    except Exception as exc:
        logger.error("database_connection_failed", error=str(exc))

    # Verify Redis connectivity
    try:
        r = aioredis.from_url(settings.REDIS_URL)
        await r.ping()
        await r.aclose()
        logger.info("redis_connected")
    except Exception as exc:
        logger.warning("redis_connection_failed", error=str(exc))

    # Initialize RAG service
    global _rag_service
    _rag_service = RAGService()
    try:
        await _rag_service.initialize(settings.CHROMA_PERSIST_DIRECTORY)
        set_rag_service(_rag_service)
        logger.info("rag_service_initialized")
    except Exception as exc:
        logger.error("rag_initialization_failed", error=str(exc))

    # Sentry
    if settings.SENTRY_DSN:
        import sentry_sdk
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT,
            traces_sample_rate=0.1,
        )
        logger.info("sentry_initialized")

    logger.info("startup_complete")
    yield

    # ── Shutdown ───────────────────────────────────────────────────────
    logger.info("shutting_down")
    await engine.dispose()
    logger.info("shutdown_complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Production-grade Agentic AI Healthcare Assistant Platform",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # ── Middleware ─────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "https://yourdomain.com"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(LoggingMiddleware)

    # ── Exception handlers ────────────────────────────────────────────
    register_exception_handlers(app)

    # ── Routers ───────────────────────────────────────────────────────
    app.include_router(api_router, prefix="/api/v1")

    # ── Prometheus metrics ────────────────────────────────────────────
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")

    # ── Health check ──────────────────────────────────────────────────
    @app.get("/health", tags=["Infrastructure"])
    async def health_check() -> dict:
        return {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @app.get("/", tags=["Infrastructure"])
    async def root() -> dict:
        return {"app": settings.APP_NAME, "version": settings.APP_VERSION, "docs": "/docs"}

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        log_level=settings.LOG_LEVEL.lower(),
    )
