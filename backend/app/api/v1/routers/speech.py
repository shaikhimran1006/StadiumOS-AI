from __future__ import annotations

import base64
import logging
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.api.v1.dependencies.getters import (
    get_speech_service,
    get_translation_service,
)
from app.core.security.auth import TokenPayload, get_current_user
from app.services.speech.speech_service import GoogleSpeechService
from app.services.translation.translation_service import GoogleTranslationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/speech", tags=["Speech"])


class TranscribeRequest(BaseModel):
    audio_base64: str = Field(..., description="Base64-encoded audio data (LINEAR16 PCM)")
    language: str | None = Field(default=None, description="BCP-47 language code")
    sample_rate: int = Field(default=16000, description="Sample rate in Hz")


class TranscribeResponse(BaseModel):
    text: str
    confidence: float = 0.0
    language: str | None = None
    alternatives: list[dict[str, Any]] = Field(default_factory=list)


class SynthesizeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    language: str = Field(default="en", description="BCP-47 language code")
    voice_name: str | None = None
    speaking_rate: float = Field(default=1.0, ge=0.25, le=4.0)
    pitch: float = Field(default=0.0, ge=-20.0, le=20.0)


class SynthesizeResponse(BaseModel):
    audio_base64: str
    content_type: str = "audio/mp3"


class TranslateSpeechRequest(BaseModel):
    audio_base64: str
    source_language: str | None = None
    target_language: str = Field(default="en")
    sample_rate: int = Field(default=16000)


class TranslateSpeechResponse(BaseModel):
    original_text: str
    translated_text: str
    source_language: str
    target_language: str


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    request: TranscribeRequest,
    current_user: TokenPayload = Depends(get_current_user),
    service: GoogleSpeechService = Depends(get_speech_service),
) -> TranscribeResponse:
    audio_data = base64.b64decode(request.audio_base64)
    result = await service.transcribe(
        audio_data=audio_data,
        language=request.language,
        sample_rate=request.sample_rate,
    )
    return TranscribeResponse(
        text=result.text,
        confidence=result.confidence,
        language=result.language,
        alternatives=result.alternatives,
    )


@router.post("/synthesize", response_model=SynthesizeResponse)
async def synthesize_speech(
    request: SynthesizeRequest,
    current_user: TokenPayload = Depends(get_current_user),
    service: GoogleSpeechService = Depends(get_speech_service),
) -> SynthesizeResponse:
    audio_bytes = await service.synthesize(
        text=request.text,
        language=request.language,
        voice_name=request.voice_name,
        speaking_rate=request.speaking_rate,
        pitch=request.pitch,
    )
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    return SynthesizeResponse(audio_base64=audio_b64)


@router.post("/translate", response_model=TranslateSpeechResponse)
async def translate_speech(
    request: TranslateSpeechRequest,
    current_user: TokenPayload = Depends(get_current_user),
    speech_service: GoogleSpeechService = Depends(get_speech_service),
    translation_service: GoogleTranslationService = Depends(get_translation_service),
) -> TranslateSpeechResponse:
    audio_data = base64.b64decode(request.audio_base64)

    transcription = await speech_service.transcribe(
        audio_data=audio_data,
        language=request.source_language,
        sample_rate=request.sample_rate,
    )

    if not transcription.text:
        return TranslateSpeechResponse(
            original_text="",
            translated_text="",
            source_language=transcription.language or "unknown",
            target_language=request.target_language,
        )

    detected_lang = transcription.language or request.source_language or "en"

    if detected_lang and detected_lang.startswith(request.target_language[:2]):
        translated_text = transcription.text
    else:
        translation = await translation_service.translate(
            text=transcription.text,
            target_language=request.target_language,
            source_language=detected_lang,
        )
        translated_text = translation.translated_text

    return TranslateSpeechResponse(
        original_text=transcription.text,
        translated_text=translated_text,
        source_language=detected_lang,
        target_language=request.target_language,
    )
