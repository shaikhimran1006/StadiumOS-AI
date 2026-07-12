from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.api.v1.dependencies.getters import get_translation_service
from app.core.security.auth import TokenPayload, get_current_user
from app.services.translation.translation_service import GoogleTranslationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/translation", tags=["Translation"])


class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000)
    target_language: str = Field(..., min_length=2, max_length=10)
    source_language: str | None = Field(default=None, min_length=2, max_length=10)


class TranslateResponse(BaseModel):
    translated_text: str
    source_language: str
    target_language: str
    confidence: float = 0.0


class DetectRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000)


class DetectResponse(BaseModel):
    language_code: str


class SupportedLanguage(BaseModel):
    language_code: str
    display_name: str


@router.post("/translate", response_model=TranslateResponse)
async def translate_text(
    request: TranslateRequest,
    current_user: TokenPayload = Depends(get_current_user),
    service: GoogleTranslationService = Depends(get_translation_service),
) -> TranslateResponse:
    result = await service.translate(
        text=request.text,
        target_language=request.target_language,
        source_language=request.source_language,
    )
    return TranslateResponse(
        translated_text=result.translated_text,
        source_language=result.source_language,
        target_language=result.target_language,
        confidence=result.confidence,
    )


@router.post("/detect", response_model=DetectResponse)
async def detect_language(
    request: DetectRequest,
    current_user: TokenPayload = Depends(get_current_user),
    service: GoogleTranslationService = Depends(get_translation_service),
) -> DetectResponse:
    language_code = await service.detect_language(text=request.text)
    return DetectResponse(language_code=language_code)


@router.get("/languages", response_model=list[SupportedLanguage])
async def get_supported_languages(
    current_user: TokenPayload = Depends(get_current_user),
    service: GoogleTranslationService = Depends(get_translation_service),
) -> list[SupportedLanguage]:
    languages = await service.get_supported_languages()
    return [
        SupportedLanguage(
            language_code=lang["language_code"],
            display_name=lang["display_name"],
        )
        for lang in languages
    ]
