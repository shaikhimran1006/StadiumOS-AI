from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class SpeechResult(BaseModel):
    text: str
    confidence: float = 0.0
    language: str | None = None
    duration_seconds: float = 0.0
    alternatives: list[dict[str, Any]] = []


class TranslationResult(BaseModel):
    translated_text: str
    source_language: str
    target_language: str
    confidence: float = 0.0


class VisionAnalysis(BaseModel):
    labels: list[dict[str, Any]] = []
    objects: list[dict[str, Any]] = []
    text_detected: str | None = None
    scene_description: str | None = None
    safety_labels: list[dict[str, Any]] = []
    crowd_density: float | None = None


class MapRoute(BaseModel):
    steps: list[dict[str, Any]] = []
    distance_meters: float = 0.0
    duration_seconds: float = 0.0
    polyline: str | None = None


class PubSubMessage(BaseModel):
    topic: str
    data: dict[str, Any]
    message_id: str | None = None
    publish_time: str | None = None
    attributes: dict[str, str] = {}


class BigQueryResult(BaseModel):
    rows: list[dict[str, Any]] = []
    total_rows: int = 0
    schema: list[dict[str, Any]] = []


class ISpeechService(ABC):
    @abstractmethod
    async def transcribe(
        self,
        audio_data: bytes,
        language: str | None = None,
        sample_rate: int = 16000,
    ) -> SpeechResult:
        """Transcribe audio data to text."""
        ...

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        language: str = "en",
        voice_name: str | None = None,
        speaking_rate: float = 1.0,
        pitch: float = 0.0,
    ) -> bytes:
        """Synthesize text to audio data (returns audio bytes)."""
        ...

    @abstractmethod
    async def detect_language(self, audio_data: bytes) -> str:
        """Detect the language of audio data."""
        ...

    @abstractmethod
    async def get_supported_voices(self, language: str | None = None) -> list[dict[str, Any]]:
        """List available voices, optionally filtered by language."""
        ...


class ITranslationService(ABC):
    @abstractmethod
    async def translate(
        self,
        text: str,
        target_language: str,
        source_language: str | None = None,
    ) -> TranslationResult:
        """Translate text to the target language."""
        ...

    @abstractmethod
    async def translate_batch(
        self,
        texts: list[str],
        target_language: str,
        source_language: str | None = None,
    ) -> list[TranslationResult]:
        """Translate a batch of texts."""
        ...

    @abstractmethod
    async def get_supported_languages(self) -> list[dict[str, str]]:
        """Return list of supported language codes and names."""
        ...


class IVisionService(ABC):
    @abstractmethod
    async def analyze_image(
        self,
        image_data: bytes,
        features: list[str] | None = None,
    ) -> VisionAnalysis:
        """Analyze an image for labels, objects, text, and safety."""
        ...

    @abstractmethod
    async def detect_crowd_density(
        self,
        image_data: bytes,
        sector_hint: str | None = None,
    ) -> dict[str, Any]:
        """Estimate crowd density from an image."""
        ...

    @abstractmethod
    async def detect_objects(
        self,
        image_data: bytes,
        object_types: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Detect specific objects in an image (e.g. suspicious packages)."""
        ...

    @abstractmethod
    async def ocr(self, image_data: bytes) -> str:
        """Extract text from an image via OCR."""
        ...


class IMapsService(ABC):
    @abstractmethod
    async def get_directions(
        self,
        origin: tuple[float, float],
        destination: tuple[float, float],
        mode: str = "walking",
        avoid: list[str] | None = None,
    ) -> MapRoute:
        """Get directions between two lat/long points."""
        ...

    @abstractmethod
    async def geocode(self, address: str) -> dict[str, Any]:
        """Convert an address to lat/long coordinates."""
        ...

    @abstractmethod
    async def reverse_geocode(self, lat: float, lon: float) -> dict[str, Any]:
        """Convert lat/long coordinates to an address."""
        ...

    @abstractmethod
    async def find_nearby(
        self,
        lat: float,
        lon: float,
        place_type: str,
        radius_meters: int = 1000,
    ) -> list[dict[str, Any]]:
        """Find nearby places of a given type."""
        ...

    @abstractmethod
    async def get_elevation(self, lat: float, lon: float) -> float:
        """Get elevation in meters for a coordinate."""
        ...


class IPubSubService(ABC):
    @abstractmethod
    async def publish(self, topic: str, message: PubSubMessage) -> str:
        """Publish a message to a topic. Returns the message ID."""
        ...

    @abstractmethod
    async def subscribe(
        self,
        topic: str,
        callback: Any,
        subscription_id: str | None = None,
    ) -> str:
        """Subscribe to a topic with a callback. Returns subscription ID."""
        ...

    @abstractmethod
    async def unsubscribe(self, subscription_id: str) -> bool:
        """Remove a subscription."""
        ...

    @abstractmethod
    async def publish_batch(self, topic: str, messages: list[PubSubMessage]) -> list[str]:
        """Publish multiple messages to a topic. Returns message IDs."""
        ...

    @abstractmethod
    async def get_topic_stats(self, topic: str) -> dict[str, Any]:
        """Return statistics about a topic (message count, subscribers, etc.)."""
        ...


class IBigQueryService(ABC):
    @abstractmethod
    async def execute_query(
        self,
        query: str,
        params: dict[str, Any] | None = None,
        max_results: int = 1000,
    ) -> BigQueryResult:
        """Execute a BigQuery SQL query with optional parameterized values."""
        ...

    @abstractmethod
    async def insert_rows(
        self,
        dataset: str,
        table: str,
        rows: list[dict[str, Any]],
    ) -> int:
        """Insert rows into a BigQuery table. Returns count of inserted rows."""
        ...

    @abstractmethod
    async def get_table_schema(self, dataset: str, table: str) -> list[dict[str, Any]]:
        """Return the schema of a BigQuery table."""
        ...

    @abstractmethod
    async def list_datasets(self) -> list[str]:
        """List all datasets in the project."""
        ...

    @abstractmethod
    async def list_tables(self, dataset: str) -> list[str]:
        """List all tables in a dataset."""
        ...

    @abstractmethod
    async def create_streaming_buffer(
        self, dataset: str, table: str
    ) -> bool:
        """Ensure a streaming buffer table exists for real-time inserts."""
        ...
