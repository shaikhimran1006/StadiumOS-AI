"""Function calling tools available to StadiumOS AI agents."""

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


def get_match_schedule(
    sport: str | None = None,
    date: str | None = None,
    team: str | None = None,
) -> dict[str, Any]:
    """Retrieve match schedules for the stadium.

    Args:
        sport: Filter by sport type (football, basketball, soccer, etc.).
        date: Filter by date in YYYY-MM-DD format.
        team: Filter by team name.

    Returns:
        Dict with match schedule data.
    """
    now = datetime.now()
    target_date = date or now.strftime("%Y-%m-%d")

    matches = [
        {
            "match_id": "M-2026-0712-001",
            "sport": "Football",
            "home_team": "Stadium FC",
            "away_team": "City United",
            "date": target_date,
            "time": "19:00",
            "gates_open": "17:00",
            "status": "scheduled",
            "section_map": "standard",
        },
        {
            "match_id": "M-2026-0715-002",
            "sport": "Soccer",
            "home_team": "Stadium SC",
            "away_team": "Metro Stars",
            "date": "2026-07-15",
            "time": "20:30",
            "gates_open": "18:30",
            "status": "scheduled",
            "section_map": "standard",
        },
    ]

    filtered = matches
    if sport:
        filtered = [m for m in filtered if m["sport"].lower() == sport.lower()]
    if team:
        filtered = [
            m for m in filtered
            if team.lower() in m["home_team"].lower()
            or team.lower() in m["away_team"].lower()
        ]

    return {
        "status": "success",
        "count": len(filtered),
        "matches": filtered,
        "query_date": target_date,
    }


def get_stadium_map(
    section: str | None = None,
    floor: str | None = None,
    zone: str | None = None,
) -> dict[str, Any]:
    """Retrieve stadium map information including sections, gates, and facilities.

    Args:
        section: Specific section to get details for (e.g., "A", "B12").
        floor: Floor level.
        zone: Stadium zone (north, south, east, west).

    Returns:
        Dict with stadium map data.
    """
    sections = {
        "A": {"capacity": 5000, "floor": 1, "zone": "north", "type": "general"},
        "B": {"capacity": 4500, "floor": 1, "zone": "south", "type": "general"},
        "C": {"capacity": 3000, "floor": 2, "zone": "east", "type": "premium"},
        "D": {"capacity": 2500, "floor": 2, "zone": "west", "type": "vip"},
    }

    if section and section.upper() in sections:
        return {
            "status": "success",
            "section": section.upper(),
            "details": sections[section.upper()],
        }

    return {
        "status": "success",
        "sections": sections,
        "total_capacity": sum(s["capacity"] for s in sections.values()),
        "gates": ["Gate 1 (North)", "Gate 2 (South)", "Gate 3 (East)", "Gate 4 (West)"],
        "levels": 4,
    }


def get_nearest_facility(
    facility_type: str,
    location: str | None = None,
    accessibility_required: bool = False,
) -> dict[str, Any]:
    """Find the nearest stadium facility of a given type.

    Args:
        facility_type: Type of facility (restroom, food, medical, merchandise, atm).
        location: Current location reference.
        accessibility_required: If True, only return accessible facilities.

    Returns:
        Dict with nearest facility information.
    """
    facilities: dict[str, list[dict[str, Any]]] = {
        "restroom": [
            {"id": "R-001", "location": "Section A, Level 1", "accessible": True, "distance_m": 50, "status": "clean"},
            {"id": "R-002", "location": "Section B, Level 1", "accessible": True, "distance_m": 80, "status": "clean"},
            {"id": "R-003", "location": "Section C, Level 2", "accessible": True, "distance_m": 120, "status": "needs_attention"},
        ],
        "food": [
            {"id": "F-001", "name": "Burger Station", "location": "Section A, Concourse", "distance_m": 40, "wait_time_min": 5},
            {"id": "F-002", "name": "Taco Stand", "location": "Section B, Concourse", "distance_m": 70, "wait_time_min": 3},
            {"id": "F-003", "name": "Pizza Corner", "location": "Section D, Concourse", "distance_m": 150, "wait_time_min": 8},
        ],
        "medical": [
            {"id": "M-001", "location": "Section A, Level 1, Gate 1", "distance_m": 30, "staffed": True, "equipment": "basic"},
            {"id": "M-002", "location": "Section C, Level 2, Gate 3", "distance_m": 200, "staffed": True, "equipment": "advanced"},
        ],
    }

    available = facilities.get(facility_type.lower(), [])
    if accessibility_required:
        available = [f for f in available if f.get("accessible", False) or facility_type.lower() != "restroom"]

    if location:
        available.sort(key=lambda f: f.get("distance_m", 9999))

    return {
        "status": "success",
        "facility_type": facility_type,
        "count": len(available),
        "facilities": available,
        "accessibility_filtered": accessibility_required,
    }


