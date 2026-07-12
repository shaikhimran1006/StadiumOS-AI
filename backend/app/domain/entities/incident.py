from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.domain.value_objects.coordinates import LatLong
from app.domain.value_objects.gps_sector import GpsSector
from app.domain.value_objects.priority import Priority


class IncidentCategory(str, Enum):
    SECURITY_THREAT = "SECURITY_THREAT"
    MEDICAL_EMERGENCY = "MEDICAL_EMERGENCY"
    CROWD_DISORDER = "CROWD_DISORDER"
    THEFT = "THEFT"
    ASSAULT = "ASSAULT"
    FIRE_HAZARD = "FIRE_HAZARD"
    STRUCTURAL_DAMAGE = "STRUCTURAL_DAMAGE"
    FOOD_SAFETY = "FOOD_SAFETY"
    INTOXICATION = "INTOXICATION"
    LOST_CHILD = "LOST_CHILD"
    LOST_ADULT = "LOST_ADULT"
    DISABILITY_ASSISTANCE = "DISABILITY_ASSISTANCE"
    NOISE_COMPLAINT = "NOISE_COMPLAINT"
    VIP_INCIDENT = "VIP_INCIDENT"
    MEDIA_INCIDENT = "MEDIA_INCIDENT"
    WEATHER_RELATED = "WEATHER_RELATED"
    TECHNICAL_FAILURE = "TECHNICAL_FAILURE"
    OTHER = "OTHER"


class IncidentStatus(str, Enum):
    REPORTED = "REPORTED"
    TRIAGED = "TRIAGED"
    DISPATCHED = "DISPATCHED"
    ON_SCENE = "ON_SCENE"
    UNDER_CONTROL = "UNDER_CONTROL"
    RESOLVED = "RESOLVED"
    ESCALATED = "ESCALATED"
    CLOSED = "CLOSED"


class IncidentSeverity(str, Enum):
    LIFE_THREATENING = "LIFE_THREATENING"
    SERIOUS = "SERIOUS"
    MODERATE = "MODERATE"
    MINOR = "MINOR"
    ADVISORY = "ADVISORY"


class Responder(BaseModel):
    user_id: UUID
    role: str = Field(..., description="e.g. security, medical, fire")
    dispatched_at: datetime | None = None
    arrived_at: datetime | None = None


class Incident(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    category: IncidentCategory
    severity: IncidentSeverity = Field(default=IncidentSeverity.MODERATE)
    priority: Priority = Field(default=Priority.MEDIUM)
    status: IncidentStatus = Field(default=IncidentStatus.REPORTED)
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=5000)
    stadium_id: UUID
    event_id: UUID | None = None
    sector: GpsSector | None = None
    location: LatLong | None = None
    reported_by_user_id: UUID | None = None
    reported_by_ai: bool = Field(default=False)
    ai_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    related_alert_id: UUID | None = None
    responders: list[Responder] = Field(default_factory=list)
    people_involved: int = Field(default=1, ge=0)
    injuries_reported: int = Field(default=0, ge=0)
    medical_transport_called: bool = Field(default=False)
    law_enforcement_called: bool = Field(default=False)
    public_visibility: bool = Field(default=False, description="Whether visible on public boards")
    internal_notes: list[str] = Field(default_factory=list)
    resolution_notes: str | None = Field(default=None, max_length=2000)
    evidence_urls: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)
    resolved_at: datetime | None = None
    closed_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def assign_responder(self, user_id: UUID, role: str) -> None:
        self.responders.append(
            Responder(user_id=user_id, role=role, dispatched_at=datetime.now(timezone.utc))
        )
        self.status = IncidentStatus.DISPATCHED
        self.updated_at = datetime.now(timezone.utc)

    def mark_on_scene(self, user_id: UUID) -> None:
        for r in self.responders:
            if r.user_id == user_id and r.arrived_at is None:
                r.arrived_at = datetime.now(timezone.utc)
                break
        self.status = IncidentStatus.ON_SCENE
        self.updated_at = datetime.now(timezone.utc)

    def resolve(self, notes: str | None = None) -> None:
        self.status = IncidentStatus.RESOLVED
        self.resolved_at = datetime.now(timezone.utc)
        self.resolution_notes = notes
        self.updated_at = datetime.now(timezone.utc)

    def close(self) -> None:
        self.status = IncidentStatus.CLOSED
        self.closed_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def escalate(self) -> None:
        self.status = IncidentStatus.ESCALATED
        self.updated_at = datetime.now(timezone.utc)

    def add_internal_note(self, note: str) -> None:
        timestamp = datetime.now(timezone.utc).isoformat()
        self.internal_notes.append(f"[{timestamp}] {note}")
        self.updated_at = datetime.now(timezone.utc)

    def is_active(self) -> bool:
        return self.status not in {IncidentStatus.RESOLVED, IncidentStatus.CLOSED}

    def response_time_seconds(self) -> float | None:
        if not self.responders:
            return None
        first_dispatched = min(
            (r.dispatched_at for r in self.responders if r.dispatched_at), default=None
        )
        if first_dispatched is None:
            return None
        return (first_dispatched - self.created_at).total_seconds()
