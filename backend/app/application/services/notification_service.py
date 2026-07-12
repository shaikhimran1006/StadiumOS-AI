from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from app.domain.entities.user import User, UserRole
from app.domain.interfaces.external_services import (
    IBigQueryService,
    IPubSubService,
    PubSubMessage,
)
from app.domain.interfaces.repositories import IUserRepository

logger = logging.getLogger(__name__)

BIGQUERY_DATASET = "stadiumos_analytics"
BIGQUERY_TABLE_NOTIFICATIONS = "notification_events"


class NotificationService:
    def __init__(
        self,
        user_repo: IUserRepository,
        pubsub: IPubSubService | None = None,
        bigquery: IBigQueryService | None = None,
    ) -> None:
        self._users = user_repo
        self._pubsub = pubsub
        self._bigquery = bigquery

    async def send_notification(
        self,
        user_id: UUID,
        title: str,
        body: str,
        notification_type: str = "info",
        data: dict[str, Any] | None = None,
        priority: str = "normal",
    ) -> bool:
        user = await self._users.get_by_id(user_id)
        if user is None:
            logger.warning("Cannot send notification: user %s not found", user_id)
            return False

        payload = {
            "user_id": str(user_id),
            "title": title,
            "body": body,
            "type": notification_type,
            "priority": priority,
            "data": data or {},
            "language": user.preferred_language.value,
        }

        published = await self._publish_notification("stadiumos-notifications", payload)
        if published:
            await self._log_notification(
                user_id=user_id,
                title=title,
                notification_type=notification_type,
                priority=priority,
                target="user",
            )
        return published

    async def send_emergency_broadcast(
        self,
        stadium_id: UUID,
        title: str,
        body: str,
        severity: str = "critical",
        sectors: list[str] | None = None,
        exclude_sectors: list[str] | None = None,
    ) -> int:
        broadcast_data = {
            "event_type": "emergency_broadcast",
            "stadium_id": str(stadium_id),
            "title": title,
            "body": body,
            "severity": severity,
            "target_sectors": sectors or [],
            "exclude_sectors": exclude_sectors or [],
        }

        sent_count = 0

        published = await self._publish_notification(
            "stadiumos-notifications",
            broadcast_data,
            attributes={"severity": severity, "broadcast": "true"},
        )
        if published:
            sent_count = 1

        if sectors is not None:
            for sector in sectors:
                sector_payload = {
                    **broadcast_data,
                    "event_type": "sector_emergency_broadcast",
                    "target_sector": sector,
                }
                sector_published = await self._publish_notification(
                    "stadiumos-notifications",
                    sector_payload,
                    attributes={
                        "severity": severity,
                        "broadcast": "true",
                        "sector": sector,
                    },
                )
                if sector_published:
                    sent_count += 1

        await self._log_notification(
            user_id=None,
            title=title,
            notification_type="emergency_broadcast",
            priority=severity,
            target=f"stadium:{stadium_id}",
        )

        logger.info(
            "Emergency broadcast sent for stadium %s: %d publications",
            stadium_id, sent_count,
        )
        return sent_count

    async def send_sector_alert(
        self,
        stadium_id: UUID,
        sector: str,
        title: str,
        body: str,
        alert_level: str = "warning",
        data: dict[str, Any] | None = None,
    ) -> bool:
        payload = {
            "event_type": "sector_alert",
            "stadium_id": str(stadium_id),
            "sector": sector,
            "title": title,
            "body": body,
            "alert_level": alert_level,
            "data": data or {},
        }

        published = await self._publish_notification(
            "stadiumos-notifications",
            payload,
            attributes={"sector": sector, "alert_level": alert_level},
        )

        if published:
            await self._log_notification(
                user_id=None,
                title=title,
                notification_type="sector_alert",
                priority=alert_level,
                target=f"sector:{sector}",
            )

        logger.info("Sector alert sent for %s sector %s", stadium_id, sector)
        return published

    async def send_targeted_notification(
        self,
        stadium_id: UUID,
        title: str,
        body: str,
        role_filter: list[str] | None = None,
        tags_filter: list[str] | None = None,
        data: dict[str, Any] | None = None,
    ) -> int:
        users = await self._users.list_by_stadium(stadium_id, limit=500)

        filtered_users = users
        if role_filter:
            allowed_roles = set()
            for r in role_filter:
                try:
                    allowed_roles.add(UserRole(r.upper()))
                except ValueError:
                    continue
            filtered_users = [u for u in filtered_users if u.role in allowed_roles]

        if tags_filter:
            tag_set = set(tags_filter)
            filtered_users = [
                u for u in filtered_users if tag_set.intersection(set(u.tags))
            ]

        if not filtered_users:
            logger.info("No users matched targeting criteria for stadium %s", stadium_id)
            return 0

        sent_count = 0
        batch_messages: list[PubSubMessage] = []

        for user in filtered_users:
            user_payload = {
                "event_type": "targeted_notification",
                "user_id": str(user.id),
                "stadium_id": str(stadium_id),
                "title": title,
                "body": body,
                "language": user.preferred_language.value,
                "data": data or {},
            }

            msg = PubSubMessage(
                topic="stadiumos-notifications",
                data=user_payload,
                attributes={
                    "user_id": str(user.id),
                    "language": user.preferred_language.value,
                },
            )
            batch_messages.append(msg)

        if batch_messages and self._pubsub is not None:
            try:
                message_ids = await self._pubsub.publish_batch(
                    "stadiumos-notifications", batch_messages
                )
                sent_count = len(message_ids)
            except Exception:
                logger.exception("Failed to publish batch notifications")
                for msg in batch_messages:
                    try:
                        await self._pubsub.publish("stadiumos-notifications", msg)
                        sent_count += 1
                    except Exception:
                        logger.exception("Failed to publish individual notification")

        await self._log_notification(
            user_id=None,
            title=title,
            notification_type="targeted_notification",
            priority="normal",
            target=f"stadium:{stadium_id}",
        )

        logger.info(
            "Targeted notification sent to %d/%d users in stadium %s",
            sent_count, len(filtered_users), stadium_id,
        )
        return sent_count

    async def send_role_notification(
        self,
        stadium_id: UUID,
        role: str,
        title: str,
        body: str,
        data: dict[str, Any] | None = None,
    ) -> int:
        return await self.send_targeted_notification(
            stadium_id=stadium_id,
            title=title,
            body=body,
            role_filter=[role],
            data=data,
        )

    async def _publish_notification(
        self,
        topic: str,
        payload: dict[str, Any],
        attributes: dict[str, str] | None = None,
    ) -> bool:
        if self._pubsub is None:
            logger.warning("Pub/Sub not configured, notification dropped")
            return False
        try:
            message = PubSubMessage(
                topic=topic,
                data=payload,
                attributes=attributes or {},
            )
            await self._pubsub.publish(topic, message)
            return True
        except Exception:
            logger.exception("Failed to publish notification to topic %s", topic)
            return False

    async def _log_notification(
        self,
        user_id: UUID | None,
        title: str,
        notification_type: str,
        priority: str,
        target: str,
    ) -> None:
        if self._bigquery is None:
            return
        try:
            from datetime import datetime, timezone

            row: dict[str, Any] = {
                "user_id": str(user_id) if user_id else None,
                "title": title,
                "notification_type": notification_type,
                "priority": priority,
                "target": target,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            await self._bigquery.insert_rows(
                BIGQUERY_DATASET, BIGQUERY_TABLE_NOTIFICATIONS, [row]
            )
        except Exception:
            logger.exception("Failed to log notification to BigQuery")
