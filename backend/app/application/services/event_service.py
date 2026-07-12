from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.domain.entities.event import Event, EventStatus, EventType
from app.domain.interfaces.external_services import IBigQueryService, IPubSubService, PubSubMessage
from app.domain.interfaces.repositories import IEventRepository

logger = logging.getLogger(__name__)

BIGQUERY_DATASET = "stadiumos_analytics"
BIGQUERY_TABLE_EVENTS = "event_tracking"


class EventService:
    def __init__(
        self,
        event_repo: IEventRepository,
        pubsub: IPubSubService | None = None,
        bigquery: IBigQueryService | None = None,
    ) -> None:
        self._events = event_repo
        self._pubsub = pubsub
        self._bigquery = bigquery

    async def create_event(
        self,
        name: str,
        stadium_id: UUID,
        event_type: str = "FOOTBALL_MATCH",
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        home_team: str | None = None,
        away_team: str | None = None,
        competition: str | None = None,
        expected_attendance: int | None = None,
        gates_open_at: datetime | None = None,
        broadcast_channels: list[str] | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, str] | None = None,
    ) -> Event:
        try:
            e_type = EventType(event_type)
        except ValueError:
            e_type = EventType.OTHER

        event = Event(
            name=name,
            event_type=e_type,
            stadium_id=stadium_id,
            kickoff_at=start_time,
            estimated_end_at=end_time,
            home_team=home_team,
            away_team=away_team,
            competition=competition,
            expected_attendance=expected_attendance,
            gates_open_at=gates_open_at,
            broadcast_channels=broadcast_channels or [],
            tags=tags or [],
            metadata=metadata or {},
        )

        created = await self._events.create(event)
        logger.info("Event created: %s (type=%s)", created.id, e_type.value)

        await self._publish_event(created, "event_created")
        await self._log_event(created, "created")

        return created

    async def get_event(self, event_id: UUID) -> Event | None:
        return await self._events.get_by_id(event_id)

    async def update_event(
        self,
        event_id: UUID,
        name: str | None = None,
        status: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        expected_attendance: int | None = None,
        actual_attendance: int | None = None,
        home_team: str | None = None,
        away_team: str | None = None,
        competition: str | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, str] | None = None,
    ) -> Event | None:
        event = await self._events.get_by_id(event_id)
        if event is None:
            return None

        if name is not None:
            event.name = name
        if status is not None:
            try:
                new_status = EventStatus(status)
                if new_status == EventStatus.IN_PROGRESS and not event.is_live():
                    event.start()
                elif new_status == EventStatus.HALFTIME:
                    event.pause_halftime()
                elif new_status == EventStatus.COMPLETED:
                    event.complete()
                elif new_status == EventStatus.CANCELLED:
                    event.cancel()
                elif new_status == EventStatus.POSTPONED:
                    event.postpone()
                else:
                    event.status = new_status
            except ValueError:
                pass
        if start_time is not None:
            event.kickoff_at = start_time
        if end_time is not None:
            event.estimated_end_at = end_time
        if expected_attendance is not None:
            event.expected_attendance = expected_attendance
        if actual_attendance is not None:
            event.actual_attendance = actual_attendance
        if home_team is not None:
            event.home_team = home_team
        if away_team is not None:
            event.away_team = away_team
        if competition is not None:
            event.competition = competition
        if tags is not None:
            event.tags = tags
        if metadata is not None:
            event.metadata.update(metadata)
        event.updated_at = datetime.now(timezone.utc)

        updated = await self._events.update(event)
        logger.info("Event updated: %s", event_id)

        await self._publish_event(updated, "event_updated")
        return updated

    async def list_events(
        self,
        stadium_id: UUID | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Event]:
        if stadium_id is not None:
            return await self._events.list_by_stadium(
                stadium_id, offset=offset, limit=limit
            )
        upcoming = await self._events.list_upcoming(offset=offset, limit=limit)
        live = await self._events.list_live()
        return live + upcoming

    async def get_live_events(self) -> list[Event]:
        return await self._events.list_live()

    async def get_upcoming_events(
        self,
        stadium_id: UUID | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Event]:
        return await self._events.list_upcoming(
            stadium_id=stadium_id, offset=offset, limit=limit
        )

    async def get_events_by_status(
        self,
        status: EventStatus,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Event]:
        return await self._events.list_by_status(status, offset=offset, limit=limit)

    async def start_event(self, event_id: UUID) -> Event | None:
        event = await self._events.get_by_id(event_id)
        if event is None:
            return None

        event.start()
        updated = await self._events.update(event)
        logger.info("Event started: %s", event_id)

        await self._publish_event(updated, "event_started")
        await self._log_event(updated, "started")
        return updated

    async def complete_event(self, event_id: UUID) -> Event | None:
        event = await self._events.get_by_id(event_id)
        if event is None:
            return None

        event.complete()
        updated = await self._events.update(event)
        logger.info("Event completed: %s", event_id)

        await self._publish_event(updated, "event_completed")
        await self._log_event(updated, "completed")
        return updated

    async def cancel_event(self, event_id: UUID) -> Event | None:
        event = await self._events.get_by_id(event_id)
        if event is None:
            return None

        event.cancel()
        updated = await self._events.update(event)
        logger.info("Event cancelled: %s", event_id)

        await self._publish_event(updated, "event_cancelled")
        await self._log_event(updated, "cancelled")
        return updated

    async def update_attendance(
        self, event_id: UUID, actual_attendance: int
    ) -> Event | None:
        event = await self._events.get_by_id(event_id)
        if event is None:
            return None

        event.actual_attendance = actual_attendance
        event.updated_at = datetime.now(timezone.utc)
        updated = await self._events.update(event)
        logger.info(
            "Attendance updated for event %s: %d (expected: %s)",
            event_id,
            actual_attendance,
            event.expected_attendance,
        )

        await self._publish_event(updated, "event_attendance_updated")
        return updated

    async def get_event_count(self, stadium_id: UUID) -> int:
        return await self._events.count_by_stadium(stadium_id)

    async def _publish_event(self, event: Event, event_type: str) -> None:
        if self._pubsub is None:
            return
        try:
            message = PubSubMessage(
                topic="stadiumos-analytics",
                data={
                    "event_type": event_type,
                    "event_id": str(event.id),
                    "name": event.name,
                    "event_category": event.event_type.value,
                    "status": event.status.value,
                    "stadium_id": str(event.stadium_id),
                    "expected_attendance": event.expected_attendance,
                    "actual_attendance": event.actual_attendance,
                    "timestamp": event.updated_at.isoformat(),
                },
                attributes={
                    "event_id": str(event.id),
                    "event_type": event.event_type.value,
                },
            )
            await self._pubsub.publish("stadiumos-analytics", message)
        except Exception:
            logger.exception("Failed to publish event to Pub/Sub")

    async def _log_event(self, event: Event, action: str) -> None:
        if self._bigquery is None:
            return
        try:
            row: dict[str, Any] = {
                "event_id": str(event.id),
                "name": event.name,
                "event_type": event.event_type.value,
                "status": event.status.value,
                "stadium_id": str(event.stadium_id),
                "expected_attendance": event.expected_attendance,
                "actual_attendance": event.actual_attendance,
                "action": action,
                "timestamp": event.updated_at.isoformat(),
            }
            if event.kickoff_at:
                row["kickoff_at"] = event.kickoff_at.isoformat()
            if event.actual_end_at:
                row["actual_end_at"] = event.actual_end_at.isoformat()
            duration = event.duration_minutes()
            if duration is not None:
                row["duration_minutes"] = duration
            await self._bigquery.insert_rows(BIGQUERY_DATASET, BIGQUERY_TABLE_EVENTS, [row])
        except Exception:
            logger.exception("Failed to log event to BigQuery")
