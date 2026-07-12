from __future__ import annotations

from typing import Any, TypeVar

from google.cloud.firestore_v1 import Client as FirestoreClient

T = TypeVar("T")


class FirestoreSerializer:
    """Mixin with helpers for serializing/deserializing Firestore documents."""

    @staticmethod
    def serialize_datetime(dt) -> str:
        return dt.isoformat() if dt else None

    @staticmethod
    def deserialize_datetime(val: str | None):
        if val is None:
            return None
        from datetime import datetime
        if isinstance(val, str):
            return datetime.fromisoformat(val)
        return val

    @staticmethod
    def serialize_uuid(u: Any) -> str | None:
        return str(u) if u else None

    @staticmethod
    def deserialize_uuid(val: str | None):
        from uuid import UUID
        return UUID(val) if val else None

    @staticmethod
    def serialize_enum(e) -> str | None:
        return e.value if e else None

    @staticmethod
    def deserialize_enum(enum_cls, val: str | None):
        if val is None:
            return None
        return enum_cls(val)