def get_emergency_info(
    emergency_type: str | None = None,
    zone: str | None = None,
) -> dict[str, Any]:
    """Retrieve emergency procedures and information.

    Args:
        emergency_type: Type of emergency (fire, medical, security, evacuation).
        zone: Specific zone for zone-specific procedures.

    Returns:
        Dict with emergency procedures and contacts.
    """
    procedures = {
        "fire": {
            "code": "CODE RED",
            "steps": [
                "Activate nearest fire alarm pull station",
                "Evacuate via nearest exit away from fire",
                "Proceed to designated assembly point",
                "Account for all personnel",
                "Wait for fire department arrival",
            ],
            "assembly_points": ["North Parking Lot A", "South Plaza", "East Gate Area"],
            "do_not": ["Use elevators", "Re-enter building", "Attempt to fight large fires"],
        },
        "medical": {
            "code": "CODE BLUE",
            "steps": [
                "Call 911 immediately",
                "Dispatch on-site medical team",
                "Clear area around patient",
                "Begin CPR if trained and needed",
                "Guide EMS to exact location",
            ],
            "medical_stations": [
                {"id": "M-001", "location": "Section A, Level 1", "phone": "555-0100"},
                {"id": "M-002", "location": "Section C, Level 2", "phone": "555-0101"},
            ],
        },
        "security": {
            "code": "CODE YELLOW",
            "steps": [
                "Assess the threat level",
                "Notify security command center",
                "Establish perimeter",
                "Gather witness information",
                "Coordinate with law enforcement",
            ],
            "command_center": {"phone": "555-0200", "location": "Operations Center, Level B1"},
        },
        "evacuation": {
            "code": "CODE ORANGE",
            "steps": [
                "Announce evacuation order via PA system",
                "Open all emergency exits",
                "Guide crowd to nearest exits",
                "Direct to assembly points",
                "Conduct sweep of evacuated areas",
            ],
            "exits": {
                "north": ["Gate 1A", "Gate 1B", "Emergency Exit N1"],
                "south": ["Gate 2A", "Gate 2B", "Emergency Exit S1"],
                "east": ["Gate 3", "Emergency Exit E1", "Emergency Exit E2"],
                "west": ["Gate 4", "Emergency Exit W1"],
            },
        },
    }

    if emergency_type and emergency_type.lower() in procedures:
        return {
            "status": "success",
            "emergency_type": emergency_type,
            "procedure": procedures[emergency_type.lower()],
            "emergency_services": {"phone": "911", "internal": "555-0000"},
        }

    return {
        "status": "success",
        "available_procedures": list(procedures.keys()),
        "emergency_services": {"phone": "911", "internal": "555-0000"},
    }


def get_transport_options(
    mode: str | None = None,
    origin: str | None = None,
    destination_zone: str | None = None,
) -> dict[str, Any]:
    """Retrieve transportation options for getting to/from the stadium.

    Args:
        mode: Transport mode filter (parking, transit, rideshare, shuttle).
        origin: Starting location for directions.
        destination_zone: Target zone at the stadium.

    Returns:
        Dict with transport options.
    """
    options: dict[str, list[dict[str, Any]]] = {
        "parking": [
            {
                "lot_id": "P-1",
                "name": "Main Garage",
                "location": "North Entrance",
                "capacity": 2000,
                "available": 342,
                "price_per_hour": 5.00,
                "accessible_spaces": 40,
                "distance_to_gate": "Gate 1 - 2 min walk",
            },
            {
                "lot_id": "P-2",
                "name": "South Lot",
                "location": "South Entrance",
                "capacity": 1500,
                "available": 187,
                "price_per_hour": 3.00,
                "accessible_spaces": 25,
                "distance_to_gate": "Gate 2 - 5 min walk",
            },
            {
                "lot_id": "P-3",
                "name": "East Structure",
                "location": "East Entrance",
                "capacity": 800,
                "available": 0,
                "price_per_hour": 4.00,
                "accessible_spaces": 15,
                "distance_to_gate": "Gate 3 - 3 min walk",
            },
        ],
        "transit": [
            {
                "route": "Metro Line A",
                "station": "Stadium Station",
                "frequency": "Every 8 minutes",
                "walk_time": "3 min from station to Gate 1",
                "last_train": "00:30",
            },
            {
                "route": "Bus Route 42",
                "stop": "Stadium Drive",
                "frequency": "Every 15 minutes",
                "walk_time": "5 min from stop to Gate 2",
                "last_bus": "23:45",
            },
        ],
        "rideshare": [
            {
                "service": "Uber/Lyft",
                "pickup_zone": "East Plaza, designated rideshare area",
                "dropoff_zone": "East Plaza, designated rideshare area",
                "surge_multiplier": 1.2,
                "estimated_wait_min": 4,
            }
        ],
        "shuttle": [
            {
                "route": "Parking P-4 to Gate 1",
                "frequency": "Every 10 minutes",
                "operating_hours": "16:00 - 23:00",
                "accessible": True,
                "wait_time_min": 6,
            }
        ],
    }

    if mode and mode.lower() in options:
        return {
            "status": "success",
            "mode": mode,
            "options": options[mode.lower()],
        }

    return {
        "status": "success",
        "all_options": options,
    }


