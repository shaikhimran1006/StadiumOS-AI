from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class SenderType(str, Enum):
    USER = "USER"
    AI = "AI"
    AGENT = "AGENT"
    SYSTEM = "SYSTEM"


class MessageType(str, Enum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    AUDIO = "AUDIO"
    VIDEO = "VIDEO"
    LOCATION = "LOCATION"
    RICH_CARD = "RICH_CARD"
    QUICK_REPLY = "QUICK_REPLY"
    SYSTEM_EVENT = "SYSTEM_EVENT"


class MessageMetadata(BaseModel):
    tokens_used: int | None = Field(default=None, ge=0)
    model_name: str | None = None
    latency_ms: int | None = Field(default=None, ge=0)
    confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)
    intent_detected: str | None = None
    entities_extracted: list[dict[str, str]] = Field(default_factory=list)
    language_detected: str | None = None
    translation_used: bool = Field(default=False)
    vision_analyzed: bool = Field(default=False)
    rag_sources: list[str] = Field(default_factory=list)
    safety_flagged: bool = Field(default=False)
    feedback_reaction: str | None = Field(default=None, description="thumbs_up, thumbs_down, etc.")


class Message(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    conversation_id: UUID
    sender_type: SenderType
    sender_id: UUID | None = Field(default=None, description="User/agent UUID, null for AI/system")
    content: str = Field(..., min_length=1, max_length=10000)
    message_type: MessageType = Field(default=MessageType.TEXT)
    metadata: MessageMetadata = Field(default_factory=MessageMetadata)
    parent_message_id: UUID | None = Field(default=None, description="For threaded replies")
    is_visible: bool = Field(default=True, description="Soft delete flag")
    translation_of: UUID | None = Field(default=None, description="Original message if translated")
    language: str | None = Field(default=None, description="BCP-47 language tag")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def is_from_user(self) -> bool:
        return self.sender_type == SenderType.USER

    def is_from_ai(self) -> bool:
        return self.sender_type == SenderType.AI

    def is_safety_flagged(self) -> bool:
        return self.metadata.safety_flagged

    def soft_delete(self) -> None:
        self.is_visible = False
        self.updated_at = datetime.now(timezone.utc)

    def set_feedback(self, reaction: str) -> None:
        self.metadata.feedback_reaction = reaction
        self.updated_at = datetime.now(timezone.utc)
