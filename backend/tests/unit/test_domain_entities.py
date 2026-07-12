"""Tests for domain entities."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.domain.entities.alert import Alert, AlertStatus, AlertType
from app.domain.entities.conversation import (
    Conversation,
    ConversationChannel,
    ConversationContext,
    ConversationStatus,
)
from app.domain.entities.event import Event, EventStatus, EventType
from app.domain.entities.feedback import Feedback, FeedbackCategory, FeedbackSource, FeedbackSentiment
from app.domain.entities.incident import (
    Incident,
    IncidentCategory,
    IncidentSeverity,
    IncidentStatus,
    Responder,
)
from app.domain.entities.message import Message, MessageMetadata, MessageType, SenderType
from app.domain.entities.stadium import (
    Facility,
    FacilityType,
    SectorConfig,
    Stadium,
    StadiumStatus,
)
from app.domain.entities.user import DeviceInfo, User, UserRole, UserStatus
from app.domain.value_objects.coordinates import LatLong
from app.domain.value_objects.gps_sector import GpsSector
from app.domain.value_objects.language import Language
from app.domain.value_objects.priority import Priority

from tests.conftest import (
    TEST_ALERT_ID,
    TEST_CONVERSATION_ID,
    TEST_EVENT_ID,
    TEST_STADIUM_ID,
    TEST_USER_ID,
)


# ═══════════════════════════════════════════════════════════════════════════
# Value Objects
# ═══════════════════════════════════════════════════════════════════════════

class TestLatLong:
    def test_create_valid_coordinates(self):
        coords = LatLong(latitude=40.7128, longitude=-74.0060)
        assert coords.latitude == 40.7128
        assert coords.longitude == -74.0060

    def test_latitude_out_of_range_raises(self):
        with pytest.raises(ValidationError):
            LatLong(latitude=91.0, longitude=0.0)

    def test_latitude_negative_out_of_range_raises(self):
        with pytest.raises(ValidationError):
            LatLong(latitude=-91.0, longitude=0.0)

    def test_longitude_out_of_range_raises(self):
        with pytest.raises(ValidationError):
            LatLong(latitude=0.0, longitude=181.0)

    def test_longitude_negative_out_of_range_raises(self):
        with pytest.raises(ValidationError):
            LatLong(latitude=0.0, longitude=-181.0)

    def test_rounding(self):
        coords = LatLong(latitude=40.7128123456, longitude=-74.0060987654)
        assert coords.latitude == 40.712812
        assert coords.longitude == -74.006099

    def test_distance_to_same_point(self):
        p = LatLong(latitude=40.7128, longitude=-74.0060)
        assert p.distance_to(p) == 0.0

    def test_distance_to_nearby_point(self):
        p1 = LatLong(latitude=40.7128, longitude=-74.0060)
        p2 = LatLong(latitude=40.7138, longitude=-74.0070)
        distance = p1.distance_to(p2)
        assert 50 < distance < 200

    def test_to_dict(self):
        coords = LatLong(latitude=40.7128, longitude=-74.0060)
        d = coords.to_dict()
        assert d == {"latitude": 40.7128, "longitude": -74.0060}

    def test_geojson_format(self):
        coords = LatLong(latitude=40.7128, longitude=-74.0060)
        geo = coords.model_dump_geojson()
        assert geo["type"] == "Point"
        assert geo["coordinates"] == [-74.0060, 40.7128]


class TestPriority:
    def test_priority_comparison(self):
        assert Priority.CRITICAL < Priority.HIGH < Priority.MEDIUM < Priority.LOW

    def test_from_label_valid(self):
        assert Priority.from_label("CRITICAL") == Priority.CRITICAL
        assert Priority.from_label("crit") == Priority.CRITICAL
        assert Priority.from_label("HIGH") == Priority.HIGH
        assert Priority.from_label("hi") == Priority.HIGH
        assert Priority.from_label("MEDIUM") == Priority.MEDIUM
        assert Priority.from_label("med") == Priority.MEDIUM
        assert Priority.from_label("LOW") == Priority.LOW
        assert Priority.from_label("lo") == Priority.LOW

    def test_from_label_invalid(self):
        with pytest.raises(ValueError, match="Unknown priority label"):
            Priority.from_label("URGENT")

    def test_label(self):
        assert Priority.CRITICAL.label() == "CRITICAL"
        assert Priority.HIGH.label() == "HIGH"

    def test_color_hex(self):
        assert Priority.CRITICAL.color_hex() == "#DC2626"
        assert Priority.HIGH.color_hex() == "#EA580C"
        assert Priority.MEDIUM.color_hex() == "#CA8A04"
        assert Priority.LOW.color_hex() == "#2563EB"

    def test_response_time_seconds(self):
        assert Priority.CRITICAL.response_time_seconds() == 30
        assert Priority.HIGH.response_time_seconds() == 120
        assert Priority.MEDIUM.response_time_seconds() == 300
        assert Priority.LOW.response_time_seconds() == 900


class TestLanguage:
    def test_default_language(self):
        assert Language.default() == Language.ENGLISH

    def test_from_bcp47_valid(self):
        assert Language.from_bcp47("en") == Language.ENGLISH
        assert Language.from_bcp47("es") == Language.SPANISH
        assert Language.from_bcp47("ar") == Language.ARABIC
        assert Language.from_bcp47("zh-CN") == Language.CHINESE_SIMPLIFIED

    def test_from_bcp47_invalid(self):
        with pytest.raises(ValueError, match="Unsupported language tag"):
            Language.from_bcp47("xx")

    def test_display_name(self):
        assert Language.ENGLISH.display_name() == "English"
        assert Language.ARABIC.display_name() == "Arabic"
        assert Language.JAPANESE.display_name() == "Japanese"

    def test_is_rtl(self):
        assert Language.ARABIC.is_rtl() is True
        assert Language.URDU.is_rtl() is True
        assert Language.ENGLISH.is_rtl() is False
        assert Language.SPANISH.is_rtl() is False


class TestGpsSector:
    def test_from_tier_and_slice(self):
        assert GpsSector.from_tier_and_slice("A", 1) == GpsSector.A1
        assert GpsSector.from_tier_and_slice("B", 10) == GpsSector.B10
        assert GpsSector.from_tier_and_slice("E", 20) == GpsSector.E20

    def test_from_tier_and_slice_invalid_slice(self):
        with pytest.raises(ValueError, match="Slice number must be between 1 and 20"):
            GpsSector.from_tier_and_slice("A", 0)
        with pytest.raises(ValueError, match="Slice number must be between 1 and 20"):
            GpsSector.from_tier_and_slice("A", 21)

    def test_tier_property(self):
        assert GpsSector.A1.tier == "A"
        assert GpsSector.C15.tier == "C"
        assert GpsSector.VIP.tier is None

    def test_slice_number_property(self):
        assert GpsSector.A1.slice_number == 1
        assert GpsSector.D20.slice_number == 20
        assert GpsSector.VIP.slice_number is None

    def test_is_seating(self):
        assert GpsSector.A1.is_seating() is True
        assert GpsSector.C10.is_seating() is True
        assert GpsSector.VIP.is_seating() is False
        assert GpsSector.PARKING_NORTH.is_seating() is False

    def test_tier_distance_from_field(self):
        assert GpsSector.A1.tier_distance_from_field() == 1
        assert GpsSector.B1.tier_distance_from_field() == 2
        assert GpsSector.C1.tier_distance_from_field() == 3
        assert GpsSector.D1.tier_distance_from_field() == 4
        assert GpsSector.E1.tier_distance_from_field() == 5
        assert GpsSector.VIP.tier_distance_from_field() is None


# ═══════════════════════════════════════════════════════════════════════════
# Entities
# ═══════════════════════════════════════════════════════════════════════════

class TestUser:
    def test_create_user(self):
        user = User(display_name="Alice")
        assert user.display_name == "Alice"
        assert user.role == UserRole.FAN
        assert user.status == UserStatus.ACTIVE
        assert user.preferred_language == Language.ENGLISH

    def test_display_name_required(self):
        with pytest.raises(ValidationError):
            User(display_name="")

    def test_user_role_assignment(self):
        user = User(display_name="Admin User", role=UserRole.ADMIN)
        assert user.role == UserRole.ADMIN
        assert user.is_staff() is True

    def test_user_role_fan_is_not_staff(self):
        user = User(display_name="Fan User", role=UserRole.FAN)
        assert user.is_staff() is False

    def test_can_manage_incidents(self):
        staff = User(display_name="Staff", role=UserRole.STAFF)
        admin = User(display_name="Admin", role=UserRole.ADMIN)
        security = User(display_name="Security", role=UserRole.SECURITY)
        fan = User(display_name="Fan", role=UserRole.FAN)

        assert staff.can_manage_incidents() is True
        assert admin.can_manage_incidents() is True
        assert security.can_manage_incidents() is True
        assert fan.can_manage_incidents() is False

    def test_update_location(self):
        user = User(display_name="Test")
        old_updated = user.updated_at
        loc = LatLong(latitude=40.7128, longitude=-74.0060)
        user.update_location(loc)
        assert user.current_location == loc
        assert user.updated_at >= old_updated

    def test_deactivate(self):
        user = User(display_name="Test")
        user.deactivate()
        assert user.status == UserStatus.DEACTIVATED

    def test_user_with_device_info(self):
        device = DeviceInfo(platform="ios", app_version="2.1.0", device_model="iPhone 15")
        user = User(display_name="Mobile User", device_info=device)
        assert user.device_info.platform == "ios"
        assert user.device_info.app_version == "2.1.0"


class TestConversation:
    def test_create_conversation(self, test_user):
        conv = Conversation(user_id=test_user.id)
        assert conv.status == ConversationStatus.ACTIVE
        assert conv.channel == ConversationChannel.IN_APP
        assert conv.language == Language.ENGLISH
        assert conv.message_count == 0

    def test_is_active(self, test_user):
        conv = Conversation(user_id=test_user.id)
        assert conv.is_active() is True

    def test_close(self, test_user):
        conv = Conversation(user_id=test_user.id)
        conv.close(summary="User got help")
        assert conv.status == ConversationStatus.CLOSED
        assert conv.ended_at is not None
        assert conv.summary == "User got help"

    def test_close_truncates_long_summary(self, test_user):
        conv = Conversation(user_id=test_user.id)
        long_summary = "A" * 3000
        conv.close(summary=long_summary)
        assert len(conv.summary) == 2000

    def test_transfer_to_agent(self, test_user):
        conv = Conversation(user_id=test_user.id)
        conv.transfer_to_agent(TEST_AGENT_ID)
        assert conv.status == ConversationStatus.TRANSFERRED
        assert conv.assigned_agent_id == TEST_AGENT_ID

    def test_increment_message_count(self, test_user):
        conv = Conversation(user_id=test_user.id)
        conv.increment_message_count()
        assert conv.message_count == 1
        assert conv.last_message_at is not None
        conv.increment_message_count()
        assert conv.message_count == 2

    def test_set_satisfaction(self, test_user):
        conv = Conversation(user_id=test_user.id)
        conv.set_satisfaction(4)
        assert conv.satisfaction_score == 4

    def test_set_satisfaction_out_of_range(self, test_user):
        conv = Conversation(user_id=test_user.id)
        with pytest.raises(ValueError, match="Satisfaction score must be between 1 and 5"):
            conv.set_satisfaction(6)
        with pytest.raises(ValueError, match="Satisfaction score must be between 1 and 5"):
            conv.set_satisfaction(0)

    def test_duration_seconds_none_when_active(self, test_user):
        conv = Conversation(user_id=test_user.id)
        assert conv.duration_seconds() is None

    def test_context(self):
        ctx = ConversationContext(
            stadium_id=uuid4(),
            event_id=uuid4(),
            sector="A5",
            entry_point="Gate 1",
        )
        assert ctx.sector == "A5"
        assert ctx.entry_point == "Gate 1"


class TestMessage:
    def test_create_user_message(self):
        msg = Message(
            conversation_id=uuid4(),
            sender_type=SenderType.USER,
            content="Hello, where is my seat?",
            message_type=MessageType.TEXT,
        )
        assert msg.is_from_user() is True
        assert msg.is_from_ai() is False
        assert msg.content == "Hello, where is my seat?"

    def test_create_ai_message(self):
        msg = Message(
            conversation_id=uuid4(),
            sender_type=SenderType.AI,
            content="Your seat is in section A5, row 12.",
        )
        assert msg.is_from_ai() is True
        assert msg.is_from_user() is False

    def test_content_required(self):
        with pytest.raises(ValidationError):
            Message(
                conversation_id=uuid4(),
                sender_type=SenderType.USER,
                content="",
            )

    def test_soft_delete(self):
        msg = Message(
            conversation_id=uuid4(),
            sender_type=SenderType.USER,
            content="test",
        )
        msg.soft_delete()
        assert msg.is_visible is False

    def test_set_feedback(self):
        msg = Message(
            conversation_id=uuid4(),
            sender_type=SenderType.AI,
            content="test",
        )
        msg.set_feedback("thumbs_up")
        assert msg.metadata.feedback_reaction == "thumbs_up"

    def test_safety_flagged(self):
        msg = Message(
            conversation_id=uuid4(),
            sender_type=SenderType.USER,
            content="dangerous content",
            metadata=MessageMetadata(safety_flagged=True),
        )
        assert msg.is_safety_flagged() is True

    def test_message_types(self):
        for msg_type in MessageType:
            msg = Message(
                conversation_id=uuid4(),
                sender_type=SenderType.USER,
                content="test",
                message_type=msg_type,
            )
            assert msg.message_type == msg_type


class TestAlert:
    def test_create_alert(self, test_alert):
        assert test_alert.alert_type == AlertType.SECURITY
        assert test_alert.priority == Priority.HIGH
        assert test_alert.status == AlertStatus.TRIGGERED
        assert test_alert.title == "Suspicious package in Sector B7"

    def test_alert_requires_title(self):
        with pytest.raises(ValidationError):
            Alert(
                alert_type=AlertType.MEDICAL,
                title="",
                description="Test",
                stadium_id=uuid4(),
            )

    def test_acknowledge(self):
        alert = Alert(
            alert_type=AlertType.MEDICAL,
            title="Test",
            description="Desc",
            stadium_id=uuid4(),
        )
        user_id = uuid4()
        alert.acknowledge(user_id)
        assert alert.status == AlertStatus.ACKNOWLEDGED
        assert alert.assigned_to_user_id == user_id
        assert alert.acknowledged_at is not None

    def test_resolve(self):
        alert = Alert(
            alert_type=AlertType.MEDICAL,
            title="Test",
            description="Desc",
            stadium_id=uuid4(),
        )
        alert.resolve()
        assert alert.status == AlertStatus.RESOLVED
        assert alert.resolved_at is not None

    def test_escalate(self):
        alert = Alert(
            alert_type=AlertType.SECURITY,
            title="Test",
            description="Desc",
            stadium_id=uuid4(),
            priority=Priority.MEDIUM,
            escalation_level=1,
        )
        alert.escalate()
        assert alert.escalation_level == 2
        assert alert.status == AlertStatus.ESCALATED

    def test_escalate_max_level(self):
        alert = Alert(
            alert_type=AlertType.SECURITY,
            title="Test",
            description="Desc",
            stadium_id=uuid4(),
            escalation_level=5,
        )
        with pytest.raises(ValueError, match="maximum escalation level"):
            alert.escalate()

    def test_cancel(self):
        alert = Alert(
            alert_type=AlertType.MEDICAL,
            title="Test",
            description="Desc",
            stadium_id=uuid4(),
        )
        alert.cancel()
        assert alert.status == AlertStatus.CANCELLED

    def test_is_active(self):
        for status in [AlertStatus.TRIGGERED, AlertStatus.ACKNOWLEDGED, AlertStatus.IN_PROGRESS, AlertStatus.ESCALATED]:
            alert = Alert(
                alert_type=AlertType.MEDICAL,
                title="Test",
                description="Desc",
                stadium_id=uuid4(),
                status=status,
            )
            assert alert.is_active() is True

        for status in [AlertStatus.RESOLVED, AlertStatus.CANCELLED]:
            alert = Alert(
                alert_type=AlertType.MEDICAL,
                title="Test",
                description="Desc",
                stadium_id=uuid4(),
                status=status,
            )
            assert alert.is_active() is False

    def test_response_time_none_when_not_acknowledged(self):
        alert = Alert(
            alert_type=AlertType.MEDICAL,
            title="Test",
            description="Desc",
            stadium_id=uuid4(),
        )
        assert alert.response_time_seconds() is None

    def test_resolution_time_none_when_not_resolved(self):
        alert = Alert(
            alert_type=AlertType.MEDICAL,
            title="Test",
            description="Desc",
            stadium_id=uuid4(),
        )
        assert alert.resolution_time_seconds() is None


class TestIncident:
    def test_create_incident(self, test_incident):
        assert test_incident.category == IncidentCategory.MEDICAL_EMERGENCY
        assert test_incident.severity == IncidentSeverity.SERIOUS
        assert test_incident.status == IncidentStatus.REPORTED

    def test_assign_responder(self):
        incident = Incident(
            category=IncidentCategory.SECURITY_THREAT,
            title="Fight",
            description="Two fans fighting",
            stadium_id=uuid4(),
        )
        responder_id = uuid4()
        incident.assign_responder(responder_id, "security")
        assert len(incident.responders) == 1
        assert incident.responders[0].user_id == responder_id
        assert incident.responders[0].role == "security"
        assert incident.status == IncidentStatus.DISPATCHED

    def test_mark_on_scene(self):
        responder_id = uuid4()
        incident = Incident(
            category=IncidentCategory.MEDICAL_EMERGENCY,
            title="Heart attack",
            description="Fan down",
            stadium_id=uuid4(),
        )
        incident.assign_responder(responder_id, "medical")
        incident.mark_on_scene(responder_id)
        assert incident.status == IncidentStatus.ON_SCENE
        assert incident.responders[0].arrived_at is not None

    def test_resolve(self):
        incident = Incident(
            category=IncidentCategory.OTHER,
            title="Test",
            description="Desc",
            stadium_id=uuid4(),
        )
        incident.resolve(notes="Resolved via mediation")
        assert incident.status == IncidentStatus.RESOLVED
        assert incident.resolution_notes == "Resolved via mediation"

    def test_close(self):
        incident = Incident(
            category=IncidentCategory.OTHER,
            title="Test",
            description="Desc",
            stadium_id=uuid4(),
        )
        incident.close()
        assert incident.status == IncidentStatus.CLOSED
        assert incident.closed_at is not None

    def test_escalate(self):
        incident = Incident(
            category=IncidentCategory.SECURITY_THREAT,
            title="Threat",
            description="Active threat",
            stadium_id=uuid4(),
        )
        incident.escalate()
        assert incident.status == IncidentStatus.ESCALATED

    def test_add_internal_note(self):
        incident = Incident(
            category=IncidentCategory.OTHER,
            title="Test",
            description="Desc",
            stadium_id=uuid4(),
        )
        incident.add_internal_note("Updated status")
        assert len(incident.internal_notes) == 1
        assert "Updated status" in incident.internal_notes[0]

    def test_is_active(self):
        active_statuses = [IncidentStatus.REPORTED, IncidentStatus.TRIAGED, IncidentStatus.DISPATCHED, IncidentStatus.ON_SCENE, IncidentStatus.UNDER_CONTROL, IncidentStatus.ESCALATED]
        for status in active_statuses:
            inc = Incident(
                category=IncidentCategory.OTHER,
                title="T",
                description="D",
                stadium_id=uuid4(),
                status=status,
            )
            assert inc.is_active() is True

        inactive_statuses = [IncidentStatus.RESOLVED, IncidentStatus.CLOSED]
        for status in inactive_statuses:
            inc = Incident(
                category=IncidentCategory.OTHER,
                title="T",
                description="D",
                stadium_id=uuid4(),
                status=status,
            )
            assert inc.is_active() is False

    def test_response_time_none_without_responders(self):
        incident = Incident(
            category=IncidentCategory.OTHER,
            title="T",
            description="D",
            stadium_id=uuid4(),
        )
        assert incident.response_time_seconds() is None


class TestEvent:
    def test_create_event(self, test_event):
        assert test_event.name == "FIFA World Cup 2026 - Group A"
        assert test_event.event_type == EventType.FOOTBALL_MATCH
        assert test_event.status == EventStatus.SCHEDULED

    def test_start(self):
        event = Event(name="Match", stadium_id=uuid4())
        event.start()
        assert event.status == EventStatus.IN_PROGRESS
        assert event.kickoff_at is not None

    def test_pause_halftime(self):
        event = Event(name="Match", stadium_id=uuid4())
        event.start()
        event.pause_halftime()
        assert event.status == EventStatus.HALFTIME

    def test_resume(self):
        event = Event(name="Match", stadium_id=uuid4())
        event.start()
        event.pause_halftime()
        event.resume()
        assert event.status == EventStatus.IN_PROGRESS

    def test_complete(self):
        event = Event(name="Match", stadium_id=uuid4())
        event.complete()
        assert event.status == EventStatus.COMPLETED
        assert event.actual_end_at is not None

    def test_cancel(self):
        event = Event(name="Match", stadium_id=uuid4())
        event.cancel()
        assert event.status == EventStatus.CANCELLED

    def test_postpone(self):
        event = Event(name="Match", stadium_id=uuid4())
        event.postpone()
        assert event.status == EventStatus.POSTPONED

    def test_is_live(self):
        event_in_progress = Event(name="Match", stadium_id=uuid4(), status=EventStatus.IN_PROGRESS)
        assert event_in_progress.is_live() is True

        event_halftime = Event(name="Match", stadium_id=uuid4(), status=EventStatus.HALFTIME)
        assert event_halftime.is_live() is True

        event_scheduled = Event(name="Match", stadium_id=uuid4(), status=EventStatus.SCHEDULED)
        assert event_scheduled.is_live() is False

    def test_attendance_percentage(self):
        event = Event(name="Match", stadium_id=uuid4(), expected_attendance=80000, actual_attendance=72000)
        assert event.attendance_percentage() == 90.0

    def test_attendance_percentage_none(self):
        event = Event(name="Match", stadium_id=uuid4(), expected_attendance=80000, actual_attendance=None)
        assert event.attendance_percentage() is None


class TestStadium:
    def test_create_stadium(self, test_stadium):
        assert test_stadium.name == "MetLife Stadium"
        assert test_stadium.total_capacity == 82500
        assert test_stadium.status == StadiumStatus.OPERATIONAL

    def test_total_occupancy(self, test_stadium):
        assert test_stadium.total_occupancy() == 3200

    def test_overall_occupancy_percentage(self, test_stadium):
        pct = test_stadium.overall_occupancy_percentage()
        assert pct == pytest.approx(3.9, abs=0.1)

    def test_open_sectors(self, test_stadium):
        open_sectors = test_stadium.open_sectors()
        assert len(open_sectors) == 4

    def test_get_sector(self, test_stadium):
        sector = test_stadium.get_sector(GpsSector.A1)
        assert sector is not None
        assert sector.capacity == 4000

    def test_get_sector_not_found(self, test_stadium):
        sector = test_stadium.get_sector(GpsSector.E20)
        assert sector is None

    def test_update_occupancy(self, test_stadium):
        test_stadium.update_occupancy(GpsSector.A1, 3500)
        sector = test_stadium.get_sector(GpsSector.A1)
        assert sector.current_occupancy == 3500

    def test_update_occupancy_invalid_sector(self, test_stadium):
        with pytest.raises(ValueError, match="not found"):
            test_stadium.update_occupancy(GpsSector.E20, 100)

    def test_facilities_by_type(self, test_stadium):
        entrance = test_stadium.facilities_by_type(FacilityType.ENTRANCE)
        assert len(entrance) == 1

    def test_sector_occupancy_percentage(self):
        sector = SectorConfig(seector=GpsSector.A1, capacity=100, tier="standard", current_occupancy=50)
        assert sector.occupancy_percentage() == 50.0

    def test_sector_occupancy_zero_capacity(self):
        sector = SectorConfig(sector=GpsSector.A1, capacity=0, tier="standard")
        assert sector.occupancy_percentage() == 0.0


class TestFeedback:
    def test_create_feedback(self, test_feedback):
        assert test_feedback.category == FeedbackCategory.FOOD_BEVERAGE
        assert test_feedback.rating == 4
        assert test_feedback.comment == "Loved the variety at the food court near Section A5."

    def test_rating_validation(self):
        with pytest.raises(ValidationError):
            Feedback(
                user_id=uuid4(),
                stadium_id=uuid4(),
                rating=6,
            )

    def test_rating_zero_invalid(self):
        with pytest.raises(ValidationError):
            Feedback(
                user_id=uuid4(),
                stadium_id=uuid4(),
                rating=0,
            )

    def test_respond(self):
        fb = Feedback(
            user_id=uuid4(),
            stadium_id=uuid4(),
            rating=2,
        )
        responder_id = uuid4()
        fb.respond("We apologize for the inconvenience.", responder_id)
        assert fb.response == "We apologize for the inconvenience."
        assert fb.responded_by_user_id == responder_id
        assert fb.responded_at is not None

    def test_respond_truncates_long_text(self):
        fb = Feedback(
            user_id=uuid4(),
            stadium_id=uuid4(),
            rating=1,
        )
        long_response = "X" * 3000
        fb.respond(long_response, uuid4())
        assert len(fb.response) == 2000

    def test_upvote(self):
        fb = Feedback(
            user_id=uuid4(),
            stadium_id=uuid4(),
            rating=5,
        )
        assert fb.upvotes == 0
        fb.upvote()
        assert fb.upvotes == 1
        fb.upvote()
        assert fb.upvotes == 2

    def test_rating_label(self):
        fb1 = Feedback(user_id=uuid4(), stadium_id=uuid4(), rating=1)
        assert fb1.rating_label() == "Very Poor"
        fb5 = Feedback(user_id=uuid4(), stadium_id=uuid4(), rating=5)
        assert fb5.rating_label() == "Excellent"

    def test_is_positive(self):
        fb_pos = Feedback(user_id=uuid4(), stadium_id=uuid4(), rating=4)
        assert fb_pos.is_positive() is True
        fb_neg = Feedback(user_id=uuid4(), stadium_id=uuid4(), rating=2)
        assert fb_neg.is_positive() is False

    def test_is_negative(self):
        fb_neg = Feedback(user_id=uuid4(), stadium_id=uuid4(), rating=2)
        assert fb_neg.is_negative() is True
        fb_pos = Feedback(user_id=uuid4(), stadium_id=uuid4(), rating=4)
        assert fb_pos.is_negative() is False
