from __future__ import annotations

from datetime import datetime
from uuid import UUID

from google.cloud.firestore_v1 import Client as FirestoreClient

from app.core.config.settings import settings
from app.domain.entities.message import Message, MessageMetadata
from app.domain.interfaces.repositories import IMessageRepository
from app.infrastructure.firestore.client import get_firestore_client


def _message_to_doc(msg: Message) -> dict:
    d = msg.model_dump(mode="json")
    d["id"] = str(msg.id)
    d["conversation_id"] = str(msg.conversation_id)
    if msg.sender_id:
        d["sender_id"] = str(msg.sender_id)
    if msg.parent_message_id:
        d["parent_message_id"] = str(msg.parent_message_id)
    if msg.translation_of:
        d["translation_of"] = str(msg.translation_of)
    d["created_at"] = msg.created_at.isoformat()
    d["updated_at"] = msg.updated_at.isoformat()
    return d


def _doc_to_message(doc: dict) -> Message:
    raw = dict(doc)
    raw["id"] = UUID(raw["id"])
    raw["conversation_id"] = UUID(raw["conversation_id"])
    if raw.get("sender_id"):
        raw["sender_id"] = UUID(raw["sender_id"])
    if raw.get("parent_message_id"):
        raw["parent_message_id"] = UUID(raw["parent_message_id"])
    if raw.get("translation_of"):
        raw["translation_of"] = UUID(raw["translation_of"])
    for field in ("created_at", "updated_at"):
        if raw.get(field) and isinstance(raw[field], str):
            raw[field] = datetime.fromisoformat(raw[field])
    return Message(**raw)


class MessageRepository(IMessageRepository):
    def __init__(self) -> None:
        self._client: FirestoreClient = get_firestore_client()
        self._collection_name = f"{settings.FIRESTORE_COLLECTION_PREFIX}_messages"
        self._collection = self._client.collection(self._collection_name)

    async def get_by_id(self, message_id: UUID) -> Message | None:
        doc_ref = self._collection.document(str(message_id))
        snapshot = doc_ref.get()
        if not snapshot.exists:
            return None
        return _doc_to_message(snapshot.to_dict())

    async def create(self, message: Message) -> Message:
        doc_ref = self._collection.document(str(message.id))
        doc_ref.set(_message_to_doc(message))
        return message

    async def update(self, message: Message) -> Message:
        doc_ref = self._collection.document(str(message.id))
        doc_ref.update(_message_to_doc(message))
        return message

    async def list_by_conversation(
        self, conversation_id: UUID, offset: int = 0, limit: int = 100
    ) -> list[Message]:
        docs = (
            self._collection.where("conversation_id", "==", str(conversation_id))
            .order_by("created_at", direction="ASCENDING")
            .offset(offset)
            .limit(limit)
            .get()
        )
        return [_doc_to_message(d.to_dict()) for d in docs]

    async def list_recent_by_conversation(
        self, conversation_id: UUID, limit: int = 20
    ) -> list[Message]:
        docs = (
            self._collection.where("conversation_id", "==", str(conversation_id))
            .order_by("created_at", direction="DESCENDING")
            .limit(limit)
            .get()
        )
        return [_doc_to_message(d.to_dict()) for d in docs]

    async def count_by_conversation(self, conversation_id: UUID) -> int:
        docs = self._collection.where("conversation_id", "==", str(conversation_id)).get()
        return len(docs)

    async def search_in_conversation(
        self, conversation_id: UUID, query: str, limit: int = 20
    ) -> list[Message]:
        q = query.lower()
        docs = (
            self._collection.where("conversation_id", "==", str(conversation_id))
            .order_by("created_at", direction="DESCENDING")
            .get()
        )
        results = []
        for d in docs:
            msg = _doc_to_message(d.to_dict())
            if q in msg.content.lower():
                results.append(msg)
                if len(results) >= limit:
                    break
        return results
