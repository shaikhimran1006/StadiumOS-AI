"""Transport coordination agent."""

import logging
from typing import Any

from app.ai.agents.base_agent import BaseAgent, AgentResponse
from app.ai.prompts.system_prompts import TRANSPORT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class TransportAgent(BaseAgent):
    """Agent specialized in transportation services and traffic management."""

    @property
    def agent_name(self) -> str:
        return "TransportAgent"

    @property
    def system_prompt(self) -> str:
        return TRANSPORT_SYSTEM_PROMPT

    def process(self, query: str, context: dict[str, Any]) -> AgentResponse:
        """Process transport-related queries."""
        query_lower = query.lower()
        mode = self._classify_transport_mode(query_lower)
        direction = self._determine_direction(query_lower)

        transport_context = context.get("transport", {})
        enriched_context = {
            **context,
            "transport_mode": mode,
            "direction": direction,
            "visitor_origin": transport_context.get("origin"),
            "vehicle_type": transport_context.get("vehicle_type"),
            "service_type": "transport_services",
        }

        prompt_parts = self._build_prompt(query, enriched_context)
        raw_response = self._call_gemini(prompt_parts)
        parsed = self._parse_response(raw_response)
        confidence = self._compute_confidence(parsed["clean_text"], query)

        if mode == "parking":
            parsed["actions"].append({"action": "get_parking_status", "id": "auto"})
        elif mode == "transit":
            parsed["actions"].append({"action": "get_transit_schedule", "id": "auto"})
        elif mode == "rideshare":
            parsed["actions"].append({"action": "get_rideshare_zone", "id": "auto"})

        return AgentResponse(
            response_text=parsed["clean_text"],
            agent_name=self.agent_name,
            confidence=confidence,
            metadata={
                "transport_mode": mode,
                "direction": direction,
                "raw_query": query,
            },
            actions=parsed["actions"],
            sources=parsed["sources"],
        )

    def _classify_transport_mode(self, query_lower: str) -> str:
        mode_keywords: dict[str, list[str]] = {
            "parking": ["park", "parking", "garage", "lot", "space", "car park", "valet"],
            "transit": ["bus", "train", "metro", "subway", "public transport", "transit", "light rail", "commuter"],
            "rideshare": ["uber", "lyft", "taxi", "cab", "ride share", "rideshare", "pickup", "dropoff"],
            "shuttle": ["shuttle", "shuttle bus", "free bus", "park and ride", "transfer"],
            "traffic": ["traffic", "congestion", "delay", "road", "route", "highway", "exit"],
            "bicycle": ["bike", "bicycle", "cycling", "bike rack", "bike share", "scooter", "e-scooter"],
            "accessible_transport": ["accessible transport", "wheelchair van", "paratransit", "accessible shuttle"],
        }

        for mode, keywords in mode_keywords.items():
            if any(kw in query_lower for kw in keywords):
                return mode

        return "general_transport"

    def _determine_direction(self, query_lower: str) -> str:
        if any(kw in query_lower for kw in ["arriving", "getting there", "going to", "to the stadium", "enter"]):
            return "arrival"
        if any(kw in query_lower for kw in ["leaving", "departure", "going home", "exit", "from stadium"]):
            return "departure"
        return "general"
