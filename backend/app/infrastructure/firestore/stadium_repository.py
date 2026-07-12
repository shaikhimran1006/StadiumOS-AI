from __future__ import annotations

from datetime import datetime
from uuid import UUID

from google.cloud.firestore_v1 import Client as FirestoreClient

from app.core.config.settings import settings
from app.domain.entities.stadium import Facility, SectorConfig, Stadium
from app.domain.interfaces.repositories import IStadiumRepository
from app.infrastructure.firestore.client import get_firestore_client


def _stadium_to_doc(stadium: Stadium) -> dict:
    d = stadium.model_dump(mode="json")
    d["id"] = str(stadium.id)
    if stadium.location:
        d["location"] = stadium.location.model_dump()
    if stadium.sectors:
        d["sectors"] = [s.model_dump(mode="json") for s in stadium.sectors]
    if stadium.facilities:
        d["facilities"] = [f.model_dump(mode="json") for f in stadium.facilities]
    d["created_at"] = stadium.created_at.isoformat()
    d["updated_at"] = stadium.updated_at.isoformat()
    return d


def _doc_to_stadium(doc: dict) -> Stadium:
    raw = dict(doc)
    raw["id"] = UUID(raw["id"])
    if raw.get("location"):
        from app.domain.value_objects.coordinates import LatLong
        raw["location"] = LatLong(**raw["location"])
    if raw.get("sectors"):
        raw["sectors"] = [SectorConfig(**s) for s in raw["sectors"]]
    if raw.get("facilities"):
        raw["facilities"] = [Facility(**f) for f in raw["facilities"]]
    for field in ("created_at", "updated_at"):
        if raw.get(field) and isinstance(raw[field], str):
            raw[field] = datetime.fromisoformat(raw[field])
    return Stadium(**raw)


class StadiumRepository(IStadiumRepository):
    def __init__(self) -> None:
        self._client: FirestoreClient = get_firestore_client()
        self._collection_name = f"{settings.FIRESTORE_COLLECTION_PREFIX}_stadiums"
        self._collection = self._client.collection(self._collection_name)

    async def get_by_id(self, stadium_id: UUID) -> Stadium | None:
        doc_ref = self._collection.document(str(stadium_id))
        snapshot = doc_ref.get()
        if not snapshot.exists:
            return None
        return _doc_to_stadium(snapshot.to_dict())

    async def create(self, stadium: Stadium) -> Stadium:
        doc_ref = self._collection.document(str(stadium.id))
        doc_ref.set(_stadium_to_doc(stadium))
        return stadium

    async def update(self, stadium: Stadium) -> Stadium:
        doc_ref = self._collection.document(str(stadium.id))
        doc_ref.update(_stadium_to_doc(stadium))
        return stadium

    async def list_all(self, offset: int = 0, limit: int = 50) -> list[Stadium]:
        docs = self._collection.offset(offset).limit(limit).get()
        return [_doc_to_stadium(d.to_dict()) for d in docs]

    async def list_by_country(self, country_code: str) -> list[Stadium]:
        docs = self._collection.where("country_code", "==", country_code).get()
        return [_doc_to_stadium(d.to_dict()) for d in docs]

    async def list_by_city(self, city: str) -> list[Stadium]:
        docs = self._collection.where("city", "==", city).get()
        return [_doc_to_stadium(d.to_dict()) for d in docs]

    async def search(self, query: str, offset: int = 0, limit: int = 50) -> list[Stadium]:
        q = query.lower()
        all_docs = self._collection.offset(offset).limit(limit).get()
        results = []
        for d in all_docs:
            stadium = _doc_to_stadium(d.to_dict())
            if q in stadium.name.lower() or q in stadium.city.lower() or q in stadium.country.lower():
                results.append(stadium)
        return results
