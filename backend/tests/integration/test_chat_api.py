"""Integration tests for chat API endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.security.auth import create_access_token


@pytest.fixture
def auth_headers():
    token = create_access_token(user_id=uuid4(), role="FAN")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client(test_client):
    return test_client


class TestPostChat:
    def test_send_message_unauthenticated(self, client):
        response = client.post("/api/v1/chat", json={"message": "Hello"})
        assert response.status_code == 401

    @patch("app.api.v1.routers.chat.get_chat_service")
    def test_send_message_success(self, mock_get_service, client, auth_headers):
        mock_service = AsyncMock()
        from app.application.dto.chat import ChatResponse
        mock_service.send_message.return_value = ChatResponse(
            response_text="Your seat is in section A5.",
            conversation_id=uuid4(),
            message_id=uuid4(),
            agent_name="FanAgent",
            confidence=0.92,
        )
        mock_get_service.return_value = mock_service

        response = client.post(
            "/api/v1/chat",
            json={"message": "Where is my seat?"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert "response_text" in data
        assert data["agent_name"] == "FanAgent"

    @patch("app.api.v1.routers.chat.get_chat_service")
    def test_send_message_with_conversation_id(self, mock_get_service, client, auth_headers):
        mock_service = AsyncMock()
        from app.application.dto.chat import ChatResponse
        mock_service.send_message.return_value = ChatResponse(
            response_text="Here is the food court info.",
            conversation_id=uuid4(),
            message_id=uuid4(),
            agent_name="FanAgent",
            confidence=0.85,
        )
        mock_get_service.return_value = mock_service

        response = client.post(
            "/api/v1/chat",
            json={
                "message": "Tell me about food options",
                "conversation_id": str(uuid4()),
            },
            headers=auth_headers,
        )
        assert response.status_code == 201

    def test_send_message_empty_body(self, client, auth_headers):
        response = client.post(
            "/api/v1/chat",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestGetConversations:
    def test_list_conversations_unauthenticated(self, client):
        response = client.get("/api/v1/chat/conversations")
        assert response.status_code == 401

    @patch("app.api.v1.routers.chat.ConversationRepository")
    @patch("app.api.v1.routers.chat.get_chat_service")
    def test_list_conversations_empty(
        self, mock_get_service, mock_repo_class, client, auth_headers
    ):
        mock_repo = AsyncMock()
        mock_repo.list_by_user.return_value = []
        mock_repo_class.return_value = mock_repo

        mock_service = AsyncMock()
        mock_get_service.return_value = mock_service

        response = client.get(
            "/api/v1/chat/conversations",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json() == []


class TestGetConversation:
    def test_get_conversation_unauthenticated(self, client):
        conv_id = uuid4()
        response = client.get(f"/api/v1/chat/conversations/{conv_id}")
        assert response.status_code == 401

    @patch("app.api.v1.routers.chat.get_chat_service")
    def test_get_conversation_not_found(self, mock_get_service, client, auth_headers):
        mock_service = AsyncMock()
        mock_service.get_conversation_history.return_value = None
        mock_get_service.return_value = mock_service

        conv_id = uuid4()
        response = client.get(
            f"/api/v1/chat/conversations/{conv_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @patch("app.api.v1.routers.chat.get_chat_service")
    def test_get_conversation_success(self, mock_get_service, client, auth_headers):
        from datetime import datetime, timezone
        from app.application.dto.chat import ConversationHistory, MessageDTO

        mock_service = AsyncMock()
        conv_id = uuid4()
        mock_service.get_conversation_history.return_value = ConversationHistory(
            conversation_id=conv_id,
            messages=[
                MessageDTO(
                    id=uuid4(),
                    sender_type="USER",
                    content="Hello",
                    message_type="TEXT",
                    created_at=datetime.now(timezone.utc),
                )
            ],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            status="ACTIVE",
            language="en",
            message_count=1,
        )
        mock_get_service.return_value = mock_service

        response = client.get(
            f"/api/v1/chat/conversations/{conv_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == str(conv_id)
        assert len(data["messages"]) == 1
