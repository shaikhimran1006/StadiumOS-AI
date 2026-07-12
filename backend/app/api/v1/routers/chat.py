from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.v1.dependencies.getters import get_chat_service
from app.application.dto.chat import ChatRequest, ChatResponse, ConversationHistory
from app.application.services.chat_service import ChatService
from app.core.security.auth import TokenPayload, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse, status_code=201)
async def send_message(
    request: ChatRequest,
    current_user: TokenPayload = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    user_id = UUID(current_user.sub)
    response = await service.send_message(request=request, user_id=user_id)
    return response


@router.get("/conversations", response_model=list[ConversationHistory])
async def list_conversations(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: TokenPayload = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> list[ConversationHistory]:
    from app.infrastructure.firestore.conversation_repository import ConversationRepository

    user_id = UUID(current_user.sub)
    repo = ConversationRepository()
    conversations = await repo.list_by_user(user_id, offset=offset, limit=limit)

    histories: list[ConversationHistory] = []
    for conv in conversations:
        history = await service.get_conversation_history(conv.id)
        if history:
            histories.append(history)

    return histories


@router.get("/conversations/{conversation_id}", response_model=ConversationHistory)
async def get_conversation(
    conversation_id: UUID,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    current_user: TokenPayload = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> ConversationHistory:
    history = await service.get_conversation_history(
        conversation_id, offset=offset, limit=limit
    )
    if history is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Conversation not found")
    return history


@router.delete("/conversations/{conversation_id}", response_model=ConversationHistory)
async def close_conversation(
    conversation_id: UUID,
    summary: str | None = Query(default=None, max_length=2000),
    satisfaction_score: int | None = Query(default=None, ge=1, le=5),
    current_user: TokenPayload = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> ConversationHistory:
    result = await service.close_conversation(
        conversation_id, summary=summary, satisfaction_score=satisfaction_score
    )
    if result is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Conversation not found")
    return result
