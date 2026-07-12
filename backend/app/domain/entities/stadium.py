from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.domain.value_objects.coordinates import LatLong
from app.domain.value_objects.gps_sector import GpsSector


class StadiumStatus(str, Enum):
    OPERATIONAL = "OPERATIONAL"
    MAINTENANCE = "MAINTENANCE"
    CLOSED = "CLOSED"
    CONSTRUCTION = "CONSTRUCTION"


class FacilityType(str, Enum):
    RESTROOM = "RESTROOM"
    FOOD_COURT = "FOOD_COURT"
    FIRST_AID = "FIRST_AID"
    INFORMATION_DESK = "INFORMATION_DESK"
    GIFT_SHOP = "GIFT_SHOP"
    ATM = "ATM"
    PARKING = "PARKING"
    ENTRANCE = "ENTRANCE"
    EXIT = "EXIT"
    ELEVATOR = "ELEVATOR"
    ESCALATOR = "ESCALATOR"
    ACCESSIBLE_RAMP = "ACCESSIBLE_RAMP"
    LOUNGE = "LOUNGE"
    MEDIA_CENTER = "MEDIA_CENTER"
    VIP_SUITE = "VIP_SUITE"
    LOCKER_ROOM = "LOCKER_ROOM"
    CONTROL_ROOM = "CONTROL_ROOM"


class Facility(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., max_length=100)
    facility_type: FacilityType
    sector: GpsSector | None = None
    floor_level: int = Field(default=0)
    capacity: int | None = Field(default=None, ge=0)
    accessible: bool = Field(default=True)
    operating: bool = Field(default=True)
    location: LatLong | None = None


class SectorConfig(BaseModel):
    sector: GpsSector
    capacity: int = Field(ge=0)
    tier: str = Field(..., description="e.g. standard, vip, press")
    accessible_seating: bool = Field(default=False)
    current_occupancy: int = Field(default=0, ge=0)
    is_open: bool = Field(default=True)

    def occupancy_percentage(self) -> float:
        if self.capacity == 0:
            return 0.0
        return round(self.current_occupancy / self.capacity * 100, 1)


class Stadium(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=200)
    city: str = Field(..., min_length=1, max_length=100)
    country: str = Field(..., min_length=2, max_length=3)
    country_code: str = Field(..., min_length=2, max_length=3, description="ISO 3166-1 alpha-3")
    timezone: str = Field(default="UTC", max_length=50)
    status: StadiumStatus = Field(default=StadiumStatus.OPERATIONAL)
    location: LatLong | None = None
    address: str | None = Field(default=None, max_length=500)
    total_capacity: int = Field(ge=0)
    standing_capacity: int = Field(default=0, ge=0)
    seated_capacity: int = Field(default=0, ge=0)
    vip_capacity: int = Field(default=0, ge=0)
    press_capacity: int = Field(default=0, ge=0)
    accessible_capacity: int = Field(default=0, ge=0)
    sectors: list[SectorConfig] = Field(default_factory=list)
    facilities: list[Facility] = Field(default_factory=list)
    gates: list[str] = Field(default_factory=list, description="Gate names/IDs")
    year_built: int | None = Field(default=None, ge=1900, le=2100)
    last_renovation_year: int | None = Field(default=None, ge=1900, le=2100)
    field_surface: str | None = Field(default=None, description="e.g. natural_grass, hybrid, artificial")
    roof_type: str | None = Field(default=None, description="e.g. retractable, fixed, open")
    parking_capacity: int = Field(default=0, ge=0)
    public_transit_info: str | None = Field(default=None, max_length=500)
    wifi_available: bool = Field(default=True)
    cell_signal_booster: bool = Field(default=True)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def total_occupancy(self) -> int:
        return sum(s.current_occupancy for s in self.sectors)

    def overall_occupancy_percentage(self) -> float:
        if self.total_capacity == 0:
            return 0.0
        return round(self.total_occupancy() / self.total_capacity * 100, 1)

    def open_sectors(self) -> list[SectorConfig]:
        return [s for s in self.sectors if s.is_open]

    def closed_sectors(self) -> list[SectorConfig]:
        return [s for s in self.sectors if not s.is_open]

    def get_sector(self, sector: GpsSector) -> SectorConfig | None:
        for s in self.sectors:
            if s.sector == sector:
                return s
        return None

    def facilities_by_type(self, facility_type: FacilityType) -> list[Facility]:
        return [f for f in self.facilities if f.facility_type == facility_type]

    def update_occupancy(self, sector: GpsSector, count: int) -> None:
        sector_config = self.get_sector(sector)
        if sector_config is None:
            raise ValueError(f"Sector {sector.value} not found in stadium {self.name}")
        sector_config.current_occupancy = count
        self.updated_at = datetime.now(timezone.utc)
