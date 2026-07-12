from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    conversation_id: UUID | None = Field(
        default=None, description="Existing conversation ID, null for new conversation"
    )
    language: str = Field(default="en", description="BCP-47 language tag")
    context: dict[str, Any] | None = Field(
        default=None,
        description="Additional context such as stadium_id, event_id, sector, location",
    )
    message_type: str = Field(default="TEXT", description="TEXT, IMAGE, AUDIO, LOCATION")


class MessageDTO(BaseModel):
    id: UUID
    sender_type: str
    content: str
    message_type: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class ChatResponse(BaseModel):
    response_text: str
    conversation_id: UUID
    message_id: UUID
    agent_name: str
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    sources: list[str] = Field(default_factory=list)
    actions: list[dict[str, Any]] = Field(default_factory=list)


class ConversationHistory(BaseModel):
    conversation_id: UUID
    messages: list[MessageDTO] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    status: str = "ACTIVE"
    language: str = "en"
    message_count: int = 0
