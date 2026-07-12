from app.api.v1.routers.alerts import router as alerts_router
from app.api.v1.routers.chat import router as chat_router
from app.api.v1.routers.dashboard import router as dashboard_router
from app.api.v1.routers.events import router as events_router
from app.api.v1.routers.feedback import router as feedback_router
from app.api.v1.routers.incidents import router as incidents_router
from app.api.v1.routers.maps import router as maps_router
from app.api.v1.routers.notifications import router as notifications_router
from app.api.v1.routers.speech import router as speech_router
from app.api.v1.routers.translation import router as translation_router
from app.api.v1.routers.vision import router as vision_router

__all__ = [
    "alerts_router",
    "chat_router",
    "dashboard_router",
    "events_router",
    "feedback_router",
    "incidents_router",
    "maps_router",
    "notifications_router",
    "speech_router",
    "translation_router",
    "vision_router",
]
