from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.domain.entities.incident import (
    Incident,
    IncidentCategory,
    IncidentSeverity,
    IncidentStatus,
)
from app.domain.entities.user import User, UserRole
from app.domain.interfaces.external_services import IBigQueryService, IPubSubService, PubSubMessage
from app.domain.interfaces.repositories import IAlertRepository, IIncidentRepository, IUserRepository
from app.domain.value_objects.coordinates import LatLong
from app.domain.value_objects.gps_sector import GpsSector
from app.domain.value_objects.priority import Priority

logger = logging.getLogger(__name__)

BIGQUERY_DATASET = "stadiumos_analytics"
BIGQUERY_TABLE_INCIDENTS = "incident_events"

SEVERITY_AUTO_ESCALATION_MAP: dict[str, Priority] = {
    IncidentSeverity.LIFE_THREATENING.value: Priority.CRITICAL,
    IncidentSeverity.SERIOUS.value: Priority.HIGH,
    IncidentSeverity.MODERATE.value: Priority.MEDIUM,
    IncidentSeverity.MINOR.value: Priority.LOW,
    IncidentSeverity.ADVISORY.value: Priority.LOW,
}


class IncidentService:
    def __init__(
        self,
        incident_repo: IIncidentRepository,
        user_repo: IUserRepository,
        alert_repo: IAlertRepository | None = None,
        pubsub: IPubSubService | None = None,
        bigquery: IBigQueryService | None = None,
    ) -> None:
        self._incidents = incident_repo
        self._users = user_repo
        self._alerts = alert_repo
        self._pubsub = pubsub
        self._bigquery = bigquery

    async def create_incident(
        self,
        category: str,
        title: str,
        description: str,
        stadium_id: UUID,
        severity: str = "MODERATE",
        sector: GpsSector | None = None,
        location: LatLong | None = None,
        event_id: UUID | None = None,
        reported_by: UUID | None = None,
        reported_by_ai: bool = False,
        ai_confidence: float | None = None,
        people_involved: int = 1,
        injuries_reported: int = 0,
        public_visibility: bool = False,
        tags: list[str] | None = None,
        metadata: dict[str, str] | None = None,
    ) -> Incident:
        try:
            cat = IncidentCategory(category)
        except ValueError:
            cat = IncidentCategory.OTHER

        try:
            sev = IncidentSeverity(severity)
        except ValueError:
            sev = IncidentSeverity.MODERATE

        priority = SEVERITY_AUTO_ESCALATION_MAP.get(sev.value, Priority.MEDIUM)

        incident = Incident(
            category=cat,
            severity=sev,
            priority=priority,
            title=title,
            description=description,
            stadium_id=stadium_id,
            event_id=event_id,
            sector=sector,
            location=location,
            reported_by_user_id=reported_by,
            reported_by_ai=reported_by_ai,
            ai_confidence=ai_confidence,
            people_involved=people_involved,
            injuries_reported=injuries_reported,
            public_visibility=public_visibility,
            tags=tags or [],
            metadata=metadata or {},
        )

        created = await self._incidents.create(incident)
        logger.info(
            "Incident created: %s (category=%s, severity=%s)",
            created.id, cat.value, sev.value,
        )

        await self._publish_incident_event(created, "incident_created")
        await self._log_incident_event(created, "created")

        if sev in (IncidentSeverity.LIFE_THREATENING, IncidentSeverity.SERIOUS):
            await self._auto_escalate(created)

        return created

    async def get_incident(self, incident_id: UUID) -> Incident | None:
        return await self._incidents.get_by_id(incident_id)

    async def update_incident(
        self,
        incident_id: UUID,
        title: str | None = None,
        description: str | None = None,
        severity: str | None = None,
        sector: GpsSector | None = None,
        location: LatLong | None = None,
        people_involved: int | None = None,
        injuries_reported: int | None = None,
        public_visibility: bool | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, str] | None = None,
    ) -> Incident | None:
        incident = await self._incidents.get_by_id(incident_id)
        if incident is None:
            return None

        if title is not None:
            incident.title = title
        if description is not None:
            incident.description = description
        if severity is not None:
            try:
                incident.severity = IncidentSeverity(severity)
                new_priority = SEVERITY_AUTO_ESCALATION_MAP.get(severity, incident.priority)
                incident.priority = new_priority
            except ValueError:
                pass
        if sector is not None:
            incident.sector = sector
        if location is not None:
            incident.location = location
        if people_involved is not None:
            incident.people_involved = people_involved
        if injuries_reported is not None:
            incident.injuries_reported = injuries_reported
        if public_visibility is not None:
            incident.public_visibility = public_visibility
        if tags is not None:
            incident.tags = tags
        if metadata is not None:
            incident.metadata.update(metadata)
        incident.updated_at = datetime.now(timezone.utc)

        updated = await self._incidents.update(incident)
        logger.info("Incident updated: %s", incident_id)

        await self._publish_incident_event(updated, "incident_updated")
        return updated

    async def list_incidents(
        self,
        stadium_id: UUID | None = None,
        status: IncidentStatus | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Incident]:
        if stadium_id is not None:
            return await self._incidents.list_by_stadium(
                stadium_id, offset=offset, limit=limit
            )
        if status is not None:
            return await self._incidents.list_by_status(
                status, offset=offset, limit=limit
            )
        return await self._incidents.list_active(offset=offset, limit=limit)

    async def list_active_incidents(
        self,
        stadium_id: UUID | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Incident]:
        if stadium_id is not None:
            all_incidents = await self._incidents.list_by_stadium(
                stadium_id, offset=offset, limit=limit * 5
            )
            return [i for i in all_incidents if i.is_active()][:limit]
        return await self._incidents.list_active(offset=offset, limit=limit)

    async def assign_responder(
        self,
        incident_id: UUID,
        user_id: UUID,
        role: str,
    ) -> Incident | None:
        incident = await self._incidents.get_by_id(incident_id)
        if incident is None:
            return None

        user = await self._users.get_by_id(user_id)
        if user is None:
            logger.warning("Responder user %s not found", user_id)
            return None

        incident.assign_responder(user_id, role)
        updated = await self._incidents.update(incident)
        logger.info(
            "Responder %s assigned to incident %s (role=%s)",
            user_id, incident_id, role,
        )

        await self._publish_incident_event(updated, "incident_responder_assigned")
        return updated

    async def resolve_incident(
        self,
        incident_id: UUID,
        resolution_notes: str | None = None,
    ) -> Incident | None:
        incident = await self._incidents.get_by_id(incident_id)
        if incident is None:
            return None

        incident.resolve(notes=resolution_notes)
        updated = await self._incidents.update(incident)
        logger.info("Incident resolved: %s", incident_id)

        await self._publish_incident_event(updated, "incident_resolved")
        await self._log_incident_event(updated, "resolved")

        return updated

    async def close_incident(self, incident_id: UUID) -> Incident | None:
        incident = await self._incidents.get_by_id(incident_id)
        if incident is None:
            return None

        incident.close()
        updated = await self._incidents.update(incident)
        logger.info("Incident closed: %s", incident_id)

        await self._publish_incident_event(updated, "incident_closed")
        return updated

    async def escalate_incident(self, incident_id: UUID) -> Incident | None:
        incident = await self._incidents.get_by_id(incident_id)
        if incident is None:
            return None

        if not incident.is_active():
            logger.warning("Cannot escalate inactive incident %s", incident_id)
            return incident

        incident.escalate()
        updated = await self._incidents.update(incident)
        logger.info("Incident escalated: %s", incident_id)

        await self._publish_incident_event(updated, "incident_escalated")
        await self._log_incident_event(updated, "escalated")

        return updated

    async def mark_on_scene(self, incident_id: UUID, user_id: UUID) -> Incident | None:
        incident = await self._incidents.get_by_id(incident_id)
        if incident is None:
            return None

        incident.mark_on_scene(user_id)
        updated = await self._incidents.update(incident)
        logger.info("Responder %s on scene for incident %s", user_id, incident_id)

        await self._publish_incident_event(updated, "incident_on_scene")
        return updated

    async def add_internal_note(
        self, incident_id: UUID, note: str
    ) -> Incident | None:
        incident = await self._incidents.get_by_id(incident_id)
        if incident is None:
            return None

        incident.add_internal_note(note)
        updated = await self._incidents.update(incident)
        return updated

    async def get_active_incident_count(self, stadium_id: UUID | None = None) -> int:
        incidents = await self.list_active_incidents(stadium_id=stadium_id, limit=1000)
        return len(incidents)

    async def get_severity_breakdown(self, stadium_id: UUID) -> dict[str, int]:
        return await self._incidents.count_by_severity(stadium_id)

    async def _auto_escalate(self, incident: Incident) -> None:
        try:
            await self.escalate_incident(incident.id)
            await self._create_emergency_alert(incident)
        except Exception:
            logger.exception("Failed to auto-escalate incident %s", incident.id)

    async def _create_emergency_alert(self, incident: Incident) -> None:
        if self._alerts is None:
            return
        try:
            from app.domain.entities.alert import Alert, AlertType

            alert_type_map = {
                IncidentCategory.MEDICAL_EMERGENCY.value: AlertType.MEDICAL,
                IncidentCategory.FIRE_HAZARD.value: AlertType.FIRE,
                IncidentCategory.SECURITY_THREAT.value: AlertType.SECURITY,
                IncidentCategory.CROWD_DISORDER.value: AlertType.CROWD_SURGE,
                IncidentCategory.STRUCTURAL_DAMAGE.value: AlertType.INFRASTRUCTURE,
            }
            alert_type = alert_type_map.get(incident.category.value, AlertType.GENERIC)

            alert = Alert(
                alert_type=alert_type,
                priority=incident.priority,
                title=f"[AUTO] {incident.title}",
                description=incident.description,
                stadium_id=incident.stadium_id,
                event_id=incident.event_id,
                sector=incident.sector,
                location=incident.location,
                triggered_by_ai=True,
                ai_confidence=1.0,
                related_incident_id=incident.id,
            )
            await self._alerts.create(alert)
            logger.info(
                "Emergency alert auto-created for incident %s", incident.id
            )
        except Exception:
            logger.exception("Failed to create emergency alert for incident %s", incident.id)

    async def _publish_incident_event(self, incident: Incident, event_type: str) -> None:
        if self._pubsub is None:
            return
        try:
            message = PubSubMessage(
                topic="stadiumos-alerts",
                data={
                    "event_type": event_type,
                    "incident_id": str(incident.id),
                    "category": incident.category.value,
                    "severity": incident.severity.value,
                    "priority": incident.priority.value,
                    "status": incident.status.value,
                    "title": incident.title,
                    "stadium_id": str(incident.stadium_id),
                    "sector": incident.sector.value if incident.sector else None,
                    "responder_count": len(incident.responders),
                    "timestamp": incident.updated_at.isoformat(),
                },
                attributes={
                    "incident_id": str(incident.id),
                    "category": incident.category.value,
                    "severity": incident.severity.value,
                },
            )
            await self._pubsub.publish("stadiumos-alerts", message)
        except Exception:
            logger.exception("Failed to publish incident event to Pub/Sub")

    async def _log_incident_event(self, incident: Incident, action: str) -> None:
        if self._bigquery is None:
            return
        try:
            row: dict[str, Any] = {
                "incident_id": str(incident.id),
                "category": incident.category.value,
                "severity": incident.severity.value,
                "priority": incident.priority.value,
                "status": incident.status.value,
                "title": incident.title,
                "stadium_id": str(incident.stadium_id),
                "event_id": str(incident.event_id) if incident.event_id else None,
                "sector": incident.sector.value if incident.sector else None,
                "reported_by_ai": incident.reported_by_ai,
                "people_involved": incident.people_involved,
                "injuries_reported": incident.injuries_reported,
                "responder_count": len(incident.responders),
                "action": action,
                "timestamp": incident.updated_at.isoformat(),
            }
            response_time = incident.response_time_seconds()
            if response_time is not None:
                row["response_time_seconds"] = response_time
            await self._bigquery.insert_rows(BIGQUERY_DATASET, BIGQUERY_TABLE_INCIDENTS, [row])
        except Exception:
            logger.exception("Failed to log incident event to BigQuery")
