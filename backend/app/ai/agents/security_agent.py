"""Security operations agent."""

import logging
from typing import Any

from app.ai.agents.base_agent import BaseAgent, AgentResponse
from app.ai.prompts.system_prompts import SECURITY_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class SecurityAgent(BaseAgent):
    """Agent specialized in stadium security operations."""

    @property
    def agent_name(self) -> str:
        return "SecurityAgent"

    @property
    def system_prompt(self) -> str:
        return SECURITY_SYSTEM_PROMPT

    def process(self, query: str, context: dict[str, Any]) -> AgentResponse:
        """Process security-related queries."""
        query_lower = query.lower()
        category = self._classify_category(query_lower)
        severity = self._assess_severity(query_lower)

        security_context = context.get("security", {})
        enriched_context = {
            **context,
            "security_category": category,
            "severity_level": severity,
            "reporting_officer": security_context.get("officer_id"),
            "zone": security_context.get("zone"),
            "service_type": "security_operations",
        }

        prompt_parts = self._build_prompt(query, enriched_context)
        raw_response = self._call_gemini(prompt_parts)
        parsed = self._parse_response(raw_response)
        confidence = self._compute_confidence(parsed["clean_text"], query)

        if severity in ("critical", "high"):
            parsed["actions"].append({"action": "escalate_security", "id": "auto"})
        if category == "incident_report":
            parsed["actions"].append({"action": "log_incident", "id": "auto"})
        if category == "evacuation":
            parsed["actions"].append({"action": "activate_evacuation_protocol", "id": "auto"})

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
            "incident_report": ["incident", "report", "crime", "theft", "assault", "vandalism", "fight", "altercation"],
            "threat_assessment": ["threat", "suspicious", "unattended", "package", "behavior", "watch", "alert"],
            "emergency_protocol": ["emergency", "code red", "code blue", "evacuate", "lockdown", "shelter"],
            "evacuation": ["evacuate", "evacuation", "exit", "escape", "fire alarm", "bomb threat"],
            "access_control": ["credential", "badge", "access", "perimeter", "restricted", "authorization", "tailgating"],
            "crowd_safety": ["crowd", "crush", "stampede", "density", "surge", "push", "trampling"],
            "lost_person": ["lost", "missing", "child", "person", "looking for", "separated"],
        }

        for category, keywords in category_keywords.items():
            if any(kw in query_lower for kw in keywords):
                return category

        return "general_security"

    def _assess_severity(self, query_lower: str) -> str:
        critical = ["active shooter", "bomb", "fire", "explosion", "mass casualty", "hostage"]
        high = ["weapon", "assault", "injury", "medical emergency", "fighting", "armed"]
        medium = ["suspicious", "theft", "trespassing", "intoxicated", "disorderly"]

        if any(kw in query_lower for kw in critical):
            return "critical"
        if any(kw in query_lower for kw in high):
            return "high"
        if any(kw in query_lower for kw in medium):
            return "medium"
        return "low"
