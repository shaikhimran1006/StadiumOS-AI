from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.domain.value_objects.coordinates import LatLong
from app.domain.value_objects.gps_sector import GpsSector
from app.domain.value_objects.language import Language


class UserRole(str, Enum):
    FAN = "FAN"
    VOLUNTEER = "VOLUNTEER"
    STAFF = "STAFF"
    ADMIN = "ADMIN"
    SECURITY = "SECURITY"
    MEDICAL = "MEDICAL"


class UserStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    DEACTIVATED = "DEACTIVATED"


class DeviceInfo(BaseModel):
    platform: str = Field(..., description="e.g. ios, android, web")
    app_version: str = Field(default="1.0.0")
    device_model: str = Field(default="unknown")
    os_version: str = Field(default="unknown")


class User(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    external_id: str | None = Field(default=None, description="External auth provider ID")
    email: str | None = Field(default=None)
    phone: str | None = Field(default=None)
    display_name: str = Field(..., min_length=1, max_length=120)
    role: UserRole = Field(default=UserRole.FAN)
    status: UserStatus = Field(default=UserStatus.ACTIVE)
    preferred_language: Language = Field(default=Language.ENGLISH)
    home_stadium_id: UUID | None = None
    assigned_sector: GpsSector | None = None
    current_location: LatLong | None = None
    device_info: DeviceInfo | None = None
    accessible_seating: bool = Field(default=False, description="Requires accessible seating")
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def is_staff(self) -> bool:
        return self.role in {
            UserRole.STAFF,
            UserRole.ADMIN,
            UserRole.SECURITY,
            UserRole.MEDICAL,
        }

    def can_manage_incidents(self) -> bool:
        return self.role in {UserRole.STAFF, UserRole.ADMIN, UserRole.SECURITY}

    def update_location(self, location: LatLong) -> None:
        self.current_location = location
        self.updated_at = datetime.now(timezone.utc)

    def deactivate(self) -> None:
        self.status = UserStatus.DEACTIVATED
        self.updated_at = datetime.now(timezone.utc)