def get_accessibility_info(
    need_type: str | None = None,
    location: str | None = None,
) -> dict[str, Any]:
    """Retrieve accessibility information and services.

    Args:
        need_type: Type of accessibility need (wheelchair, hearing, visual, cognitive).
        location: Current location for nearest accessible resources.

    Returns:
        Dict with accessibility information.
    """
    info: dict[str, Any] = {
        "wheelchair": {
            "accessible_entrances": ["Gate 1 (North) - Ramp", "Gate 2 (South) - Ramp", "Gate 3 (East) - Elevator"],
            "elevator_locations": [
                {"location": "Section A, Level 1 to 2", "status": "operational"},
                {"location": "Section C, Level 1 to 3", "status": "operational"},
                {"location": "Section D, Level 1 to VIP", "status": "maintenance scheduled"},
            ],
            "accessible_seating": {
                "sections": ["A1-A5", "B1-B3", "C1-C2"],
                "companion_seats": True,
                "wheelchair_positions": 120,
            },
            "accessible_restrooms": [
                {"location": "Section A, Level 1", "features": ["roll-in shower", "grab bars", "lowered sink"]},
                {"location": "Section B, Level 1", "features": ["grab bars", "lowered sink"]},
            ],
        },
        "hearing": {
            "assistive_listening": {
                "available": True,
                "pickup_location": "Information Desk, Gate 1",
                "deposit_required": False,
                "frequency_range": "72MHz - 76MHz",
            },
            "sign_language": {
                "available": True,
                "request_advance": True,
                "contact": "555-0300",
            },
            "captioning": {
                "location": "Main scoreboard, Section C screen",
                "available": True,
            },
        },
        "visual": {
            "audio_descriptions": {
                "available": True,
                "device_location": "Information Desk, Gate 1",
                "languages": ["English", "Spanish"],
            },
            "braille_guides": {
                "available": True,
                "pickup_location": "Information Desk",
            },
            "large_print": {
                "available": True,
                "pickup_location": "Information Desk",
            },
            "service_animals": {
                "welcome": True,
                "relief_areas": ["North Plaza", "South Plaza"],
                "water_stations": ["Gate 1", "Gate 2", "Gate 3", "Gate 4"],
            },
        },
        "cognitive": {
            "sensory_rooms": [
                {"location": "Section A, Level 2", "capacity": 6, "features": ["dim lighting", "noise cancelling", "weighted blankets"]},
                {"location": "Section D, Level 1", "capacity": 4, "features": ["quiet space", "fidget tools"]},
            ],
            "quiet_zones": ["Section D lounge", "VIP area (with ticket)"],
            "visual_schedules": {
                "available": True,
                "pickup_location": "Information Desk",
            },
        },
    }

    if need_type and need_type.lower() in info:
        return {
            "status": "success",
            "need_type": need_type,
            "information": info[need_type.lower()],
        }

    return {
        "status": "success",
        "available_types": list(info.keys()),
        "information": info,
    }


