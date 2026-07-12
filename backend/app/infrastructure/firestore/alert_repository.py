from __future__ import annotations

from datetime import datetime
from uuid import UUID

from google.cloud.firestore_v1 import Client as FirestoreClient

from app.core.config.settings import settings
from app.domain.entities.alert import Alert, AlertStatus, AlertType
from app.domain.interfaces.repositories import IAlertRepository
from app.domain.value_objects.priority import Priority
from app.infrastructure.firestore.client import get_firestore_client


def _alert_to_doc(alert: Alert) -> dict:
    d = alert.model_dump(mode="json")
    d["id"] = str(alert.id)
    d["stadium_id"] = str(alert.stadium_id)
    if alert.event_id:
        d["event_id"] = str(alert.event_id)
    if alert.sector:
        d["sector"] = alert.sector.value
    if alert.location:
        d["location"] = alert.location.model_dump()
    if alert.triggered_by_user_id:
        d["triggered_by_user_id"] = str(alert.triggered_by_user_id)
    if alert.assigned_to_user_id:
        d["assigned_to_user_id"] = str(alert.assigned_to_user_id)
    if alert.related_incident_id:
        d["related_incident_id"] = str(alert.related_incident_id)
    if alert.affected_sectors:
        d["affected_sectors"] = [s.value for s in alert.affected_sectors]
    for field in ("resolved_at", "acknowledged_at", "created_at", "updated_at"):
        val = getattr(alert, field, None)
        if val:
            d[field] = val.isoformat()
    return d


def _doc_to_alert(doc: dict) -> Alert:
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
    if raw.get("triggered_by_user_id"):
        raw["triggered_by_user_id"] = UUID(raw["triggered_by_user_id"])
    if raw.get("assigned_to_user_id"):
        raw["assigned_to_user_id"] = UUID(raw["assigned_to_user_id"])
    if raw.get("related_incident_id"):
        raw["related_incident_id"] = UUID(raw["related_incident_id"])
    if raw.get("affected_sectors"):
        from app.domain.value_objects.gps_sector import GpsSector
        raw["affected_sectors"] = [GpsSector(s) for s in raw["affected_sectors"]]
    for field in ("resolved_at", "acknowledged_at", "created_at", "updated_at"):
        if raw.get(field) and isinstance(raw[field], str):
            raw[field] = datetime.fromisoformat(raw[field])
    return Alert(**raw)


class AlertRepository(IAlertRepository):
    def __init__(self) -> None:
        self._client: FirestoreClient = get_firestore_client()
        self._collection_name = f"{settings.FIRESTORE_COLLECTION_PREFIX}_alerts"
        self._collection = self._client.collection(self._collection_name)

    async def get_by_id(self, alert_id: UUID) -> Alert | None:
        doc_ref = self._collection.document(str(alert_id))
        snapshot = doc_ref.get()
        if not snapshot.exists:
            return None
        return _doc_to_alert(snapshot.to_dict())

    async def create(self, alert: Alert) -> Alert:
        doc_ref = self._collection.document(str(alert.id))
        doc_ref.set(_alert_to_doc(alert))
        return alert

    async def update(self, alert: Alert) -> Alert:
        doc_ref = self._collection.document(str(alert.id))
        doc_ref.update(_alert_to_doc(alert))
        return alert

    async def list_active(self, offset: int = 0, limit: int = 50) -> list[Alert]:
        docs = (
            self._collection.where(
                "status", "in", [
                    AlertStatus.TRIGGERED.value,
                    AlertStatus.ACKNOWLEDGED.value,
                    AlertStatus.IN_PROGRESS.value,
                    AlertStatus.ESCALATED.value,
                ]
            )
            .order_by("created_at", direction="DESCENDING")
            .offset(offset)
            .limit(limit)
            .get()
        )
        return [_doc_to_alert(d.to_dict()) for d in docs]

    async def list_by_status(self, status: AlertStatus, offset: int = 0, limit: int = 50) -> list[Alert]:
        docs = (
            self._collection.where("status", "==", status.value)
            .order_by("created_at", direction="DESCENDING")
            .offset(offset)
            .limit(limit)
            .get()
        )
        return [_doc_to_alert(d.to_dict()) for d in docs]

    async def list_by_type(self, alert_type: AlertType, offset: int = 0, limit: int = 50) -> list[Alert]:
        docs = (
            self._collection.where("alert_type", "==", alert_type.value)
            .order_by("created_at", direction="DESCENDING")
            .offset(offset)
            .limit(limit)
            .get()
        )
        return [_doc_to_alert(d.to_dict()) for d in docs]

    async def list_by_stadium(self, stadium_id: UUID, offset: int = 0, limit: int = 50) -> list[Alert]:
        docs = (
            self._collection.where("stadium_id", "==", str(stadium_id))
            .order_by("created_at", direction="DESCENDING")
            .offset(offset)
            .limit(limit)
            .get()
        )
        return [_doc_to_alert(d.to_dict()) for d in docs]

    async def list_by_priority(self, priority: Priority, offset: int = 0, limit: int = 50) -> list[Alert]:
        docs = (
            self._collection.where("priority", "==", priority.value)
            .order_by("created_at", direction="DESCENDING")
            .offset(offset)
            .limit(limit)
            .get()
        )
        return [_doc_to_alert(d.to_dict()) for d in docs]

    async def count_active(self) -> int:
        docs = self._collection.where(
            "status", "in", [
                AlertStatus.TRIGGERED.value,
                AlertStatus.ACKNOWLEDGED.value,
                AlertStatus.IN_PROGRESS.value,
                AlertStatus.ESCALATED.value,
            ]
        ).get()
        return len(docs)

    async def count_active_by_stadium(self, stadium_id: UUID) -> int:
        docs = (
            self._collection.where("stadium_id", "==", str(stadium_id))
            .where(
                "status", "in", [
                    AlertStatus.TRIGGERED.value,
                    AlertStatus.ACKNOWLEDGED.value,
                    AlertStatus.IN_PROGRESS.value,
                    AlertStatus.ESCALATED.value,
                ]
            )
            .get()
        )
        return len(docs)
