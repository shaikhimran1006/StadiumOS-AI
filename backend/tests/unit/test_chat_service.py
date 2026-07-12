"""Tests for ChatService."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from app.ai.agents.base_agent import AgentResponse
from app.ai.router.agent_router import AgentRouter
from app.application.dto.chat import ChatRequest, ChatResponse
from app.application.services.chat_service import ChatService
from app.domain.entities.conversation import Conversation, ConversationChannel, ConversationStatus
from app.domain.entities.message import Message, SenderType
from app.domain.entities.user import User, UserRole


@pytest.fixture
def mock_conversation_repo():
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_message_repo():
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_user_repo():
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_agent_router():
    router = MagicMock(spec=AgentRouter)
    router.process_query.return_value = AgentResponse(
        response_text="Your seat is in section A5, row 12, seat 8.",
        agent_name="FanAgent",
        confidence=0.92,
        metadata={"intent": "seating"},
        actions=[],
        sources=["stadium_map"],
    )
    return router


@pytest.fixture
def chat_service(
    mock_conversation_repo,
    mock_message_repo,
    mock_user_repo,
    mock_agent_router,
):
    return ChatService(
        conversation_repo=mock_conversation_repo,
        message_repo=mock_message_repo,
        user_repo=mock_user_repo,
        agent_router=mock_agent_router,
        generative_ai=None,
        translation_service=None,
        pubsub=None,
        bigquery=None,
    )


@pytest.mark.asyncio
class TestChatServiceSendMessage:
    async def test_send_message_creates_new_conversation(
        self, chat_service, mock_conversation_repo
    ):
        new_conv = Conversation(
            id=uuid4(),
            user_id=uuid4(),
            channel=ConversationChannel.IN_APP,
        )
        mock_conversation_repo.create.return_value = new_conv
        mock_conversation_repo.get_by_id.return_value = new_conv

        request = ChatRequest(message="Where is my seat?")

        mock_user_message = MagicMock()
        mock_user_message.id = uuid4()
        mock_ai_message = MagicMock()
        mock_ai_message.id = uuid4()

        with patch.object(chat_service, '_save_user_message', new_callable=AsyncMock) as mock_save_user, \
             patch.object(chat_service, '_save_ai_message', new_callable=AsyncMock) as mock_save_ai, \
             patch.object(chat_service, '_get_conversation_history_for_context', new_callable=AsyncMock, return_value=[]), \
             patch.object(chat_service, '_log_conversation_event', new_callable=AsyncMock), \
             patch.object(chat_service, '_publish_chat_event', new_callable=AsyncMock):

            mock_save_user.return_value = mock_user_message
            mock_save_ai.return_value = mock_ai_message

            response = await chat_service.send_message(
                request=request,
                user_id=uuid4(),
            )

            assert isinstance(response, ChatResponse)
            assert response.response_text == "Your seat is in section A5, row 12, seat 8."
            assert response.agent_name == "FanAgent"

    async def test_send_message_with_existing_conversation(
        self, chat_service, mock_conversation_repo
    ):
        existing_conv = Conversation(
            id=uuid4(),
            user_id=uuid4(),
            channel=ConversationChannel.IN_APP,
            status=ConversationStatus.ACTIVE,
        )
        mock_conversation_repo.get_by_id.return_value = existing_conv

        request = ChatRequest(
            message="Thanks! What about food?",
            conversation_id=existing_conv.id,
        )

        mock_user_message = MagicMock()
        mock_user_message.id = uuid4()
        mock_ai_message = MagicMock()
        mock_ai_message.id = uuid4()

        with patch.object(chat_service, '_save_user_message', new_callable=AsyncMock) as mock_save_user, \
             patch.object(chat_service, '_save_ai_message', new_callable=AsyncMock) as mock_save_ai, \
             patch.object(chat_service, '_get_conversation_history_for_context', new_callable=AsyncMock, return_value=[]), \
             patch.object(chat_service, '_log_conversation_event', new_callable=AsyncMock), \
             patch.object(chat_service, '_publish_chat_event', new_callable=AsyncMock):

            mock_save_user.return_value = mock_user_message
            mock_save_ai.return_value = mock_ai_message

            response = await chat_service.send_message(
                request=request,
                user_id=existing_conv.user_id,
            )

            assert isinstance(response, ChatResponse)

    async def test_send_message_with_language(
        self, chat_service, mock_conversation_repo
    ):
        mock_conversation_repo.create.return_value = Conversation(
            id=uuid4(),
            user_id=uuid4(),
        )
        mock_conversation_repo.get_by_id.return_value = None

        request = ChatRequest(
            message="Hola, donde esta mi asiento?",
            language="es",
        )

        with patch.object(chat_service, '_save_user_message', new_callable=AsyncMock) as mock_save_user, \
             patch.object(chat_service, '_save_ai_message', new_callable=AsyncMock) as mock_save_ai, \
             patch.object(chat_service, '_get_conversation_history_for_context', new_callable=AsyncMock, return_value=[]), \
             patch.object(chat_service, '_log_conversation_event', new_callable=AsyncMock), \
             patch.object(chat_service, '_publish_chat_event', new_callable=AsyncMock):

            mock_save_user.return_value = MagicMock()
            mock_save_ai.return_value = MagicMock()

            response = await chat_service.send_message(
                request=request,
                user_id=uuid4(),
            )

            assert isinstance(response, ChatResponse)

    async def test_send_message_error_handling(
        self, chat_service, mock_conversation_repo
    ):
        mock_conversation_repo.get_by_id.return_value = None
        mock_conversation_repo.create.side_effect = Exception("Firestore unavailable")

        request = ChatRequest(message="Hello")

        with pytest.raises(Exception, match="Firestore unavailable"):
            await chat_service.send_message(
                request=request,
                user_id=uuid4(),
            )


@pytest.mark.asyncio
class TestChatServiceConversationHistory:
    async def test_get_conversation_history(
        self, chat_service, mock_conversation_repo, mock_message_repo
    ):
        conv = Conversation(
            id=uuid4(),
            user_id=uuid4(),
            message_count=2,
        )
        mock_conversation_repo.get_by_id.return_value = conv
        mock_message_repo.list_by_conversation.return_value = [
            Message(
                conversation_id=conv.id,
                sender_type=SenderType.USER,
                content="Hello",
            ),
            Message(
                conversation_id=conv.id,
                sender_type=SenderType.AI,
                content="Hi there!",
            ),
        ]

        history = await chat_service.get_conversation_history(conv.id)
        assert history is not None
        assert history.conversation_id == conv.id
        assert len(history.messages) == 2

    async def test_get_conversation_history_not_found(
        self, chat_service, mock_conversation_repo
    ):
        mock_conversation_repo.get_by_id.return_value = None
        history = await chat_service.get_conversation_history(uuid4())
        assert history is None


@pytest.mark.asyncio
class TestChatServiceCloseConversation:
    async def test_close_conversation(
        self, chat_service, mock_conversation_repo, mock_message_repo
    ):
        conv = Conversation(
            id=uuid4(),
            user_id=uuid4(),
            status=ConversationStatus.ACTIVE,
        )
        mock_conversation_repo.get_by_id.return_value = conv
        mock_conversation_repo.update.return_value = conv
        mock_message_repo.list_by_conversation.return_value = []

        result = await chat_service.close_conversation(
            conv.id,
            summary="User got seating help",
            satisfaction_score=5,
        )

        assert result is not None

    async def test_close_nonexistent_conversation(
        self, chat_service, mock_conversation_repo
    ):
        mock_conversation_repo.get_by_id.return_value = None
        result = await chat_service.close_conversation(uuid4())
        assert result is None
