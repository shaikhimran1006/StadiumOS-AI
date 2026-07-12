from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

from google.cloud import storage

from app.core.config.settings import settings

logger = logging.getLogger(__name__)

BUCKET_MAP = {
    "media": settings.GCS_BUCKET_MEDIA,
    "documents": settings.GCS_BUCKET_DOCUMENTS,
    "backups": settings.GCS_BUCKET_BACKUPS,
}


class GCStorageService:
    def __init__(self) -> None:
        self._client = storage.Client(project=settings.GCP_PROJECT_ID)

    def _resolve_bucket(self, bucket_name: str) -> storage.Bucket:
        if bucket_name in BUCKET_MAP:
            bucket_name = BUCKET_MAP[bucket_name]
        return self._client.bucket(bucket_name)

    async def upload(
        self, bucket_name: str, destination_blob: str, data: bytes,
        content_type: str = "application/octet-stream", metadata: dict[str, str] | None = None,
    ) -> str:
        bucket = self._resolve_bucket(bucket_name)
        blob = bucket.blob(destination_blob)
        blob.content_type = content_type
        if metadata:
            blob.metadata = metadata
        blob.upload(data)
        logger.info("Uploaded gs://%s/%s", bucket.name, destination_blob)
        return f"gs://{bucket.name}/{destination_blob}"

    async def download(self, bucket_name: str, blob_name: str) -> bytes:
        bucket = self._resolve_bucket(bucket_name)
        blob = bucket.blob(blob_name)
        data = blob.download()
        return data

    async def delete(self, bucket_name: str, blob_name: str) -> bool:
        bucket = self._resolve_bucket(bucket_name)
        blob = bucket.blob(blob_name)
        if not blob.exists():
            return False
        blob.delete()
        logger.info("Deleted gs://%s/%s", bucket.name, blob_name)
        return True

    async def generate_signed_url(
        self, bucket_name: str, blob_name: str,
        expiration_seconds: int = 3600, method: str = "GET",
    ) -> str:
        bucket = self._resolve_bucket(bucket_name)
        blob = bucket.blob(blob_name)
        url = blob.generate_signed_url(
            expiration=expiration_seconds,
            method=method,
            version="v4",
        )
        return url

    async def list_files(
        self, bucket_name: str, prefix: str = "", delimiter: str | None = None,
    ) -> list[dict[str, Any]]:
        bucket = self._resolve_bucket(bucket_name)
        blobs = self._client.list_blobs(
            bucket.name, prefix=prefix, delimiter=delimiter,
        )
        results = []
        for blob in blobs:
            results.append({
                "name": blob.name,
                "size": blob.size,
                "content_type": blob.content_type,
                "updated": blob.updated.isoformat() if blob.updated else None,
                "metadata": blob.metadata or {},
                "etag": blob.etag,
            })
        return results

    async def blob_exists(self, bucket_name: str, blob_name: str) -> bool:
        bucket = self._resolve_bucket(bucket_name)
        blob = bucket.blob(blob_name)
        return blob.exists()

    async def copy_blob(
        self, source_bucket: str, source_blob: str,
        destination_bucket: str, destination_blob: str | None = None,
    ) -> str:
        src_bucket = self._resolve_bucket(source_bucket)
        dst_bucket = self._resolve_bucket(destination_bucket)
        src = src_bucket.blob(source_blob)
        dst_name = destination_blob or source_blob
        src.copy(dst_bucket, dst_name)
        logger.info("Copied gs://%s/%s to gs://%s/%s", src_bucket.name, source_blob, dst_bucket.name, dst_name)
        return f"gs://{dst_bucket.name}/{dst_name}"
