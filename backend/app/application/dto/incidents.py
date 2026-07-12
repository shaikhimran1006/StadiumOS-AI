from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.value_objects.coordinates import LatLong
from app.domain.value_objects.gps_sector import GpsSector
from app.domain.value_objects.priority import Priority


class IncidentCreateRequest(BaseModel):
    category: str = Field(..., description="IncidentCategory enum value e.g. MEDICAL_EMERGENCY")
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=5000)
    severity: str = Field(default="MODERATE", description="IncidentSeverity enum value")
    sector: GpsSector | None = None
    location: LatLong | None = None
    stadium_id: UUID
    event_id: UUID | None = None
    reported_by: UUID | None = Field(default=None, description="User ID of reporter")
    reported_by_ai: bool = False
    ai_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    people_involved: int = Field(default=1, ge=0)
    injuries_reported: int = Field(default=0, ge=0)
    public_visibility: bool = False
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)


class ResponderDTO(BaseModel):
    user_id: UUID
    role: str
    dispatched_at: datetime | None = None
    arrived_at: datetime | None = None


class IncidentResponse(BaseModel):
    id: UUID
    category: str
    title: str
    description: str
    severity: str
    priority: int
    status: str
    sector: GpsSector | None = None
    location: LatLong | None = None
    stadium_id: UUID
    event_id: UUID | None = None
    reported_by_user_id: UUID | None = None
    reported_by_ai: bool = False
    ai_confidence: float | None = None
    responders: list[ResponderDTO] = Field(default_factory=list)
    people_involved: int = 1
    injuries_reported: int = 0
    medical_transport_called: bool = False
    law_enforcement_called: bool = False
    public_visibility: bool = False
    resolution_notes: str | None = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None = None
    closed_at: datetime | None = None


class IncidentListResponse(BaseModel):
    incidents: list[IncidentResponse] = Field(default_factory=list)
    total_count: int = 0
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
