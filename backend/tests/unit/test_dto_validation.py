"""Tests for DTO validation."""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from app.application.dto.alerts import AlertCreateRequest, AlertListResponse, AlertResponse
from app.application.dto.chat import ChatRequest, ChatResponse, ConversationHistory, MessageDTO
from app.application.dto.events import EventCreateRequest, EventListResponse, EventResponse
from app.application.dto.feedback import FeedbackAnalytics, FeedbackCreateRequest, FeedbackResponse
from app.application.dto.incidents import IncidentCreateRequest, IncidentListResponse, IncidentResponse, ResponderDTO
from app.domain.value_objects.gps_sector import GpsSector
from app.domain.value_objects.priority import Priority


# ═══════════════════════════════════════════════════════════════════════════
# ChatRequest
# ═══════════════════════════════════════════════════════════════════════════

class TestChatRequest:
    def test_valid_request(self):
        req = ChatRequest(message="Hello!")
        assert req.message == "Hello!"
        assert req.conversation_id is None
        assert req.language == "en"
        assert req.message_type == "TEXT"

    def test_message_required(self):
        with pytest.raises(ValidationError):
            ChatRequest(message="")

    def test_message_too_long(self):
        with pytest.raises(ValidationError):
            ChatRequest(message="A" * 10001)

    def test_message_max_length(self):
        req = ChatRequest(message="A" * 10000)
        assert len(req.message) == 10000

    def test_with_conversation_id(self):
        conv_id = uuid4()
        req = ChatRequest(message="Continue", conversation_id=conv_id)
        assert req.conversation_id == conv_id

    def test_with_context(self):
        ctx = {"stadium_id": str(uuid4()), "sector": "A5"}
        req = ChatRequest(message="Where is A5?", context=ctx)
        assert req.context["sector"] == "A5"

    def test_language_override(self):
        req = ChatRequest(message="Hola", language="es")
        assert req.language == "es"


# ═══════════════════════════════════════════════════════════════════════════
# AlertCreateRequest
# ═══════════════════════════════════════════════════════════════════════════

class TestAlertCreateRequest:
    def test_valid_request(self):
        req = AlertCreateRequest(
            alert_type="SECURITY",
            title="Suspicious activity",
            description="Person acting suspiciously near Gate 3",
            stadium_id=uuid4(),
        )
        assert req.alert_type == "SECURITY"
        assert req.priority == Priority.MEDIUM

    def test_title_required(self):
        with pytest.raises(ValidationError):
            AlertCreateRequest(
                alert_type="MEDICAL",
                title="",
                description="Desc",
                stadium_id=uuid4(),
            )

    def test_title_too_long(self):
        with pytest.raises(ValidationError):
            AlertCreateRequest(
                alert_type="MEDICAL",
                title="A" * 201,
                description="Desc",
                stadium_id=uuid4(),
            )

    def test_description_required(self):
        with pytest.raises(ValidationError):
            AlertCreateRequest(
                alert_type="MEDICAL",
                title="Alert",
                description="",
                stadium_id=uuid4(),
            )

    def test_ai_confidence_bounds(self):
        req = AlertCreateRequest(
            alert_type="SECURITY",
            title="Test",
            description="Desc",
            stadium_id=uuid4(),
            triggered_by_ai=True,
            ai_confidence=0.95,
        )
        assert req.ai_confidence == 0.95

    def test_ai_confidence_out_of_range(self):
        with pytest.raises(ValidationError):
            AlertCreateRequest(
                alert_type="SECURITY",
                title="Test",
                description="Desc",
                stadium_id=uuid4(),
                ai_confidence=1.5,
            )

    def test_with_sector_and_location(self):
        from app.domain.value_objects.coordinates import LatLong
        req = AlertCreateRequest(
            alert_type="FIRE",
            title="Smoke detected",
            description="Smoke coming from food court",
            stadium_id=uuid4(),
            sector=GpsSector.A5,
            location=LatLong(latitude=40.71, longitude=-74.00),
            priority=Priority.HIGH,
        )
        assert req.sector == GpsSector.A5
        assert req.priority == Priority.HIGH


# ═══════════════════════════════════════════════════════════════════════════
# IncidentCreateRequest
# ═══════════════════════════════════════════════════════════════════════════

