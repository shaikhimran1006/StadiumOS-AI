from __future__ import annotations

import logging
from typing import Any

from google.cloud import translate_v3
from google.api_core.exceptions import GoogleAPIError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config.settings import settings
from app.domain.interfaces.external_services import ITranslationService, TranslationResult

logger = logging.getLogger(__name__)


class GoogleTranslationService(ITranslationService):
    def __init__(self) -> None:
        self._client: translate_v3.TranslationServiceClient | None = None
        self._initialized = False
        self._initialize()

    def _initialize(self) -> None:
        try:
            self._client = translate_v3.TranslationServiceClient()
            self._initialized = True
            logger.info("GoogleTranslationService initialized")
        except Exception:
            logger.exception("Failed to initialize GoogleTranslationService")
            self._initialized = False

    def _get_parent(self) -> str:
        return f"projects/{settings.GCP_PROJECT_ID}/locations/{settings.GCP_REGION}"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(GoogleAPIError),
        reraise=True,
    )
    async def translate(
        self,
        text: str,
        target_language: str,
        source_language: str | None = None,
    ) -> TranslationResult:
        if not self._initialized or self._client is None:
            raise RuntimeError("GoogleTranslationService not initialized")

        request = translate_v3.TranslateTextRequest(
            parent=self._get_parent(),
            contents=[text],
            target_language_code=target_language,
            mime_type="text/plain",
        )
        if source_language:
            request.source_language_code = source_language

        response = self._client.translate_text(request=request)

        if not response.translations:
            return TranslationResult(
                translated_text=text,
                source_language=source_language or "und",
                target_language=target_language,
                confidence=0.0,
            )

        translation = response.translations[0]
        detected_lang = (
            translation.detected_language_code
            if hasattr(translation, "detected_language_code")
            else (source_language or "und")
        )

        return TranslationResult(
            translated_text=translation.translated_text,
            source_language=detected_lang,
            target_language=target_language,
            confidence=1.0,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(GoogleAPIError),
        reraise=True,
    )
    async def detect_language(self, text: str) -> str:
        if not self._initialized or self._client is None:
            raise RuntimeError("GoogleTranslationService not initialized")

        request = translate_v3.DetectLanguageRequest(
            parent=self._get_parent(),
            content=text,
            mime_type="text/plain",
        )

        response = self._client.detect_language(request=request)

        if response.languages:
            return response.languages[0].language_code

        return settings.TRANSLATION_DEFAULT_TARGET

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(GoogleAPIError),
        reraise=True,
    )
    async def translate_batch(
        self,
        texts: list[str],
        target_language: str,
        source_language: str | None = None,
    ) -> list[TranslationResult]:
        if not self._initialized or self._client is None:
            raise RuntimeError("GoogleTranslationService not initialized")

        if not texts:
            return []

        request = translate_v3.TranslateTextRequest(
            parent=self._get_parent(),
            contents=texts,
            target_language_code=target_language,
            mime_type="text/plain",
        )
        if source_language:
            request.source_language_code = source_language

        response = self._client.translate_text(request=request)

        results: list[TranslationResult] = []
        for i, translation in enumerate(response.translations):
            detected_lang = (
                translation.detected_language_code
                if hasattr(translation, "detected_language_code")
                else (source_language or "und")
            )
            results.append(
                TranslationResult(
                    translated_text=translation.translated_text,
                    source_language=detected_lang,
                    target_language=target_language,
                    confidence=1.0,
                )
            )

        while len(results) < len(texts):
            results.append(
                TranslationResult(
                    translated_text=texts[len(results)],
                    source_language=source_language or "und",
                    target_language=target_language,
                    confidence=0.0,
                )
            )

        return results

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(GoogleAPIError),
        reraise=True,
    )
    async def get_supported_languages(self) -> list[dict[str, str]]:
        if not self._initialized or self._client is None:
            raise RuntimeError("GoogleTranslationService not initialized")

        request = translate_v3.GetSupportedLanguagesRequest(
            parent=self._get_parent(),
            display_language_code="en",
        )

        response = self._client.get_supported_languages(request=request)

        languages: list[dict[str, str]] = []
        for lang in response.languages:
            languages.append({
                "language_code": lang.language_code,
                "display_name": lang.display_name,
            })

        return languages
