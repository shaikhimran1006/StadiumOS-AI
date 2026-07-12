"""Vertex AI Gemini generative AI service implementation."""

import json
import logging
from typing import Any

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
from app.domain.interfaces.ai_services import IGenerativeAIService

logger = logging.getLogger(__name__)


class GenerativeAIService(IGenerativeAIService):
    """Service for interacting with Vertex AI Gemini for text generation.

    Provides methods for basic response generation, context-aware generation,
    and structured output generation with proper error handling and retry logic.
    """

    def __init__(self) -> None:
        self._initialized = False
        self._model: GenerativeModel | None = None
        self._generation_config: GenerationConfig | None = None
        self._initialize()

    def _initialize(self) -> None:
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
            self._initialized = True
            logger.info(
                "GenerativeAIService initialized with model %s in %s/%s",
                settings.VERTEX_AI_MODEL,
                settings.GCP_PROJECT_ID,
                settings.GCP_REGION,
            )
        except Exception:
            logger.exception("Failed to initialize GenerativeAIService")
            self._initialized = False

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ResourceExhausted, ServiceUnavailable)),
        reraise=True,
    )
    async def generate_response(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Generate a text response from a prompt.

        Args:
            prompt: The user prompt to generate a response for.
            system_instruction: Optional system instruction to guide behavior.
            temperature: Override default temperature.
            max_tokens: Override default max tokens.

        Returns:
            Generated text response.

        Raises:
            RuntimeError: If the service is not initialized.
            GoogleAPIError: If the API call fails after retries.
        """
        if not self._initialized or self._model is None:
            raise RuntimeError("GenerativeAIService not initialized")

        gen_config = self._build_generation_config(temperature, max_tokens)

        contents: list[str] = []
        if system_instruction:
            contents.append(f"System: {system_instruction}\n\n")
        contents.append(prompt)

        try:
            response = self._model.generate_content(
                contents,
                generation_config=gen_config,
            )
            if response.text is None:
                logger.warning("Gemini returned empty response")
                return ""
            return response.text
        except InvalidArgument as exc:
            logger.error("Invalid argument to Gemini: %s", exc)
            raise
        except GoogleAPIError as exc:
            logger.error("Gemini API error: %s", exc)
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ResourceExhausted, ServiceUnavailable)),
        reraise=True,
    )
    async def generate_with_context(
        self,
        query: str,
        context: list[dict[str, str]],
        system_instruction: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Generate a response grounded in provided context documents.

        Args:
            query: The user's question.
            context: List of context documents, each with 'content' and optionally 'source'.
            system_instruction: Optional system instruction.
            temperature: Override default temperature.
            max_tokens: Override default max tokens.

        Returns:
            Grounded text response.
        """
        if not self._initialized or self._model is None:
            raise RuntimeError("GenerativeAIService not initialized")

        gen_config = self._build_generation_config(temperature, max_tokens)

        context_block = self._format_context_block(context)
        full_prompt = (
            f"Use the following context to answer the question. "
            f"If the answer is not in the context, say so clearly.\n\n"
            f"CONTEXT:\n{context_block}\n\n"
            f"QUESTION: {query}"
        )

        contents: list[str] = []
        if system_instruction:
            contents.append(f"System: {system_instruction}\n\n")
        contents.append(full_prompt)

        try:
            response = self._model.generate_content(
                contents,
                generation_config=gen_config,
            )
            if response.text is None:
                logger.warning("Gemini returned empty response for context query")
                return "I could not find a relevant answer in the provided context."
            return response.text
        except InvalidArgument as exc:
            logger.error("Invalid argument to Gemini: %s", exc)
            raise
        except GoogleAPIError as exc:
            logger.error("Gemini API error: %s", exc)
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ResourceExhausted, ServiceUnavailable)),
        reraise=True,
    )
    async def generate_structured_output(
        self,
        prompt: str,
        output_schema: dict[str, Any],
        system_instruction: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Generate a response and parse it as structured JSON matching a schema.

        Args:
            prompt: The user prompt.
            output_schema: Expected JSON schema for the output.
            system_instruction: Optional system instruction.
            temperature: Override default temperature.
            max_tokens: Override default max tokens.

        Returns:
            Parsed JSON dict matching the output schema.
        """
        schema_description = json.dumps(output_schema, indent=2)
        structured_prompt = (
            f"{prompt}\n\n"
            f"You MUST respond with valid JSON matching this schema:\n"
            f"```json\n{schema_description}\n```\n"
            f"Return ONLY the JSON object, no markdown formatting or explanations."
        )

        raw_response = await self.generate_response(
            prompt=structured_prompt,
            system_instruction=system_instruction,
            temperature=temperature or 0.1,
            max_tokens=max_tokens,
        )

        return self._parse_json_response(raw_response, output_schema)

    def _build_generation_config(
        self,
        temperature: float | None,
        max_tokens: int | None,
    ) -> GenerationConfig:
        kwargs: dict[str, Any] = {}
        if temperature is not None:
            kwargs["temperature"] = temperature
        if max_tokens is not None:
            kwargs["max_output_tokens"] = max_tokens

        if self._generation_config is not None:
            return GenerationConfig(
                temperature=kwargs.get("temperature", self._generation_config.temperature),
                max_output_tokens=kwargs.get("max_output_tokens", self._generation_config.max_output_tokens),
                top_p=self._generation_config.top_p,
            )

        return GenerationConfig(**kwargs)

    def _format_context_block(self, context: list[dict[str, str]]) -> str:
        parts: list[str] = []
        for i, doc in enumerate(context, 1):
            source = doc.get("source", f"Document {i}")
            content = doc.get("content", "")
            parts.append(f"[Source: {source}]\n{content}")
        return "\n\n".join(parts)

    def _parse_json_response(self, raw: str, schema: dict[str, Any]) -> dict[str, Any]:
        cleaned = raw.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                return parsed
            logger.warning("Gemini returned non-object JSON")
            return {"raw_output": parsed}
        except json.JSONDecodeError:
            logger.error("Failed to parse Gemini response as JSON: %s", cleaned[:200])
            return {"raw_output": cleaned, "parse_error": True}
