from __future__ import annotations

import json
import logging
from typing import Any

from google.cloud import scheduler
from google.cloud.scheduler_v1.types import Job
from google.protobuf import duration_pb2, field_mask_pb2

from app.core.config.settings import settings

logger = logging.getLogger(__name__)


class CloudSchedulerService:
    def __init__(self) -> None:
        self._client = scheduler.CloudSchedulerClient()
        self._parent = f"projects/{settings.GCP_PROJECT_ID}/locations/{settings.GCP_REGION}"

    def _build_job_path(self, job_id: str) -> str:
        return f"{self._parent}/jobs/{job_id}"

    def _build_http_target(
        self, uri: str, method: str = "POST",
        body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict:
        http_target = {
            "uri": uri,
            "http_method": method.upper(),
            "headers": headers or {"Content-Type": "application/json"},
        }
        if body:
            http_target["body"] = json.dumps(body).encode("utf-8")
        return http_target

    async def create_job(
        self, job_id: str, schedule: str, uri: str,
        method: str = "POST", body: dict[str, Any] | None = None,
        timezone: str = "UTC", description: str = "",
        headers: dict[str, str] | None = None,
    ) -> Job:
        job = Job(
            name=self._build_job_path(job_id),
            description=description,
            schedule=schedule,
            time_zone=timezone,
            http_target=self._build_http_target(uri, method, body, headers),
        )
        parent = self._parent
        created = self._client.create_job(
            request={"parent": parent, "job": job}
        )
        logger.info("Created scheduler job %s (%s)", created.name, schedule)
        return created

    async def update_job(
        self, job_id: str, schedule: str | None = None,
        uri: str | None = None, method: str | None = None,
        body: dict[str, Any] | None = None,
        description: str | None = None, enabled: bool | None = None,
    ) -> Job:
        name = self._build_job_path(job_id)
        job = Job(name=name)
        paths: list[str] = []

        if schedule is not None:
            job.schedule = schedule
            paths.append("schedule")
        if description is not None:
            job.description = description
            paths.append("description")
        if enabled is not None:
            job.state = Job.State.ENABLED if enabled else Job.State.DISABLED
            paths.append("state")
        if uri is not None or method is not None or body is not None:
            http_target = self._build_http_target(
                uri or "", method or "POST", body,
            )
            job.http_target = http_target
            paths.append("http_target")

        update_mask = field_mask_pb2.FieldMask(paths=paths)
        updated = self._client.update_job(
            request={"job": job, "update_mask": update_mask}
        )
        logger.info("Updated scheduler job %s", name)
        return updated

    async def delete_job(self, job_id: str) -> bool:
        name = self._build_job_path(job_id)
        try:
            self._client.delete_job(request={"name": name})
            logger.info("Deleted scheduler job %s", name)
            return True
        except Exception as exc:
            logger.error("Failed to delete job %s: %s", name, exc)
            return False

    async def list_jobs(self) -> list[dict[str, Any]]:
        jobs = self._client.list_jobs(request={"parent": self._parent})
        results = []
        for job in jobs:
            http = job.http_target
            results.append({
                "name": job.name,
                "schedule": job.schedule,
                "time_zone": job.time_zone,
                "description": job.description,
                "state": Job.State.Name(job.state),
                "uri": http.uri if http else None,
                "http_method": http.http_method if http else None,
                "user_update_time": job.user_update_time.isoformat() if job.user_update_time else None,
            })
        return results

    async def run_job(self, job_id: str) -> bool:
        name = self._build_job_path(job_id)
        try:
            self._client.run_job(request={"name": name})
            logger.info("Triggered manual run of job %s", name)
            return True
        except Exception as exc:
            logger.error("Failed to run job %s: %s", name, exc)
            return False

    async def pause_job(self, job_id: str) -> Job:
        return await self.update_job(job_id, enabled=False)

    async def resume_job(self, job_id: str) -> Job:
        return await self.update_job(job_id, enabled=True)
