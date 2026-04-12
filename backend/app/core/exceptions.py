"""Custom exception hierarchy and FastAPI exception handlers."""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        detail: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        extra: dict[str, Any] | None = None,
    ) -> None:
        self.detail = detail
        self.status_code = status_code
        self.error_code = error_code
        self.extra = extra or {}
        super().__init__(detail)


class NotFoundError(AppException):
    def __init__(self, resource: str, resource_id: Any = None) -> None:
        detail = f"{resource} not found"
        if resource_id:
            detail = f"{resource} with id '{resource_id}' not found"
        super().__init__(detail=detail, status_code=404, error_code="NOT_FOUND")


class ValidationError(AppException):
    def __init__(self, detail: str, field: str | None = None) -> None:
        extra = {"field": field} if field else {}
        super().__init__(detail=detail, status_code=422, error_code="VALIDATION_ERROR", extra=extra)


class AuthenticationError(AppException):
    def __init__(self, detail: str = "Authentication required") -> None:
        super().__init__(detail=detail, status_code=401, error_code="AUTHENTICATION_ERROR")


class AuthorizationError(AppException):
    def __init__(self, detail: str = "Insufficient permissions") -> None:
        super().__init__(detail=detail, status_code=403, error_code="AUTHORIZATION_ERROR")


class RateLimitError(AppException):
    def __init__(self, retry_after: int = 60) -> None:
        super().__init__(
            detail="Rate limit exceeded",
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
            extra={"retry_after": retry_after},
        )


class AgentExecutionError(AppException):
    def __init__(self, agent: str, detail: str) -> None:
        super().__init__(
            detail=f"Agent '{agent}' failed: {detail}",
            status_code=500,
            error_code="AGENT_EXECUTION_ERROR",
            extra={"agent": agent},
        )


class ExternalServiceError(AppException):
    def __init__(self, service: str, detail: str) -> None:
        super().__init__(
            detail=f"External service '{service}' error: {detail}",
            status_code=502,
            error_code="EXTERNAL_SERVICE_ERROR",
            extra={"service": service},
        )


class ConflictError(AppException):
    def __init__(self, detail: str) -> None:
        super().__init__(detail=detail, status_code=409, error_code="CONFLICT")


def _error_response(exc: AppException) -> JSONResponse:
    content: dict[str, Any] = {
        "error": exc.error_code,
        "detail": exc.detail,
    }
    if exc.extra:
        content["extra"] = exc.extra
    return JSONResponse(status_code=exc.status_code, content=content)


def register_exception_handlers(app: FastAPI) -> None:
    """Register all custom exception handlers on the FastAPI app."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        return _error_response(exc)

    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
        return _error_response(exc)

    @app.exception_handler(AuthenticationError)
    async def auth_handler(request: Request, exc: AuthenticationError) -> JSONResponse:
        return _error_response(exc)

    @app.exception_handler(AuthorizationError)
    async def authz_handler(request: Request, exc: AuthorizationError) -> JSONResponse:
        return _error_response(exc)

    @app.exception_handler(RateLimitError)
    async def rate_limit_handler(request: Request, exc: RateLimitError) -> JSONResponse:
        response = _error_response(exc)
        response.headers["Retry-After"] = str(exc.extra.get("retry_after", 60))
        return response

    @app.exception_handler(AgentExecutionError)
    async def agent_error_handler(request: Request, exc: AgentExecutionError) -> JSONResponse:
        return _error_response(exc)
