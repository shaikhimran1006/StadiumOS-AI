from __future__ import annotations

from enum import Enum


class GpsSector(str, Enum):
    """GPS sector mapping for stadium sections.

    Sectors are divided into lettered tiers (A-E from field outward)
    and numbered slices (1-20 clockwise around the stadium).
    """

    A1 = "A1"
    A2 = "A2"
    A3 = "A3"
    A4 = "A4"
    A5 = "A5"
    A6 = "A6"
    A7 = "A7"
    A8 = "A8"
    A9 = "A9"
    A10 = "A10"
    A11 = "A11"
    A12 = "A12"
    A13 = "A13"
    A14 = "A14"
    A15 = "A15"
    A16 = "A16"
    A17 = "A17"
    A18 = "A18"
    A19 = "A19"
    A20 = "A20"

    B1 = "B1"
    B2 = "B2"
    B3 = "B3"
    B4 = "B4"
    B5 = "B5"
    B6 = "B6"
    B7 = "B7"
    B8 = "B8"
    B9 = "B9"
    B10 = "B10"
    B11 = "B11"
    B12 = "B12"
    B13 = "B13"
    B14 = "B14"
    B15 = "B15"
    B16 = "B16"
    B17 = "B17"
    B18 = "B18"
    B19 = "B19"
    B20 = "B20"

    C1 = "C1"
    C2 = "C2"
    C3 = "C3"
    C4 = "C4"
    C5 = "C5"
    C6 = "C6"
    C7 = "C7"
    C8 = "C8"
    C9 = "C9"
    C10 = "C10"
    C11 = "C11"
    C12 = "C12"
    C13 = "C13"
    C14 = "C14"
    C15 = "C15"
    C16 = "C16"
    C17 = "C17"
    C18 = "C18"
    C19 = "C19"
    C20 = "C20"

    D1 = "D1"
    D2 = "D2"
    D3 = "D3"
    D4 = "D4"
    D5 = "D5"
    D6 = "D6"
    D7 = "D7"
    D8 = "D8"
    D9 = "D9"
    D10 = "D10"
    D11 = "D11"
    D12 = "D12"
    D13 = "D13"
    D14 = "D14"
    D15 = "D15"
    D16 = "D16"
    D17 = "D17"
    D18 = "D18"
    D19 = "D19"
    D20 = "D20"

    E1 = "E1"
    E2 = "E2"
    E3 = "E3"
    E4 = "E4"
    E5 = "E5"
    E6 = "E6"
    E7 = "E7"
    E8 = "E8"
    E9 = "E9"
    E10 = "E10"
    E11 = "E11"
    E12 = "E12"
    E13 = "E13"
    E14 = "E14"
    E15 = "E15"
    E16 = "E16"
    E17 = "E17"
    E18 = "E18"
    E19 = "E19"
    E20 = "E20"

    VIP = "VIP"
    PRESS = "PRESS"
    FIELD_LEVEL = "FIELD_LEVEL"
    TUNNEL = "TUNNEL"
    CONCOURSE_UPPER = "CONCOURSE_UPPER"
    CONCOURSE_LOWER = "CONCOURSE_LOWER"
    PARKING_NORTH = "PARKING_NORTH"
    PARKING_SOUTH = "PARKING_SOUTH"
    PARKING_EAST = "PARKING_EAST"
    PARKING_WEST = "PARKING_WEST"

    @classmethod
    def from_tier_and_slice(cls, tier: str, slice_num: int) -> GpsSector:
        if not 1 <= slice_num <= 20:
            raise ValueError(f"Slice number must be between 1 and 20, got {slice_num}")
        tier_upper = tier.upper()
        return cls(f"{tier_upper}{slice_num}")

    @property
    def tier(self) -> str | None:
        value = self.value
        if len(value) >= 2 and value[0].isalpha() and value[1:].isdigit():
            return value[0]
        return None

    @property
    def slice_number(self) -> int | None:
        value = self.value
        if len(value) >= 2 and value[0].isalpha() and value[1:].isdigit():
            return int(value[1:])
        return None

    def is_seating(self) -> bool:
        return self.tier is not None and self.slice_number is not None

    def tier_distance_from_field(self) -> int | None:
        tier_map = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5}
        t = self.tier
        if t and t in tier_map:
            return tier_map[t]
        return None
