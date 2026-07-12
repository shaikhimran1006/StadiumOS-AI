from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.value_objects.gps_sector import GpsSector


class FeedbackCreateRequest(BaseModel):
    category: str = Field(default="GENERAL", description="FeedbackCategory enum value")
    rating: int = Field(..., ge=1, le=5)
    comment: str = Field(default="", max_length=5000)
    event_id: UUID | None = None
    stadium_id: UUID
    sector: GpsSector | None = None
    anonymous: bool = False
    conversation_id: UUID | None = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)


class FeedbackResponse(BaseModel):
    id: UUID
    category: str
    rating: int
    comment: str
    sentiment: str | None = None
    status: str = "submitted"
    event_id: UUID | None = None
    sector: GpsSector | None = None
    is_anonymous: bool = False
    tags: list[str] = Field(default_factory=list)
    upvotes: int = 0
    created_at: datetime
    updated_at: datetime


class FeedbackAnalytics(BaseModel):
    total_count: int = 0
    average_rating: float = 0.0
    category_breakdown: dict[str, int] = Field(default_factory=dict)
    sentiment_distribution: dict[str, int] = Field(default_factory=dict)
    rating_distribution: dict[str, int] = Field(
        default_factory=dict, description="Key is rating 1-5, value is count"
    )
    top_negative_categories: list[dict[str, Any]] = Field(default_factory=list)
    response_rate: float = Field(default=0.0, ge=0.0, le=1.0)
