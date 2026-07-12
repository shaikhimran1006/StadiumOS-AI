"""Volunteer coordination agent."""

import logging
from typing import Any

from app.ai.agents.base_agent import BaseAgent, AgentResponse
from app.ai.prompts.system_prompts import VOLUNTEER_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class VolunteerAgent(BaseAgent):
    """Agent specialized in volunteer coordination and management."""

    @property
    def agent_name(self) -> str:
        return "VolunteerAgent"

    @property
    def system_prompt(self) -> str:
        return VOLUNTEER_SYSTEM_PROMPT

    def process(self, query: str, context: dict[str, Any]) -> AgentResponse:
        """Process volunteer-related queries."""
        query_lower = query.lower()
        intent = self._classify_intent(query_lower)

        volunteer_context = context.get("volunteer", {})
        enriched_context = {
            **context,
            "volunteer_intent": intent,
            "volunteer_id": volunteer_context.get("volunteer_id"),
            "volunteer_skills": volunteer_context.get("skills", []),
            "current_shift": volunteer_context.get("current_shift"),
            "service_type": "volunteer_management",
        }

        prompt_parts = self._build_prompt(query, enriched_context)
        raw_response = self._call_gemini(prompt_parts)
        parsed = self._parse_response(raw_response)
        confidence = self._compute_confidence(parsed["clean_text"], query)

        if intent == "task_assignment":
            parsed["actions"].append({"action": "assign_volunteer_task", "id": "auto"})
        elif intent == "scheduling":
            parsed["actions"].append({"action": "update_volunteer_schedule", "id": "auto"})
        elif intent == "training":
            parsed["actions"].append({"action": "provide_training_material", "id": "auto"})

        return AgentResponse(
            response_text=parsed["clean_text"],
            agent_name=self.agent_name,
            confidence=confidence,
            metadata={
                "intent": intent,
                "volunteer_id": volunteer_context.get("volunteer_id"),
                "raw_query": query,
            },
            actions=parsed["actions"],
            sources=parsed["sources"],
        )

    def _classify_intent(self, query_lower: str) -> str:
        intent_keywords: dict[str, list[str]] = {
            "task_assignment": ["task", "assign", "role", "duty", "position", "what should i do", "help with"],
            "scheduling": ["schedule", "shift", "time", "when", "calendar", "availability", "swap", "change shift"],
            "training": ["training", "how to", "procedure", "protocol", "learn", "orientation", "guide"],
            "check_in": ["check in", "clock in", "arrived", "here", "reporting", "starting shift"],
            "check_out": ["check out", "clock out", "leaving", "end shift", "done", "finished"],
            "equipment": ["equipment", "supplies", "badge", "vest", "radio", "walkie", "uniform"],
            "reporting": ["report", "incident", "issue", "problem", "feedback", "suggest"],
        }

        for intent, keywords in intent_keywords.items():
            if any(kw in query_lower for kw in keywords):
                return intent

        return "general_volunteer"
