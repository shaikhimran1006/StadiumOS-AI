from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings validated with Pydantic.

    All secrets are loaded from environment variables or Secret Manager at runtime.
    Never commit real values to source control.
    """

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    # ── Application ──────────────────────────────────────────────
    APP_NAME: str = "StadiumOS AI"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    PROJECT_ID: str = ""
    REGION: str = "us-central1"
    STADIUM_ID: str = ""
    STADIUM_NAME: str = ""

    # ── API ──────────────────────────────────────────────────────
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list[str] = ["*"]
    RATE_LIMIT_PER_MINUTE: int = 60

    # ── Google Cloud ─────────────────────────────────────────────
    GCP_PROJECT_ID: str = ""
    GCP_REGION: str = "us-central1"
    GOOGLE_APPLICATION_CREDENTIALS: str | None = None

    # ── Vertex AI ────────────────────────────────────────────────
    VERTEX_AI_MODEL: str = "gemini-2.0-flash-001"
    VERTEX_AI_MAX_TOKENS: int = 8192
    VERTEX_AI_TEMPERATURE: float = 0.3
    VERTEX_AI_TOP_P: float = 0.95

    # ── Firestore ────────────────────────────────────────────────
    FIRESTORE_COLLECTION_PREFIX: str = "stadiumos"

    # ── Identity ─────────────────────────────────────────────────
    AUTH_PROVIDER: Literal["identity_platform", "oauth2"] = "oauth2"
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    OAUTH2_CLIENT_ID: str = ""
    OAUTH2_CLIENT_SECRET: str = ""
    OAUTH2_REDIRECT_URI: str = "http://localhost:5173/auth/callback"

    # ── Google Maps ──────────────────────────────────────────────
    GOOGLE_MAPS_API_KEY: str = ""
    GOOGLE_MAPS_MAP_ID: str = ""

    # ── Speech ───────────────────────────────────────────────────
    SPEECH_SAMPLE_RATE: int = 16000
    SPEECH_LANGUAGE_CODE: str = "en-US"
    SPEECH_MULTIPLE_LANGUAGE_CODES: list[str] = [
        "en-US", "es-ES", "fr-FR", "de-DE", "pt-BR",
        "ar-SA", "zh-CN", "ja-JP", "ko-KR", "hi-IN",
    ]

    # ── Translation ──────────────────────────────────────────────
    TRANSLATION_DEFAULT_TARGET: str = "en"
    TRANSLATION_SUPPORTED_LANGUAGES: list[str] = [
        "en", "es", "fr", "de", "pt", "ar", "zh", "ja", "ko", "hi",
        "ru", "tr", "it", "nl", "pl", "th", "vi", "id", "ms", "sw",
    ]

    # ── BigQuery ─────────────────────────────────────────────────
    BIGQUERY_DATASET: str = "stadiumos_analytics"
    BIGQUERY_TABLE_EVENTS: str = "fan_events"
    BIGQUERY_TABLE_CONVERSATIONS: str = "ai_conversations"
    BIGQUERY_TABLE_METRICS: str = "platform_metrics"

    # ── Pub/Sub ──────────────────────────────────────────────────
    PUBSUB_TOPIC_ALERTS: str = "stadiumos-alerts"
    PUBSUB_TOPIC_ANALYTICS: str = "stadiumos-analytics"
    PUBSUB_TOPIC_NOTIFICATIONS: str = "stadiumos-notifications"
    PUBSUB_SUBSCRIPTION_ALERTS: str = "stadiumos-alerts-sub"

    # ── Storage ──────────────────────────────────────────────────
    GCS_BUCKET_MEDIA: str = "stadiumos-media"
    GCS_BUCKET_DOCUMENTS: str = "stadiumos-documents"
    GCS_BUCKET_BACKUPS: str = "stadiumos-backups"

    # ── Cloud Scheduler ──────────────────────────────────────────
    SCHEDULER_CRON_REPORTS: str = "0 6 * * *"
    SCHEDULER_CRON_HEALTH_CHECK: str = "*/5 * * * *"

    # ── Frontend ─────────────────────────────────────────────────
    FRONTEND_URL: str = "http://localhost:5173"

    @field_validator("GCP_PROJECT_ID", mode="before")
    @classmethod
    def _fallback_project(cls, v: str, info) -> str:
        return v or info.data.get("PROJECT_ID", "")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
