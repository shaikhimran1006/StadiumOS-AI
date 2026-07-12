from __future__ import annotations

import json
import logging
from typing import Any

from google.cloud import secretmanager

from app.core.config.settings import settings

logger = logging.getLogger(__name__)


class SecretManagerService:
    def __init__(self) -> None:
        self._client = secretmanager.SecretManagerServiceClient()
        self._parent = f"projects/{settings.GCP_PROJECT_ID}"

    def _build_secret_path(self, secret_id: str, version: str = "latest") -> str:
        return f"{self._parent}/secrets/{secret_id}/versions/{version}"

    def _build_secret_name(self, secret_id: str) -> str:
        return f"{self._parent}/secrets/{secret_id}"

    async def get_secret(self, secret_id: str, default: str | None = None) -> str | None:
        try:
            return await self.access_secret_version(secret_id)
        except Exception as exc:
            logger.warning("Secret %s not found: %s", secret_id, exc)
            return default

    async def set_secret(
        self, secret_id: str, payload: str | dict[str, Any],
    ) -> str:
        if isinstance(payload, dict):
            payload = json.dumps(payload)
        secret_name = self._build_secret_name(secret_id)
        try:
            self._client.get_secret(request={"name": secret_name})
        except Exception:
            self._client.create_secret(
                request={
                    "parent": self._parent,
                    "secret_id": secret_id,
                    "secret": {"replication": {"automatic": {}}},
                }
            )
        version = self._client.add_secret_version(
            request={
                "parent": secret_name,
                "payload": {"data": payload.encode("utf-8")},
            }
        )
        logger.info("Set secret %s version %s", secret_id, version.name)
        return version.name

    async def list_secrets(self) -> list[dict[str, Any]]:
        secrets = self._client.list_secrets(request={"parent": self._parent})
        results = []
        for secret in secrets:
            labels = dict(secret.labels) if secret.labels else {}
            results.append({
                "name": secret.name,
                "labels": labels,
                "create_time": secret.create_time.isoformat() if secret.create_time else None,
            })
        return results

    async def access_secret_version(self, secret_id: str, version: str = "latest") -> str:
        name = self._build_secret_path(secret_id, version)
        response = self._client.access_secret_version(request={"name": name})
        payload = response.payload.data.decode("utf-8")
        return payload

    async def delete_secret(self, secret_id: str) -> bool:
        name = self._build_secret_name(secret_id)
        try:
            self._client.delete_secret(request={"name": name})
            logger.info("Deleted secret %s", name)
            return True
        except Exception as exc:
            logger.error("Failed to delete secret %s: %s", name, exc)
            return False
