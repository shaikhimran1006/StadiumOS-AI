from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.domain.value_objects.gps_sector import GpsSector


class FeedbackCategory(str, Enum):
    AI_ASSISTANT = "AI_ASSISTANT"
    FOOD_BEVERAGE = "FOOD_BEVERAGE"
    CLEANLINESS = "CLEANLINESS"
    SECURITY = "SECURITY"
    COMFORT = "COMFORT"
    WAYFINDING = "WAYFINDING"
    ACCESSIBILITY = "ACCESSIBILITY"
    WIFI_CONNECTIVITY = "WIFI_CONNECTIVITY"
    PARKING = "PARKING"
    TICKETING = "TICKETING"
    ENTERTAINMENT = "ENTERTAINMENT"
    STAFF_BEHAVIOR = "STAFF_BEHAVIOR"
    FACILITY_QUALITY = "FACILITY_QUALITY"
    WAIT_TIMES = "WAIT_TIMES"
    SAFETY = "SAFETY"
    GENERAL = "GENERAL"


class FeedbackSentiment(str, Enum):
    VERY_POSITIVE = "VERY_POSITIVE"
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    NEGATIVE = "NEGATIVE"
    VERY_NEGATIVE = "VERY_NEGATIVE"


class FeedbackSource(str, Enum):
    IN_APP = "IN_APP"
    AI_CHAT = "AI_CHAT"
    QR_CODE = "QR_CODE"
    KIOSK = "KIOSK"
    SMS_SURVEY = "SMS_SURVEY"
    STAFF_REPORT = "STAFF_REPORT"
    SOCIAL_MEDIA = "SOCIAL_MEDIA"


class Feedback(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    event_id: UUID | None = None
    stadium_id: UUID
    category: FeedbackCategory = Field(default=FeedbackCategory.GENERAL)
    source: FeedbackSource = Field(default=FeedbackSource.IN_APP)
    rating: int = Field(..., ge=1, le=5, description="1=worst, 5=best")
    title: str | None = Field(default=None, max_length=200)
    comment: str = Field(default="", max_length=5000)
    sentiment: FeedbackSentiment | None = None
    sector: GpsSector | None = None
    conversation_id: UUID | None = Field(default=None, description="Linked AI conversation")
    tags: list[str] = Field(default_factory=list)
    response: str | None = Field(default=None, max_length=2000, description="Official response")
    responded_by_user_id: UUID | None = None
    responded_at: datetime | None = None
    is_anonymous: bool = Field(default=False)
    is_public: bool = Field(default=False)
    upvotes: int = Field(default=0, ge=0)
    metadata: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def respond(self, response: str, responder_id: UUID) -> None:
        self.response = response[:2000]
        self.responded_by_user_id = responder_id
        self.responded_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def upvote(self) -> None:
        self.upvotes += 1
        self.updated_at = datetime.now(timezone.utc)

    def rating_label(self) -> str:
        labels = {1: "Very Poor", 2: "Poor", 3: "Average", 4: "Good", 5: "Excellent"}
        return labels.get(self.rating, "Unknown")

    def is_positive(self) -> bool:
        return self.rating >= 4

    def is_negative(self) -> bool:
        return self.rating <= 2
