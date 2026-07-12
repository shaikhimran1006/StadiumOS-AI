from __future__ import annotations

import logging
from typing import Any

from google.cloud import speech_v1, texttospeech_v1
from google.cloud.speech_v1 import enums
from google.api_core.exceptions import GoogleAPIError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config.settings import settings
from app.domain.interfaces.external_services import ISpeechService, SpeechResult

logger = logging.getLogger(__name__)


class GoogleSpeechService(ISpeechService):
    def __init__(self) -> None:
        self._speech_client: speech_v1.SpeechClient | None = None
        self._tts_client: texttospeech_v1.TextToSpeechClient | None = None
        self._initialized = False
        self._initialize()

    def _initialize(self) -> None:
        try:
            self._speech_client = speech_v1.SpeechClient()
            self._tts_client = texttospeech_v1.TextToSpeechClient()
            self._initialized = True
            logger.info("GoogleSpeechService initialized")
        except Exception:
            logger.exception("Failed to initialize GoogleSpeechService")
            self._initialized = False

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(GoogleAPIError),
        reraise=True,
    )
    async def transcribe(
        self,
        audio_data: bytes,
        language: str | None = None,
        sample_rate: int = 16000,
    ) -> SpeechResult:
        if not self._initialized or self._speech_client is None:
            raise RuntimeError("GoogleSpeechService not initialized")

        lang_code = language or settings.SPEECH_LANGUAGE_CODE

        audio = speech_v1.RecognitionAudio(content=audio_data)
        config = speech_v1.RecognitionConfig(
            encoding=speech_v1.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=sample_rate,
            language_code=lang_code,
            enable_automatic_punctuation=True,
            enable_word_time_offsets=True,
            model="latest_long",
            use_enhanced=True,
            alternative_language_codes=[
                lc for lc in settings.SPEECH_MULTIPLE_LANGUAGE_CODES if lc != lang_code
            ][:3],
        )

        try:
            operation = self._speech_client.long_running_recognize(
                config=config, audio=audio
            )
            response = operation.result(timeout=120)
        except GoogleAPIError:
            config.model = "default"
            config.use_enhanced = False
            config.alternative_language_codes.clear()
            response = self._speech_client.recognize(config=config, audio=audio)

        if not response.results:
            return SpeechResult(text="", confidence=0.0, language=lang_code)

        result = response.results[0]
        best_alternative = result.alternatives[0] if result.alternatives else None
        text = best_alternative.transcript if best_alternative else ""
        confidence = best_alternative.confidence if best_alternative else 0.0

        alternatives: list[dict[str, Any]] = []
        if best_alternative and len(result.alternatives) > 1:
            for alt in result.alternatives[1:5]:
                alternatives.append({
                    "transcript": alt.transcript,
                    "confidence": alt.confidence,
                })

        detected_language = lang_code
        if hasattr(result, "language_code") and result.language_code:
            detected_language = result.language_code

        return SpeechResult(
            text=text,
            confidence=confidence,
            language=detected_language,
            alternatives=alternatives,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(GoogleAPIError),
        reraise=True,
    )
    async def synthesize(
        self,
        text: str,
        language: str = "en",
        voice_name: str | None = None,
        speaking_rate: float = 1.0,
        pitch: float = 0.0,
    ) -> bytes:
        if not self._initialized or self._tts_client is None:
            raise RuntimeError("GoogleSpeechService not initialized")

        voice = texttospeech_v1.VoiceSelectionParams(
            language_code=language,
            ssml_gender=texttospeech_v1.SsmlVoiceGender.NEUTRAL,
        )
        if voice_name:
            voice.name = voice_name

        audio_config = texttospeech_v1.AudioConfig(
            audio_encoding=texttospeech_v1.AudioEncoding.MP3,
            speaking_rate=speaking_rate,
            pitch=pitch,
            sample_rate_hertz=24000,
        )

        synthesis_input = texttospeech_v1.SynthesisInput(text=text)

        response = self._tts_client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config,
        )

        return response.audio_content

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(GoogleAPIError),
        reraise=True,
    )
    async def detect_language(self, audio_data: bytes) -> str:
        if not self._initialized or self._speech_client is None:
            raise RuntimeError("GoogleSpeechService not initialized")

        audio = speech_v1.RecognitionAudio(content=audio_data)
        config = speech_v1.RecognitionConfig(
            encoding=speech_v1.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=settings.SPEECH_SAMPLE_RATE,
            language_code="en-US",
            alternative_language_codes=settings.SPEECH_MULTIPLE_LANGUAGE_CODES,
        )

        response = self._speech_client.recognize(config=config, audio=audio)

        if response.results:
            result = response.results[0]
            if hasattr(result, "language_code") and result.language_code:
                return result.language_code
            if result.alternatives:
                return settings.SPEECH_LANGUAGE_CODE

        return settings.SPEECH_LANGUAGE_CODE

    async def get_supported_voices(
        self, language: str | None = None
    ) -> list[dict[str, Any]]:
        if not self._initialized or self._tts_client is None:
            raise RuntimeError("GoogleSpeechService not initialized")

        request = texttospeech_v1.ListVoicesRequest()
        if language:
            request.language_code = language

        response = self._tts_client.list_voices(request=request)

        voices: list[dict[str, Any]] = []
        for voice in response.voices:
            voices.append({
                "name": voice.name,
                "language_codes": list(voice.language_codes),
                "ssml_gender": voice.ssml_gender.name,
                "natural_sample_rate_hertz": voice.natural_sample_rate_hertz,
            })

        return voices

    async def transcribe_streaming(
        self,
        audio_chunks: Any,
        language: str | None = None,
        sample_rate: int = 16000,
    ) -> Any:
        if not self._initialized or self._speech_client is None:
            raise RuntimeError("GoogleSpeechService not initialized")

        lang_code = language or settings.SPEECH_LANGUAGE_CODE

        config = speech_v1.RecognitionConfig(
            encoding=speech_v1.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=sample_rate,
            language_code=lang_code,
            enable_automatic_punctuation=True,
            interim_results=True,
        )

        streaming_config = speech_v1.StreamingRecognitionConfig(
            config=config,
            interim_results=True,
        )

        def audio_generator():
            for chunk in audio_chunks:
                yield speech_v1.StreamingRecognizeRequest(audio_content=chunk)

        requests = audio_generator()
        responses = self._speech_client.streaming_recognize(
            config=streaming_config, requests=requests
        )

        results: list[dict[str, Any]] = []
        for response in responses:
            for result in response.results:
                if result.alternatives:
                    results.append({
                        "transcript": result.alternatives[0].transcript,
                        "confidence": result.alternatives[0].confidence,
                        "is_final": result.is_final,
                    })

        return results
