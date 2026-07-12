from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.v1.dependencies.getters import get_event_service
from app.application.dto.events import EventCreateRequest, EventListResponse, EventResponse
from app.application.services.event_service import EventService
from app.core.security.auth import TokenPayload, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/events", tags=["Events"])


def _event_to_response(event: Any) -> EventResponse:
    return EventResponse(
        id=event.id,
        name=event.name,
        event_type=event.event_type.value,
        status=event.status.value,
        start_time=event.kickoff_at,
        end_time=event.estimated_end_at,
        stadium_id=event.stadium_id,
        home_team=event.home_team,
        away_team=event.away_team,
        competition=event.competition,
        expected_attendance=event.expected_attendance,
        actual_attendance=event.actual_attendance,
        attendance_percentage=event.attendance_percentage(),
        tags=event.tags,
        metadata=event.metadata,
        created_at=event.created_at,
        updated_at=event.updated_at,
    )


@router.post("", response_model=EventResponse, status_code=201)
async def create_event(
    request: EventCreateRequest,
    current_user: TokenPayload = Depends(get_current_user),
    service: EventService = Depends(get_event_service),
) -> EventResponse:
    event = await service.create_event(
        name=request.name,
        stadium_id=request.stadium_id,
        event_type=request.event_type,
        start_time=request.start_time,
        end_time=request.end_time,
        home_team=request.home_team,
        away_team=request.away_team,
        competition=request.competition,
        expected_attendance=request.expected_attendance,
        gates_open_at=request.gates_open_at,
        broadcast_channels=request.broadcast_channels,
        tags=request.tags,
        metadata=request.metadata,
    )
    return _event_to_response(event)


@router.get("", response_model=EventListResponse)
async def list_events(
    stadium_id: UUID | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: TokenPayload = Depends(get_current_user),
    service: EventService = Depends(get_event_service),
) -> EventListResponse:
    events = await service.list_events(
        stadium_id=stadium_id, offset=offset, limit=limit
    )
    return EventListResponse(
        events=[_event_to_response(e) for e in events],
        total_count=len(events),
        page=(offset // limit) + 1,
        page_size=limit,
    )


@router.get("/live", response_model=list[EventResponse])
async def get_live_events(
    current_user: TokenPayload = Depends(get_current_user),
    service: EventService = Depends(get_event_service),
) -> list[EventResponse]:
    events = await service.get_live_events()
    return [_event_to_response(e) for e in events]


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
    service: EventService = Depends(get_event_service),
) -> EventResponse:
    event = await service.get_event(event_id)
    if event is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Event not found")
    return _event_to_response(event)


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: UUID,
    name: str | None = Query(default=None),
    status: str | None = Query(default=None),
    expected_attendance: int | None = Query(default=None),
    actual_attendance: int | None = Query(default=None),
    current_user: TokenPayload = Depends(get_current_user),
    service: EventService = Depends(get_event_service),
) -> EventResponse:
    event = await service.update_event(
        event_id=event_id,
        name=name,
        status=status,
        expected_attendance=expected_attendance,
        actual_attendance=actual_attendance,
    )
    if event is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Event not found")
    return _event_to_response(event)
