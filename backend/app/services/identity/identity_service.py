from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

import httpx
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app.core.config.settings import settings
from app.core.security.auth import create_access_token, create_refresh_token

logger = logging.getLogger(__name__)

GOOGLE_OAUTH2_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"


class SessionData:
    def __init__(
        self,
        session_id: str,
        user_id: UUID,
        access_token: str,
        refresh_token: str,
        expires_at: datetime,
        created_at: datetime,
        user_info: dict[str, Any],
    ) -> None:
        self.session_id = session_id
        self.user_id = user_id
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expires_at = expires_at
        self.created_at = created_at
        self.user_info = user_info
        self.is_revoked = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": str(self.user_id),
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at.isoformat(),
            "created_at": self.created_at.isoformat(),
            "user_info": self.user_info,
            "is_revoked": self.is_revoked,
        }


class IdentityService:
    def __init__(self) -> None:
        self._sessions: dict[str, SessionData] = {}
        self._refresh_sessions: dict[str, str] = {}
        self._client: httpx.AsyncClient | None = None

    async def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def verify_google_token(self, token: str) -> dict[str, Any]:
        try:
            if settings.ENVIRONMENT == "development" and settings.OAUTH2_CLIENT_ID:
                idinfo = id_token.verify_oauth2_token(
                    token,
                    google_requests.Request(),
                    settings.OAUTH2_CLIENT_ID,
                )
            else:
                client = await self._ensure_client()
                response = await client.get(
                    GOOGLE_TOKENINFO_URL,
                    params={"access_token": token},
                )
                if response.status_code != 200:
                    raise ValueError("Invalid Google token")
                idinfo = response.json()

            user_info = {
                "external_id": idinfo.get("sub", ""),
                "email": idinfo.get("email", ""),
                "name": idinfo.get("name", ""),
                "picture": idinfo.get("picture", ""),
                "locale": idinfo.get("locale", "en"),
                "email_verified": idinfo.get("email_verified", False),
            }
            return user_info

        except Exception:
            logger.exception("Failed to verify Google token")
            raise

    async def get_user_info(self, access_token: str) -> dict[str, Any]:
        client = await self._ensure_client()
        response = await client.get(
            GOOGLE_OAUTH2_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if response.status_code != 200:
            raise ValueError("Failed to fetch user info from Google")

        return response.json()

    async def create_session(
        self,
        user_id: UUID,
        google_user_info: dict[str, Any],
        role: str = "FAN",
        stadium_id: UUID | None = None,
    ) -> SessionData:
        session_id = str(uuid4())
        now = datetime.now(timezone.utc)

        access_token = create_access_token(
            user_id=user_id, role=role, stadium_id=stadium_id
        )
        refresh_token = create_refresh_token(
            user_id=user_id, role=role, stadium_id=stadium_id
        )

        from datetime import timedelta

        session = SessionData(
            session_id=session_id,
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
            created_at=now,
            user_info=google_user_info,
        )

        self._sessions[session_id] = session
        self._refresh_sessions[refresh_token] = session_id

        logger.info("Session created: %s for user %s", session_id, user_id)
        return session

    async def refresh_session(self, refresh_token: str) -> SessionData | None:
        session_id = self._refresh_sessions.get(refresh_token)
        if session_id is None:
            logger.warning("Refresh token not recognized")
            return None

        session = self._sessions.get(session_id)
        if session is None:
            logger.warning("Session %s not found for refresh", session_id)
            return None

        if session.is_revoked:
            logger.warning("Attempted refresh on revoked session %s", session_id)
            return None

        new_access_token = create_access_token(
            user_id=session.user_id,
            role=session.user_info.get("role", "FAN"),
        )

        from datetime import timedelta

        now = datetime.now(timezone.utc)
        session.access_token = new_access_token
        session.expires_at = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

        logger.info("Session refreshed: %s", session_id)
        return session

    async def revoke_session(self, session_id: str) -> bool:
        session = self._sessions.get(session_id)
        if session is None:
            return False

        session.is_revoked = True
        self._refresh_sessions.pop(session.refresh_token, None)

        logger.info("Session revoked: %s", session_id)
        return True

    async def get_session(self, session_id: str) -> SessionData | None:
        session = self._sessions.get(session_id)
        if session and session.is_revoked:
            return None
        return session

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
