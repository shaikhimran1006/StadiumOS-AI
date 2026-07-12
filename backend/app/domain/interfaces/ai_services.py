from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class AIResponse(BaseModel):
    content: str
    intent: str | None = None
    confidence: float = 0.0
    entities: list[dict[str, Any]] = []
    sources: list[str] = []
    needs_human_agent: bool = False
    metadata: dict[str, Any] = {}


class RouteDecision(BaseModel):
    route: str
    target_agent: str | None = None
    priority: str = "normal"
    context: dict[str, Any] = {}


class RAGQueryResult(BaseModel):
    content: str
    source: str
    score: float
    metadata: dict[str, Any] = {}


class IAgentRouter(ABC):
    @abstractmethod
    async def route_message(
        self,
        message: str,
        user_id: UUID,
        conversation_id: UUID,
        context: dict[str, Any] | None = None,
    ) -> RouteDecision:
        """Route an incoming message to the appropriate AI agent or human handler."""
        ...

    @abstractmethod
    async def get_agent_capabilities(self, agent_id: str) -> dict[str, Any]:
        """Return the capabilities and specialties of a given agent."""
        ...

    @abstractmethod
    async def should_escalate(
        self,
        conversation_id: UUID,
        message_history: list[dict[str, str]],
    ) -> bool:
        """Determine if a conversation should be escalated to a human agent."""
        ...

    @abstractmethod
    async def get_available_agents(
        self, stadium_id: UUID | None = None
    ) -> list[dict[str, Any]]:
        """List available AI/human agents for assignment."""
        ...


class IGenerativeAIService(ABC):
    @abstractmethod
    async def generate_response(
        self,
        prompt: str,
        system_instruction: str | None = None,
        conversation_history: list[dict[str, str]] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> AIResponse:
        """Generate an AI response for a given prompt with optional context."""
        ...

    @abstractmethod
    async def generate_embedding(self, text: str) -> list[float]:
        """Generate a vector embedding for the given text."""
        ...

    @abstractmethod
    async def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate vector embeddings for a batch of texts."""
        ...

    @abstractmethod
    async def detect_language(self, text: str) -> str:
        """Detect the BCP-47 language tag of the input text."""
        ...

    @abstractmethod
    async def analyze_sentiment(self, text: str) -> dict[str, Any]:
        """Analyze sentiment of the given text, returning label and score."""
        ...

    @abstractmethod
    async def extract_entities(self, text: str) -> list[dict[str, Any]]:
        """Extract named entities from the given text."""
        ...

    @abstractmethod
    async def moderate_content(self, text: str) -> dict[str, Any]:
        """Check if content violates safety policies."""
        ...


class IRAGService(ABC):
    @abstractmethod
    async def index_document(
        self,
        document_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
        collection: str = "default",
    ) -> bool:
        """Index a document for retrieval."""
        ...

    @abstractmethod
    async def index_documents_batch(
        self,
        documents: list[dict[str, Any]],
        collection: str = "default",
    ) -> int:
        """Index a batch of documents. Returns count of successfully indexed."""
        ...

    @abstractmethod
    async def query(
        self,
        query: str,
        collection: str = "default",
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[RAGQueryResult]:
        """Query the RAG index and return relevant results."""
        ...

    @abstractmethod
    async def delete_document(self, document_id: str, collection: str = "default") -> bool:
        """Remove a document from the index."""
        ...

    @abstractmethod
    async def delete_collection(self, collection: str) -> bool:
        """Delete an entire collection from the index."""
        ...

    @abstractmethod
    async def get_collection_stats(self, collection: str) -> dict[str, Any]:
        """Return statistics about a collection (count, size, etc.)."""
        ...

    @abstractmethod
    async def hybrid_search(
        self,
        query: str,
        collection: str = "default",
        top_k: int = 5,
        keyword_weight: float = 0.3,
        semantic_weight: float = 0.7,
        filters: dict[str, Any] | None = None,
    ) -> list[RAGQueryResult]:
        """Perform hybrid keyword + semantic search."""
        ...
