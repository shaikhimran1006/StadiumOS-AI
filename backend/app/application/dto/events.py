from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class EventCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=300)
    event_type: str = Field(default="FOOTBALL_MATCH", description="EventType enum value")
    start_time: datetime | None = Field(default=None, description="Alias for kickoff_at")
    end_time: datetime | None = Field(default=None, description="Alias for estimated_end_at")
    stadium_id: UUID
    description: str | None = Field(default=None, max_length=2000)
    home_team: str | None = Field(default=None, max_length=100)
    away_team: str | None = Field(default=None, max_length=100)
    competition: str | None = Field(default=None, max_length=200)
    expected_attendance: int | None = Field(default=None, ge=0)
    gates_open_at: datetime | None = None
    broadcast_channels: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)


class EventResponse(BaseModel):
    id: UUID
    name: str
    event_type: str
    status: str
    start_time: datetime | None = None
    end_time: datetime | None = None
    stadium_id: UUID
    home_team: str | None = None
    away_team: str | None = None
    competition: str | None = None
    expected_attendance: int | None = None
    actual_attendance: int | None = None
    attendance_percentage: float | None = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class EventListResponse(BaseModel):
    events: list[EventResponse] = Field(default_factory=list)
    total_count: int = 0
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
