from __future__ import annotations

import logging
import time
from typing import Any
from uuid import UUID, uuid4

from app.ai.agents.base_agent import AgentResponse
from app.ai.router.agent_router import AgentRouter
from app.application.dto.chat import (
    ChatRequest,
    ChatResponse,
    ConversationHistory,
    MessageDTO,
)
from app.domain.entities.conversation import (
    Conversation,
    ConversationChannel,
    ConversationContext,
    ConversationStatus,
)
from app.domain.entities.message import Message, MessageMetadata, MessageType, SenderType
from app.domain.entities.user import User
from app.domain.interfaces.ai_services import IGenerativeAIService
from app.domain.interfaces.external_services import (
    IBigQueryService,
    IPubSubService,
    ITranslationService,
)
from app.domain.interfaces.repositories import (
    IConversationRepository,
    IMessageRepository,
    IUserRepository,
)
from app.domain.value_objects.language import Language

logger = logging.getLogger(__name__)

BIGQUERY_DATASET = "stadiumos_analytics"
BIGQUERY_TABLE_CONVERSATIONS = "ai_conversations"
BIGQUERY_TABLE_MESSAGES = "ai_messages"


class ChatService:
    def __init__(
        self,
        conversation_repo: IConversationRepository,
        message_repo: IMessageRepository,
        user_repo: IUserRepository,
        agent_router: AgentRouter,
        generative_ai: IGenerativeAIService | None = None,
        translation_service: ITranslationService | None = None,
        pubsub: IPubSubService | None = None,
        bigquery: IBigQueryService | None = None,
    ) -> None:
        self._conversations = conversation_repo
        self._messages = message_repo
        self._users = user_repo
        self._router = agent_router
        self._ai = generative_ai
        self._translator = translation_service
        self._pubsub = pubsub
        self._bigquery = bigquery

    async def send_message(
        self,
        request: ChatRequest,
        user_id: UUID,
        channel: str = "IN_APP",
    ) -> ChatResponse:
        start_time = time.time()

        conversation = await self._get_or_create_conversation(
            conversation_id=request.conversation_id,
            user_id=user_id,
            channel=channel,
            language=request.language,
            context=request.context,
        )

        user_message = await self._save_user_message(
            conversation_id=conversation.id,
            content=request.message,
            message_type=request.message_type,
            language=request.language,
        )

        translated_text = request.message
        translation_used = False
        if (
            self._translator
            and request.language != Language.ENGLISH.value
        ):
            try:
                result = await self._translator.translate(
                    text=request.message,
                    target_language=Language.ENGLISH.value,
                    source_language=request.language,
                )
                translated_text = result.translated_text
                translation_used = True
            except Exception:
                logger.warning("Translation failed for language %s, using original", request.language)

        recent_history = await self._get_conversation_history_for_context(conversation.id)

        context = request.context or {}
        context["conversation_id"] = str(conversation.id)
        context["user_id"] = str(user_id)
        context["language"] = request.language
        context["channel"] = channel
        if conversation.context.stadium_id:
            context["stadium_id"] = str(conversation.context.stadium_id)
        if conversation.context.event_id:
            context["event_id"] = str(conversation.context.event_id)
        if conversation.context.sector:
            context["sector"] = conversation.context.sector

        agent_response = self._router.process_query(translated_text, context)

        latency_ms = int((time.time() - start_time) * 1000)

        ai_message = await self._save_ai_message(
            conversation_id=conversation.id,
            content=agent_response.response_text,
            agent_name=agent_response.agent_name,
            confidence=agent_response.confidence,
            latency_ms=latency_ms,
            sources=agent_response.sources,
            translation_used=translation_used,
        )

        conversation.increment_message_count()
        await self._conversations.update(conversation)

        await self._log_conversation_event(conversation, user_message, ai_message, latency_ms)

        await self._publish_chat_event(conversation, user_message, ai_message)

        return ChatResponse(
            response_text=agent_response.response_text,
            conversation_id=conversation.id,
            message_id=ai_message.id,
            agent_name=agent_response.agent_name,
            confidence=agent_response.confidence,
            metadata={**agent_response.metadata, "latency_ms": latency_ms},
            sources=agent_response.sources,
            actions=agent_response.actions,
        )

    async def get_conversation_history(
        self,
        conversation_id: UUID,
        offset: int = 0,
        limit: int = 50,
    ) -> ConversationHistory | None:
        conversation = await self._conversations.get_by_id(conversation_id)
        if conversation is None:
            return None

        messages = await self._messages.list_by_conversation(
            conversation_id, offset=offset, limit=limit
        )

        message_dtos = [
            MessageDTO(
                id=msg.id,
                sender_type=msg.sender_type.value,
                content=msg.content,
                message_type=msg.message_type.value,
                metadata={
                    "confidence_score": msg.metadata.confidence_score,
                    "intent_detected": msg.metadata.intent_detected,
                    "tokens_used": msg.metadata.tokens_used,
                    "model_name": msg.metadata.model_name,
                    "language_detected": msg.metadata.language_detected,
                    "rag_sources": msg.metadata.rag_sources,
                },
                created_at=msg.created_at,
            )
            for msg in messages
        ]

        return ConversationHistory(
            conversation_id=conversation.id,
            messages=message_dtos,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            status=conversation.status.value,
            language=conversation.language.value,
            message_count=conversation.message_count,
        )

    async def close_conversation(
        self,
        conversation_id: UUID,
        summary: str | None = None,
        satisfaction_score: int | None = None,
    ) -> ConversationHistory | None:
        conversation = await self._conversations.get_by_id(conversation_id)
        if conversation is None:
            return None

        conversation.close(summary=summary)
        if satisfaction_score is not None:
            conversation.set_satisfaction(satisfaction_score)
        await self._conversations.update(conversation)

        system_message = Message(
            conversation_id=conversation.id,
            sender_type=SenderType.SYSTEM,
            content="Conversation closed." + (f" Summary: {summary}" if summary else ""),
            message_type=MessageType.SYSTEM_EVENT,
        )
        await self._messages.create(system_message)

        await self._log_conversation_event(conversation, None, None, 0)

        return await self.get_conversation_history(conversation_id)

    async def transfer_conversation(
        self,
        conversation_id: UUID,
        agent_id: UUID,
    ) -> ConversationHistory | None:
        conversation = await self._conversations.get_by_id(conversation_id)
        if conversation is None:
            return None

        conversation.transfer_to_agent(agent_id)
        await self._conversations.update(conversation)

        transfer_message = Message(
            conversation_id=conversation.id,
            sender_type=SenderType.SYSTEM,
            content=f"Conversation transferred to human agent {agent_id}.",
            message_type=MessageType.SYSTEM_EVENT,
        )
        await self._messages.create(transfer_message)

        await self._publish_transfer_event(conversation, agent_id)

        return await self.get_conversation_history(conversation_id)

    async def _get_or_create_conversation(
        self,
        conversation_id: UUID | None,
        user_id: UUID,
        channel: str,
        language: str,
        context: dict[str, Any] | None,
    ) -> Conversation:
        if conversation_id is not None:
            conversation = await self._conversations.get_by_id(conversation_id)
            if conversation is not None and conversation.is_active():
                return conversation

        conv_channel = ConversationChannel(channel) if channel in ConversationChannel.__members__.values() else ConversationChannel.IN_APP
        try:
            conv_language = Language.from_bcp47(language)
        except ValueError:
            conv_language = Language.ENGLISH

        conv_context = ConversationContext()
        if context:
            if "stadium_id" in context:
                try:
                    conv_context.stadium_id = UUID(context["stadium_id"])
                except (ValueError, TypeError):
                    pass
            if "event_id" in context:
                try:
                    conv_context.event_id = UUID(context["event_id"])
                except (ValueError, TypeError):
                    pass
            if "sector" in context:
                conv_context.sector = context["sector"]
            if "entry_point" in context:
                conv_context.entry_point = context["entry_point"]

        new_conversation = Conversation(
            user_id=user_id,
            channel=conv_channel,
            language=conv_language,
            context=conv_context,
        )
        return await self._conversations.create(new_conversation)

    async def _save_user_message(
        self,
        conversation_id: UUID,
        content: str,
        message_type: str,
        language: str,
    ) -> Message:
        try:
            msg_type = MessageType(message_type)
        except ValueError:
            msg_type = MessageType.TEXT

        message = Message(
            conversation_id=conversation_id,
            sender_type=SenderType.USER,
            content=content,
            message_type=msg_type,
            language=language,
        )
        return await self._messages.create(message)

    async def _save_ai_message(
        self,
        conversation_id: UUID,
        content: str,
        agent_name: str,
        confidence: float,
        latency_ms: int,
        sources: list[str],
        translation_used: bool,
    ) -> Message:
        metadata = MessageMetadata(
            confidence_score=confidence,
            latency_ms=latency_ms,
            model_name=agent_name,
            rag_sources=sources,
            translation_used=translation_used,
        )

        message = Message(
            conversation_id=conversation_id,
            sender_type=SenderType.AI,
            content=content,
            message_type=MessageType.TEXT,
            metadata=metadata,
        )
        return await self._messages.create(message)

    async def _get_conversation_history_for_context(
        self, conversation_id: UUID, limit: int = 20
    ) -> list[dict[str, str]]:
        messages = await self._messages.list_recent_by_conversation(
            conversation_id, limit=limit
        )
        history: list[dict[str, str]] = []
        for msg in messages:
            role = "assistant" if msg.sender_type in (SenderType.AI, SenderType.AGENT) else "user"
            history.append({"role": role, "content": msg.content})
        return history

    async def _log_conversation_event(
        self,
        conversation: Conversation,
        user_message: Message | None,
        ai_message: Message | None,
        latency_ms: int,
    ) -> None:
        if self._bigquery is None:
            return
        try:
            row: dict[str, Any] = {
                "conversation_id": str(conversation.id),
                "user_id": str(conversation.user_id),
                "channel": conversation.channel.value,
                "language": conversation.language.value,
                "message_count": conversation.message_count,
                "status": conversation.status.value,
                "latency_ms": latency_ms,
                "timestamp": conversation.updated_at.isoformat(),
            }
            if user_message:
                row["user_message_id"] = str(user_message.id)
                row["user_message_length"] = len(user_message.content)
            if ai_message:
                row["ai_message_id"] = str(ai_message.id)
                row["ai_agent"] = ai_message.metadata.model_name or ""
                row["confidence"] = ai_message.metadata.confidence_score or 0.0
            await self._bigquery.insert_rows(
                BIGQUERY_DATASET, BIGQUERY_TABLE_CONVERSATIONS, [row]
            )
        except Exception:
            logger.exception("Failed to log conversation to BigQuery")

    async def _publish_chat_event(
        self,
        conversation: Conversation,
        user_message: Message,
        ai_message: Message,
    ) -> None:
        if self._pubsub is None:
            return
        try:
            from app.domain.interfaces.external_services import PubSubMessage

            msg = PubSubMessage(
                topic="stadiumos-analytics",
                data={
                    "event_type": "chat_message",
                    "conversation_id": str(conversation.id),
                    "user_id": str(conversation.user_id),
                    "agent_name": ai_message.metadata.model_name or "",
                    "confidence": ai_message.metadata.confidence_score or 0.0,
                    "channel": conversation.channel.value,
                    "language": conversation.language.value,
                },
                attributes={
                    "conversation_id": str(conversation.id),
                    "language": conversation.language.value,
                },
            )
            await self._pubsub.publish("stadiumos-analytics", msg)
        except Exception:
            logger.exception("Failed to publish chat event to Pub/Sub")

    async def _publish_transfer_event(
        self, conversation: Conversation, agent_id: UUID
    ) -> None:
        if self._pubsub is None:
            return
        try:
            from app.domain.interfaces.external_services import PubSubMessage

            msg = PubSubMessage(
                topic="stadiumos-notifications",
                data={
                    "event_type": "conversation_transfer",
                    "conversation_id": str(conversation.id),
                    "user_id": str(conversation.user_id),
                    "agent_id": str(agent_id),
                    "channel": conversation.channel.value,
                },
                attributes={"conversation_id": str(conversation.id)},
            )
            await self._pubsub.publish("stadiumos-notifications", msg)
        except Exception:
            logger.exception("Failed to publish transfer event to Pub/Sub")
