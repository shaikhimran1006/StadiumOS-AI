from __future__ import annotations

import logging
import time
from collections import defaultdict
from typing import Any

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.config.settings import settings

logger = logging.getLogger(__name__)


class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Any, max_requests_per_minute: int | None = None) -> None:
        super().__init__(app)
        self._max_requests = max_requests_per_minute or settings.RATE_LIMIT_PER_MINUTE
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _get_client_id(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"

    def _clean_old_entries(self, client_id: str, now: float) -> None:
        window = now - 60.0
        self._requests[client_id] = [
            ts for ts in self._requests[client_id] if ts > window
        ]

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if request.url.path.endswith("/health") or request.url.path.endswith("/ready"):
            return await call_next(request)

        client_id = self._get_client_id(request)
        now = time.time()

        self._clean_old_entries(client_id, now)

        request_count = len(self._requests[client_id])

        remaining = max(0, self._max_requests - request_count - 1)
        reset_time = int(now) + 60

        if request_count >= self._max_requests:
            logger.warning(
                "Rate limit exceeded for client %s: %d requests in window",
                client_id,
                request_count,
            )
            return Response(
                content='{"error": {"code": "RATE_LIMIT_EXCEEDED", "message": "Rate limit exceeded. Please try again later."}}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={
                    "Content-Type": "application/json",
                    "X-RateLimit-Limit": str(self._max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_time),
                    "Retry-After": "60",
                },
                media_type="application/json",
            )

        self._requests[client_id].append(now)

        response = await call_next(request)

        response.headers["X-RateLimit-Limit"] = str(self._max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)

        return response
