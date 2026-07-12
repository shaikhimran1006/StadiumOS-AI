"""Shared pytest fixtures for StadiumOS AI test suite."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
import pytest_asyncio


# ---------------------------------------------------------------------------
# Prevent real GCP calls during tests
# ---------------------------------------------------------------------------
os.environ.setdefault("GCP_PROJECT_ID", "test-project")
os.environ.setdefault("GCP_REGION", "us-central1")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only-32chars!!")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("FIRESTORE_EMULATOR_HOST", "localhost:8180")
os.environ.setdefault("PUBSUB_EMULATOR_HOST", "localhost:8280")


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------
from app.domain.value_objects.coordinates import LatLong
from app.domain.value_objects.gps_sector import GpsSector
from app.domain.value_objects.language import Language
from app.domain.value_objects.priority import Priority


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
from app.domain.entities.user import User, UserRole, UserStatus, DeviceInfo
from app.domain.entities.conversation import (
    Conversation,
    ConversationChannel,
    ConversationContext,
    ConversationStatus,
)
from app.domain.entities.message import Message, MessageMetadata, MessageType, SenderType
from app.domain.entities.alert import Alert, AlertStatus, AlertType
from app.domain.entities.incident import (
    Incident,
    IncidentCategory,
    IncidentSeverity,
    IncidentStatus,
)
from app.domain.entities.event import Event, EventType, EventStatus
from app.domain.entities.stadium import Stadium, StadiumStatus, SectorConfig, Facility, FacilityType
from app.domain.entities.feedback import Feedback, FeedbackCategory, FeedbackSource


# ---------------------------------------------------------------------------
# Repository mocks
# ---------------------------------------------------------------------------
from app.domain.interfaces.repositories import (
    IConversationRepository,
    IMessageRepository,
    IAlertRepository,
    IIncidentRepository,
    IEventRepository,
    IStadiumRepository,
    IUserRepository,
    IFeedbackRepository,
)
from app.domain.interfaces.external_services import IPubSubService, IBigQueryService, ITranslationService
from app.domain.interfaces.ai_services import IGenerativeAIService


# ── UUID constants ──────────────────────────────────────────────────────────
TEST_USER_ID = UUID("11111111-1111-1111-1111-111111111111")
TEST_STADIUM_ID = UUID("22222222-2222-2222-2222-222222222222")
TEST_EVENT_ID = UUID("33333333-3333-3333-3333-333333333333")
TEST_CONVERSATION_ID = UUID("44444444-4444-4444-4444-444444444444")
TEST_ALERT_ID = UUID("55555555-5555-5555-5555-555555555555")
TEST_INCIDENT_ID = UUID("66666666-6666-6666-6666-666666666666")
TEST_AGENT_ID = UUID("77777777-7777-7777-7777-777777777777")


# ── Settings fixture ────────────────────────────────────────────────────────
@pytest.fixture
def get_test_settings():
    from app.core.config.settings import Settings
    return Settings(
        APP_NAME="StadiumOS AI Test",
        APP_VERSION="0.0.1-test",
        ENVIRONMENT="development",
        DEBUG=True,
        GCP_PROJECT_ID="test-project",
        GCP_REGION="us-central1",
        JWT_SECRET_KEY="test-secret-key-for-testing-only-32chars!!",
        JWT_ALGORITHM="HS256",
        JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60,
        JWT_REFRESH_TOKEN_EXPIRE_DAYS=7,
        STADIUM_ID="test-stadium",
        STADIUM_NAME="Test Stadium",
    )


# ── Entity fixtures ─────────────────────────────────────────────────────────
@pytest.fixture
def test_user() -> User:
    return User(
        id=TEST_USER_ID,
        external_id="google-uid-123",
        email="fan@example.com",
        phone="+15551234567",
        display_name="Test Fan",
        role=UserRole.FAN,
        status=UserStatus.ACTIVE,
        preferred_language=Language.ENGLISH,
        home_stadium_id=TEST_STADIUM_ID,
        accessible_seating=False,
        emergency_contact_name="Jane Doe",
        emergency_contact_phone="+15559876543",
    )


@pytest.fixture
def test_staff_user() -> User:
    return User(
        id=uuid4(),
        display_name="Security Officer",
        role=UserRole.SECURITY,
        status=UserStatus.ACTIVE,
        preferred_language=Language.ENGLISH,
        home_stadium_id=TEST_STADIUM_ID,
        assigned_sector=GpsSector.A1,
    )


@pytest.fixture
def test_conversation(test_user: User) -> Conversation:
    return Conversation(
        id=TEST_CONVERSATION_ID,
        user_id=test_user.id,
        channel=ConversationChannel.IN_APP,
        status=ConversationStatus.ACTIVE,
        language=Language.ENGLISH,
        context=ConversationContext(
            stadium_id=TEST_STADIUM_ID,
            event_id=TEST_EVENT_ID,
            sector="A5",
        ),
        message_count=0,
    )


@pytest.fixture
def test_alert() -> Alert:
    return Alert(
        id=TEST_ALERT_ID,
        alert_type=AlertType.SECURITY,
        priority=Priority.HIGH,
        status=AlertStatus.TRIGGERED,
        title="Suspicious package in Sector B7",
        description="Unattended black bag reported near Gate 4 entrance in sector B7.",
        stadium_id=TEST_STADIUM_ID,
        event_id=TEST_EVENT_ID,
        sector=GpsSector.B7,
        location=LatLong(latitude=40.7128, longitude=-74.0060),
        triggered_by_user_id=TEST_USER_ID,
        triggered_by_ai=True,
        ai_confidence=0.87,
        affected_sectors=[GpsSector.B7, GpsSector.B8],
    )


@pytest.fixture
def test_event() -> Event:
    return Event(
        id=TEST_EVENT_ID,
        name="FIFA World Cup 2026 - Group A",
        event_type=EventType.FOOTBALL_MATCH,
        status=EventStatus.SCHEDULED,
        stadium_id=TEST_STADIUM_ID,
        home_team="USA",
        away_team="England",
        competition="FIFA World Cup 2026",
        expected_attendance=82000,
        ticket_tiers=["VIP", "STANDARD", "GENERAL"],
        tags=["world-cup", "group-stage"],
    )


@pytest.fixture
def test_stadium() -> Stadium:
    return Stadium(
        id=TEST_STADIUM_ID,
        name="MetLife Stadium",
        city="East Rutherford",
        country="United States",
        country_code="USA",
        timezone="America/New_York",
        status=StadiumStatus.OPERATIONAL,
        location=LatLong(latitude=40.8135, longitude=-74.0745),
        address="1 MetLife Stadium Dr, East Rutherford, NJ 07073",
        total_capacity=82500,
        seated_capacity=82500,
        vip_capacity=2500,
        press_capacity=500,
        accessible_capacity=1000,
        sectors=[
            SectorConfig(sector=GpsSector.A1, capacity=4000, tier="standard", current_occupancy=3200),
            SectorConfig(sector=GpsSector.A5, capacity=4000, tier="vip", accessible_seating=False),
            SectorConfig(sector=GpsSector.B1, capacity=4500, tier="standard"),
            SectorConfig(sector=GpsSector.C1, capacity=5000, tier="standard"),
        ],
        facilities=[
            Facility(name="Main Entrance", facility_type=FacilityType.ENTRANCE, sector=GpsSector.GATE_1 if hasattr(GpsSector, "GATE_1") else GpsSector.A1),
        ],
        gates=["Gate 1", "Gate 2", "Gate 3", "Gate 4"],
        year_built=2010,
        last_renovation_year=2022,
        field_surface="hybrid",
        roof_type="open",
        parking_capacity=20000,
        wifi_available=True,
        cell_signal_booster=True,
    )


@pytest.fixture
def test_incident(test_user: User) -> Incident:
    return Incident(
        id=TEST_INCIDENT_ID,
        category=IncidentCategory.MEDICAL_EMERGENCY,
        severity=IncidentSeverity.SERIOUS,
        priority=Priority.HIGH,
        status=IncidentStatus.REPORTED,
        title="Fan collapsed in Sector C3",
        description="Male fan in his 50s collapsed while walking to seat. Conscious but disoriented.",
        stadium_id=TEST_STADIUM_ID,
        event_id=TEST_EVENT_ID,
        sector=GpsSector.C3,
        location=LatLong(latitude=40.7130, longitude=-74.0062),
        reported_by_user_id=test_user.id,
        people_involved=1,
        injuries_reported=1,
    )


@pytest.fixture
def test_feedback(test_user: User) -> Feedback:
    return Feedback(
        id=uuid4(),
        user_id=test_user.id,
        event_id=TEST_EVENT_ID,
        stadium_id=TEST_STADIUM_ID,
        category=FeedbackCategory.FOOD_BEVERAGE,
        source=FeedbackSource.IN_APP,
        rating=4,
        title="Great food options",
        comment="Loved the variety at the food court near Section A5.",
        sector=GpsSector.A5,
        tags=["food", "positive"],
    )


# ── Repository mock fixtures ────────────────────────────────────────────────
@pytest_asyncio.fixture
async def mock_user_repo() -> AsyncMock:
    repo = AsyncMock(spec=IUserRepository)
    return repo


@pytest_asyncio.fixture
async def mock_conversation_repo() -> AsyncMock:
    repo = AsyncMock(spec=IConversationRepository)
    return repo


@pytest_asyncio.fixture
async def mock_message_repo() -> AsyncMock:
    repo = AsyncMock(spec=IMessageRepository)
    return repo


@pytest_asyncio.fixture
async def mock_alert_repo() -> AsyncMock:
    repo = AsyncMock(spec=IAlertRepository)
    return repo


@pytest_asyncio.fixture
async def mock_incident_repo() -> AsyncMock:
    repo = AsyncMock(spec=IIncidentRepository)
    return repo


@pytest_asyncio.fixture
async def mock_event_repo() -> AsyncMock:
    repo = AsyncMock(spec=IEventRepository)
    return repo


@pytest_asyncio.fixture
async def mock_stadium_repo() -> AsyncMock:
    repo = AsyncMock(spec=IStadiumRepository)
    return repo


@pytest_asyncio.fixture
async def mock_feedback_repo() -> AsyncMock:
    repo = AsyncMock(spec=IFeedbackRepository)
    return repo


@pytest_asyncio.fixture
async def mock_pubsub_client() -> AsyncMock:
    return AsyncMock(spec=IPubSubService)


@pytest_asyncio.fixture
async def mock_bigquery_client() -> AsyncMock:
    return AsyncMock(spec=IBigQueryService)


@pytest_asyncio.fixture
async def mock_firestore_client() -> AsyncMock:
    client = MagicMock()
    client.collection.return_value = MagicMock()
    client.collection.return_value.document.return_value = MagicMock()
    client.collection.return_value.document.return_value.set = MagicMock()
    client.collection.return_value.document.return_value.get = MagicMock()
    client.collection.return_value.document.return_value.update = MagicMock()
    client.collection.return_value.document.return_value.delete = MagicMock()
    client.collection.return_value.limit.return_value = MagicMock()
    client.collection.return_value.limit.return_value.get.return_value = []
    return client


@pytest_asyncio.fixture
async def mock_translation_service() -> AsyncMock:
    from app.domain.interfaces.external_services import TranslationResult
    service = AsyncMock(spec=ITranslationService)
    service.translate.return_value = TranslationResult(
        translated_text="Hello, how are you?",
        source_language="es",
        target_language="en",
        confidence=0.95,
    )
    return service


@pytest_asyncio.fixture
async def mock_generative_ai() -> AsyncMock:
    service = AsyncMock(spec=IGenerativeAIService)
    service.generate_response.return_value = "I can help you with that!"
    return service


# ── FastAPI TestClient fixture ──────────────────────────────────────────────
@pytest.fixture
def test_client():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.core.exceptions.handlers import register_exception_handlers
    from app.api.v1.router import api_router

    app = FastAPI(title="StadiumOS AI Test")
    app.include_router(api_router, prefix="/api/v1")
    register_exception_handlers(app)

    @app.get("/health")
    async def health():
        return {"status": "healthy", "service": "test"}

    client = TestClient(app)
    return client
