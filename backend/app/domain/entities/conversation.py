from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.domain.value_objects.language import Language


class ConversationStatus(str, Enum):
    ACTIVE = "ACTIVE"
    WAITING = "WAITING"
    CLOSED = "CLOSED"
    TRANSFERRED = "TRANSFERRED"


class ConversationChannel(str, Enum):
    IN_APP = "IN_APP"
    WEB = "WEB"
    WHATSAPP = "WHATSAPP"
    SMS = "SMS"
    VOICE = "VOICE"
    KIOSK = "KIOSK"


class ConversationContext(BaseModel):
    stadium_id: UUID | None = None
    event_id: UUID | None = None
    sector: str | None = None
    entry_point: str | None = None
    initial_intent: str | None = None
    referrer: str | None = None


class Conversation(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    channel: ConversationChannel = Field(default=ConversationChannel.IN_APP)
    status: ConversationStatus = Field(default=ConversationStatus.ACTIVE)
    language: Language = Field(default=Language.ENGLISH)
    context: ConversationContext = Field(default_factory=ConversationContext)
    assigned_agent_id: UUID | None = Field(default=None, description="Human agent if transferred")
    ai_agent_version: str = Field(default="v1")
    message_count: int = Field(default=0)
    satisfaction_score: int | None = Field(default=None, ge=1, le=5)
    summary: str | None = Field(default=None, max_length=2000)
    tags: list[str] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: datetime | None = None
    last_message_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def is_active(self) -> bool:
        return self.status == ConversationStatus.ACTIVE

    def close(self, summary: str | None = None) -> None:
        self.status = ConversationStatus.CLOSED
        self.ended_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        if summary:
            self.summary = summary[:2000]

    def transfer_to_agent(self, agent_id: UUID) -> None:
        self.status = ConversationStatus.TRANSFERRED
        self.assigned_agent_id = agent_id
        self.updated_at = datetime.now(timezone.utc)

    def increment_message_count(self) -> None:
        self.message_count += 1
        self.last_message_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def set_satisfaction(self, score: int) -> None:
        if not 1 <= score <= 5:
            raise ValueError("Satisfaction score must be between 1 and 5")
        self.satisfaction_score = score
        self.updated_at = datetime.now(timezone.utc)

    def duration_seconds(self) -> float | None:
        if self.ended_at is None:
            return None
        return (self.ended_at - self.started_at).total_seconds()
