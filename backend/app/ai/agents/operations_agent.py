"""Stadium operations agent for facility management."""

import logging
from typing import Any

from app.ai.agents.base_agent import BaseAgent, AgentResponse
from app.ai.prompts.system_prompts import OPERATIONS_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class OperationsAgent(BaseAgent):
    """Agent specialized in stadium operations and facility management."""

    @property
    def agent_name(self) -> str:
        return "OperationsAgent"

    @property
    def system_prompt(self) -> str:
        return OPERATIONS_SYSTEM_PROMPT

    def process(self, query: str, context: dict[str, Any]) -> AgentResponse:
        """Process operations-related queries."""
        query_lower = query.lower()
        domain = self._classify_domain(query_lower)
        priority = self._assess_priority(query_lower)

        enriched_context = {
            **context,
            "ops_domain": domain,
            "priority_level": priority,
            "service_type": "operations",
        }

        prompt_parts = self._build_prompt(query, enriched_context)
        raw_response = self._call_gemini(prompt_parts)
        parsed = self._parse_response(raw_response)
        confidence = self._compute_confidence(parsed["clean_text"], query)

        if priority == "critical":
            parsed["actions"].append({"action": "escalate_operations", "id": "auto"})
        if domain == "crowd_flow":
            parsed["actions"].append({"action": "monitor_crowd_density", "id": "auto"})

        return AgentResponse(
            response_text=parsed["clean_text"],
            agent_name=self.agent_name,
            confidence=confidence,
            metadata={
                "domain": domain,
                "priority": priority,
                "raw_query": query,
            },
            actions=parsed["actions"],
            sources=parsed["sources"],
        )

    def _classify_domain(self, query_lower: str) -> str:
        domain_keywords: dict[str, list[str]] = {
            "facility": ["hvac", "lighting", "plumbing", "electrical", "facility", "building", "infrastructure", "maintenance", "repair"],
            "crowd_flow": ["crowd", "flow", "density", "congestion", "capacity", "occupancy", "bottleneck", "crowd control"],
            "logistics": ["delivery", "shipping", "supply", "inventory", "warehouse", "freight", "loading dock"],
            "staffing": ["staff", "shift", "schedule", "workforce", "employee", "personnel", "overtime", "labor"],
            "vendor": ["vendor", "concession", "catering", "food service", "beverage", "vendor management"],
            "utilities": ["power", "water", "gas", "electricity", "utility", "energy consumption", "outage"],
        }

        for domain, keywords in domain_keywords.items():
            if any(kw in query_lower for kw in keywords):
                return domain

        return "general_ops"

    def _assess_priority(self, query_lower: str) -> str:
        critical_keywords = ["emergency", "critical", "failure", "down", "outage", "flooding", "fire", "gas leak"]
        high_keywords = ["urgent", "asap", "immediately", "broken", "not working", "complaint"]

        if any(kw in query_lower for kw in critical_keywords):
            return "critical"
        if any(kw in query_lower for kw in high_keywords):
            return "high"
        return "normal"
