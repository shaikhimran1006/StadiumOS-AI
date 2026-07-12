from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.api.v1.dependencies.getters import get_notification_service
from app.application.services.notification_service import NotificationService
from app.core.security.auth import TokenPayload, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


class SendNotificationRequest(BaseModel):
    user_id: UUID
    title: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1, max_length=2000)
    notification_type: str = Field(default="info", description="info, warning, error, success")
    priority: str = Field(default="normal", description="normal, high, urgent")
    data: dict[str, Any] | None = None


class BroadcastRequest(BaseModel):
    stadium_id: UUID
    title: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1, max_length=2000)
    severity: str = Field(default="critical", description="low, medium, high, critical")
    sectors: list[str] | None = Field(default=None, description="Target specific sectors")
    exclude_sectors: list[str] | None = None


class SectorAlertRequest(BaseModel):
    stadium_id: UUID
    sector: str = Field(..., min_length=1, max_length=20)
    title: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1, max_length=2000)
    alert_level: str = Field(default="warning", description="info, warning, critical")
    data: dict[str, Any] | None = None


class SendNotificationResponse(BaseModel):
    success: bool
    message: str


class BroadcastResponse(BaseModel):
    sent_count: int
    message: str


@router.post("/send", response_model=SendNotificationResponse)
async def send_notification(
    request: SendNotificationRequest,
    current_user: TokenPayload = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> SendNotificationResponse:
    success = await service.send_notification(
        user_id=request.user_id,
        title=request.title,
        body=request.body,
        notification_type=request.notification_type,
        priority=request.priority,
        data=request.data,
    )
    return SendNotificationResponse(
        success=success,
        message="Notification sent successfully" if success else "Failed to send notification",
    )


@router.post("/broadcast", response_model=BroadcastResponse)
async def broadcast_emergency(
    request: BroadcastRequest,
    current_user: TokenPayload = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> BroadcastResponse:
    sent_count = await service.send_emergency_broadcast(
        stadium_id=request.stadium_id,
        title=request.title,
        body=request.body,
        severity=request.severity,
        sectors=request.sectors,
        exclude_sectors=request.exclude_sectors,
    )
    return BroadcastResponse(
        sent_count=sent_count,
        message=f"Emergency broadcast sent to {sent_count} targets",
    )


@router.post("/sector", response_model=SendNotificationResponse)
async def send_sector_alert(
    request: SectorAlertRequest,
    current_user: TokenPayload = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> SendNotificationResponse:
    success = await service.send_sector_alert(
        stadium_id=request.stadium_id,
        sector=request.sector,
        title=request.title,
        body=request.body,
        alert_level=request.alert_level,
        data=request.data,
    )
    return SendNotificationResponse(
        success=success,
        message="Sector alert sent successfully" if success else "Failed to send sector alert",
    )
