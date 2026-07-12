from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from app.domain.entities.alert import Alert, AlertStatus, AlertType
from app.domain.entities.conversation import Conversation, ConversationStatus
from app.domain.entities.event import Event, EventStatus
from app.domain.entities.feedback import Feedback, FeedbackCategory
from app.domain.entities.incident import Incident, IncidentStatus
from app.domain.entities.message import Message
from app.domain.entities.stadium import Stadium
from app.domain.entities.user import User, UserRole, UserStatus
from app.domain.value_objects.priority import Priority


class IUserRepository(ABC):
    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None: ...

    @abstractmethod
    async def get_by_external_id(self, external_id: str) -> User | None: ...

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    async def get_by_phone(self, phone: str) -> User | None: ...

    @abstractmethod
    async def create(self, user: User) -> User: ...

    @abstractmethod
    async def update(self, user: User) -> User: ...

    @abstractmethod
    async def delete(self, user_id: UUID) -> bool: ...

    @abstractmethod
    async def list_by_role(
        self, role: UserRole, offset: int = 0, limit: int = 50
    ) -> list[User]: ...

    @abstractmethod
    async def list_by_status(
        self, status: UserStatus, offset: int = 0, limit: int = 50
    ) -> list[User]: ...

    @abstractmethod
    async def list_by_stadium(
        self, stadium_id: UUID, offset: int = 0, limit: int = 50
    ) -> list[User]: ...

    @abstractmethod
    async def search(self, query: str, offset: int = 0, limit: int = 50) -> list[User]: ...

    @abstractmethod
    async def count_by_role(self, role: UserRole) -> int: ...

    @abstractmethod
    async def count_by_stadium(self, stadium_id: UUID) -> int: ...


class IConversationRepository(ABC):
    @abstractmethod
    async def get_by_id(self, conversation_id: UUID) -> Conversation | None: ...

    @abstractmethod
    async def create(self, conversation: Conversation) -> Conversation: ...

    @abstractmethod
    async def update(self, conversation: Conversation) -> Conversation: ...

    @abstractmethod
    async def list_by_user(
        self, user_id: UUID, offset: int = 0, limit: int = 50
    ) -> list[Conversation]: ...

    @abstractmethod
    async def list_by_status(
        self, status: ConversationStatus, offset: int = 0, limit: int = 50
    ) -> list[Conversation]: ...

    @abstractmethod
    async def list_active_by_user(self, user_id: UUID) -> list[Conversation]: ...

    @abstractmethod
    async def list_by_stadium(
        self, stadium_id: UUID, offset: int = 0, limit: int = 50
    ) -> list[Conversation]: ...

    @abstractmethod
    async def count_active(self) -> int: ...

    @abstractmethod
    async def count_by_stadium(self, stadium_id: UUID) -> int: ...


class IMessageRepository(ABC):
    @abstractmethod
    async def get_by_id(self, message_id: UUID) -> Message | None: ...

    @abstractmethod
    async def create(self, message: Message) -> Message: ...

    @abstractmethod
    async def update(self, message: Message) -> Message: ...

    @abstractmethod
    async def list_by_conversation(
        self, conversation_id: UUID, offset: int = 0, limit: int = 100
    ) -> list[Message]: ...

    @abstractmethod
    async def list_recent_by_conversation(
        self, conversation_id: UUID, limit: int = 20
    ) -> list[Message]: ...

    @abstractmethod
    async def count_by_conversation(self, conversation_id: UUID) -> int: ...

    @abstractmethod
    async def search_in_conversation(
        self, conversation_id: UUID, query: str, limit: int = 20
    ) -> list[Message]: ...


class IAlertRepository(ABC):
    @abstractmethod
    async def get_by_id(self, alert_id: UUID) -> Alert | None: ...

    @abstractmethod
    async def create(self, alert: Alert) -> Alert: ...

    @abstractmethod
    async def update(self, alert: Alert) -> Alert: ...

    @abstractmethod
    async def list_active(self, offset: int = 0, limit: int = 50) -> list[Alert]: ...

    @abstractmethod
    async def list_by_status(
        self, status: AlertStatus, offset: int = 0, limit: int = 50
    ) -> list[Alert]: ...

    @abstractmethod
    async def list_by_type(
        self, alert_type: AlertType, offset: int = 0, limit: int = 50
    ) -> list[Alert]: ...

    @abstractmethod
    async def list_by_stadium(
        self, stadium_id: UUID, offset: int = 0, limit: int = 50
    ) -> list[Alert]: ...

    @abstractmethod
    async def list_by_priority(
        self, priority: Priority, offset: int = 0, limit: int = 50
    ) -> list[Alert]: ...

    @abstractmethod
    async def count_active(self) -> int: ...

    @abstractmethod
    async def count_active_by_stadium(self, stadium_id: UUID) -> int: ...


