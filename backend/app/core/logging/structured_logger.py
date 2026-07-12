from __future__ import annotations

import logging
import sys
import time
from typing import Any, Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

_structlog_configured = False


def setup_logging(log_level: str = "INFO") -> None:
    global _structlog_configured
    if _structlog_configured:
        return

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper(), logging.INFO),
    )

    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    logging.getLogger("google").setLevel(logging.WARNING)
    logging.getLogger("google.api_core").setLevel(logging.WARNING)
    logging.getLogger("google.cloud").setLevel(logging.WARNING)

    _structlog_configured = True


def _get_bound_logger() -> structlog.stdlib.BoundLogger:
    return structlog.get_logger("stadiumos")


def request_logger(
    request: Request,
    response: Response,
    process_time: float,
    extra: dict[str, Any] | None = None,
) -> None:
    logger = _get_bound_logger()
    log_data: dict[str, Any] = {
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code,
        "process_time_ms": round(process_time * 1000, 2),
        "client_ip": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", ""),
        "request_id": getattr(request.state, "request_id", None),
    }
    if extra:
        log_data.update(extra)

    status_code = response.status_code
    if status_code >= 500:
        logger.error("request_completed", **log_data)
    elif status_code >= 400:
        logger.warning("request_completed", **log_data)
    else:
        logger.info("request_completed", **log_data)


def ai_interaction_logger(
    event_type: str,
    user_id: str | None = None,
    conversation_id: str | None = None,
    agent_name: str | None = None,
    confidence: float | None = None,
    latency_ms: int | None = None,
    language: str | None = None,
    **kwargs: Any,
) -> None:
    logger = _get_bound_logger()
    data: dict[str, Any] = {
        "event_category": "ai_interaction",
        "event_type": event_type,
    }
    if user_id:
        data["user_id"] = user_id
    if conversation_id:
        data["conversation_id"] = conversation_id
    if agent_name:
        data["agent_name"] = agent_name
    if confidence is not None:
        data["confidence"] = confidence
    if latency_ms is not None:
        data["latency_ms"] = latency_ms
    if language:
        data["language"] = language
    data.update(kwargs)
    logger.info("ai_interaction", **data)


def security_event_logger(
    event_type: str,
    user_id: str | None = None,
    severity: str = "INFO",
    details: dict[str, Any] | None = None,
    **kwargs: Any,
) -> None:
    logger = _get_bound_logger()
    data: dict[str, Any] = {
        "event_category": "security",
        "event_type": event_type,
        "severity": severity,
    }
    if user_id:
        data["user_id"] = user_id
    if details:
        data["details"] = details
    data.update(kwargs)

    log_method = getattr(logger, severity.lower(), logger.info)
    log_method("security_event", **data)


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        request_logger(request, response, process_time)
        return response
