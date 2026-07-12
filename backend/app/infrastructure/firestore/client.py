from __future__ import annotations

from functools import lru_cache

from google.cloud import firestore_v1

from app.core.config.settings import settings


@lru_cache
def get_firestore_client() -> firestore_v1.Client:
    return firestore_v1.Client(
        project=settings.GCP_PROJECT_ID,
    )