class TestIncidentCreateRequest:
    def test_valid_request(self):
        req = IncidentCreateRequest(
            category="MEDICAL_EMERGENCY",
            title="Fan injured",
            description="Fan fell from seat",
            stadium_id=uuid4(),
        )
        assert req.category == "MEDICAL_EMERGENCY"
        assert req.severity == "MODERATE"

    def test_title_min_length(self):
        with pytest.raises(ValidationError):
            IncidentCreateRequest(
                category="OTHER",
                title="",
                description="Desc",
                stadium_id=uuid4(),
            )

    def test_description_max_length(self):
        with pytest.raises(ValidationError):
            IncidentCreateRequest(
                category="OTHER",
                title="Test",
                description="A" * 5001,
                stadium_id=uuid4(),
            )

    def test_people_involved_non_negative(self):
        req = IncidentCreateRequest(
            category="CROWD_DISORDER",
            title="Fight",
            description="Multiple people fighting",
            stadium_id=uuid4(),
            people_involved=5,
            injuries_reported=2,
        )
        assert req.people_involved == 5
        assert req.injuries_reported == 2

    def test_people_involved_negative(self):
        with pytest.raises(ValidationError):
            IncidentCreateRequest(
                category="OTHER",
                title="T",
                description="D",
                stadium_id=uuid4(),
                people_involved=-1,
            )

    def test_with_tags(self):
        req = IncidentCreateRequest(
            category="SECURITY_THREAT",
            title="Threat",
            description="Active threat",
            stadium_id=uuid4(),
            tags=["vip", "critical"],
            public_visibility=False,
        )
        assert "vip" in req.tags


# ═══════════════════════════════════════════════════════════════════════════
# EventCreateRequest
# ═══════════════════════════════════════════════════════════════════════════

class TestEventCreateRequest:
    def test_valid_request(self):
        req = EventCreateRequest(
            name="Champions League Final",
            stadium_id=uuid4(),
        )
        assert req.name == "Champions League Final"
        assert req.event_type == "FOOTBALL_MATCH"

    def test_name_required(self):
        with pytest.raises(ValidationError):
            EventCreateRequest(name="", stadium_id=uuid4())

    def test_name_too_long(self):
        with pytest.raises(ValidationError):
            EventCreateRequest(name="A" * 301, stadium_id=uuid4())

    def test_with_team_names(self):
        req = EventCreateRequest(
            name="El Clasico",
            stadium_id=uuid4(),
            home_team="Real Madrid",
            away_team="Barcelona",
            competition="La Liga",
        )
        assert req.home_team == "Real Madrid"
        assert req.away_team == "Barcelona"

    def test_expected_attendance_non_negative(self):
        req = EventCreateRequest(
            name="Match",
            stadium_id=uuid4(),
            expected_attendance=80000,
        )
        assert req.expected_attendance == 80000


# ═══════════════════════════════════════════════════════════════════════════
# FeedbackCreateRequest
# ═══════════════════════════════════════════════════════════════════════════

class TestFeedbackCreateRequest:
    def test_valid_request(self):
        req = FeedbackCreateRequest(
            rating=5,
            stadium_id=uuid4(),
        )
        assert req.rating == 5
        assert req.category == "GENERAL"

    def test_rating_too_low(self):
        with pytest.raises(ValidationError):
            FeedbackCreateRequest(rating=0, stadium_id=uuid4())

    def test_rating_too_high(self):
        with pytest.raises(ValidationError):
            FeedbackCreateRequest(rating=6, stadium_id=uuid4())

    def test_comment_max_length(self):
        req = FeedbackCreateRequest(
            rating=4,
            stadium_id=uuid4(),
            comment="A" * 5000,
        )
        assert len(req.comment) == 5000

    def test_with_sector(self):
        req = FeedbackCreateRequest(
            rating=3,
            stadium_id=uuid4(),
            sector=GpsSector.B5,
            category="FOOD_BEVERAGE",
            anonymous=True,
        )
        assert req.sector == GpsSector.B5
        assert req.anonymous is True


# ═══════════════════════════════════════════════════════════════════════════
# Response DTOs
# ═══════════════════════════════════════════════════════════════════════════

class TestChatResponse:
    def test_valid_response(self):
        from datetime import datetime, timezone
        resp = ChatResponse(
            response_text="Your seat is in A5",
            conversation_id=uuid4(),
            message_id=uuid4(),
            agent_name="FanAgent",
            confidence=0.92,
        )
        assert resp.confidence == 0.92

    def test_confidence_bounds(self):
        with pytest.raises(ValidationError):
            ChatResponse(
                response_text="Hi",
                conversation_id=uuid4(),
                message_id=uuid4(),
                agent_name="FanAgent",
                confidence=1.5,
            )


class TestAlertListResponse:
    def test_default_values(self):
        resp = AlertListResponse()
        assert resp.alerts == []
        assert resp.total_count == 0
        assert resp.page == 1

    def test_page_validation(self):
        with pytest.raises(ValidationError):
            AlertListResponse(page=0)


class TestIncidentListResponse:
    def test_default_values(self):
        resp = IncidentListResponse()
        assert resp.incidents == []
        assert resp.total_count == 0


class TestEventListResponse:
    def test_default_values(self):
        resp = EventListResponse()
        assert resp.events == []
        assert resp.total_count == 0

    def test_page_size_bounds(self):
        with pytest.raises(ValidationError):
            EventListResponse(page_size=101)


class TestFeedbackAnalytics:
    def test_default_values(self):
        analytics = FeedbackAnalytics()
        assert analytics.total_count == 0
        assert analytics.average_rating == 0.0
        assert analytics.response_rate == 0.0