class IEventRepository(ABC):
    @abstractmethod
    async def get_by_id(self, event_id: UUID) -> Event | None: ...

    @abstractmethod
    async def create(self, event: Event) -> Event: ...

    @abstractmethod
    async def update(self, event: Event) -> Event: ...

    @abstractmethod
    async def list_by_stadium(
        self, stadium_id: UUID, offset: int = 0, limit: int = 50
    ) -> list[Event]: ...

    @abstractmethod
    async def list_by_status(
        self, status: EventStatus, offset: int = 0, limit: int = 50
    ) -> list[Event]: ...

    @abstractmethod
    async def list_live(self) -> list[Event]: ...

    @abstractmethod
    async def list_upcoming(
        self, stadium_id: UUID | None = None, offset: int = 0, limit: int = 50
    ) -> list[Event]: ...

    @abstractmethod
    async def count_by_stadium(self, stadium_id: UUID) -> int: ...


class IStadiumRepository(ABC):
    @abstractmethod
    async def get_by_id(self, stadium_id: UUID) -> Stadium | None: ...

    @abstractmethod
    async def create(self, stadium: Stadium) -> Stadium: ...

    @abstractmethod
    async def update(self, stadium: Stadium) -> Stadium: ...

    @abstractmethod
    async def list_all(self, offset: int = 0, limit: int = 50) -> list[Stadium]: ...

    @abstractmethod
    async def list_by_country(self, country_code: str) -> list[Stadium]: ...

    @abstractmethod
    async def list_by_city(self, city: str) -> list[Stadium]: ...

    @abstractmethod
    async def search(self, query: str, offset: int = 0, limit: int = 50) -> list[Stadium]: ...


class IIncidentRepository(ABC):
    @abstractmethod
    async def get_by_id(self, incident_id: UUID) -> Incident | None: ...

    @abstractmethod
    async def create(self, incident: Incident) -> Incident: ...

    @abstractmethod
    async def update(self, incident: Incident) -> Incident: ...

    @abstractmethod
    async def list_active(self, offset: int = 0, limit: int = 50) -> list[Incident]: ...

    @abstractmethod
    async def list_by_status(
        self, status: IncidentStatus, offset: int = 0, limit: int = 50
    ) -> list[Incident]: ...

    @abstractmethod
    async def list_by_stadium(
        self, stadium_id: UUID, offset: int = 0, limit: int = 50
    ) -> list[Incident]: ...

    @abstractmethod
    async def list_by_event(
        self, event_id: UUID, offset: int = 0, limit: int = 50
    ) -> list[Incident]: ...

    @abstractmethod
    async def count_active_by_stadium(self, stadium_id: UUID) -> int: ...

    @abstractmethod
    async def count_by_severity(self, stadium_id: UUID) -> dict[str, int]: ...


class IFeedbackRepository(ABC):
    @abstractmethod
    async def get_by_id(self, feedback_id: UUID) -> Feedback | None: ...

    @abstractmethod
    async def create(self, feedback: Feedback) -> Feedback: ...

    @abstractmethod
    async def update(self, feedback: Feedback) -> Feedback: ...

    @abstractmethod
    async def list_by_event(
        self, event_id: UUID, offset: int = 0, limit: int = 50
    ) -> list[Feedback]: ...

    @abstractmethod
    async def list_by_stadium(
        self, stadium_id: UUID, offset: int = 0, limit: int = 50
    ) -> list[Feedback]: ...

    @abstractmethod
    async def list_by_user(
        self, user_id: UUID, offset: int = 0, limit: int = 50
    ) -> list[Feedback]: ...

    @abstractmethod
    async def list_by_category(
        self, category: FeedbackCategory, stadium_id: UUID | None = None, offset: int = 0, limit: int = 50
    ) -> list[Feedback]: ...

    @abstractmethod
    async def average_rating_by_event(self, event_id: UUID) -> float | None: ...

    @abstractmethod
    async def average_rating_by_stadium(self, stadium_id: UUID) -> float | None: ...

    @abstractmethod
    async def count_by_category(self, stadium_id: UUID) -> dict[str, int]: ...
