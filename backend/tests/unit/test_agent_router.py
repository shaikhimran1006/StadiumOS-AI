"""Tests for AgentRouter."""

from __future__ import annotations

import pytest

from app.ai.agents.base_agent import AgentResponse
from app.ai.router.agent_router import (
    AGENT_KEYWORDS,
    CATEGORY_PRIORITY,
    AgentRouter,
)


@pytest.fixture
def router() -> AgentRouter:
    return AgentRouter()


class TestAgentRouterInit:
    def test_agents_loaded(self, router: AgentRouter):
        assert len(router.available_agents) == 8
        assert "fan" in router.available_agents
        assert "security" in router.available_agents
        assert "medical" in router.available_agents
        assert "transport" in router.available_agents

    def test_fallback_is_fan(self, router: AgentRouter):
        assert router._fallback_agent.agent_name == "FanAgent"


class TestRouteQuery:
    def test_route_fan_query(self, router: AgentRouter):
        assert router.route_query("Where can I get food?") == "fan"

    def test_route_security_query(self, router: AgentRouter):
        assert router.route_query("There is a suspicious package near Gate 3") == "security"

    def test_route_medical_query(self, router: AgentRouter):
        assert router.route_query("Someone is having a heart attack") == "medical"

    def test_route_transport_query(self, router: AgentRouter):
        assert router.route_query("Where can I park my car?") == "transport"

    def test_route_operations_query(self, router: AgentRouter):
        assert router.route_query("The HVAC system in section B needs repair") == "operations"

    def test_route_accessibility_query(self, router: AgentRouter):
        assert router.route_query("I need wheelchair accessible seating") == "accessibility"

    def test_route_volunteer_query(self, router: AgentRouter):
        assert router.route_query("Volunteer check in for shift assignment") == "volunteer"

    def test_route_sustainability_query(self, router: AgentRouter):
        assert router.route_query("Where is the recycling bin?") == "sustainability"

    def test_fallback_when_no_match(self, router: AgentRouter):
        assert router.route_query("asdfghjkl") == "fan"

    def test_empty_query_fallback(self, router: AgentRouter):
        assert router.route_query("") == "fan"

    def test_context_force_agent(self, router: AgentRouter):
        ctx = {"force_agent": "security"}
        result = router.route_query("random text", ctx)
        assert result == "security"

    def test_context_force_invalid_agent_ignored(self, router: AgentRouter):
        ctx = {"force_agent": "nonexistent"}
        result = router.route_query("random text", ctx)
        assert result == "fan"


class TestScoreCategories:
    def test_security_keywords_score(self, router: AgentRouter):
        scores = router._score_categories("suspicious package bomb threat")
        assert scores["security"] >= 3

    def test_medical_keywords_score(self, router: AgentRouter):
        scores = router._score_categories("heart attack chest pain")
        assert scores["medical"] >= 2

    def test_multi_word_keywords(self, router: AgentRouter):
        scores = router._score_categories("lost and found")
        assert scores["fan"] >= 2

    def test_case_insensitive(self, router: AgentRouter):
        scores_lower = router._score_categories("SECURITY incident threat")
        scores_upper = router._score_categories("security incident threat")
        assert scores_lower["security"] == scores_upper["security"]


class TestGetAgent:
    def test_get_valid_agent(self, router: AgentRouter):
        agent = router.get_agent("fan")
        assert agent.agent_name == "FanAgent"

    def test_get_invalid_agent_raises(self, router: AgentRouter):
        with pytest.raises(ValueError, match="Unknown agent"):
            router.get_agent("nonexistent")

    def test_available_agents_list(self, router: AgentRouter):
        agents = router.available_agents
        assert isinstance(agents, list)
        assert len(agents) > 0


class TestProcessQuery:
    def test_returns_agent_response(self, router: AgentRouter):
        response = router.process_query("Where is my seat?")
        assert isinstance(response, AgentResponse)
        assert response.response_text is not None
        assert response.agent_name is not None
        assert 0.0 <= response.confidence <= 1.0


class TestKeywordCoverage:
    def test_all_agents_have_keywords(self):
        for agent_name in AGENT_KEYWORDS:
            assert len(AGENT_KEYWORDS[agent_name]) > 0

    def test_priority_order(self):
        assert CATEGORY_PRIORITY[0] == "security"
        assert CATEGORY_PRIORITY[-1] == "fan"
