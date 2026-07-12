from __future__ import annotations

from enum import IntEnum


class Priority(IntEnum):
    """Priority levels for alerts, incidents, and tasks.

    Ordered by severity descending so comparisons work naturally:
    Priority.CRITICAL > Priority.HIGH > Priority.MEDIUM > Priority.LOW
    """

    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

    @classmethod
    def from_label(cls, label: str) -> Priority:
        normalized = label.strip().upper()
        mapping = {
            "CRITICAL": cls.CRITICAL,
            "CRIT": cls.CRITICAL,
            "HIGH": cls.HIGH,
            "HI": cls.HIGH,
            "MEDIUM": cls.MEDIUM,
            "MED": cls.MEDIUM,
            "LOW": cls.LOW,
            "LO": cls.LOW,
        }
        if normalized not in mapping:
            raise ValueError(f"Unknown priority label: {label}")
        return mapping[normalized]

    def label(self) -> str:
        return self.name

    def color_hex(self) -> str:
        colors = {
            Priority.CRITICAL: "#DC2626",
            Priority.HIGH: "#EA580C",
            Priority.MEDIUM: "#CA8A04",
            Priority.LOW: "#2563EB",
        }
        return colors[self]

    def response_time_seconds(self) -> int:
        response_times = {
            Priority.CRITICAL: 30,
            Priority.HIGH: 120,
            Priority.MEDIUM: 300,
            Priority.LOW: 900,
        }
        return response_times[self]
