"""Agent router for classifying and dispatching queries to specialized agents."""

import logging
import re
from typing import Any

from app.ai.agents.base_agent import AgentResponse, BaseAgent
from app.ai.agents.fan_agent import FanAgent
from app.ai.agents.operations_agent import OperationsAgent
from app.ai.agents.volunteer_agent import VolunteerAgent
from app.ai.agents.security_agent import SecurityAgent
from app.ai.agents.accessibility_agent import AccessibilityAgent
from app.ai.agents.transport_agent import TransportAgent
from app.ai.agents.medical_agent import MedicalAgent
from app.ai.agents.sustainability_agent import SustainabilityAgent

logger = logging.getLogger(__name__)

AGENT_KEYWORDS: dict[str, list[str]] = {
    "fan": [
        "match", "game", "score", "seat", "section", "gate", "food", "drink",
        "restroom", "bathroom", "merchandise", "store", "jersey", "schedule",
        "halftime", "event", "wifi", "lost and found", "ticket", "fan",
        "concession", "menu", "upgrade", "atmosphere", "team",
    ],
    "operations": [
        "hvac", "lighting", "maintenance", "repair", "staff", "shift", "logistics",
        "delivery", "vendor", "concession management", "crowd flow", "capacity",
        "facility", "infrastructure", "power", "water", "utility", "setup",
        "teardown", "cleaning", "sanitation", "building",
    ],
    "volunteer": [
        "volunteer", "volunteering", "task assignment", "training", "orientation",
        "check in", "clock in", "shift swap", "volunteer schedule", "supervisor",
        "volunteer coordinator", "unteer", "help out",
    ],
    "security": [
        "security", "incident", "threat", "suspicious", "emergency", "evacuate",
        "evacuation", "fire", "bomb", "weapon", "theft", "crime", "police",
        "law enforcement", "access control", "credential", "badge", "perimeter",
        "crowd safety", "lost person", "lockdown", "code red",
    ],
    "accessibility": [
        "wheelchair", "accessible", "accessibility", "disability", "hearing",
        "deaf", "sign language", "visual", "blind", "braille", "ramp",
        "elevator", "assistive", "mobility", "special needs", "companion",
        "caregiver", "sensory", "autism", "neurodivergent",
    ],
    "transport": [
        "parking", "park", "bus", "train", "metro", "subway", "transit",
        "uber", "lyft", "taxi", "rideshare", "shuttle", "traffic", "road",
        "highway", "bike", "bicycle", "scooter", "pickup", "dropoff",
        "commute", "route",
    ],
    "medical": [
        "medical", "first aid", "injury", "hurt", "sick", "pain", "heart attack",
        "stroke", "seizure", "allergic", "epipen", "oxygen", "doctor", "nurse",
        "hospital", "clinic", "medication", "prescription", "emergency medical",
        "ambulance", "health", "breathing", "unconscious",
    ],
    "sustainability": [
        "recycle", "recycling", "sustainability", "green", "environment",
        "carbon", "emission", "energy", "solar", "water conservation",
        "waste", "compost", "eco-friendly", "sustainable", "leed",
        "renewable", "climate", "footprint",
    ],
}

# Priority order: higher priority categories checked first
CATEGORY_PRIORITY = [
    "security",
    "medical",
    "accessibility",
    "operations",
    "transport",
    "volunteer",
    "sustainability",
    "fan",
]


class AgentRouter:
    """Routes user queries to the appropriate specialized agent.

    Uses keyword/intent analysis to classify incoming queries and
    dispatch them to the correct agent for processing.
    """

    def __init__(self) -> None:
        self._agents: dict[str, BaseAgent] = {
            "fan": FanAgent(),
            "operations": OperationsAgent(),
            "volunteer": VolunteerAgent(),
            "security": SecurityAgent(),
            "accessibility": AccessibilityAgent(),
            "transport": TransportAgent(),
            "medical": MedicalAgent(),
            "sustainability": SustainabilityAgent(),
        }
        self._fallback_agent: BaseAgent = self._agents["fan"]
        logger.info(
            "AgentRouter initialized with agents: %s",
            list(self._agents.keys()),
        )

    def route_query(self, query: str, context: dict[str, Any] | None = None) -> str:
        """Classify a user query and return the name of the best matching agent.

        Args:
            query: The user's natural language query.
            context: Optional context dict with user/session information.

        Returns:
            The agent name string (e.g., "fan", "security", "medical").
        """
        if context and context.get("force_agent") in self._agents:
            return context["force_agent"]

        query_lower = query.lower().strip()
        scores = self._score_categories(query_lower)

        best_category = max(scores, key=scores.get)  # type: ignore[arg-type]
        best_score = scores[best_category]

        if best_score == 0:
            logger.info("No keyword match for query, falling back to FanAgent")
            return "fan"

        if best_score >= 2:
            logger.info("Query routed to '%s' (score=%d)", best_category, best_score)
            return best_category

        # Tie-breaking: use priority order
        for category in CATEGORY_PRIORITY:
            if scores.get(category, 0) == best_score:
                logger.info("Query routed to '%s' via priority tie-break", category)
                return category

        return "fan"

    def _score_categories(self, query_lower: str) -> dict[str, int]:
        """Score each category by counting keyword matches."""
        scores: dict[str, int] = {}
        words = set(re.findall(r"\w+", query_lower))

        for category, keywords in AGENT_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                if " " in keyword:
                    if keyword in query_lower:
                        score += 2
                elif keyword in words:
                    score += 1
            scores[category] = score

        return scores

    def get_agent(self, agent_name: str) -> BaseAgent:
        """Retrieve an agent instance by name.

        Args:
            agent_name: The agent identifier (e.g., "fan", "security").

        Returns:
            The BaseAgent instance.

        Raises:
            ValueError: If no agent exists with the given name.
        """
        agent = self._agents.get(agent_name)
        if agent is None:
            available = ", ".join(self._agents.keys())
            raise ValueError(
                f"Unknown agent '{agent_name}'. Available agents: {available}"
            )
        return agent

    def process_query(self, query: str, context: dict[str, Any] | None = None) -> AgentResponse:
        """Route and process a query end-to-end.

        Args:
            query: The user's natural language query.
            context: Optional context dict.

        Returns:
            AgentResponse from the routed agent.
        """
        ctx = context or {}
        agent_name = self.route_query(query, ctx)
        agent = self.get_agent(agent_name)

        logger.info("Processing query with %s", agent_name)
        response = agent.process(query, ctx)
        return response

    @property
    def available_agents(self) -> list[str]:
        """Return list of available agent names."""
        return list(self._agents.keys())
