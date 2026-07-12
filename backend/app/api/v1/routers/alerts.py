from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.v1.dependencies.getters import get_alert_service
from app.application.dto.alerts import AlertCreateRequest, AlertListResponse, AlertResponse
from app.application.services.alert_service import AlertService
from app.core.security.auth import TokenPayload, get_current_user
from app.domain.entities.alert import AlertStatus
from app.domain.value_objects.priority import Priority

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/alerts", tags=["Alerts"])


def _alert_to_response(alert: Any) -> AlertResponse:
    return AlertResponse(
        id=alert.id,
        alert_type=alert.alert_type.value,
        title=alert.title,
        description=alert.description,
        priority=alert.priority.value,
        status=alert.status.value,
        sector=alert.sector,
        location=alert.location,
        stadium_id=alert.stadium_id,
        event_id=alert.event_id,
        triggered_by_user_id=alert.triggered_by_user_id,
        assigned_to_user_id=alert.assigned_to_user_id,
        triggered_by_ai=alert.triggered_by_ai,
        ai_confidence=alert.ai_confidence,
        escalation_level=alert.escalation_level,
        notifications_sent=alert.notifications_sent,
        public_announcement=alert.public_announcement,
        metadata=alert.metadata,
        created_at=alert.created_at,
        updated_at=alert.updated_at,
        resolved_at=alert.resolved_at,
        acknowledged_at=alert.acknowledged_at,
    )


@router.post("", response_model=AlertResponse, status_code=201)
async def create_alert(
    request: AlertCreateRequest,
    current_user: TokenPayload = Depends(get_current_user),
    service: AlertService = Depends(get_alert_service),
) -> AlertResponse:
    alert = await service.create_alert(
        alert_type=request.alert_type,
        title=request.title,
        description=request.description,
        stadium_id=request.stadium_id,
        priority=request.priority,
        sector=request.sector,
        location=request.location,
        event_id=request.event_id,
        affected_sectors=request.affected_sectors,
        triggered_by_user_id=request.triggered_by_user_id or UUID(current_user.sub),
        triggered_by_ai=request.triggered_by_ai,
        ai_confidence=request.ai_confidence,
        metadata=request.metadata,
    )
    return _alert_to_response(alert)


@router.get("", response_model=AlertListResponse)
async def list_alerts(
    stadium_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: TokenPayload = Depends(get_current_user),
    service: AlertService = Depends(get_alert_service),
) -> AlertListResponse:
    if status:
        try:
            alert_status = AlertStatus(status)
            alerts = await service.list_alerts_by_status(
                alert_status, offset=offset, limit=limit
            )
        except ValueError:
            alerts = await service.list_active_alerts(
                stadium_id=stadium_id, offset=offset, limit=limit
            )
    else:
        alerts = await service.list_active_alerts(
            stadium_id=stadium_id, offset=offset, limit=limit
        )

    return AlertListResponse(
        alerts=[_alert_to_response(a) for a in alerts],
        total_count=len(alerts),
        page=(offset // limit) + 1,
        page_size=limit,
    )


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
    service: AlertService = Depends(get_alert_service),
) -> AlertResponse:
    alert = await service.get_alert(alert_id)
    if alert is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Alert not found")
    return _alert_to_response(alert)


@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: UUID,
    title: str | None = Query(default=None),
    description: str | None = Query(default=None),
    current_user: TokenPayload = Depends(get_current_user),
    service: AlertService = Depends(get_alert_service),
) -> AlertResponse:
    alert = await service.update_alert(
        alert_id=alert_id, title=title, description=description
    )
    if alert is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Alert not found")
    return _alert_to_response(alert)


@router.post("/{alert_id}/escalate", response_model=AlertResponse)
async def escalate_alert(
    alert_id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
    service: AlertService = Depends(get_alert_service),
) -> AlertResponse:
    alert = await service.escalate_alert(
        alert_id=alert_id, user_id=UUID(current_user.sub)
    )
    if alert is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Alert not found")
    return _alert_to_response(alert)


@router.post("/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert(
    alert_id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
    service: AlertService = Depends(get_alert_service),
) -> AlertResponse:
    alert = await service.resolve_alert(alert_id)
    if alert is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Alert not found")
    return _alert_to_response(alert)


@router.post("/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
    service: AlertService = Depends(get_alert_service),
) -> AlertResponse:
    alert = await service.acknowledge_alert(
        alert_id=alert_id, user_id=UUID(current_user.sub)
    )
    if alert is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Alert not found")
    return _alert_to_response(alert)
