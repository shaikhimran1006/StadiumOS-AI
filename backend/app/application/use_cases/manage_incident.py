from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from app.application.services.alert_service import AlertService
from app.application.services.incident_service import IncidentService
from app.application.services.notification_service import NotificationService
from app.domain.entities.incident import Incident, IncidentCategory, IncidentSeverity
from app.domain.value_objects.coordinates import LatLong
from app.domain.value_objects.gps_sector import GpsSector
from app.domain.value_objects.priority import Priority

logger = logging.getLogger(__name__)


class ManageIncidentUseCase:
    def __init__(
        self,
        incident_service: IncidentService,
        alert_service: AlertService,
        notification_service: NotificationService,
    ) -> None:
        self._incidents = incident_service
        self._alerts = alert_service
        self._notifications = notification_service

    async def execute(
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
        incident = await self._incidents.create_incident(
            category=category,
            title=title,
            description=description,
            stadium_id=stadium_id,
            severity=severity,
            sector=sector,
            location=location,
            event_id=event_id,
            reported_by=reported_by,
            reported_by_ai=reported_by_ai,
            ai_confidence=ai_confidence,
            people_involved=people_involved,
            injuries_reported=injuries_reported,
            public_visibility=public_visibility,
            tags=tags,
            metadata=metadata,
        )

        await self._handle_incident_side_effects(incident, stadium_id)

        return incident

    async def escalate(
        self,
        incident_id: UUID,
        notify_roles: list[str] | None = None,
    ) -> Incident | None:
        incident = await self._incidents.escalate_incident(incident_id)
        if incident is None:
            return None

        await self._notifications.send_emergency_broadcast(
            stadium_id=incident.stadium_id,
            title=f"Incident Escalated: {incident.title}",
            body=(
                f"Category: {incident.category.value}\n"
                f"Severity: {incident.severity.value}\n"
                f"Sector: {incident.sector.value if incident.sector else 'Unknown'}\n"
                f"Description: {incident.description[:200]}"
            ),
            severity="critical" if incident.severity == IncidentSeverity.LIFE_THREATENING else "high",
            sectors=[incident.sector.value] if incident.sector else None,
        )

        if notify_roles:
            for role in notify_roles:
                await self._notifications.send_role_notification(
                    stadium_id=incident.stadium_id,
                    role=role,
                    title=f"Escalated Incident: {incident.title}",
                    body=(
                        f"A {incident.severity.value.lower()} incident has been escalated "
                        f"in sector {incident.sector.value if incident.sector else 'unknown'}. "
                        f"Immediate response required."
                    ),
                    data={"incident_id": str(incident.id)},
                )

        logger.info(
            "Incident %s escalated with notifications to roles: %s",
            incident_id, notify_roles,
        )
        return incident

    async def resolve(
        self,
        incident_id: UUID,
        resolution_notes: str | None = None,
        auto_close: bool = False,
    ) -> Incident | None:
        incident = await self._incidents.resolve_incident(
            incident_id, resolution_notes=resolution_notes
        )
        if incident is None:
            return None

        if incident.public_visibility:
            await self._notifications.send_sector_alert(
                stadium_id=incident.stadium_id,
                sector=incident.sector.value if incident.sector else "unknown",
                title="Incident Resolved",
                body=(
                    f"The incident \"{incident.title}\" has been resolved. "
                    + (f"Notes: {resolution_notes}" if resolution_notes else "")
                ),
                alert_level="info",
                data={"incident_id": str(incident.id)},
            )

        if auto_close:
            closed = await self._incidents.close_incident(incident_id)
            if closed is not None:
                return closed

        return incident

    async def assign_and_dispatch(
        self,
        incident_id: UUID,
        responder_id: UUID,
        responder_role: str,
        stadium_id: UUID,
    ) -> Incident | None:
        incident = await self._incidents.assign_responder(
            incident_id=incident_id,
            user_id=responder_id,
            role=responder_role,
        )
        if incident is None:
            return None

        await self._notifications.send_notification(
            user_id=responder_id,
            title="Incident Assignment",
            body=(
                f"You have been assigned to incident: {incident.title}\n"
                f"Category: {incident.category.value}\n"
                f"Severity: {incident.severity.value}\n"
                f"Sector: {incident.sector.value if incident.sector else 'Unknown'}"
            ),
            notification_type="incident_assignment",
            priority="high" if incident.severity in (
                IncidentSeverity.LIFE_THREATENING, IncidentSeverity.SERIOUS
            ) else "normal",
            data={"incident_id": str(incident.id)},
        )

        logger.info(
            "Responder %s dispatched to incident %s", responder_id, incident_id
        )
        return incident

    async def add_note(
        self, incident_id: UUID, note: str
    ) -> Incident | None:
        return await self._incidents.add_internal_note(incident_id, note)

    async def _handle_incident_side_effects(
        self, incident: Incident, stadium_id: UUID
    ) -> None:
        if incident.severity in (
            IncidentSeverity.LIFE_THREATENING,
            IncidentSeverity.SERIOUS,
        ):
            try:
                alert_priority = Priority.CRITICAL if (
                    incident.severity == IncidentSeverity.LIFE_THREATENING
                ) else Priority.HIGH

                await self._alerts.create_alert(
                    alert_type=self._map_category_to_alert_type(incident.category),
                    title=f"[AUTO] {incident.title}",
                    description=incident.description,
                    stadium_id=stadium_id,
                    priority=alert_priority,
                    sector=incident.sector,
                    location=incident.location,
                    event_id=incident.event_id,
                    triggered_by_ai=incident.reported_by_ai,
                    ai_confidence=incident.ai_confidence,
                    metadata={"related_incident_id": str(incident.id)},
                )
            except Exception:
                logger.exception("Failed to auto-create alert for incident %s", incident.id)

        try:
            severity_label = incident.severity.value.lower().replace("_", " ")
            await self._notifications.send_role_notification(
                stadium_id=stadium_id,
                role="security",
                title=f"New {severity_label} Incident",
                body=(
                    f"{incident.category.value}: {incident.title}\n"
                    f"Sector: {incident.sector.value if incident.sector else 'Unknown'}"
                ),
                data={"incident_id": str(incident.id)},
            )
        except Exception:
            logger.exception("Failed to send notification for incident %s", incident.id)

    @staticmethod
    def _map_category_to_alert_type(category: IncidentCategory) -> str:
        mapping = {
            IncidentCategory.SECURITY_THREAT: "SECURITY",
            IncidentCategory.MEDICAL_EMERGENCY: "MEDICAL",
            IncidentCategory.FIRE_HAZARD: "FIRE",
            IncidentCategory.CROWD_DISORDER: "CROWD_SURGE",
            IncidentCategory.STRUCTURAL_DAMAGE: "INFRASTRUCTURE",
            IncidentCategory.LOST_CHILD: "LOST_PERSON",
            IncidentCategory.LOST_ADULT: "LOST_PERSON",
        }
        return mapping.get(category, "GENERIC")
