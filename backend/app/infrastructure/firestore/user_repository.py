from __future__ import annotations

from datetime import timezone
from uuid import UUID

from google.cloud.firestore_v1 import Client as FirestoreClient

from app.core.config.settings import settings
from app.domain.entities.user import DeviceInfo, User, UserRole, UserStatus
from app.domain.interfaces.repositories import IUserRepository
from app.infrastructure.firestore.client import get_firestore_client


def _user_to_doc(user: User) -> dict:
    d = user.model_dump(mode="json")
    d["id"] = str(user.id)
    if user.home_stadium_id:
        d["home_stadium_id"] = str(user.home_stadium_id)
    if user.current_location:
        d["current_location"] = user.current_location.model_dump()
    if user.device_info:
        d["device_info"] = user.device_info.model_dump()
    if user.assigned_sector:
        d["assigned_sector"] = user.assigned_sector.value
    d["created_at"] = user.created_at.isoformat()
    d["updated_at"] = user.updated_at.isoformat()
    return d


def _doc_to_user(doc: dict) -> User:
    raw = dict(doc)
    raw["id"] = UUID(raw["id"]) if isinstance(raw.get("id"), str) else raw.get("id")
    if raw.get("home_stadium_id"):
        raw["home_stadium_id"] = UUID(raw["home_stadium_id"])
    if raw.get("current_location"):
        from app.domain.value_objects.coordinates import LatLong
        raw["current_location"] = LatLong(**raw["current_location"])
    if raw.get("device_info"):
        raw["device_info"] = DeviceInfo(**raw["device_info"])
    if raw.get("assigned_sector"):
        from app.domain.value_objects.gps_sector import GpsSector
        raw["assigned_sector"] = GpsSector(raw["assigned_sector"])
    if raw.get("created_at") and isinstance(raw["created_at"], str):
        from datetime import datetime
        raw["created_at"] = datetime.fromisoformat(raw["created_at"])
    if raw.get("updated_at") and isinstance(raw["updated_at"], str):
        from datetime import datetime
        raw["updated_at"] = datetime.fromisoformat(raw["updated_at"])
    return User(**raw)


class UserRepository(IUserRepository):
    def __init__(self) -> None:
        self._client: FirestoreClient = get_firestore_client()
        self._collection_name = f"{settings.FIRESTORE_COLLECTION_PREFIX}_users"
        self._collection = self._client.collection(self._collection_name)

    async def get_by_id(self, user_id: UUID) -> User | None:
        doc_ref = self._collection.document(str(user_id))
        snapshot = doc_ref.get()
        if not snapshot.exists:
            return None
        return _doc_to_user(snapshot.to_dict())

    async def get_by_external_id(self, external_id: str) -> User | None:
        docs = self._collection.where("external_id", "==", external_id).limit(1).get()
        for doc in docs:
            return _doc_to_user(doc.to_dict())
        return None

    async def get_by_email(self, email: str) -> User | None:
        docs = self._collection.where("email", "==", email).limit(1).get()
        for doc in docs:
            return _doc_to_user(doc.to_dict())
        return None

    async def get_by_phone(self, phone: str) -> User | None:
        docs = self._collection.where("phone", "==", phone).limit(1).get()
        for doc in docs:
            return _doc_to_user(doc.to_dict())
        return None

    async def create(self, user: User) -> User:
        doc_ref = self._collection.document(str(user.id))
        doc_ref.set(_user_to_doc(user))
        return user

    async def update(self, user: User) -> User:
        doc_ref = self._collection.document(str(user.id))
        doc_ref.update(_user_to_doc(user))
        return user

    async def delete(self, user_id: UUID) -> bool:
        doc_ref = self._collection.document(str(user_id))
        snapshot = doc_ref.get()
        if not snapshot.exists:
            return False
        doc_ref.delete()
        return True

    async def list_by_role(self, role: UserRole, offset: int = 0, limit: int = 50) -> list[User]:
        docs = self._collection.where("role", "==", role.value).offset(offset).limit(limit).get()
        return [_doc_to_user(d.to_dict()) for d in docs]

    async def list_by_status(self, status: UserStatus, offset: int = 0, limit: int = 50) -> list[User]:
        docs = self._collection.where("status", "==", status.value).offset(offset).limit(limit).get()
        return [_doc_to_user(d.to_dict()) for d in docs]

    async def list_by_stadium(self, stadium_id: UUID, offset: int = 0, limit: int = 50) -> list[User]:
        docs = self._collection.where("home_stadium_id", "==", str(stadium_id)).offset(offset).limit(limit).get()
        return [_doc_to_user(d.to_dict()) for d in docs]

    async def search(self, query: str, offset: int = 0, limit: int = 50) -> list[User]:
        q = query.lower()
        all_docs = self._collection.offset(offset).limit(limit).get()
        results = []
        for d in all_docs:
            user = _doc_to_user(d.to_dict())
            if q in user.display_name.lower() or (user.email and q in user.email.lower()):
                results.append(user)
        return results

    async def count_by_role(self, role: UserRole) -> int:
        docs = self._collection.where("role", "==", role.value).get()
        return len(docs)

    async def count_by_stadium(self, stadium_id: UUID) -> int:
        docs = self._collection.where("home_stadium_id", "==", str(stadium_id)).get()
        return len(docs)
