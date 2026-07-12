from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from google.cloud.firestore_v1 import Client as FirestoreClient

from app.core.config.settings import settings
from app.domain.entities.event import Event, EventStatus
from app.domain.interfaces.repositories import IEventRepository
from app.infrastructure.firestore.client import get_firestore_client


def _event_to_doc(event: Event) -> dict:
    d = event.model_dump(mode="json")
    d["id"] = str(event.id)
    d["stadium_id"] = str(event.stadium_id)
    if event.allowed_sector_ids:
        d["allowed_sector_ids"] = [str(s) for s in event.allowed_sector_ids]
    for field in ("gates_open_at", "kickoff_at", "estimated_end_at", "actual_end_at", "created_at", "updated_at"):
        val = getattr(event, field, None)
        if val:
            d[field] = val.isoformat()
    return d


def _doc_to_event(doc: dict) -> Event:
    raw = dict(doc)
    raw["id"] = UUID(raw["id"])
    raw["stadium_id"] = UUID(raw["stadium_id"])
    if raw.get("allowed_sector_ids"):
        raw["allowed_sector_ids"] = [UUID(s) for s in raw["allowed_sector_ids"]]
    for field in ("gates_open_at", "kickoff_at", "estimated_end_at", "actual_end_at", "created_at", "updated_at"):
        if raw.get(field) and isinstance(raw[field], str):
            raw[field] = datetime.fromisoformat(raw[field])
    return Event(**raw)


class EventRepository(IEventRepository):
    def __init__(self) -> None:
        self._client: FirestoreClient = get_firestore_client()
        self._collection_name = f"{settings.FIRESTORE_COLLECTION_PREFIX}_events"
        self._collection = self._client.collection(self._collection_name)

    async def get_by_id(self, event_id: UUID) -> Event | None:
        doc_ref = self._collection.document(str(event_id))
        snapshot = doc_ref.get()
        if not snapshot.exists:
            return None
        return _doc_to_event(snapshot.to_dict())

    async def create(self, event: Event) -> Event:
        doc_ref = self._collection.document(str(event.id))
        doc_ref.set(_event_to_doc(event))
        return event

    async def update(self, event: Event) -> Event:
        doc_ref = self._collection.document(str(event.id))
        doc_ref.update(_event_to_doc(event))
        return event

    async def list_by_stadium(self, stadium_id: UUID, offset: int = 0, limit: int = 50) -> list[Event]:
        docs = (
            self._collection.where("stadium_id", "==", str(stadium_id))
            .order_by("kickoff_at", direction="DESCENDING")
            .offset(offset)
            .limit(limit)
            .get()
        )
        return [_doc_to_event(d.to_dict()) for d in docs]

    async def list_by_status(self, status: EventStatus, offset: int = 0, limit: int = 50) -> list[Event]:
        docs = (
            self._collection.where("status", "==", status.value)
            .order_by("kickoff_at", direction="DESCENDING")
            .offset(offset)
            .limit(limit)
            .get()
        )
        return [_doc_to_event(d.to_dict()) for d in docs]

    async def list_live(self) -> list[Event]:
        docs = (
            self._collection.where(
                "status", "in", [EventStatus.IN_PROGRESS.value, EventStatus.HALFTIME.value]
            )
            .get()
        )
        return [_doc_to_event(d.to_dict()) for d in docs]

    async def list_upcoming(
        self, stadium_id: UUID | None = None, offset: int = 0, limit: int = 50
    ) -> list[Event]:
        now = datetime.now(timezone.utc).isoformat()
        if stadium_id:
            docs = (
                self._collection.where("stadium_id", "==", str(stadium_id))
                .where("kickoff_at", ">", now)
                .order_by("kickoff_at", direction="ASCENDING")
                .offset(offset)
                .limit(limit)
                .get()
            )
        else:
            docs = (
                self._collection.where("kickoff_at", ">", now)
                .order_by("kickoff_at", direction="ASCENDING")
                .offset(offset)
                .limit(limit)
                .get()
            )
        return [_doc_to_event(d.to_dict()) for d in docs]

    async def count_by_stadium(self, stadium_id: UUID) -> int:
        docs = self._collection.where("stadium_id", "==", str(stadium_id)).get()
        return len(docs)
