from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.v1.dependencies.getters import get_dashboard_service
from app.application.dto.dashboard import (
    DashboardMetrics,
    SectorStatus,
    StadiumOverview,
    TimeSeriesData,
)
from app.application.services.dashboard_service import DashboardService
from app.core.security.auth import TokenPayload, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/overview", response_model=DashboardMetrics)
async def get_overview(
    stadium_id: UUID = Query(...),
    current_user: TokenPayload = Depends(get_current_user),
    service: DashboardService = Depends(get_dashboard_service),
) -> DashboardMetrics:
    metrics = await service.get_overview_metrics(stadium_id)
    return DashboardMetrics(**metrics)


@router.get("/sectors", response_model=list[SectorStatus])
async def get_sector_status(
    stadium_id: UUID = Query(...),
    current_user: TokenPayload = Depends(get_current_user),
    service: DashboardService = Depends(get_dashboard_service),
) -> list[SectorStatus]:
    sectors = await service.get_sector_status(stadium_id)
    return [SectorStatus(**s) for s in sectors]


@router.get("/stadium/{stadium_id}", response_model=StadiumOverview)
async def get_stadium_overview(
    stadium_id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
    service: DashboardService = Depends(get_dashboard_service),
) -> StadiumOverview:
    overview = await service.get_stadium_overview(stadium_id)
    return StadiumOverview(**overview)


@router.get("/analytics/{metric}", response_model=TimeSeriesData)
async def get_analytics(
    metric: str,
    stadium_id: UUID = Query(...),
    granularity: str = Query(default="hour"),
    hours_back: int = Query(default=24, ge=1, le=168),
    current_user: TokenPayload = Depends(get_current_user),
    service: DashboardService = Depends(get_dashboard_service),
) -> TimeSeriesData:
    data = await service.get_time_series_data(
        stadium_id=stadium_id,
        metric_name=metric,
        granularity=granularity,
        hours_back=hours_back,
    )
    return TimeSeriesData(**data)
