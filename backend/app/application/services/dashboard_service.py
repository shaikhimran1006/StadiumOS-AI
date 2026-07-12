from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.domain.entities.alert import AlertStatus
from app.domain.entities.event import EventStatus
from app.domain.entities.incident import IncidentStatus
from app.domain.entities.stadium import SectorConfig
from app.domain.interfaces.repositories import (
    IAlertRepository,
    IConversationRepository,
    IEventRepository,
    IFeedbackRepository,
    IIncidentRepository,
    IStadiumRepository,
    IUserRepository,
)
from app.domain.value_objects.coordinates import LatLong
from app.domain.value_objects.gps_sector import GpsSector

logger = logging.getLogger(__name__)


class DashboardService:
    def __init__(
        self,
        stadium_repo: IStadiumRepository,
        user_repo: IUserRepository,
        alert_repo: IAlertRepository,
        incident_repo: IIncidentRepository,
        event_repo: IEventRepository,
        conversation_repo: IConversationRepository,
        feedback_repo: IFeedbackRepository,
    ) -> None:
        self._stadiums = stadium_repo
        self._users = user_repo
        self._alerts = alert_repo
        self._incidents = incident_repo
        self._events = event_repo
        self._conversations = conversation_repo
        self._feedback = feedback_repo

    async def get_overview_metrics(self, stadium_id: UUID) -> dict[str, Any]:
        stadium = await self._stadiums.get_by_id(stadium_id)
        if stadium is None:
            return self._empty_metrics()

        total_capacity = stadium.total_capacity
        current_occupancy = stadium.total_occupancy()
        occupancy_pct = stadium.overall_occupancy_percentage()

        active_incidents = await self._incidents.count_active_by_stadium(stadium_id)
        open_alerts = await self._alerts.count_active_by_stadium(stadium_id)
        active_conversations = await self._conversations.count_by_stadium(stadium_id)

        avg_response_time = await self._compute_avg_response_time(stadium_id)

        satisfaction_score = 0.0
        try:
            avg_rating = await self._feedback.average_rating_by_stadium(stadium_id)
            if avg_rating is not None:
                satisfaction_score = round(avg_rating, 2)
        except Exception:
            pass

        total_fans = await self._users.count_by_stadium(stadium_id)

        live_events = await self._events.list_live()
        stadium_events = [e for e in live_events if e.stadium_id == stadium_id]

        return {
            "total_fans": total_fans,
            "active_incidents": active_incidents,
            "open_alerts": open_alerts,
            "avg_response_time": avg_response_time,
            "satisfaction_score": satisfaction_score,
            "occupancy_percentage": occupancy_pct,
            "active_conversations": active_conversations,
            "total_events_today": len(stadium_events),
            "total_feedback_today": 0,
            "alerts_resolved_today": 0,
            "incidents_resolved_today": 0,
        }

    async def get_sector_status(self, stadium_id: UUID) -> list[dict[str, Any]]:
        stadium = await self._stadiums.get_by_id(stadium_id)
        if stadium is None:
            return []

        active_alerts = await self._alerts.list_by_stadium(stadium_id, limit=200)
        active_incidents_list = await self._incidents.list_by_stadium(stadium_id, limit=200)

        sector_alert_counts: dict[str, int] = {}
        sector_incident_counts: dict[str, int] = {}

        for alert in active_alerts:
            if alert.is_active() and alert.sector is not None:
                sector_key = alert.sector.value
                sector_alert_counts[sector_key] = sector_alert_counts.get(sector_key, 0) + 1

        for incident in active_incidents_list:
            if incident.is_active() and incident.sector is not None:
                sector_key = incident.sector.value
                sector_incident_counts[sector_key] = sector_incident_counts.get(sector_key, 0) + 1

        sectors: list[dict[str, Any]] = []
        for sc in stadium.sectors:
            sector_value = sc.sector.value
            sectors.append({
                "sector_id": sector_value,
                "name": f"Sector {sector_value}",
                "capacity": sc.capacity,
                "occupancy": sc.current_occupancy,
                "occupancy_percentage": sc.occupancy_percentage(),
                "alerts": sector_alert_counts.get(sector_value, 0),
                "incidents": sector_incident_counts.get(sector_value, 0),
                "is_open": sc.is_open,
                "tier": sc.tier,
            })

        return sectors

    async def get_stadium_overview(self, stadium_id: UUID) -> dict[str, Any]:
        stadium = await self._stadiums.get_by_id(stadium_id)
        if stadium is None:
            return {
                "stadium_id": str(stadium_id),
                "name": "Unknown",
                "total_capacity": 0,
                "current_occupancy": 0,
                "occupancy_percentage": 0.0,
                "sectors": [],
                "alerts_summary": {},
                "incidents_summary": {},
                "live_events": 0,
                "active_staff": 0,
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }

        sectors = await self.get_sector_status(stadium_id)

        alerts_summary: dict[str, int] = {}
        active_alerts = await self._alerts.list_by_stadium(stadium_id, limit=500)
        for alert in active_alerts:
            if alert.is_active():
                alert_type = alert.alert_type.value
                alerts_summary[alert_type] = alerts_summary.get(alert_type, 0) + 1

        incidents_summary: dict[str, int] = {}
        severity_breakdown = await self._incidents.count_by_severity(stadium_id)
        incidents_summary = severity_breakdown

        live_events = await self._events.list_live()
        live_count = len([e for e in live_events if e.stadium_id == stadium_id])

        return {
            "stadium_id": str(stadium.id),
            "name": stadium.name,
            "total_capacity": stadium.total_capacity,
            "current_occupancy": stadium.total_occupancy(),
            "occupancy_percentage": stadium.overall_occupancy_percentage(),
            "sectors": sectors,
            "alerts_summary": alerts_summary,
            "incidents_summary": incidents_summary,
            "live_events": live_count,
            "active_staff": 0,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

    async def get_time_series_data(
        self,
        stadium_id: UUID,
        metric_name: str,
        granularity: str = "hour",
        hours_back: int = 24,
    ) -> dict[str, Any]:
        timestamps: list[str] = []
        values: list[float] = []

        now = datetime.now(timezone.utc)

        if granularity == "minute":
            step_count = min(hours_back * 60, 1440)
            delta_minutes = 1
        elif granularity == "hour":
            step_count = min(hours_back, 168)
            delta_minutes = 60
        elif granularity == "day":
            step_count = min(hours_back // 24, 30)
            delta_minutes = 1440
        else:
            step_count = min(hours_back, 168)
            delta_minutes = 60

        from datetime import timedelta

        for i in range(step_count, 0, -1):
            ts = now - timedelta(minutes=delta_minutes * i)
            timestamps.append(ts.isoformat())

            if metric_name == "occupancy":
                values.append(0.0)
            elif metric_name == "alerts":
                values.append(0.0)
            elif metric_name == "incidents":
                values.append(0.0)
            elif metric_name == "conversations":
                values.append(0.0)
            elif metric_name == "satisfaction":
                values.append(0.0)
            else:
                values.append(0.0)

        return {
            "timestamps": timestamps,
            "values": values,
            "metric_name": metric_name,
            "unit": self._metric_unit(metric_name),
            "granularity": granularity,
        }

    async def get_live_dashboard(self, stadium_id: UUID) -> dict[str, Any]:
        metrics = await self.get_overview_metrics(stadium_id)
        sectors = await self.get_sector_status(stadium_id)
        overview = await self.get_stadium_overview(stadium_id)

        return {
            "metrics": metrics,
            "sectors": sectors,
            "overview": overview,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def _compute_avg_response_time(self, stadium_id: UUID) -> float:
        try:
            active_alerts = await self._alerts.list_by_stadium(stadium_id, limit=50)
            response_times: list[float] = []
            for alert in active_alerts:
                rt = alert.response_time_seconds()
                if rt is not None:
                    response_times.append(rt)
            if response_times:
                return round(sum(response_times) / len(response_times), 1)
        except Exception:
            logger.exception("Failed to compute avg response time")
        return 0.0

    def _empty_metrics(self) -> dict[str, Any]:
        return {
            "total_fans": 0,
            "active_incidents": 0,
            "open_alerts": 0,
            "avg_response_time": 0.0,
            "satisfaction_score": 0.0,
            "occupancy_percentage": 0.0,
            "active_conversations": 0,
            "total_events_today": 0,
            "total_feedback_today": 0,
            "alerts_resolved_today": 0,
            "incidents_resolved_today": 0,
        }

    @staticmethod
    def _metric_unit(metric_name: str) -> str:
        units = {
            "occupancy": "%",
            "alerts": "count",
            "incidents": "count",
            "conversations": "count",
            "satisfaction": "score",
            "response_time": "seconds",
        }
        return units.get(metric_name, "count")
