"""Medical services agent."""

import logging
from typing import Any

from app.ai.agents.base_agent import BaseAgent, AgentResponse
from app.ai.prompts.system_prompts import MEDICAL_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class MedicalAgent(BaseAgent):
    """Agent specialized in medical services and health support."""

    @property
    def agent_name(self) -> str:
        return "MedicalAgent"

    @property
    def system_prompt(self) -> str:
        return MEDICAL_SYSTEM_PROMPT

    def process(self, query: str, context: dict[str, Any]) -> AgentResponse:
        """Process medical-related queries."""
        query_lower = query.lower()
        category = self._classify_category(query_lower)
        severity = self._assess_severity(query_lower)

        medical_context = context.get("medical", {})
        enriched_context = {
            **context,
            "medical_category": category,
            "severity": severity,
            "visitor_info": medical_context.get("visitor_info"),
            "known_conditions": medical_context.get("known_conditions", []),
            "service_type": "medical_services",
        }

        prompt_parts = self._build_prompt(query, enriched_context)
        raw_response = self._call_gemini(prompt_parts)
        parsed = self._parse_response(raw_response)
        confidence = self._compute_confidence(parsed["clean_text"], query)

        if severity in ("critical", "emergency"):
            parsed["actions"].append({"action": "activate_emergency_medical", "id": "auto"})
        if category == "first_aid":
            parsed["actions"].append({"action": "dispatch_first_aid", "id": "auto"})
        if category == "medical_station":
            parsed["actions"].append({"action": "get_nearest_medical_station", "id": "auto"})

        return AgentResponse(
            response_text=parsed["clean_text"],
            agent_name=self.agent_name,
            confidence=confidence,
            metadata={
                "category": category,
                "severity": severity,
                "raw_query": query,
            },
            actions=parsed["actions"],
            sources=parsed["sources"],
        )

    def _classify_category(self, query_lower: str) -> str:
        category_keywords: dict[str, list[str]] = {
            "first_aid": ["first aid", "bandage", "ice", "wound", "cut", "burn", "sprain", "headache", "pain", "medication"],
            "emergency_medical": ["heart attack", "stroke", "seizure", "unconscious", "not breathing", "choking", "allergic reaction", "anaphylaxis"],
            "medical_station": ["medical station", "first aid station", "infirmary", "clinic", "where is medical", "need a doctor"],
            "health_alert": ["heat", "heatstroke", "dehydration", "sunburn", "cold", "hypothermia", "air quality", "uv index"],
            "mental_health": ["anxiety", "panic", "stress", "overwhelmed", "mental health", "need to calm", "sensory overload"],
            "medication": ["medication", "pills", "prescription", "medicine", "pharmacy", "drug", "insulin", "epipen"],
        }

        for category, keywords in category_keywords.items():
            if any(kw in query_lower for kw in keywords):
                return category

        return "general_medical"

    def _assess_severity(self, query_lower: str) -> str:
        emergency = ["unconscious", "not breathing", "heart attack", "stroke", "seizure", "choking", "severe bleeding", "anaphylaxis"]
        high = ["chest pain", "difficulty breathing", "severe pain", "high fever", "allergic reaction", "broken bone"]
        medium = ["injury", "wound", "burn", "sprain", "faint", "dizzy", "nausea"]

        if any(kw in query_lower for kw in emergency):
            return "emergency"
        if any(kw in query_lower for kw in high):
            return "high"
        if any(kw in query_lower for kw in medium):
            return "medium"
        return "low"