def report_incident(
    incident_type: str,
    location: str,
    description: str,
    severity: str = "medium",
    reporter_info: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Report a security or safety incident.

    Args:
        incident_type: Type of incident (suspicious_activity, medical, fire, etc.).
        location: Exact location within the stadium.
        description: Detailed description of the incident.
        severity: Severity level (low, medium, high, critical).
        reporter_info: Optional dict with reporter details.

    Returns:
        Dict with incident report confirmation.
    """
    import uuid

    incident_id = f"INC-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"

    report = {
        "incident_id": incident_id,
        "incident_type": incident_type,
        "location": location,
        "description": description,
        "severity": severity,
        "reported_at": datetime.now().isoformat(),
        "status": "open",
        "assigned_to": None,
        "reporter": reporter_info or {"type": "anonymous"},
        "actions_taken": [],
        "escalated": severity in ("high", "critical"),
    }

    logger.warning(
        "Incident reported: %s | Type: %s | Location: %s | Severity: %s",
        incident_id,
        incident_type,
        location,
        severity,
    )

    return {
        "status": "success",
        "incident_id": incident_id,
        "report": report,
        "next_steps": [
            "Incident logged in system",
            "Security team notified" if severity in ("high", "critical") else "Security team will review",
            "Follow-up within 15 minutes" if severity == "critical" else "Follow-up within 30 minutes",
        ],
    }


def get_weather(
    event_date: str | None = None,
) -> dict[str, Any]:
    """Retrieve weather information relevant to stadium events.

    Args:
        event_date: Date for weather forecast (YYYY-MM-DD). Defaults to today.

    Returns:
        Dict with weather data and recommendations.
    """
    target_date = event_date or datetime.now().strftime("%Y-%m-%d")

    weather_data = {
        "date": target_date,
        "current": {
            "temperature_f": 78,
            "temperature_c": 26,
            "condition": "Partly Cloudy",
            "humidity_percent": 62,
            "wind_speed_mph": 8,
            "wind_direction": "NW",
            "uv_index": 6,
            "air_quality_index": 42,
        },
        "forecast": {
            "high_f": 85,
            "low_f": 68,
            "precipitation_chance_percent": 20,
            "sunset_time": "20:15",
        },
        "recommendations": {
            "hydration": "Stay hydrated - drink water regularly",
            "sun_protection": "Moderate UV - consider sunscreen and hat",
            "clothing": "Light, breathable clothing recommended",
            "umbrella": "Low chance of rain - umbrella optional",
        },
        "alerts": [],
    }

    if weather_data["current"]["uv_index"] >= 8:
        weather_data["alerts"].append({
            "type": "uv_warning",
            "message": "High UV index - seek shade during breaks",
        })
    if weather_data["forecast"]["precipitation_chance_percent"] >= 60:
        weather_data["alerts"].append({
            "type": "rain_warning",
            "message": "High chance of rain - bring rain gear",
        })

    return {
        "status": "success",
        "weather": weather_data,
    }


FUNCTION_TOOLS: dict[str, dict[str, Any]] = {
    "get_match_schedule": {
        "function": get_match_schedule,
        "description": "Retrieve match schedules for the stadium",
        "parameters": {
            "sport": {"type": "string", "description": "Sport type filter"},
            "date": {"type": "string", "description": "Date filter (YYYY-MM-DD)"},
            "team": {"type": "string", "description": "Team name filter"},
        },
    },
    "get_stadium_map": {
        "function": get_stadium_map,
        "description": "Get stadium map and section information",
        "parameters": {
            "section": {"type": "string", "description": "Section identifier"},
            "floor": {"type": "string", "description": "Floor level"},
            "zone": {"type": "string", "description": "Stadium zone"},
        },
    },
    "get_nearest_facility": {
        "function": get_nearest_facility,
        "description": "Find nearest facility of a given type",
        "parameters": {
            "facility_type": {"type": "string", "description": "Facility type"},
            "location": {"type": "string", "description": "Current location"},
            "accessibility_required": {"type": "boolean", "description": "Filter for accessible only"},
        },
    },
    "get_emergency_info": {
        "function": get_emergency_info,
        "description": "Get emergency procedures and contacts",
        "parameters": {
            "emergency_type": {"type": "string", "description": "Emergency type"},
            "zone": {"type": "string", "description": "Stadium zone"},
        },
    },
    "get_transport_options": {
        "function": get_transport_options,
        "description": "Get transportation options to/from stadium",
        "parameters": {
            "mode": {"type": "string", "description": "Transport mode"},
            "origin": {"type": "string", "description": "Starting location"},
            "destination_zone": {"type": "string", "description": "Target zone"},
        },
    },
    "get_accessibility_info": {
        "function": get_accessibility_info,
        "description": "Get accessibility services information",
        "parameters": {
            "need_type": {"type": "string", "description": "Type of accessibility need"},
            "location": {"type": "string", "description": "Current location"},
        },
    },
    "report_incident": {
        "function": report_incident,
        "description": "Report a security or safety incident",
        "parameters": {
            "incident_type": {"type": "string", "description": "Incident type"},
            "location": {"type": "string", "description": "Incident location"},
            "description": {"type": "string", "description": "Incident description"},
            "severity": {"type": "string", "description": "Severity level"},
            "reporter_info": {"type": "object", "description": "Reporter details"},
        },
    },
    "get_weather": {
        "function": get_weather,
        "description": "Get weather information for stadium events",
        "parameters": {
            "event_date": {"type": "string", "description": "Event date (YYYY-MM-DD)"},
        },
    },
}
