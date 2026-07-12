from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from google.cloud import bigquery

from app.core.config.settings import settings
from app.domain.interfaces.external_services import BigQueryResult, IBigQueryService

logger = logging.getLogger(__name__)


class BigQueryService(IBigQueryService):
    def __init__(self) -> None:
        self._client = bigquery.Client(project=settings.GCP_PROJECT_ID)
        self._dataset_id = settings.BIGQUERY_DATASET

    @property
    def _dataset_ref(self) -> str:
        return f"{settings.GCP_PROJECT_ID}.{self._dataset_id}"

    def _table_ref(self, table: str) -> str:
        return f"{self._dataset_ref}.{table}"

    async def execute_query(
        self, query: str, params: dict[str, Any] | None = None,
        max_results: int = 1000,
    ) -> BigQueryResult:
        job_config = bigquery.QueryJobConfig()
        if params:
            query_params = [
                bigquery.ScalarQueryParameter(key, self._infer_type(val), val)
                for key, val in params.items()
            ]
            job_config.query_parameters = query_params

        job = self._client.query(query, job_config=job_config)
        results = job.result(max_results=max_results)
        rows = [dict(row.items()) for row in results]
        schema = [{"name": s.name, "type": s.field_type, "mode": s.mode} for s in results.schema]
        return BigQueryResult(
            rows=rows,
            total_rows=len(rows),
            schema=schema,
        )

    async def insert_rows(
        self, dataset: str, table: str, rows: list[dict[str, Any]],
    ) -> int:
        table_id = self._table_ref(table)
        errors = self._client.insert_rows_json(table_id, rows)
        if errors:
            logger.error("BigQuery insert errors: %s", errors)
            raise RuntimeError(f"BigQuery insert failed: {errors}")
        logger.info("Inserted %d rows into %s", len(rows), table_id)
        return len(rows)

    async def get_table_schema(self, dataset: str, table: str) -> list[dict[str, Any]]:
        table_id = self._table_ref(table)
        bq_table = self._client.get_table(table_id)
        return [
            {"name": s.name, "type": s.field_type, "mode": s.mode, "description": s.description}
            for s in bq_table.schema
        ]

    async def list_datasets(self) -> list[str]:
        datasets = list(self._client.list_datasets())
        return [d.dataset_id for d in datasets]

    async def list_tables(self, dataset: str) -> list[str]:
        dataset_ref = bigquery.DatasetReference(settings.GCP_PROJECT_ID, dataset)
        tables = list(self._client.list_tables(dataset_ref))
        return [t.table_id for t in tables]

    async def create_streaming_buffer(self, dataset: str, table: str) -> bool:
        table_id = self._table_ref(table)
        try:
            bq_table = self._client.get_table(table_id)
            if bq_table.streaming_buffer is not None:
                return True
            logger.info("Table %s already has a streaming buffer", table_id)
            return True
        except Exception:
            schema = [
                bigquery.SchemaField("inserted_at", "TIMESTAMP", mode="REQUIRED"),
            ]
            bq_table = bigquery.Table(table_id, schema=schema)
            self._client.create_table(bq_table)
            logger.info("Created table %s with streaming buffer", table_id)
            return True

    async def create_dataset_if_not_exists(self) -> str:
        dataset_ref = bigquery.DatasetReference(
            settings.GCP_PROJECT_ID, self._dataset_id
        )
        try:
            self._client.get_dataset(dataset_ref)
            logger.info("Dataset %s already exists", self._dataset_id)
        except Exception:
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = settings.GCP_REGION
            self._client.create_dataset(dataset)
            logger.info("Created dataset %s in %s", self._dataset_id, settings.GCP_REGION)
        return self._dataset_id

    async def log_event(
        self, event_type: str, user_id: str | None, stadium_id: str | None,
        payload: dict[str, Any],
    ) -> int:
        row = {
            "event_id": payload.pop("event_id", ""),
            "event_type": event_type,
            "user_id": user_id or "",
            "stadium_id": stadium_id or "",
            "payload": payload,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        return await self.insert_rows(
            self._dataset_id, settings.BIGQUERY_TABLE_EVENTS, [row],
        )

    async def log_conversation(
        self, conversation_id: str, user_id: str, message: str,
        response: str, model_name: str, latency_ms: int,
        tokens_used: int, language: str = "en",
    ) -> int:
        row = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "message": message,
            "response": response,
            "model_name": model_name,
            "latency_ms": latency_ms,
            "tokens_used": tokens_used,
            "language": language,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        return await self.insert_rows(
            self._dataset_id, settings.BIGQUERY_TABLE_CONVERSATIONS, [row],
        )

    async def log_metric(
        self, metric_name: str, value: float,
        labels: dict[str, str] | None = None,
        stadium_id: str | None = None,
    ) -> int:
        row = {
            "metric_name": metric_name,
            "value": value,
            "labels": labels or {},
            "stadium_id": stadium_id or "",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        return await self.insert_rows(
            self._dataset_id, settings.BIGQUERY_TABLE_METRICS, [row],
        )

    async def query_analytics(
        self, query: str, params: dict[str, Any] | None = None,
        max_results: int = 1000,
    ) -> BigQueryResult:
        return await self.execute_query(query, params, max_results)

    @staticmethod
    def _infer_type(val: Any) -> str:
        if isinstance(val, bool):
            return "BOOL"
        if isinstance(val, int):
            return "INT64"
        if isinstance(val, float):
            return "FLOAT64"
        return "STRING"
