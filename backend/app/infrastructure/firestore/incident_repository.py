from __future__ import annotations

from datetime import datetime
from uuid import UUID

from google.cloud.firestore_v1 import Client as FirestoreClient

from app.core.config.settings import settings
from app.domain.entities.incident import Incident, IncidentStatus, Responder
from app.domain.interfaces.repositories import IIncidentRepository
from app.infrastructure.firestore.client import get_firestore_client


def _incident_to_doc(incident: Incident) -> dict:
    d = incident.model_dump(mode="json")
    d["id"] = str(incident.id)
    d["stadium_id"] = str(incident.stadium_id)
    if incident.event_id:
        d["event_id"] = str(incident.event_id)
    if incident.sector:
        d["sector"] = incident.sector.value
    if incident.location:
        d["location"] = incident.location.model_dump()
    if incident.reported_by_user_id:
        d["reported_by_user_id"] = str(incident.reported_by_user_id)
    if incident.related_alert_id:
        d["related_alert_id"] = str(incident.related_alert_id)
    if incident.responders:
        d["responders"] = [
            {
                "user_id": str(r.user_id),
                "role": r.role,
                "dispatched_at": r.dispatched_at.isoformat() if r.dispatched_at else None,
                "arrived_at": r.arrived_at.isoformat() if r.arrived_at else None,
            }
            for r in incident.responders
        ]
    for field in ("resolved_at", "closed_at", "created_at", "updated_at"):
        val = getattr(incident, field, None)
        if val:
            d[field] = val.isoformat()
    return d


def _doc_to_incident(doc: dict) -> Incident:
    raw = dict(doc)
    raw["id"] = UUID(raw["id"])
    raw["stadium_id"] = UUID(raw["stadium_id"])
    if raw.get("event_id"):
        raw["event_id"] = UUID(raw["event_id"])
    if raw.get("sector"):
        from app.domain.value_objects.gps_sector import GpsSector
        raw["sector"] = GpsSector(raw["sector"])
    if raw.get("location"):
        from app.domain.value_objects.coordinates import LatLong
        raw["location"] = LatLong(**raw["location"])
    if raw.get("reported_by_user_id"):
        raw["reported_by_user_id"] = UUID(raw["reported_by_user_id"])
    if raw.get("related_alert_id"):
        raw["related_alert_id"] = UUID(raw["related_alert_id"])
    if raw.get("responders"):
        parsed = []
        for r in raw["responders"]:
            responder = {"user_id": UUID(r["user_id"]), "role": r["role"]}
            if r.get("dispatched_at"):
                responder["dispatched_at"] = datetime.fromisoformat(r["dispatched_at"])
            if r.get("arrived_at"):
                responder["arrived_at"] = datetime.fromisoformat(r["arrived_at"])
            parsed.append(Responder(**responder))
        raw["responders"] = parsed
    for field in ("resolved_at", "closed_at", "created_at", "updated_at"):
        if raw.get(field) and isinstance(raw[field], str):
            raw[field] = datetime.fromisoformat(raw[field])
    return Incident(**raw)


class IncidentRepository(IIncidentRepository):
    def __init__(self) -> None:
        self._client: FirestoreClient = get_firestore_client()
        self._collection_name = f"{settings.FIRESTORE_COLLECTION_PREFIX}_incidents"
        self._collection = self._client.collection(self._collection_name)

    async def get_by_id(self, incident_id: UUID) -> Incident | None:
        doc_ref = self._collection.document(str(incident_id))
        snapshot = doc_ref.get()
        if not snapshot.exists:
            return None
        return _doc_to_incident(snapshot.to_dict())

    async def create(self, incident: Incident) -> Incident:
        doc_ref = self._collection.document(str(incident.id))
        doc_ref.set(_incident_to_doc(incident))
        return incident

    async def update(self, incident: Incident) -> Incident:
        doc_ref = self._collection.document(str(incident.id))
        doc_ref.update(_incident_to_doc(incident))
        return incident

    async def list_active(self, offset: int = 0, limit: int = 50) -> list[Incident]:
        active_statuses = [
            IncidentStatus.REPORTED.value, IncidentStatus.TRIAGED.value,
            IncidentStatus.DISPATCHED.value, IncidentStatus.ON_SCENE.value,
            IncidentStatus.UNDER_CONTROL.value, IncidentStatus.ESCALATED.value,
        ]
        docs = (
            self._collection.where("status", "in", active_statuses)
            .order_by("created_at", direction="DESCENDING")
            .offset(offset)
            .limit(limit)
            .get()
        )
        return [_doc_to_incident(d.to_dict()) for d in docs]

    async def list_by_status(self, status: IncidentStatus, offset: int = 0, limit: int = 50) -> list[Incident]:
        docs = (
            self._collection.where("status", "==", status.value)
            .order_by("created_at", direction="DESCENDING")
            .offset(offset)
            .limit(limit)
            .get()
        )
        return [_doc_to_incident(d.to_dict()) for d in docs]

    async def list_by_stadium(self, stadium_id: UUID, offset: int = 0, limit: int = 50) -> list[Incident]:
        docs = (
            self._collection.where("stadium_id", "==", str(stadium_id))
            .order_by("created_at", direction="DESCENDING")
            .offset(offset)
            .limit(limit)
            .get()
        )
        return [_doc_to_incident(d.to_dict()) for d in docs]

    async def list_by_event(self, event_id: UUID, offset: int = 0, limit: int = 50) -> list[Incident]:
        docs = (
            self._collection.where("event_id", "==", str(event_id))
            .order_by("created_at", direction="DESCENDING")
            .offset(offset)
            .limit(limit)
            .get()
        )
        return [_doc_to_incident(d.to_dict()) for d in docs]

    async def count_active_by_stadium(self, stadium_id: UUID) -> int:
        active_statuses = [
            IncidentStatus.REPORTED.value, IncidentStatus.TRIAGED.value,
            IncidentStatus.DISPATCHED.value, IncidentStatus.ON_SCENE.value,
            IncidentStatus.UNDER_CONTROL.value, IncidentStatus.ESCALATED.value,
        ]
        docs = (
            self._collection.where("stadium_id", "==", str(stadium_id))
            .where("status", "in", active_statuses)
            .get()
        )
        return len(docs)

    async def count_by_severity(self, stadium_id: UUID) -> dict[str, int]:
        docs = self._collection.where("stadium_id", "==", str(stadium_id)).get()
        counts: dict[str, int] = {}
        for d in docs:
            incident = _doc_to_incident(d.to_dict())
            sev = incident.severity.value
            counts[sev] = counts.get(sev, 0) + 1
        return counts
