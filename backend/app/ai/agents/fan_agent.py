"""Fan experience agent for visitor queries."""

import logging
from typing import Any

from app.ai.agents.base_agent import BaseAgent, AgentResponse
from app.ai.prompts.system_prompts import FAN_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class FanAgent(BaseAgent):
    """Agent specialized in fan experience and visitor services."""

    @property
    def agent_name(self) -> str:
        return "FanAgent"

    @property
    def system_prompt(self) -> str:
        return FAN_SYSTEM_PROMPT

    def process(self, query: str, context: dict[str, Any]) -> AgentResponse:
        """Process fan-related queries."""
        query_lower = query.lower()
        intent = self._classify_intent(query_lower)

        enriched_context = {
            **context,
            "fan_intent": intent,
            "service_type": "fan_experience",
        }

        prompt_parts = self._build_prompt(query, enriched_context)
        raw_response = self._call_gemini(prompt_parts)
        parsed = self._parse_response(raw_response)
        confidence = self._compute_confidence(parsed["clean_text"], query)

        if intent == "match_info":
            parsed["actions"].append({"action": "lookup_match_schedule", "id": "auto"})
        elif intent == "seating":
            parsed["actions"].append({"action": "get_stadium_map", "id": "auto"})
        elif intent == "food":
            parsed["actions"].append({"action": "get_concession_info", "id": "auto"})
        elif intent == "merchandise":
            parsed["actions"].append({"action": "get_merchandise_info", "id": "auto"})

        return AgentResponse(
            response_text=parsed["clean_text"],
            agent_name=self.agent_name,
            confidence=confidence,
            metadata={"intent": intent, "raw_query": query},
            actions=parsed["actions"],
            sources=parsed["sources"],
        )

    def _classify_intent(self, query_lower: str) -> str:
        intent_keywords: dict[str, list[str]] = {
            "match_info": ["schedule", "game", "match", "score", "lineup", "team", "kickoff", "first pitch", "tip-off"],
            "seating": ["seat", "section", "row", "gate", "where is", "find my seat", "upgrade"],
            "food": ["food", "eat", "drink", "concession", "restaurant", "menu", "hungry", "thirsty", "beer", "water"],
            "restroom": ["restroom", "bathroom", "toilet", "wc", "loo"],
            "merchandise": ["merchandise", "store", "shop", "jersey", "souvenir", "gift", "buy"],
            "events": ["event", "halftime", "pre-game", "post-game", "concert", "activities"],
            "amenities": ["wifi", "wi-fi", "charging", "lost and found", "coat check", "family room"],
            "policies": ["policy", "rule", "allowed", "prohibited", "bag", "re-entry", "age limit"],
        }

        for intent, keywords in intent_keywords.items():
            if any(kw in query_lower for kw in keywords):
                return intent

        return "general"
