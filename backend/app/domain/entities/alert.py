from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.domain.value_objects.coordinates import LatLong
from app.domain.value_objects.gps_sector import GpsSector
from app.domain.value_objects.priority import Priority


class AlertType(str, Enum):
    SECURITY = "SECURITY"
    MEDICAL = "MEDICAL"
    FIRE = "FIRE"
    EVACUATION = "EVACUATION"
    CROWD_SURGE = "CROWD_SURGE"
    WEATHER = "WEATHER"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    LOST_PERSON = "LOST_PERSON"
    SUSPICIOUS_PACKAGE = "SUSPICIOUS_PACKAGE"
    POWER_OUTAGE = "POWER_OUTAGE"
    WATER_LEAK = "WATER_LEAK"
    GENERIC = "GENERIC"


class AlertStatus(str, Enum):
    TRIGGERED = "TRIGGERED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    ESCALATED = "ESCALATED"
    CANCELLED = "CANCELLED"


class Alert(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    alert_type: AlertType
    priority: Priority = Field(default=Priority.MEDIUM)
    status: AlertStatus = Field(default=AlertStatus.TRIGGERED)
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    stadium_id: UUID
    event_id: UUID | None = None
    sector: GpsSector | None = None
    location: LatLong | None = None
    triggered_by_user_id: UUID | None = None
    assigned_to_user_id: UUID | None = None
    triggered_by_ai: bool = Field(default=False)
    ai_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    affected_sectors: list[GpsSector] = Field(default_factory=list)
    affected_capacity: int | None = Field(default=None, ge=0)
    related_incident_id: UUID | None = None
    escalation_level: int = Field(default=0, ge=0, le=5)
    auto_resolve_after_seconds: int | None = Field(default=None, ge=0)
    notifications_sent: bool = Field(default=False)
    public_announcement: bool = Field(default=False)
    metadata: dict[str, str] = Field(default_factory=dict)
    resolved_at: datetime | None = None
    acknowledged_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def acknowledge(self, user_id: UUID) -> None:
        self.status = AlertStatus.ACKNOWLEDGED
        self.assigned_to_user_id = user_id
        self.acknowledged_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def start_resolution(self) -> None:
        self.status = AlertStatus.IN_PROGRESS
        self.updated_at = datetime.now(timezone.utc)

    def resolve(self) -> None:
        self.status = AlertStatus.RESOLVED
        self.resolved_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def escalate(self) -> None:
        if self.escalation_level >= 5:
            raise ValueError("Alert already at maximum escalation level")
        self.escalation_level += 1
        self.status = AlertStatus.ESCALATED
        self.priority = Priority(min(self.priority.value, Priority.CRITICAL.value))
        self.updated_at = datetime.now(timezone.utc)

    def cancel(self) -> None:
        self.status = AlertStatus.CANCELLED
        self.updated_at = datetime.now(timezone.utc)

    def is_active(self) -> bool:
        return self.status in {
            AlertStatus.TRIGGERED,
            AlertStatus.ACKNOWLEDGED,
            AlertStatus.IN_PROGRESS,
            AlertStatus.ESCALATED,
        }

    def response_time_seconds(self) -> float | None:
        if self.acknowledged_at is None:
            return None
        return (self.acknowledged_at - self.created_at).total_seconds()

    def resolution_time_seconds(self) -> float | None:
        if self.resolved_at is None:
            return None
        return (self.resolved_at - self.created_at).total_seconds()
