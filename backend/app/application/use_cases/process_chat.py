from __future__ import annotations

import logging
import time
from typing import Any
from uuid import UUID

from app.application.dto.chat import ChatRequest, ChatResponse
from app.application.services.chat_service import ChatService
from app.domain.interfaces.ai_services import IGenerativeAIService, IRAGService
from app.domain.interfaces.external_services import (
    IPubSubService,
    ITranslationService,
    IVisionService,
)

logger = logging.getLogger(__name__)


class ProcessChatUseCase:
    def __init__(
        self,
        chat_service: ChatService,
        rag_service: IRAGService | None = None,
        vision_service: IVisionService | None = None,
    ) -> None:
        self._chat = chat_service
        self._rag = rag_service
        self._vision = vision_service

    async def execute(
        self,
        request: ChatRequest,
        user_id: UUID,
        channel: str = "IN_APP",
    ) -> ChatResponse:
        start_time = time.time()

        context = request.context or {}

        if self._rag is not None and self._should_enrich_context(request.message):
            rag_context = await self._enrich_with_rag(request.message, context)
            if rag_context:
                context["rag_results"] = rag_context

        if request.message_type == "IMAGE" and self._vision is not None:
            vision_context = await self._analyze_image_context(request, context)
            if vision_context:
                context["vision_analysis"] = vision_context

        enriched_request = ChatRequest(
            message=request.message,
            conversation_id=request.conversation_id,
            language=request.language,
            context=context,
            message_type=request.message_type,
        )

        response = await self._chat.send_message(
            request=enriched_request,
            user_id=user_id,
            channel=channel,
        )

        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.info(
            "ProcessChatUseCase completed in %dms (conversation=%s, agent=%s)",
            elapsed_ms, response.conversation_id, response.agent_name,
        )

        return response

    def _should_enrich_context(self, message: str) -> bool:
        keywords = [
            "where", "how", "what", "find", "show", "tell",
            "schedule", "direction", "nearest", "located",
        ]
        message_lower = message.lower()
        return any(kw in message_lower for kw in keywords)

    async def _enrich_with_rag(
        self, message: str, context: dict[str, Any]
    ) -> list[dict[str, Any]]:
        try:
            collection = "stadium_knowledge"
            if "stadium_id" in context:
                collection = f"stadium_{context['stadium_id']}"

            results = await self._rag.query(
                query=message,
                collection=collection,
                top_k=5,
            )
            return [
                {
                    "content": r.content,
                    "source": r.source,
                    "score": r.score,
                }
                for r in results
            ]
        except Exception:
            logger.exception("RAG enrichment failed")
            return []

    async def _analyze_image_context(
        self, request: ChatRequest, context: dict[str, Any]
    ) -> dict[str, Any] | None:
        return None
