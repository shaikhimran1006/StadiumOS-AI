from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.v1.dependencies.getters import get_incident_service
from app.application.dto.incidents import (
    IncidentCreateRequest,
    IncidentListResponse,
    IncidentResponse,
    ResponderDTO,
)
from app.application.services.incident_service import IncidentService
from app.core.security.auth import TokenPayload, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/incidents", tags=["Incidents"])


def _incident_to_response(incident: Any) -> IncidentResponse:
    responders = [
        ResponderDTO(
            user_id=r.user_id,
            role=r.role,
            dispatched_at=r.dispatched_at,
            arrived_at=r.arrived_at,
        )
        for r in incident.responders
    ]
    return IncidentResponse(
        id=incident.id,
        category=incident.category.value,
        title=incident.title,
        description=incident.description,
        severity=incident.severity.value,
        priority=incident.priority.value,
        status=incident.status.value,
        sector=incident.sector,
        location=incident.location,
        stadium_id=incident.stadium_id,
        event_id=incident.event_id,
        reported_by_user_id=incident.reported_by_user_id,
        reported_by_ai=incident.reported_by_ai,
        ai_confidence=incident.ai_confidence,
        responders=responders,
        people_involved=incident.people_involved,
        injuries_reported=incident.injuries_reported,
        medical_transport_called=incident.medical_transport_called,
        law_enforcement_called=incident.law_enforcement_called,
        public_visibility=incident.public_visibility,
        resolution_notes=incident.resolution_notes,
        tags=incident.tags,
        metadata=incident.metadata,
        created_at=incident.created_at,
        updated_at=incident.updated_at,
        resolved_at=incident.resolved_at,
        closed_at=incident.closed_at,
    )


@router.post("", response_model=IncidentResponse, status_code=201)
async def create_incident(
    request: IncidentCreateRequest,
    current_user: TokenPayload = Depends(get_current_user),
    service: IncidentService = Depends(get_incident_service),
) -> IncidentResponse:
    incident = await service.create_incident(
        category=request.category,
        title=request.title,
        description=request.description,
        stadium_id=request.stadium_id,
        severity=request.severity,
        sector=request.sector,
        location=request.location,
        event_id=request.event_id,
        reported_by=request.reported_by or UUID(current_user.sub),
        reported_by_ai=request.reported_by_ai,
        ai_confidence=request.ai_confidence,
        people_involved=request.people_involved,
        injuries_reported=request.injuries_reported,
        public_visibility=request.public_visibility,
        tags=request.tags,
        metadata=request.metadata,
    )
    return _incident_to_response(incident)


@router.get("", response_model=IncidentListResponse)
async def list_incidents(
    stadium_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: TokenPayload = Depends(get_current_user),
    service: IncidentService = Depends(get_incident_service),
) -> IncidentListResponse:
    from app.domain.entities.incident import IncidentStatus

    incident_status = None
    if status:
        try:
            incident_status = IncidentStatus(status)
        except ValueError:
            pass

    incidents = await service.list_incidents(
        stadium_id=stadium_id,
        status=incident_status,
        offset=offset,
        limit=limit,
    )

    return IncidentListResponse(
        incidents=[_incident_to_response(i) for i in incidents],
        total_count=len(incidents),
        page=(offset // limit) + 1,
        page_size=limit,
    )


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
    service: IncidentService = Depends(get_incident_service),
) -> IncidentResponse:
    incident = await service.get_incident(incident_id)
    if incident is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Incident not found")
    return _incident_to_response(incident)


@router.put("/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    incident_id: UUID,
    title: str | None = Query(default=None),
    description: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    current_user: TokenPayload = Depends(get_current_user),
    service: IncidentService = Depends(get_incident_service),
) -> IncidentResponse:
    incident = await service.update_incident(
        incident_id=incident_id,
        title=title,
        description=description,
        severity=severity,
    )
    if incident is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Incident not found")
    return _incident_to_response(incident)


@router.post("/{incident_id}/assign", response_model=IncidentResponse)
async def assign_responder(
    incident_id: UUID,
    responder_id: UUID = Query(...),
    role: str = Query(...),
    current_user: TokenPayload = Depends(get_current_user),
    service: IncidentService = Depends(get_incident_service),
) -> IncidentResponse:
    incident = await service.assign_responder(
        incident_id=incident_id,
        user_id=responder_id,
        role=role,
    )
    if incident is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Incident not found")
    return _incident_to_response(incident)


@router.post("/{incident_id}/resolve", response_model=IncidentResponse)
async def resolve_incident(
    incident_id: UUID,
    resolution_notes: str | None = Query(default=None),
    current_user: TokenPayload = Depends(get_current_user),
    service: IncidentService = Depends(get_incident_service),
) -> IncidentResponse:
    incident = await service.resolve_incident(
        incident_id=incident_id,
        resolution_notes=resolution_notes,
    )
    if incident is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Incident not found")
    return _incident_to_response(incident)
