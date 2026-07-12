from __future__ import annotations

import base64
import logging
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.v1.dependencies.getters import get_vision_service
from app.core.security.auth import TokenPayload, get_current_user
from app.services.vision.vision_service import GoogleVisionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vision", tags=["Vision"])


class AnalyzeRequest(BaseModel):
    image_base64: str = Field(..., description="Base64-encoded image data")
    features: list[str] | None = Field(
        default=None,
        description="Specific features: LABEL_DETECTION, OBJECT_LOCALIZATION, TEXT_DETECTION, SAFE_SEARCH_DETECTION, FACE_DETECTION, LANDMARK_DETECTION",
    )


class AnalyzeResponse(BaseModel):
    labels: list[dict[str, Any]] = Field(default_factory=list)
    objects: list[dict[str, Any]] = Field(default_factory=list)
    text_detected: str | None = None
    safety_labels: list[dict[str, Any]] = Field(default_factory=list)


class OCRRequest(BaseModel):
    image_base64: str = Field(..., description="Base64-encoded image data")


class OCRResponse(BaseModel):
    extracted_text: str
    text_length: int = 0


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_image(
    request: AnalyzeRequest,
    current_user: TokenPayload = Depends(get_current_user),
    service: GoogleVisionService = Depends(get_vision_service),
) -> AnalyzeResponse:
    image_data = base64.b64decode(request.image_base64)
    analysis = await service.analyze_image(
        image_data=image_data,
        features=request.features,
    )
    return AnalyzeResponse(
        labels=analysis.labels,
        objects=analysis.objects,
        text_detected=analysis.text_detected,
        safety_labels=analysis.safety_labels,
    )


@router.post("/ocr", response_model=OCRResponse)
async def ocr_image(
    request: OCRRequest,
    current_user: TokenPayload = Depends(get_current_user),
    service: GoogleVisionService = Depends(get_vision_service),
) -> OCRResponse:
    image_data = base64.b64decode(request.image_base64)
    text = await service.ocr(image_data=image_data)
    return OCRResponse(
        extracted_text=text,
        text_length=len(text),
    )
