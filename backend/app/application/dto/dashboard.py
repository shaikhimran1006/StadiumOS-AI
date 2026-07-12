from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class DashboardMetrics(BaseModel):
    total_fans: int = 0
    active_incidents: int = 0
    open_alerts: int = 0
    avg_response_time: float = Field(default=0.0, description="Average response time in seconds")
    satisfaction_score: float = Field(default=0.0, ge=0.0, le=5.0)
    occupancy_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    active_conversations: int = 0
    total_events_today: int = 0
    total_feedback_today: int = 0
    alerts_resolved_today: int = 0
    incidents_resolved_today: int = 0


class SectorStatus(BaseModel):
    sector_id: str
    name: str
    capacity: int = 0
    occupancy: int = 0
    occupancy_percentage: float = 0.0
    alerts: int = 0
    incidents: int = 0
    is_open: bool = True
    tier: str = "standard"


class StadiumOverview(BaseModel):
    stadium_id: UUID
    name: str
    total_capacity: int = 0
    current_occupancy: int = 0
    occupancy_percentage: float = 0.0
    sectors: list[SectorStatus] = Field(default_factory=list)
    alerts_summary: dict[str, int] = Field(
        default_factory=dict, description="AlertType -> count"
    )
    incidents_summary: dict[str, int] = Field(
        default_factory=dict, description="IncidentSeverity -> count"
    )
    live_events: int = 0
    active_staff: int = 0
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class TimeSeriesData(BaseModel):
    timestamps: list[str] = Field(default_factory=list, description="ISO format timestamps")
    values: list[float] = Field(default_factory=list)
    metric_name: str = ""
    unit: str = ""
    granularity: str = Field(default="hour", description="minute, hour, day, week")
