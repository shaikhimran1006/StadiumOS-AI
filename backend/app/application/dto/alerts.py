from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.value_objects.coordinates import LatLong
from app.domain.value_objects.gps_sector import GpsSector
from app.domain.value_objects.priority import Priority


class AlertCreateRequest(BaseModel):
    alert_type: str = Field(..., description="AlertType enum value e.g. SECURITY, MEDICAL")
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    priority: Priority = Field(default=Priority.MEDIUM)
    sector: GpsSector | None = None
    location: LatLong | None = None
    stadium_id: UUID
    event_id: UUID | None = None
    affected_sectors: list[GpsSector] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)
    triggered_by_user_id: UUID | None = None
    triggered_by_ai: bool = False
    ai_confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class AlertResponse(BaseModel):
    id: UUID
    alert_type: str
    title: str
    description: str
    priority: int
    status: str
    sector: GpsSector | None = None
    location: LatLong | None = None
    stadium_id: UUID
    event_id: UUID | None = None
    triggered_by_user_id: UUID | None = None
    assigned_to_user_id: UUID | None = None
    triggered_by_ai: bool = False
    ai_confidence: float | None = None
    escalation_level: int = 0
    notifications_sent: bool = False
    public_announcement: bool = False
    metadata: dict[str, str] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None = None
    acknowledged_at: datetime | None = None


class AlertListResponse(BaseModel):
    alerts: list[AlertResponse] = Field(default_factory=list)
    total_count: int = 0
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
