"""Redis-backed sliding window rate limiter middleware."""
from __future__ import annotations

import time

import redis.asyncio as aioredis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings

settings = get_settings()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-user (or per-IP) sliding window rate limiter backed by Redis.

    Uses a sorted set per user to track request timestamps in the last minute.
    Falls back gracefully if Redis is unavailable.
    """

    def __init__(self, app, limit: int | None = None) -> None:
        super().__init__(app)
        self.limit = limit or settings.RATE_LIMIT_PER_MINUTE
        self.window = 60  # seconds
        self._redis: aioredis.Redis | None = None

    async def _get_redis(self) -> aioredis.Redis | None:
        if self._redis is None:
            try:
                self._redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
                await self._redis.ping()
            except Exception:
                self._redis = None
        return self._redis

    def _get_identifier(self, request: Request) -> str:
        """Use JWT sub if available, otherwise fall back to IP address."""
        auth = request.headers.get("authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
            try:
                from app.core.security import verify_token
                data = verify_token(token)
                return f"user:{data.user_id}"
            except Exception:
                pass
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip rate limiting for health/metrics endpoints
        if request.url.path in ("/health", "/metrics", "/docs", "/openapi.json"):
            return await call_next(request)

        r = await self._get_redis()
        if r is None:
            # Redis unavailable — allow request (fail open)
            return await call_next(request)

        identifier = self._get_identifier(request)
        key = f"ratelimit:{identifier}"
        now = time.time()
        window_start = now - self.window

        try:
            pipe = r.pipeline()
            pipe.zremrangebyscore(key, "-inf", window_start)
            pipe.zadd(key, {str(now): now})
            pipe.zcard(key)
            pipe.expire(key, self.window)
            results = await pipe.execute()
            count = results[2]
        except Exception:
            self._redis = None
            return await call_next(request)

        response_headers = {
            "X-RateLimit-Limit": str(self.limit),
            "X-RateLimit-Remaining": str(max(0, self.limit - count)),
            "X-RateLimit-Reset": str(int(now + self.window)),
        }

        if count > self.limit:
            return JSONResponse(
                status_code=429,
                content={"error": "RATE_LIMIT_EXCEEDED", "detail": "Rate limit exceeded"},
                headers={**response_headers, "Retry-After": str(self.window)},
            )

        response = await call_next(request)
        for k, v in response_headers.items():
            response.headers[k] = v
        return response
