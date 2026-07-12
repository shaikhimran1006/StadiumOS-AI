from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from google.cloud import logging as cloud_logging
from google.cloud.logging_v2 import Logger as CloudLogger

from app.core.config.settings import settings

logger = logging.getLogger(__name__)

SEVERITY_MAP = {
    "DEFAULT": 0,
    "DEBUG": 100,
    "INFO": 200,
    "NOTICE": 300,
    "WARNING": 400,
    "ERROR": 500,
    "CRITICAL": 600,
    "ALERT": 700,
    "EMERGENCY": 800,
}


class CloudLoggingService:
    def __init__(self) -> None:
        self._client = cloud_logging.Client(project=settings.GCP_PROJECT_ID)
        self._client.setup_logging()
        self._logger: CloudLogger = self._client.logger("stadiumos-ai")

    async def log_entry(
        self, message: str, severity: str = "INFO",
        labels: dict[str, str] | None = None,
        resource_type: str = "global",
    ) -> None:
        severity_num = SEVERITY_MAP.get(severity.upper(), 200)
        entry = {
            "message": message,
            "severity": severity_num,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "labels": labels or {},
            "resource": {"type": resource_type},
        }
        self._logger.log_struct(entry)
        logger.debug("Logged entry: %s", message)

    async def structured_log(
        self, data: dict[str, Any], severity: str = "INFO",
    ) -> None:
        severity_num = SEVERITY_MAP.get(severity.upper(), 200)
        entry = {
            **data,
            "severity": severity_num,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._logger.log_struct(entry)

    async def log_ai_interaction(
        self, user_id: str, conversation_id: str,
        prompt: str, response: str, model_name: str,
        latency_ms: int, tokens_used: int,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        entry = {
            "type": "ai_interaction",
            "user_id": user_id,
            "conversation_id": conversation_id,
            "prompt": prompt,
            "response": response,
            "model_name": model_name,
            "latency_ms": latency_ms,
            "tokens_used": tokens_used,
            "metadata": metadata or {},
            "severity": SEVERITY_MAP["INFO"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._logger.log_struct(entry)

    async def log_security_event(
        self, event_type: str, user_id: str | None,
        ip_address: str | None, details: dict[str, Any],
        severity: str = "WARNING",
    ) -> None:
        entry = {
            "type": "security_event",
            "event_type": event_type,
            "user_id": user_id or "anonymous",
            "ip_address": ip_address or "unknown",
            "details": details,
            "severity": SEVERITY_MAP.get(severity.upper(), 400),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._logger.log_struct(entry)

    async def log_request(
        self, method: str, path: str, status_code: int,
        latency_ms: float, user_id: str | None = None,
        request_body: str | None = None,
        response_body: str | None = None,
    ) -> None:
        entry = {
            "type": "http_request",
            "method": method,
            "path": path,
            "status_code": status_code,
            "latency_ms": latency_ms,
            "user_id": user_id or "anonymous",
            "request_body": request_body,
            "response_body": response_body,
            "severity": SEVERITY_MAP["INFO"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._logger.log_struct(entry)
