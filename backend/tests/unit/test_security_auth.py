"""Tests for security authentication (JWT tokens)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.core.security.auth import (
    TokenPayload,
    create_access_token,
    create_refresh_token,
    get_current_user,
    verify_token,
)


@pytest.fixture
def mock_settings():
    with patch("app.core.security.auth.settings") as settings:
        settings.JWT_SECRET_KEY = "test-secret-key-for-testing-only-32chars!!"
        settings.JWT_ALGORITHM = "HS256"
        settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60
        settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7
        yield settings


class TestCreateAccessToken:
    def test_create_access_token(self, mock_settings):
        user_id = uuid4()
        token = create_access_token(user_id=user_id, role="FAN")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_access_token_contains_role(self, mock_settings):
        user_id = uuid4()
        token = create_access_token(user_id=user_id, role="ADMIN")
        payload = verify_token(token)
        assert payload.role == "ADMIN"
        assert payload.sub == str(user_id)

    def test_access_token_with_stadium_id(self, mock_settings):
        user_id = uuid4()
        stadium_id = uuid4()
        token = create_access_token(
            user_id=user_id,
            role="STAFF",
            stadium_id=stadium_id,
        )
        payload = verify_token(token)
        assert payload.stadium_id == str(stadium_id)

    def test_access_token_type_is_access(self, mock_settings):
        token = create_access_token(user_id=uuid4())
        payload = verify_token(token)
        assert payload.type == "access"

    def test_access_token_with_extra_claims(self, mock_settings):
        token = create_access_token(
            user_id=uuid4(),
            extra_claims={"custom_claim": "value"},
        )
        payload_dict = __import__("jose").jwt.decode(
            token,
            mock_settings.JWT_SECRET_KEY,
            algorithms=[mock_settings.JWT_ALGORITHM],
        )
        assert payload_dict["custom_claim"] == "value"


class TestCreateRefreshToken:
    def test_create_refresh_token(self, mock_settings):
        token = create_refresh_token(user_id=uuid4(), role="FAN")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_refresh_token_type(self, mock_settings):
        token = create_refresh_token(user_id=uuid4())
        payload = verify_token(token)
        assert payload.type == "refresh"

    def test_refresh_token_has_longer_expiry(self, mock_settings):
        access_token = create_access_token(user_id=uuid4())
        refresh_token = create_refresh_token(user_id=uuid4())

        access_payload = verify_token(access_token)
        refresh_payload = verify_token(refresh_token)

        assert refresh_payload.exp > access_payload.exp


class TestVerifyToken:
    def test_verify_valid_token(self, mock_settings):
        token = create_access_token(user_id=uuid4(), role="SECURITY")
        payload = verify_token(token)
        assert payload.role == "SECURITY"
        assert payload.type == "access"

    def test_verify_expired_token(self, mock_settings):
        import jose

        now = datetime.now(timezone.utc)
        expired = now - timedelta(hours=1)
        payload_dict = {
            "sub": str(uuid4()),
            "exp": expired,
            "iat": now,
            "type": "access",
            "role": "FAN",
            "stadium_id": None,
            "jti": "test",
        }
        token = jose.encode(
            payload_dict,
            mock_settings.JWT_SECRET_KEY,
            algorithm=mock_settings.JWT_ALGORITHM,
        )

        with pytest.raises(HTTPException) as exc_info:
            verify_token(token)
        assert exc_info.value.status_code == 401

    def test_verify_invalid_signature(self, mock_settings):
        import jose

        now = datetime.now(timezone.utc)
        payload_dict = {
            "sub": str(uuid4()),
            "exp": now + timedelta(hours=1),
            "iat": now,
            "type": "access",
            "role": "FAN",
            "stadium_id": None,
            "jti": "test",
        }
        token = jose.encode(
            payload_dict,
            "wrong-secret-key-12345678901234567890!!",
            algorithm=mock_settings.JWT_ALGORITHM,
        )

        with pytest.raises(HTTPException) as exc_info:
            verify_token(token)
        assert exc_info.value.status_code == 401

    def test_verify_malformed_token(self, mock_settings):
        with pytest.raises(HTTPException) as exc_info:
            verify_token("not.a.valid.jwt.token")
        assert exc_info.value.status_code == 401


class TestGetCurrentUser:
    @pytest.mark.asyncio
    async def test_get_current_user_with_valid_token(self, mock_settings):
        token = create_access_token(user_id=uuid4(), role="FAN")
        user = await get_current_user(token=token)
        assert user.type == "access"
        assert user.role == "FAN"

    @pytest.mark.asyncio
    async def test_get_current_user_no_token(self, mock_settings):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=None)
        assert exc_info.value.status_code == 401
        assert "Authentication required" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_refresh_token_rejected(self, mock_settings):
        token = create_refresh_token(user_id=uuid4())
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token)
        assert exc_info.value.status_code == 401
        assert "Invalid token type" in exc_info.value.detail


class TestTokenPayload:
    def test_token_payload_model(self):
        now = datetime.now(timezone.utc)
        payload = TokenPayload(
            sub=str(uuid4()),
            exp=now + timedelta(hours=1),
            iat=now,
            type="access",
            role="FAN",
            stadium_id=None,
            jti="test-123",
        )
        assert payload.type == "access"
        assert payload.role == "FAN"
        assert payload.jti == "test-123"
