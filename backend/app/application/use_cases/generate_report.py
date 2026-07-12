from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.domain.entities.event import Event
from app.domain.entities.feedback import Feedback
from app.domain.entities.incident import Incident
from app.domain.entities.alert import Alert
from app.domain.interfaces.ai_services import IGenerativeAIService
from app.domain.interfaces.repositories import (
    IAlertRepository,
    IEventRepository,
    IFeedbackRepository,
    IIncidentRepository,
    IStadiumRepository,
)

logger = logging.getLogger(__name__)

REPORT_SYSTEM_PROMPT = """You are StadiumOS AI Report Generator. Generate comprehensive, 
data-driven stadium operations reports based on the provided data. 

Format your response as structured JSON with the following keys:
- "title": Report title
- "summary": Executive summary (2-3 paragraphs)
- "sections": List of report sections, each with "heading" and "content"
- "key_findings": List of key findings
- "recommendations": List of actionable recommendations
- "risk_assessment": Overall risk assessment text
- "generated_at": ISO timestamp

Be specific, cite actual numbers from the data, and provide actionable insights."""


class GenerateReportUseCase:
    def __init__(
        self,
        stadium_repo: IStadiumRepository,
        event_repo: IEventRepository,
        incident_repo: IIncidentRepository,
        alert_repo: IAlertRepository,
        feedback_repo: IFeedbackRepository,
        generative_ai: IGenerativeAIService,
    ) -> None:
        self._stadiums = stadium_repo
        self._events = event_repo
        self._incidents = incident_repo
        self._alerts = alert_repo
        self._feedback = feedback_repo
        self._ai = generative_ai

    async def execute(
        self,
        stadium_id: UUID,
        report_type: str = "operations",
        event_id: UUID | None = None,
        date_range_days: int = 7,
    ) -> dict[str, Any]:
        data = await self._gather_report_data(
            stadium_id=stadium_id,
            event_id=event_id,
            date_range_days=date_range_days,
        )

        prompt = self._build_report_prompt(report_type, data, date_range_days)

        ai_response = await self._ai.generate_response(
            prompt=prompt,
            system_instruction=REPORT_SYSTEM_PROMPT,
            temperature=0.4,
            max_tokens=4096,
        )

        report = self._parse_report_response(ai_response.content, data)

        return report

    async def execute_quick_summary(
        self,
        stadium_id: UUID,
    ) -> dict[str, Any]:
        metrics = await self._gather_quick_metrics(stadium_id)

        prompt = (
            f"Generate a brief real-time operational summary for stadium {metrics['stadium_name']}.\n"
            f"Current occupancy: {metrics['occupancy_percentage']}%\n"
            f"Active incidents: {metrics['active_incidents']}\n"
            f"Open alerts: {metrics['open_alerts']}\n"
            f"Live events: {metrics['live_events']}\n"
            f"Active conversations: {metrics['active_conversations']}\n"
            f"Provide a 3-5 sentence executive summary with any immediate concerns."
        )

        ai_response = await self._ai.generate_response(
            prompt=prompt,
            system_instruction="You are a stadium operations assistant. Provide concise operational summaries.",
            temperature=0.3,
            max_tokens=512,
        )

        return {
            "summary": ai_response.content,
            "metrics": metrics,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "report_type": "quick_summary",
        }

    async def execute_event_report(
        self,
        event_id: UUID,
    ) -> dict[str, Any]:
        event = await self._events.get_by_id(event_id)
        if event is None:
            return {"error": "Event not found"}

        incidents = await self._incidents.list_by_event(event_id, limit=500)
        feedback = await self._feedback.list_by_event(event_id, limit=500)

        feedback_ratings = [f.rating for f in feedback]
        avg_rating = round(sum(feedback_ratings) / len(feedback_ratings), 2) if feedback_ratings else 0.0

        incident_categories: dict[str, int] = {}
        for inc in incidents:
            cat = inc.category.value
            incident_categories[cat] = incident_categories.get(cat, 0) + 1

        prompt = (
            f"Generate a post-event report for: {event.name}\n"
            f"Event type: {event.event_type.value}\n"
            f"Status: {event.status.value}\n"
            f"Expected attendance: {event.expected_attendance}\n"
            f"Actual attendance: {event.actual_attendance}\n"
            f"Total incidents: {len(incidents)}\n"
            f"Incident breakdown: {json.dumps(incident_categories)}\n"
            f"Total feedback: {len(feedback)}\n"
            f"Average rating: {avg_rating}/5\n"
            f"Duration: {event.duration_minutes()} minutes\n\n"
            f"Provide a comprehensive post-event analysis with:\n"
            f"1. Event overview\n"
            f"2. Safety and incident analysis\n"
            f"3. Fan satisfaction analysis\n"
            f"4. Operational highlights\n"
            f"5. Recommendations for future events"
        )

        ai_response = await self._ai.generate_response(
            prompt=prompt,
            system_instruction=REPORT_SYSTEM_PROMPT,
            temperature=0.4,
            max_tokens=4096,
        )

        report = self._parse_report_response(ai_response.content, {
            "event": {
                "name": event.name,
                "type": event.event_type.value,
                "status": event.status.value,
            },
            "incidents_count": len(incidents),
            "feedback_count": len(feedback),
            "avg_rating": avg_rating,
        })

        report["event_id"] = str(event_id)
        report["report_type"] = "event_report"

        return report

    async def _gather_report_data(
        self,
        stadium_id: UUID,
        event_id: UUID | None,
        date_range_days: int,
    ) -> dict[str, Any]:
        stadium = await self._stadiums.get_by_id(stadium_id)

        if event_id is not None:
            incidents = await self._incidents.list_by_event(event_id, limit=500)
            alerts_list = []
            feedback_list = await self._feedback.list_by_event(event_id, limit=500)
        else:
            incidents = await self._incidents.list_by_stadium(stadium_id, limit=500)
            alerts_list = await self._alerts.list_by_stadium(stadium_id, limit=500)
            feedback_list = await self._feedback.list_by_stadium(stadium_id, limit=500)

        active_incidents = [i for i in incidents if i.is_active()]
        resolved_incidents = [i for i in incidents if not i.is_active()]
        active_alerts = [a for a in alerts_list if a.is_active()]

        severity_breakdown: dict[str, int] = {}
        for inc in incidents:
            sev = inc.severity.value
            severity_breakdown[sev] = severity_breakdown.get(sev, 0) + 1

        category_breakdown: dict[str, int] = {}
        for inc in incidents:
            cat = inc.category.value
            category_breakdown[cat] = category_breakdown.get(cat, 0) + 1

        alert_type_breakdown: dict[str, int] = {}
        for alert in alerts_list:
            at = alert.alert_type.value
            alert_type_breakdown[at] = alert_type_breakdown.get(at, 0) + 1

        ratings = [f.rating for f in feedback_list]
        avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else 0.0

        sentiment_breakdown: dict[str, int] = {}
        for f in feedback_list:
            if f.sentiment:
                s = f.sentiment.value
                sentiment_breakdown[s] = sentiment_breakdown.get(s, 0) + 1

        response_times: list[float] = []
        for alert in alerts_list:
            rt = alert.response_time_seconds()
            if rt is not None:
                response_times.append(rt)
        avg_response_time = round(sum(response_times) / len(response_times), 1) if response_times else 0.0

        resolution_times: list[float] = []
        for alert in alerts_list:
            rtime = alert.resolution_time_seconds()
            if rtime is not None:
                resolution_times.append(rtime)
        avg_resolution_time = round(sum(resolution_times) / len(resolution_times), 1) if resolution_times else 0.0

        return {
            "stadium": {
                "name": stadium.name if stadium else "Unknown",
                "capacity": stadium.total_capacity if stadium else 0,
                "occupancy": stadium.total_occupancy() if stadium else 0,
                "occupancy_pct": stadium.overall_occupancy_percentage() if stadium else 0,
                "total_sectors": len(stadium.sectors) if stadium else 0,
            },
            "incidents": {
                "total": len(incidents),
                "active": len(active_incidents),
                "resolved": len(resolved_incidents),
                "severity_breakdown": severity_breakdown,
                "category_breakdown": category_breakdown,
            },
            "alerts": {
                "total": len(alerts_list),
                "active": len(active_alerts),
                "type_breakdown": alert_type_breakdown,
                "avg_response_time_seconds": avg_response_time,
                "avg_resolution_time_seconds": avg_resolution_time,
            },
            "feedback": {
                "total": len(feedback_list),
                "average_rating": avg_rating,
                "sentiment_breakdown": sentiment_breakdown,
            },
            "date_range_days": date_range_days,
        }

    async def _gather_quick_metrics(self, stadium_id: UUID) -> dict[str, Any]:
        stadium = await self._stadiums.get_by_id(stadium_id)
        active_incidents = await self._incidents.count_active_by_stadium(stadium_id)
        active_alerts = await self._alerts.count_active_by_stadium(stadium_id)
        live_events = await self._events.list_live()
        active_conversations = await self._conversations_count(stadium_id)

        return {
            "stadium_name": stadium.name if stadium else "Unknown",
            "occupancy_percentage": stadium.overall_occupancy_percentage() if stadium else 0.0,
            "active_incidents": active_incidents,
            "open_alerts": active_alerts,
            "live_events": len([e for e in live_events if e.stadium_id == stadium_id]),
            "active_conversations": active_conversations,
        }

    async def _conversations_count(self, stadium_id: UUID) -> int:
        return 0

    def _build_report_prompt(
        self, report_type: str, data: dict[str, Any], date_range_days: int
    ) -> str:
        report_type_labels = {
            "operations": "Operations Summary",
            "safety": "Safety & Security Report",
            "fan_experience": "Fan Experience Report",
            "full": "Comprehensive Operations Report",
        }
        label = report_type_labels.get(report_type, "Operations Report")

        stadium = data.get("stadium", {})
        incidents = data.get("incidents", {})
        alerts = data.get("alerts", {})
        feedback = data.get("feedback", {})

        return (
            f"Generate a {label} for the following stadium over the last {date_range_days} days.\n\n"
            f"STADIUM INFORMATION:\n"
            f"- Name: {stadium.get('name', 'Unknown')}\n"
            f"- Total Capacity: {stadium.get('capacity', 0)}\n"
            f"- Current Occupancy: {stadium.get('occupancy', 0)} ({stadium.get('occupancy_pct', 0)}%)\n"
            f"- Total Sectors: {stadium.get('total_sectors', 0)}\n\n"
            f"INCIDENT DATA:\n"
            f"- Total Incidents: {incidents.get('total', 0)}\n"
            f"- Active: {incidents.get('active', 0)}\n"
            f"- Resolved: {incidents.get('resolved', 0)}\n"
            f"- Severity Breakdown: {json.dumps(incidents.get('severity_breakdown', {}))}\n"
            f"- Category Breakdown: {json.dumps(incidents.get('category_breakdown', {}))}\n\n"
            f"ALERT DATA:\n"
            f"- Total Alerts: {alerts.get('total', 0)}\n"
            f"- Active: {alerts.get('active', 0)}\n"
            f"- Type Breakdown: {json.dumps(alerts.get('type_breakdown', {}))}\n"
            f"- Avg Response Time: {alerts.get('avg_response_time_seconds', 0)}s\n"
            f"- Avg Resolution Time: {alerts.get('avg_resolution_time_seconds', 0)}s\n\n"
            f"FAN FEEDBACK:\n"
            f"- Total Feedback: {feedback.get('total', 0)}\n"
            f"- Average Rating: {feedback.get('average_rating', 0)}/5\n"
            f"- Sentiment: {json.dumps(feedback.get('sentiment_breakdown', {}))}\n"
        )

    def _parse_report_response(
        self, response_text: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        try:
            report = json.loads(response_text)
            report["generated_at"] = datetime.now(timezone.utc).isoformat()
            report["raw_data_summary"] = data
            return report
        except json.JSONDecodeError:
            return {
                "title": "Stadium Operations Report",
                "summary": response_text,
                "sections": [],
                "key_findings": [],
                "recommendations": [],
                "risk_assessment": "Unable to parse structured report.",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "raw_data_summary": data,
            }
