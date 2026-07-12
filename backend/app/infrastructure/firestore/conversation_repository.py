from __future__ import annotations

from datetime import datetime
from uuid import UUID

from google.cloud.firestore_v1 import Client as FirestoreClient

from app.core.config.settings import settings
from app.domain.entities.conversation import (
    Conversation,
    ConversationChannel,
    ConversationContext,
    ConversationStatus,
)
from app.domain.interfaces.repositories import IConversationRepository
from app.infrastructure.firestore.client import get_firestore_client


def _conversation_to_doc(conv: Conversation) -> dict:
    d = conv.model_dump(mode="json")
    d["id"] = str(conv.id)
    d["user_id"] = str(conv.user_id)
    if conv.context.stadium_id:
        d["context"] = {
            "stadium_id": str(conv.context.stadium_id) if conv.context.stadium_id else None,
            "event_id": str(conv.context.event_id) if conv.context.event_id else None,
            "sector": conv.context.sector,
            "entry_point": conv.context.entry_point,
            "initial_intent": conv.context.initial_intent,
            "referrer": conv.context.referrer,
        }
    if conv.assigned_agent_id:
        d["assigned_agent_id"] = str(conv.assigned_agent_id)
    if conv.started_at:
        d["started_at"] = conv.started_at.isoformat()
    if conv.ended_at:
        d["ended_at"] = conv.ended_at.isoformat()
    if conv.last_message_at:
        d["last_message_at"] = conv.last_message_at.isoformat()
    d["created_at"] = conv.created_at.isoformat()
    d["updated_at"] = conv.updated_at.isoformat()
    return d


def _doc_to_conversation(doc: dict) -> Conversation:
    raw = dict(doc)
    raw["id"] = UUID(raw["id"])
    raw["user_id"] = UUID(raw["user_id"])
    if raw.get("context") and isinstance(raw["context"], dict):
        ctx = raw["context"]
        if ctx.get("stadium_id"):
            ctx["stadium_id"] = UUID(ctx["stadium_id"])
        if ctx.get("event_id"):
            ctx["event_id"] = UUID(ctx["event_id"])
    if raw.get("assigned_agent_id"):
        raw["assigned_agent_id"] = UUID(raw["assigned_agent_id"])
    for field in ("started_at", "ended_at", "last_message_at", "created_at", "updated_at"):
        if raw.get(field) and isinstance(raw[field], str):
            raw[field] = datetime.fromisoformat(raw[field])
    return Conversation(**raw)


class ConversationRepository(IConversationRepository):
    def __init__(self) -> None:
        self._client: FirestoreClient = get_firestore_client()
        self._collection_name = f"{settings.FIRESTORE_COLLECTION_PREFIX}_conversations"
        self._collection = self._client.collection(self._collection_name)

    async def get_by_id(self, conversation_id: UUID) -> Conversation | None:
        doc_ref = self._collection.document(str(conversation_id))
        snapshot = doc_ref.get()
        if not snapshot.exists:
            return None
        return _doc_to_conversation(snapshot.to_dict())

    async def create(self, conversation: Conversation) -> Conversation:
        doc_ref = self._collection.document(str(conversation.id))
        doc_ref.set(_conversation_to_doc(conversation))
        return conversation

    async def update(self, conversation: Conversation) -> Conversation:
        doc_ref = self._collection.document(str(conversation.id))
        doc_ref.update(_conversation_to_doc(conversation))
        return conversation

    async def list_by_user(self, user_id: UUID, offset: int = 0, limit: int = 50) -> list[Conversation]:
        docs = (
            self._collection.where("user_id", "==", str(user_id))
            .order_by("created_at", direction="DESCENDING")
            .offset(offset)
            .limit(limit)
            .get()
        )
        return [_doc_to_conversation(d.to_dict()) for d in docs]

    async def list_by_status(self, status: ConversationStatus, offset: int = 0, limit: int = 50) -> list[Conversation]:
        docs = (
            self._collection.where("status", "==", status.value)
            .order_by("created_at", direction="DESCENDING")
            .offset(offset)
            .limit(limit)
            .get()
        )
        return [_doc_to_conversation(d.to_dict()) for d in docs]

    async def list_active_by_user(self, user_id: UUID) -> list[Conversation]:
        docs = (
            self._collection.where("user_id", "==", str(user_id))
            .where("status", "==", ConversationStatus.ACTIVE.value)
            .get()
        )
        return [_doc_to_conversation(d.to_dict()) for d in docs]

    async def list_by_stadium(self, stadium_id: UUID, offset: int = 0, limit: int = 50) -> list[Conversation]:
        docs = (
            self._collection.where("context.stadium_id", "==", str(stadium_id))
            .order_by("created_at", direction="DESCENDING")
            .offset(offset)
            .limit(limit)
            .get()
        )
        return [_doc_to_conversation(d.to_dict()) for d in docs]

    async def count_active(self) -> int:
        docs = self._collection.where("status", "==", ConversationStatus.ACTIVE.value).get()
        return len(docs)

    async def count_by_stadium(self, stadium_id: UUID) -> int:
        docs = self._collection.where("context.stadium_id", "==", str(stadium_id)).get()
        return len(docs)
