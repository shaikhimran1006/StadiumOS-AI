"""Tests for exception handlers."""

from __future__ import annotations

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.core.exceptions.handlers import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    InternalServerException,
    NotFoundException,
    StadiumOSException,
    UnauthorizedException,
    ValidationException,
    AIServiceException,
    register_exception_handlers,
)


@pytest.fixture
def app():
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/test/not-found")
    async def not_found():
        raise NotFoundException(detail="User not found")

    @app.get("/test/bad-request")
    async def bad_request():
        raise BadRequestException(detail="Invalid input provided")

    @app.get("/test/unauthorized")
    async def unauthorized():
        raise UnauthorizedException(detail="Token expired")

    @app.get("/test/forbidden")
    async def forbidden():
        raise ForbiddenException(detail="Insufficient permissions")

    @app.get("/test/conflict")
    async def conflict():
        raise ConflictException(detail="Resource already exists")

    @app.get("/test/internal")
    async def internal():
        raise InternalServerException(detail="Database connection failed")

    @app.get("/test/validation")
    async def validation():
        raise ValidationException(detail="Field required")

    @app.get("/test/ai-service")
    async def ai_service():
        raise AIServiceException(detail="Gemini API unavailable")

    @app.get("/test/generic")
    async def generic():
        raise StadiumOSException(detail="Something went wrong", status_code=503, error_code="CUSTOM_ERROR")

    @app.get("/test/unhandled")
    async def unhandled():
        raise RuntimeError("Unexpected failure")

    return app


@pytest.fixture
def client(app):
    return TestClient(app, raise_server_exceptions=False)


class TestNotFoundHandler:
    def test_not_found_returns_404(self, client):
        response = client.get("/test/not-found")
        assert response.status_code == 404
        body = response.json()
        assert body["error"]["code"] == "NOT_FOUND"
        assert body["error"]["message"] == "User not found"
        assert "path" in body["error"]


class TestBadRequestHandler:
    def test_bad_request_returns_400(self, client):
        response = client.get("/test/bad-request")
        assert response.status_code == 400
        body = response.json()
        assert body["error"]["code"] == "BAD_REQUEST"
        assert "Invalid input" in body["error"]["message"]


class TestUnauthorizedHandler:
    def test_unauthorized_returns_401(self, client):
        response = client.get("/test/unauthorized")
        assert response.status_code == 401
        body = response.json()
        assert body["error"]["code"] == "UNAUTHORIZED"


class TestForbiddenHandler:
    def test_forbidden_returns_403(self, client):
        response = client.get("/test/forbidden")
        assert response.status_code == 403
        body = response.json()
        assert body["error"]["code"] == "FORBIDDEN"


class TestConflictHandler:
    def test_conflict_returns_409(self, client):
        response = client.get("/test/conflict")
        assert response.status_code == 409
        body = response.json()
        assert body["error"]["code"] == "CONFLICT"


class TestInternalServerHandler:
    def test_internal_returns_500(self, client):
        response = client.get("/test/internal")
        assert response.status_code == 500
        body = response.json()
        assert body["error"]["code"] == "INTERNAL_SERVER_ERROR"


class TestValidationHandler:
    def test_validation_returns_422(self, client):
        response = client.get("/test/validation")
        assert response.status_code == 422
        body = response.json()
        assert body["error"]["code"] == "VALIDATION_ERROR"


class TestAIServiceHandler:
    def test_ai_service_returns_502(self, client):
        response = client.get("/test/ai-service")
        assert response.status_code == 502
        body = response.json()
        assert body["error"]["code"] == "AI_SERVICE_ERROR"


class TestGenericExceptionHandler:
    def test_generic_exception_with_custom_status(self, client):
        response = client.get("/test/generic")
        assert response.status_code == 503
        body = response.json()
        assert body["error"]["code"] == "CUSTOM_ERROR"


class TestUnhandledExceptionHandler:
    def test_unhandled_returns_500(self, client):
        response = client.get("/test/unhandled")
        assert response.status_code == 500
        body = response.json()
        assert body["error"]["code"] == "INTERNAL_SERVER_ERROR"
        assert "unexpected" in body["error"]["message"].lower()


class TestStadiumOSExceptionDefaults:
    def test_base_exception_defaults(self):
        exc = StadiumOSException()
        assert exc.status_code == 500
        assert exc.detail == "An internal error occurred"
        assert exc.error_code == "INTERNAL_ERROR"

    def test_exception_custom_detail(self):
        exc = StadiumOSException(detail="Custom error")
        assert exc.detail == "Custom error"

    def test_exception_custom_status(self):
        exc = StadiumOSException(status_code=418)
        assert exc.status_code == 418

    def test_not_found_defaults(self):
        exc = NotFoundException()
        assert exc.status_code == 404

    def test_bad_request_defaults(self):
        exc = BadRequestException()
        assert exc.status_code == 400

    def test_unauthorized_defaults(self):
        exc = UnauthorizedException()
        assert exc.status_code == 401

    def test_forbidden_defaults(self):
        exc = ForbiddenException()
        assert exc.status_code == 403

    def test_conflict_defaults(self):
        exc = ConflictException()
        assert exc.status_code == 409

    def test_ai_service_defaults(self):
        exc = AIServiceException()
        assert exc.status_code == 502
