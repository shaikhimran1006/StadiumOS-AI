from __future__ import annotations

from datetime import datetime
from uuid import UUID

from google.cloud.firestore_v1 import Client as FirestoreClient

from app.core.config.settings import settings
from app.domain.entities.feedback import Feedback, FeedbackCategory
from app.domain.interfaces.repositories import IFeedbackRepository
from app.infrastructure.firestore.client import get_firestore_client


def _feedback_to_doc(feedback: Feedback) -> dict:
    d = feedback.model_dump(mode="json")
    d["id"] = str(feedback.id)
    d["user_id"] = str(feedback.user_id)
    d["stadium_id"] = str(feedback.stadium_id)
    if feedback.event_id:
        d["event_id"] = str(feedback.event_id)
    if feedback.sector:
        d["sector"] = feedback.sector.value
    if feedback.conversation_id:
        d["conversation_id"] = str(feedback.conversation_id)
    if feedback.responded_by_user_id:
        d["responded_by_user_id"] = str(feedback.responded_by_user_id)
    for field in ("responded_at", "created_at", "updated_at"):
        val = getattr(feedback, field, None)
        if val:
            d[field] = val.isoformat()
    return d


def _doc_to_feedback(doc: dict) -> Feedback:
    raw = dict(doc)
    raw["id"] = UUID(raw["id"])
    raw["user_id"] = UUID(raw["user_id"])
    raw["stadium_id"] = UUID(raw["stadium_id"])
    if raw.get("event_id"):
        raw["event_id"] = UUID(raw["event_id"])
    if raw.get("sector"):
        from app.domain.value_objects.gps_sector import GpsSector
        raw["sector"] = GpsSector(raw["sector"])
    if raw.get("conversation_id"):
        raw["conversation_id"] = UUID(raw["conversation_id"])
    if raw.get("responded_by_user_id"):
        raw["responded_by_user_id"] = UUID(raw["responded_by_user_id"])
    for field in ("responded_at", "created_at", "updated_at"):
        if raw.get(field) and isinstance(raw[field], str):
            raw[field] = datetime.fromisoformat(raw[field])
    return Feedback(**raw)


class FeedbackRepository(IFeedbackRepository):
    def __init__(self) -> None:
        self._client: FirestoreClient = get_firestore_client()
        self._collection_name = f"{settings.FIRESTORE_COLLECTION_PREFIX}_feedback"
        self._collection = self._client.collection(self._collection_name)

    async def get_by_id(self, feedback_id: UUID) -> Feedback | None:
        doc_ref = self._collection.document(str(feedback_id))
        snapshot = doc_ref.get()
        if not snapshot.exists:
            return None
        return _doc_to_feedback(snapshot.to_dict())

    async def create(self, feedback: Feedback) -> Feedback:
        doc_ref = self._collection.document(str(feedback.id))
        doc_ref.set(_feedback_to_doc(feedback))
        return feedback

    async def update(self, feedback: Feedback) -> Feedback:
        doc_ref = self._collection.document(str(feedback.id))
        doc_ref.update(_feedback_to_doc(feedback))
        return feedback

    async def list_by_event(self, event_id: UUID, offset: int = 0, limit: int = 50) -> list[Feedback]:
        docs = (
            self._collection.where("event_id", "==", str(event_id))
            .order_by("created_at", direction="DESCENDING")
            .offset(offset)
            .limit(limit)
            .get()
        )
        return [_doc_to_feedback(d.to_dict()) for d in docs]

    async def list_by_stadium(self, stadium_id: UUID, offset: int = 0, limit: int = 50) -> list[Feedback]:
        docs = (
            self._collection.where("stadium_id", "==", str(stadium_id))
            .order_by("created_at", direction="DESCENDING")
            .offset(offset)
            .limit(limit)
            .get()
        )
        return [_doc_to_feedback(d.to_dict()) for d in docs]

    async def list_by_user(self, user_id: UUID, offset: int = 0, limit: int = 50) -> list[Feedback]:
        docs = (
            self._collection.where("user_id", "==", str(user_id))
            .order_by("created_at", direction="DESCENDING")
            .offset(offset)
            .limit(limit)
            .get()
        )
        return [_doc_to_feedback(d.to_dict()) for d in docs]

    async def list_by_category(
        self, category: FeedbackCategory, stadium_id: UUID | None = None,
        offset: int = 0, limit: int = 50,
    ) -> list[Feedback]:
        if stadium_id:
            docs = (
                self._collection.where("stadium_id", "==", str(stadium_id))
                .where("category", "==", category.value)
                .order_by("created_at", direction="DESCENDING")
                .offset(offset)
                .limit(limit)
                .get()
            )
        else:
            docs = (
                self._collection.where("category", "==", category.value)
                .order_by("created_at", direction="DESCENDING")
                .offset(offset)
                .limit(limit)
                .get()
            )
        return [_doc_to_feedback(d.to_dict()) for d in docs]

    async def average_rating_by_event(self, event_id: UUID) -> float | None:
        docs = self._collection.where("event_id", "==", str(event_id)).get()
        ratings = [
            _doc_to_feedback(d.to_dict()).rating for d in docs
            if _doc_to_feedback(d.to_dict()).rating is not None
        ]
        if not ratings:
            return None
        return round(sum(ratings) / len(ratings), 2)

    async def average_rating_by_stadium(self, stadium_id: UUID) -> float | None:
        docs = self._collection.where("stadium_id", "==", str(stadium_id)).get()
        ratings = [
            _doc_to_feedback(d.to_dict()).rating for d in docs
            if _doc_to_feedback(d.to_dict()).rating is not None
        ]
        if not ratings:
            return None
        return round(sum(ratings) / len(ratings), 2)

    async def count_by_category(self, stadium_id: UUID) -> dict[str, int]:
        docs = self._collection.where("stadium_id", "==", str(stadium_id)).get()
        counts: dict[str, int] = {}
        for d in docs:
            cat = _doc_to_feedback(d.to_dict()).category.value
            counts[cat] = counts.get(cat, 0) + 1
        return counts
