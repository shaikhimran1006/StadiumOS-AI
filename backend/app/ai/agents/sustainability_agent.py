"""Sustainability advisory agent."""

import logging
from typing import Any

from app.ai.agents.base_agent import BaseAgent, AgentResponse
from app.ai.prompts.system_prompts import SUSTAINABILITY_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class SustainabilityAgent(BaseAgent):
    """Agent specialized in sustainability and environmental initiatives."""

    @property
    def agent_name(self) -> str:
        return "SustainabilityAgent"

    @property
    def system_prompt(self) -> str:
        return SUSTAINABILITY_SYSTEM_PROMPT

    def process(self, query: str, context: dict[str, Any]) -> AgentResponse:
        """Process sustainability-related queries."""
        query_lower = query.lower()
        domain = self._classify_domain(query_lower)
        audience = self._determine_audience(query_lower)

        sustainability_context = context.get("sustainability", {})
        enriched_context = {
            **context,
            "sustainability_domain": domain,
            "audience": audience,
            "current_metrics": sustainability_context.get("metrics", {}),
            "service_type": "sustainability",
        }

        prompt_parts = self._build_prompt(query, enriched_context)
        raw_response = self._call_gemini(prompt_parts)
        parsed = self._parse_response(raw_response)
        confidence = self._compute_confidence(parsed["clean_text"], query)

        if domain == "recycling":
            parsed["actions"].append({"action": "get_recycling_guide", "id": "auto"})
        elif domain == "energy":
            parsed["actions"].append({"action": "get_energy_metrics", "id": "auto"})
        elif domain == "carbon":
            parsed["actions"].append({"action": "calculate_carbon_footprint", "id": "auto"})

        return AgentResponse(
            response_text=parsed["clean_text"],
            agent_name=self.agent_name,
            confidence=confidence,
            metadata={
                "domain": domain,
                "audience": audience,
                "raw_query": query,
            },
            actions=parsed["actions"],
            sources=parsed["sources"],
        )

    def _classify_domain(self, query_lower: str) -> str:
        domain_keywords: dict[str, list[str]] = {
            "recycling": ["recycle", "recycling", "waste", "trash", "garbage", "compost", "sort", "disposal", "bin"],
            "energy": ["energy", "power", "electricity", "solar", "renewable", "grid", "consumption", "efficiency", "led"],
            "water": ["water", "conservation", "drought", "rainwater", "irrigation", "plumbing", "leak"],
            "carbon": ["carbon", "emission", "footprint", "offset", "climate", "co2", "greenhouse", "neutral"],
            "green_initiatives": ["green", "initiative", "program", "certification", "leed", "sustainable", "eco-friendly", "environment"],
            "vendor_sustainability": ["vendor", "supplier", "procurement", "sourcing", "supply chain", "local sourcing"],
        }

        for domain, keywords in domain_keywords.items():
            if any(kw in query_lower for kw in keywords):
                return domain

        return "general_sustainability"

    def _determine_audience(self, query_lower: str) -> str:
        if any(kw in query_lower for kw in ["fan", "visitor", "attendee", "guest", "where do i recycle"]):
            return "fan"
        if any(kw in query_lower for kw in ["operations", "staff", "facility", "building", "install"]):
            return "operations"
        if any(kw in query_lower for kw in ["report", "metrics", "kpi", "goal", "target", "compliance"]):
            return "management"
        return "general"
