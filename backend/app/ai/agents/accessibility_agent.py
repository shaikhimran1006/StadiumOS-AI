"""Accessibility services agent."""

import logging
from typing import Any

from app.ai.agents.base_agent import BaseAgent, AgentResponse
from app.ai.prompts.system_prompts import ACCESSIBILITY_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class AccessibilityAgent(BaseAgent):
    """Agent specialized in accessibility services and accommodations."""

    @property
    def agent_name(self) -> str:
        return "AccessibilityAgent"

    @property
    def system_prompt(self) -> str:
        return ACCESSIBILITY_SYSTEM_PROMPT

    def process(self, query: str, context: dict[str, Any]) -> AgentResponse:
        """Process accessibility-related queries."""
        query_lower = query.lower()
        need_type = self._classify_need(query_lower)
        urgency = self._assess_urgency(query_lower)

        accessibility_context = context.get("accessibility", {})
        enriched_context = {
            **context,
            "accessibility_need": need_type,
            "urgency": urgency,
            "visitor_location": accessibility_context.get("current_location"),
            "mobility_level": accessibility_context.get("mobility_level"),
            "service_type": "accessibility_services",
        }

        prompt_parts = self._build_prompt(query, enriched_context)
        raw_response = self._call_gemini(prompt_parts)
        parsed = self._parse_response(raw_response)
        confidence = self._compute_confidence(parsed["clean_text"], query)

        if need_type == "wheelchair":
            parsed["actions"].append({"action": "get_accessible_route", "id": "auto"})
        elif need_type == "hearing":
            parsed["actions"].append({"action": "request_sign_language", "id": "auto"})

        return AgentResponse(
            response_text=parsed["clean_text"],
            agent_name=self.agent_name,
            confidence=confidence,
            metadata={
                "need_type": need_type,
                "urgency": urgency,
                "raw_query": query,
            },
            actions=parsed["actions"],
            sources=parsed["sources"],
        )

    def _classify_need(self, query_lower: str) -> str:
        need_keywords: dict[str, list[str]] = {
            "wheelchair": ["wheelchair", "mobility", "walker", "scooter", "ramp", "elevator", "lift", "accessible seating", "disability"],
            "hearing": ["hearing", "deaf", "sign language", "interpreter", "assistive listening", "caption", "subtitle", "audio"],
            "visual": ["visual", "blind", "low vision", "braille", "large print", "audio description", "guide dog", "service animal"],
            "cognitive": ["cognitive", "autism", "sensory", "quiet room", "sensory room", "overstimulation", "neurodivergent"],
            "medical_equipment": ["oxygen", "medical device", "electric wheelchair", "power chair", "medical equipment", "cpap"],
            "companion": ["companion", "caregiver", "assistant", "aide", "helper", "companion seat"],
        }

        for need, keywords in need_keywords.items():
            if any(kw in query_lower for kw in keywords):
                return need

        return "general_accessibility"

    def _assess_urgency(self, query_lower: str) -> str:
        if any(kw in query_lower for kw in ["emergency", "stuck", "trapped", "cannot move", "fallen"]):
            return "immediate"
        if any(kw in query_lower for kw in ["right now", "currently", "where am i", "need help now"]):
            return "high"
        return "normal"
