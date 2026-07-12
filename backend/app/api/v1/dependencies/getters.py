from __future__ import annotations

import logging
from typing import Any

from app.ai.router.agent_router import AgentRouter
from app.ai.services.generative_ai_service import GenerativeAIService
from app.ai.services.rag_service import RAGService
from app.application.services.alert_service import AlertService
from app.application.services.chat_service import ChatService
from app.application.services.dashboard_service import DashboardService
from app.application.services.event_service import EventService
from app.application.services.feedback_service import FeedbackService
from app.application.services.incident_service import IncidentService
from app.application.services.notification_service import NotificationService
from app.infrastructure.firestore.alert_repository import AlertRepository
from app.infrastructure.firestore.conversation_repository import ConversationRepository
from app.infrastructure.firestore.event_repository import EventRepository
from app.infrastructure.firestore.feedback_repository import FeedbackRepository
from app.infrastructure.firestore.incident_repository import IncidentRepository
from app.infrastructure.firestore.message_repository import MessageRepository
from app.infrastructure.firestore.stadium_repository import StadiumRepository
from app.infrastructure.firestore.user_repository import UserRepository
from app.services.identity.identity_service import IdentityService
from app.services.maps.maps_service import GoogleMapsService
from app.services.speech.speech_service import GoogleSpeechService
from app.services.translation.translation_service import GoogleTranslationService
from app.services.vision.vision_service import GoogleVisionService

logger = logging.getLogger(__name__)

_agent_router: AgentRouter | None = None
_generative_ai_service: GenerativeAIService | None = None
_rag_service: RAGService | None = None
_speech_service: GoogleSpeechService | None = None
_translation_service: GoogleTranslationService | None = None
_vision_service: GoogleVisionService | None = None
_maps_service: GoogleMapsService | None = None
_identity_service: IdentityService | None = None

_user_repo: UserRepository | None = None
_conversation_repo: ConversationRepository | None = None
_message_repo: MessageRepository | None = None
_alert_repo: AlertRepository | None = None
_incident_repo: IncidentRepository | None = None
_event_repo: EventRepository | None = None
_feedback_repo: FeedbackRepository | None = None
_stadium_repo: StadiumRepository | None = None


def _get_user_repo() -> UserRepository:
    global _user_repo
    if _user_repo is None:
        _user_repo = UserRepository()
    return _user_repo


def _get_conversation_repo() -> ConversationRepository:
    global _conversation_repo
    if _conversation_repo is None:
        _conversation_repo = ConversationRepository()
    return _conversation_repo


def _get_message_repo() -> MessageRepository:
    global _message_repo
    if _message_repo is None:
        _message_repo = MessageRepository()
    return _message_repo


def _get_alert_repo() -> AlertRepository:
    global _alert_repo
    if _alert_repo is None:
        _alert_repo = AlertRepository()
    return _alert_repo


def _get_incident_repo() -> IncidentRepository:
    global _incident_repo
    if _incident_repo is None:
        _incident_repo = IncidentRepository()
    return _incident_repo


def _get_event_repo() -> EventRepository:
    global _event_repo
    if _event_repo is None:
        _event_repo = EventRepository()
    return _event_repo


def _get_feedback_repo() -> FeedbackRepository:
    global _feedback_repo
    if _feedback_repo is None:
        _feedback_repo = FeedbackRepository()
    return _feedback_repo


def _get_stadium_repo() -> StadiumRepository:
    global _stadium_repo
    if _stadium_repo is None:
        _stadium_repo = StadiumRepository()
    return _stadium_repo


def get_agent_router() -> AgentRouter:
    global _agent_router
    if _agent_router is None:
        _agent_router = AgentRouter()
    return _agent_router


def get_generative_ai_service() -> GenerativeAIService:
    global _generative_ai_service
    if _generative_ai_service is None:
        _generative_ai_service = GenerativeAIService()
    return _generative_ai_service


def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service


def get_speech_service() -> GoogleSpeechService:
    global _speech_service
    if _speech_service is None:
        _speech_service = GoogleSpeechService()
    return _speech_service


def get_translation_service() -> GoogleTranslationService:
    global _translation_service
    if _translation_service is None:
        _translation_service = GoogleTranslationService()
    return _translation_service


def get_vision_service() -> GoogleVisionService:
    global _vision_service
    if _vision_service is None:
        _vision_service = GoogleVisionService()
    return _vision_service


def get_maps_service() -> GoogleMapsService:
    global _maps_service
    if _maps_service is None:
        _maps_service = GoogleMapsService()
    return _maps_service


def get_identity_service() -> IdentityService:
    global _identity_service
    if _identity_service is None:
        _identity_service = IdentityService()
    return _identity_service


def get_chat_service() -> ChatService:
    return ChatService(
        conversation_repo=_get_conversation_repo(),
        message_repo=_get_message_repo(),
        user_repo=_get_user_repo(),
        agent_router=get_agent_router(),
        generative_ai=get_generative_ai_service(),
        translation_service=get_translation_service(),
    )


def get_alert_service() -> AlertService:
    return AlertService(
        alert_repo=_get_alert_repo(),
        user_repo=_get_user_repo(),
    )


def get_incident_service() -> IncidentService:
    return IncidentService(
        incident_repo=_get_incident_repo(),
        user_repo=_get_user_repo(),
        alert_repo=_get_alert_repo(),
    )


def get_event_service() -> EventService:
    return EventService(
        event_repo=_get_event_repo(),
    )


def get_feedback_service() -> FeedbackService:
    return FeedbackService(
        feedback_repo=_get_feedback_repo(),
        generative_ai=get_generative_ai_service(),
    )


def get_dashboard_service() -> DashboardService:
    return DashboardService(
        stadium_repo=_get_stadium_repo(),
        user_repo=_get_user_repo(),
        alert_repo=_get_alert_repo(),
        incident_repo=_get_incident_repo(),
        event_repo=_get_event_repo(),
        conversation_repo=_get_conversation_repo(),
        feedback_repo=_get_feedback_repo(),
    )


def get_notification_service() -> NotificationService:
    return NotificationService(
        user_repo=_get_user_repo(),
    )
