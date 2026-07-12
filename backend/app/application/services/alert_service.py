from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.domain.entities.alert import Alert, AlertStatus, AlertType
from app.domain.entities.user import User
from app.domain.interfaces.external_services import IBigQueryService, IPubSubService, PubSubMessage
from app.domain.interfaces.repositories import IAlertRepository, IUserRepository
from app.domain.value_objects.coordinates import LatLong
from app.domain.value_objects.gps_sector import GpsSector
from app.domain.value_objects.priority import Priority

logger = logging.getLogger(__name__)

BIGQUERY_DATASET = "stadiumos_analytics"
BIGQUERY_TABLE_ALERTS = "alert_events"


class AlertService:
    def __init__(
        self,
        alert_repo: IAlertRepository,
        user_repo: IUserRepository,
        pubsub: IPubSubService | None = None,
        bigquery: IBigQueryService | None = None,
    ) -> None:
        self._alerts = alert_repo
        self._users = user_repo
        self._pubsub = pubsub
        self._bigquery = bigquery

    async def create_alert(
        self,
        alert_type: str,
        title: str,
        description: str,
        stadium_id: UUID,
        priority: Priority = Priority.MEDIUM,
        sector: GpsSector | None = None,
        location: LatLong | None = None,
        event_id: UUID | None = None,
        affected_sectors: list[GpsSector] | None = None,
        triggered_by_user_id: UUID | None = None,
        triggered_by_ai: bool = False,
        ai_confidence: float | None = None,
        metadata: dict[str, str] | None = None,
    ) -> Alert:
        try:
            a_type = AlertType(alert_type)
        except ValueError:
            a_type = AlertType.GENERIC

        alert = Alert(
            alert_type=a_type,
            priority=priority,
            title=title,
            description=description,
            stadium_id=stadium_id,
            event_id=event_id,
            sector=sector,
            location=location,
            triggered_by_user_id=triggered_by_user_id,
            triggered_by_ai=triggered_by_ai,
            ai_confidence=ai_confidence,
            affected_sectors=affected_sectors or [],
            metadata=metadata or {},
        )

        created = await self._alerts.create(alert)
        logger.info("Alert created: %s (type=%s, priority=%d)", created.id, a_type.value, priority.value)

        await self._publish_alert_event(created, "alert_created")
        await self._log_alert_event(created, "created")

        return created

    async def get_alert(self, alert_id: UUID) -> Alert | None:
        return await self._alerts.get_by_id(alert_id)

    async def update_alert(
        self,
        alert_id: UUID,
        title: str | None = None,
        description: str | None = None,
        priority: Priority | None = None,
        sector: GpsSector | None = None,
        location: LatLong | None = None,
        metadata: dict[str, str] | None = None,
    ) -> Alert | None:
        alert = await self._alerts.get_by_id(alert_id)
        if alert is None:
            return None

        if title is not None:
            alert.title = title
        if description is not None:
            alert.description = description
        if priority is not None:
            alert.priority = priority
        if sector is not None:
            alert.sector = sector
        if location is not None:
            alert.location = location
        if metadata is not None:
            alert.metadata.update(metadata)
        alert.updated_at = datetime.now(timezone.utc)

        updated = await self._alerts.update(alert)
        logger.info("Alert updated: %s", alert_id)

        await self._publish_alert_event(updated, "alert_updated")
        return updated

    async def list_active_alerts(
        self,
        stadium_id: UUID | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Alert]:
        if stadium_id is not None:
            all_alerts = await self._alerts.list_by_stadium(
                stadium_id, offset=offset, limit=limit * 5
            )
            return [a for a in all_alerts if a.is_active()][:limit]
        return await self._alerts.list_active(offset=offset, limit=limit)

    async def list_alerts_by_status(
        self,
        status: AlertStatus,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Alert]:
        return await self._alerts.list_by_status(status, offset=offset, limit=limit)

    async def list_alerts_by_type(
        self,
        alert_type: AlertType,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Alert]:
        return await self._alerts.list_by_type(alert_type, offset=offset, limit=limit)

    async def escalate_alert(self, alert_id: UUID, user_id: UUID | None = None) -> Alert | None:
        alert = await self._alerts.get_by_id(alert_id)
        if alert is None:
            return None

        if not alert.is_active():
            logger.warning("Cannot escalate inactive alert %s", alert_id)
            return alert

        alert.escalate()
        if user_id is not None:
            alert.assigned_to_user_id = user_id

        updated = await self._alerts.update(alert)
        logger.info(
            "Alert escalated: %s to level %d", alert_id, updated.escalation_level
        )

        await self._publish_alert_event(updated, "alert_escalated")
        await self._log_alert_event(updated, "escalated")

        return updated

    async def resolve_alert(self, alert_id: UUID) -> Alert | None:
        alert = await self._alerts.get_by_id(alert_id)
        if alert is None:
            return None

        alert.resolve()
        updated = await self._alerts.update(alert)
        logger.info("Alert resolved: %s", alert_id)

        await self._publish_alert_event(updated, "alert_resolved")
        await self._log_alert_event(updated, "resolved")

        return updated

    async def acknowledge_alert(
        self, alert_id: UUID, user_id: UUID
    ) -> Alert | None:
        alert = await self._alerts.get_by_id(alert_id)
        if alert is None:
            return None

        alert.acknowledge(user_id)
        updated = await self._alerts.update(alert)
        logger.info("Alert acknowledged: %s by user %s", alert_id, user_id)

        await self._publish_alert_event(updated, "alert_acknowledged")
        return updated

    async def cancel_alert(self, alert_id: UUID) -> Alert | None:
        alert = await self._alerts.get_by_id(alert_id)
        if alert is None:
            return None

        alert.cancel()
        updated = await self._alerts.update(alert)
        logger.info("Alert cancelled: %s", alert_id)

        await self._publish_alert_event(updated, "alert_cancelled")
        return updated

    async def get_active_alert_count(self, stadium_id: UUID | None = None) -> int:
        if stadium_id is not None:
            return await self._alerts.count_active_by_stadium(stadium_id)
        return await self._alerts.count_active()

    async def _publish_alert_event(self, alert: Alert, event_type: str) -> None:
        if self._pubsub is None:
            return
        try:
            message = PubSubMessage(
                topic="stadiumos-alerts",
                data={
                    "event_type": event_type,
                    "alert_id": str(alert.id),
                    "alert_type": alert.alert_type.value,
                    "priority": alert.priority.value,
                    "status": alert.status.value,
                    "title": alert.title,
                    "stadium_id": str(alert.stadium_id),
                    "sector": alert.sector.value if alert.sector else None,
                    "escalation_level": alert.escalation_level,
                    "timestamp": alert.updated_at.isoformat(),
                },
                attributes={
                    "alert_id": str(alert.id),
                    "alert_type": alert.alert_type.value,
                    "priority": alert.priority.label(),
                },
            )
            await self._pubsub.publish("stadiumos-alerts", message)
        except Exception:
            logger.exception("Failed to publish alert event to Pub/Sub")

    async def _log_alert_event(self, alert: Alert, action: str) -> None:
        if self._bigquery is None:
            return
        try:
            row: dict[str, Any] = {
                "alert_id": str(alert.id),
                "alert_type": alert.alert_type.value,
                "priority": alert.priority.value,
                "status": alert.status.value,
                "title": alert.title,
                "stadium_id": str(alert.stadium_id),
                "event_id": str(alert.event_id) if alert.event_id else None,
                "sector": alert.sector.value if alert.sector else None,
                "escalation_level": alert.escalation_level,
                "action": action,
                "triggered_by_ai": alert.triggered_by_ai,
                "timestamp": alert.updated_at.isoformat(),
            }
            if alert.response_time_seconds() is not None:
                row["response_time_seconds"] = alert.response_time_seconds()
            if alert.resolution_time_seconds() is not None:
                row["resolution_time_seconds"] = alert.resolution_time_seconds()
            await self._bigquery.insert_rows(BIGQUERY_DATASET, BIGQUERY_TABLE_ALERTS, [row])
        except Exception:
            logger.exception("Failed to log alert event to BigQuery")
