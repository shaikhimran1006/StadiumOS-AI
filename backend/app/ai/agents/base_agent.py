"""Base agent class for all StadiumOS AI agents."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
import logging
import time
import uuid

import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google.api_core.exceptions import (
    GoogleAPIError,
    InvalidArgument,
    ResourceExhausted,
    ServiceUnavailable,
)

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class AgentResponse:
    """Standardized response from all agents."""
    response_text: str
    agent_name: str
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    actions: list[dict[str, Any]] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "response_text": self.response_text,
            "agent_name": self.agent_name,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "actions": self.actions,
            "sources": self.sources,
        }


class BaseAgent(ABC):
    """Abstract base class for all StadiumOS AI agents.

    Each specialized agent inherits from this class and provides
    domain-specific system prompts and processing logic.
    """

    def __init__(self) -> None:
        self._model: GenerativeModel | None = None
        self._generation_config: GenerationConfig | None = None
        self._initialize_vertex_ai()

    def _initialize_vertex_ai(self) -> None:
        try:
            vertexai.init(
                project=settings.GCP_PROJECT_ID,
                location=settings.GCP_REGION,
            )
            self._generation_config = GenerationConfig(
                max_output_tokens=settings.VERTEX_AI_MAX_TOKENS,
                temperature=settings.VERTEX_AI_TEMPERATURE,
                top_p=settings.VERTEX_AI_TOP_P,
            )
            self._model = GenerativeModel(settings.VERTEX_AI_MODEL)
            logger.info("Vertex AI initialized for agent %s", self.agent_name)
        except Exception:
            logger.exception("Failed to initialize Vertex AI for agent %s", self.agent_name)

    @property
    @abstractmethod
    def agent_name(self) -> str:
        """Unique identifier for this agent."""

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """System prompt that defines agent behavior."""

    @abstractmethod
    def process(self, query: str, context: dict[str, Any]) -> AgentResponse:
        """Process a user query and return an agent response."""

    def _build_prompt(self, query: str, context: dict[str, Any]) -> list[str]:
        """Build the full prompt including system instructions and context."""
        prompt_parts: list[str] = []

        prompt_parts.append(f"SYSTEM INSTRUCTIONS:\n{self.system_prompt}\n")

        if context:
            context_str = self._format_context(context)
            prompt_parts.append(f"CONTEXT:\n{context_str}\n")

        prompt_parts.append(f"USER QUERY:\n{query}\n")
        prompt_parts.append(
            "Respond as the StadiumOS " + self.agent_name + ". "
            "If you need to trigger an action, include [ACTION: action_name] in your response. "
            "If you are referencing external information, include [SOURCE: source_name] in your response."
        )

        return ["".join(prompt_parts)]

    def _format_context(self, context: dict[str, Any]) -> str:
        """Format context dictionary into a readable string."""
        lines: list[str] = []
        for key, value in context.items():
            if isinstance(value, dict):
                lines.append(f"{key}:")
                for k, v in value.items():
                    lines.append(f"  {k}: {v}")
            else:
                lines.append(f"{key}: {value}")
        return "\n".join(lines)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ResourceExhausted, ServiceUnavailable)),
        reraise=True,
    )
    def _call_gemini(self, prompt_parts: list[str]) -> str:
        """Call Vertex AI Gemini with retry logic."""
        if self._model is None:
            raise RuntimeError(f"Vertex AI model not initialized for {self.agent_name}")

        try:
            start_time = time.time()
            response = self._model.generate_content(
                prompt_parts,
                generation_config=self._generation_config,
            )
            elapsed = time.time() - start_time
            logger.info(
                "Gemini response received for %s in %.2fs",
                self.agent_name,
                elapsed,
            )

            if response.text is None:
                return "I apologize, but I was unable to generate a response at this time. Please try again."

            return response.text

        except InvalidArgument as exc:
            logger.error("Invalid argument to Gemini for %s: %s", self.agent_name, exc)
            return "I encountered an issue processing your request. Please rephrase and try again."
        except GoogleAPIError as exc:
            logger.error("Gemini API error for %s: %s", self.agent_name, exc)
            raise

    def _parse_response(self, raw_response: str) -> dict[str, Any]:
        """Parse Gemini response to extract actions, sources, and metadata."""
        result: dict[str, Any] = {
            "actions": [],
            "sources": [],
            "clean_text": raw_response,
        }

        import re

        action_pattern = re.compile(r"\[ACTION:\s*(\w+)\]")
        actions = action_pattern.findall(raw_response)
        result["actions"] = [{"action": a, "id": str(uuid.uuid4())} for a in actions]
        result["clean_text"] = action_pattern.sub("", result["clean_text"]).strip()

        source_pattern = re.compile(r"\[SOURCE:\s*([^\]]+)\]")
        sources = source_pattern.findall(raw_response)
        result["sources"] = sources
        result["clean_text"] = source_pattern.sub("", result["clean_text"]).strip()

        return result

    def _compute_confidence(self, response_text: str, query: str) -> float:
        """Compute a simple confidence score based on response characteristics."""
        if not response_text:
            return 0.0

        confidence = 0.5

        if "sorry" in response_text.lower() or "i don't know" in response_text.lower():
            confidence -= 0.2
        if "i apologize" in response_text.lower():
            confidence -= 0.1
        if len(response_text) > 100:
            confidence += 0.1
        if any(word in response_text.lower() for word in ["definitely", "certainly", "absolutely"]):
            confidence += 0.1
        if any(phrase in response_text.lower() for phrase in ["not sure", "may vary", "depending"]):
            confidence -= 0.05

        return max(0.0, min(1.0, confidence))
