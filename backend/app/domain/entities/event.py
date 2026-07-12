from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class EventType(str, Enum):
    FOOTBALL_MATCH = "FOOTBALL_MATCH"
    CONCERT = "CONCERT"
    RUGBY = "RUGBY"
    ATHLETICS = "ATHLETICS"
    AMERICAN_FOOTBALL = "AMERICAN_FOOTBALL"
    BOXING = "BOXING"
    ESPORTS = "ESPORTS"
    CEREMONY = "CEREMONY"
    FESTIVAL = "FESTIVAL"
    OTHER = "OTHER"


class EventStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    DELAYED = "DELAYED"
    IN_PROGRESS = "IN_PROGRESS"
    HALFTIME = "HALFTIME"
    COMPLETED = "COMPLETED"
    POSTPONED = "POSTPONED"
    CANCELLED = "CANCELLED"


class Event(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=300)
    event_type: EventType = Field(default=EventType.FOOTBALL_MATCH)
    status: EventStatus = Field(default=EventStatus.SCHEDULED)
    stadium_id: UUID
    home_team: str | None = Field(default=None, max_length=100)
    away_team: str | None = Field(default=None, max_length=100)
    competition: str | None = Field(default=None, max_length=200, description="e.g. FIFA World Cup 2026")
    match_day: int | None = Field(default=None, ge=0)
    expected_attendance: int | None = Field(default=None, ge=0)
    actual_attendance: int | None = Field(default=None, ge=0)
    gates_open_at: datetime | None = None
    kickoff_at: datetime | None = None
    estimated_end_at: datetime | None = None
    actual_end_at: datetime | None = None
    broadcast_channels: list[str] = Field(default_factory=list)
    ticket_tiers: list[str] = Field(default_factory=list, description="e.g. VIP, STANDARD, GENERAL")
    allowed_sector_ids: list[UUID] = Field(default_factory=list)
    restrictions: dict[str, str] = Field(default_factory=dict, description="e.g. bag_size, age_limit")
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def start(self) -> None:
        self.status = EventStatus.IN_PROGRESS
        self.kickoff_at = self.kickoff_at or datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def pause_halftime(self) -> None:
        self.status = EventStatus.HALFTIME
        self.updated_at = datetime.now(timezone.utc)

    def resume(self) -> None:
        self.status = EventStatus.IN_PROGRESS
        self.updated_at = datetime.now(timezone.utc)

    def complete(self) -> None:
        self.status = EventStatus.COMPLETED
        self.actual_end_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def cancel(self) -> None:
        self.status = EventStatus.CANCELLED
        self.updated_at = datetime.now(timezone.utc)

    def postpone(self) -> None:
        self.status = EventStatus.POSTPONED
        self.updated_at = datetime.now(timezone.utc)

    def is_live(self) -> bool:
        return self.status in {EventStatus.IN_PROGRESS, EventStatus.HALFTIME}

    def attendance_percentage(self) -> float | None:
        if self.expected_attendance and self.actual_attendance:
            return round(self.actual_attendance / self.expected_attendance * 100, 1)
        return None

    def duration_minutes(self) -> float | None:
        if self.kickoff_at and self.actual_end_at:
            return round((self.actual_end_at - self.kickoff_at).total_seconds() / 60, 1)
        return None
