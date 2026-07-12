from __future__ import annotations

import time
import uuid
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


class RequestTrackingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id

        start_time = time.time()

        response = await call_next(request)

        process_time = time.time() - start_time
        process_time_ms = round(process_time * 1000, 2)

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time_ms}ms"

        if hasattr(request.state, "user_id"):
            response.headers["X-User-ID"] = str(request.state.user_id)

        return response
