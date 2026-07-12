from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.v1.dependencies.getters import get_feedback_service
from app.application.dto.feedback import (
    FeedbackAnalytics,
    FeedbackCreateRequest,
    FeedbackResponse,
)
from app.application.services.feedback_service import FeedbackService
from app.core.security.auth import TokenPayload, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feedback", tags=["Feedback"])


def _feedback_to_response(feedback: Any) -> FeedbackResponse:
    return FeedbackResponse(
        id=feedback.id,
        category=feedback.category.value,
        rating=feedback.rating,
        comment=feedback.comment,
        sentiment=feedback.sentiment.value if feedback.sentiment else None,
        event_id=feedback.event_id,
        sector=feedback.sector,
        is_anonymous=feedback.is_anonymous,
        tags=feedback.tags,
        upvotes=feedback.upvotes,
        created_at=feedback.created_at,
        updated_at=feedback.updated_at,
    )


@router.post("", response_model=FeedbackResponse, status_code=201)
async def submit_feedback(
    request: FeedbackCreateRequest,
    current_user: TokenPayload = Depends(get_current_user),
    service: FeedbackService = Depends(get_feedback_service),
) -> FeedbackResponse:
    feedback = await service.create_feedback(
        user_id=UUID(current_user.sub),
        stadium_id=request.stadium_id,
        category=request.category,
        rating=request.rating,
        comment=request.comment,
        event_id=request.event_id,
        sector=request.sector,
        anonymous=request.anonymous,
        conversation_id=request.conversation_id,
        tags=request.tags,
        metadata=request.metadata,
    )
    return _feedback_to_response(feedback)


@router.get("", response_model=list[FeedbackResponse])
async def list_feedback(
    stadium_id: UUID | None = Query(default=None),
    event_id: UUID | None = Query(default=None),
    category: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: TokenPayload = Depends(get_current_user),
    service: FeedbackService = Depends(get_feedback_service),
) -> list[FeedbackResponse]:
    if event_id:
        feedback_list = await service.list_feedback_by_event(
            event_id, offset=offset, limit=limit
        )
    elif category:
        from app.domain.entities.feedback import FeedbackCategory

        try:
            cat = FeedbackCategory(category)
            feedback_list = await service.list_feedback_by_category(
                cat, stadium_id=stadium_id, offset=offset, limit=limit
            )
        except ValueError:
            feedback_list = []
    elif stadium_id:
        feedback_list = await service.list_feedback_by_stadium(
            stadium_id, offset=offset, limit=limit
        )
    else:
        feedback_list = []

    return [_feedback_to_response(f) for f in feedback_list]


@router.get("/analytics", response_model=FeedbackAnalytics)
async def get_feedback_analytics(
    stadium_id: UUID = Query(...),
    event_id: UUID | None = Query(default=None),
    current_user: TokenPayload = Depends(get_current_user),
    service: FeedbackService = Depends(get_feedback_service),
) -> FeedbackAnalytics:
    analytics = await service.get_analytics(
        stadium_id=stadium_id, event_id=event_id
    )
    return FeedbackAnalytics(**analytics)


@router.get("/{feedback_id}", response_model=FeedbackResponse)
async def get_feedback(
    feedback_id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
    service: FeedbackService = Depends(get_feedback_service),
) -> FeedbackResponse:
    feedback = await service.get_feedback(feedback_id)
    if feedback is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Feedback not found")
    return _feedback_to_response(feedback)
