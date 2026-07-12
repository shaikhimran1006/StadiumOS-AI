"""Tests for AI agents."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.ai.agents.accessibility_agent import AccessibilityAgent
from app.ai.agents.base_agent import AgentResponse, BaseAgent
from app.ai.agents.fan_agent import FanAgent
from app.ai.agents.medical_agent import MedicalAgent
from app.ai.agents.operations_agent import OperationsAgent
from app.ai.agents.security_agent import SecurityAgent
from app.ai.agents.sustainability_agent import SustainabilityAgent
from app.ai.agents.transport_agent import TransportAgent
from app.ai.agents.volunteer_agent import VolunteerAgent


@pytest.fixture(autouse=True)
def mock_vertex_ai():
    with patch("app.ai.agents.base_agent.vertexai") as mock_vertexai, \
         patch("app.ai.agents.base_agent.GenerativeModel") as mock_model_cls, \
         patch("app.ai.agents.base_agent.GenerationConfig") as mock_config_cls:
        mock_model = MagicMock()
        mock_model_cls.return_value = mock_model
        yield


class TestBaseAgentAbstract:
    def test_cannot_instantiate_base_agent(self):
        with pytest.raises(TypeError):
            BaseAgent()


class TestAgentResponse:
    def test_create_agent_response(self):
        resp = AgentResponse(
            response_text="Hello!",
            agent_name="FanAgent",
            confidence=0.95,
        )
        assert resp.response_text == "Hello!"
        assert resp.agent_name == "FanAgent"
        assert resp.confidence == 0.95
        assert resp.actions == []
        assert resp.sources == []

    def test_agent_response_to_dict(self):
        resp = AgentResponse(
            response_text="Help",
            agent_name="MedicalAgent",
            confidence=0.80,
            metadata={"intent": "first_aid"},
            actions=[{"action": "dispatch_first_aid", "id": "123"}],
            sources=["medical_protocol_v2"],
        )
        d = resp.to_dict()
        assert d["response_text"] == "Help"
        assert d["agent_name"] == "MedicalAgent"
        assert len(d["actions"]) == 1
        assert len(d["sources"]) == 1


class TestFanAgent:
    def test_agent_name(self):
        agent = FanAgent()
        assert agent.agent_name == "FanAgent"

    def test_system_prompt_not_empty(self):
        agent = FanAgent()
        assert len(agent.system_prompt) > 0

    @patch.object(FanAgent, "_call_gemini")
    def test_process_returns_agent_response(self, mock_call_gemini):
        mock_call_gemini.return_value = "The food court is near section A5!"
        agent = FanAgent()
        response = agent.process("Where can I get food?", {})
        assert isinstance(response, AgentResponse)
        assert response.agent_name == "FanAgent"
        assert 0.0 <= response.confidence <= 1.0

    @patch.object(FanAgent, "_call_gemini")
    def test_process_classifies_seating_intent(self, mock_call_gemini):
        mock_call_gemini.return_value = "Your seat is in row 12."
        agent = FanAgent()
        response = agent.process("Where is my seat?", {})
        assert response.metadata["intent"] == "seating"

    @patch.object(FanAgent, "_call_gemini")
    def test_process_classifies_food_intent(self, mock_call_gemini):
        mock_call_gemini.return_value = "Try the food court!"
        agent = FanAgent()
        response = agent.process("I'm hungry, what food is available?", {})
        assert response.metadata["intent"] == "food"

    @patch.object(FanAgent, "_call_gemini")
    def test_process_classifies_match_intent(self, mock_call_gemini):
        mock_call_gemini.return_value = "The match starts at 3pm."
        agent = FanAgent()
        response = agent.process("What time is the game?", {})
        assert response.metadata["intent"] == "match_info"


class TestSecurityAgent:
    def test_agent_name(self):
        agent = SecurityAgent()
        assert agent.agent_name == "SecurityAgent"

    @patch.object(SecurityAgent, "_call_gemini")
    def test_process_returns_agent_response(self, mock_call_gemini):
        mock_call_gemini.return_value = "Security team has been alerted."
        agent = SecurityAgent()
        response = agent.process("There is a suspicious person", {})
        assert isinstance(response, AgentResponse)
        assert response.agent_name == "SecurityAgent"

    @patch.object(SecurityAgent, "_call_gemini")
    def test_process_classifies_incident_report(self, mock_call_gemini):
        mock_call_gemini.return_value = "Incident logged."
        agent = SecurityAgent()
        response = agent.process("I want to report an incident - theft", {})
        assert response.metadata["category"] == "incident_report"

    @patch.object(SecurityAgent, "_call_gemini")
    def test_process_assesses_critical_severity(self, mock_call_gemini):
        mock_call_gemini.return_value = "Emergency protocol activated."
        agent = SecurityAgent()
        response = agent.process("Active shooter reported at Gate 3", {})
        assert response.metadata["severity"] == "critical"

    @patch.object(SecurityAgent, "_call_gemini")
    def test_process_assesses_medium_severity(self, mock_call_gemini):
        mock_call_gemini.return_value = "Investigating."
        agent = SecurityAgent()
        response = agent.process("Suspicious behavior near VIP section", {})
        assert response.metadata["severity"] == "medium"

    @patch.object(SecurityAgent, "_call_gemini")
    def test_process_evacuation_category(self, mock_call_gemini):
        mock_call_gemini.return_value = "Evacuation protocol initiated."
        agent = SecurityAgent()
        response = agent.process("Fire alarm activated, need evacuation", {})
        assert response.metadata["category"] == "evacuation"


class TestMedicalAgent:
    def test_agent_name(self):
        agent = MedicalAgent()
        assert agent.agent_name == "MedicalAgent"

    @patch.object(MedicalAgent, "_call_gemini")
    def test_process_returns_agent_response(self, mock_call_gemini):
        mock_call_gemini.return_value = "Medical team dispatched."
        agent = MedicalAgent()
        response = agent.process("Someone is having chest pain", {})
        assert isinstance(response, AgentResponse)
        assert response.agent_name == "MedicalAgent"

    @patch.object(MedicalAgent, "_call_gemini")
    def test_process_classifies_emergency_medical(self, mock_call_gemini):
        mock_call_gemini.return_value = "Emergency protocol activated."
        agent = MedicalAgent()
        response = agent.process("Heart attack! Person is unconscious", {})
        assert response.metadata["category"] == "emergency_medical"

    @patch.object(MedicalAgent, "_call_gemini")
    def test_process_assesses_emergency_severity(self, mock_call_gemini):
        mock_call_gemini.return_value = "EMT dispatched immediately."
        agent = MedicalAgent()
        response = agent.process("Person is not breathing", {})
        assert response.metadata["severity"] == "emergency"


class TestTransportAgent:
    def test_agent_name(self):
        agent = TransportAgent()
        assert agent.agent_name == "TransportAgent"

    @patch.object(TransportAgent, "_call_gemini")
    def test_process_returns_agent_response(self, mock_call_gemini):
        mock_call_gemini.return_value = "Parking lot B is available."
        agent = TransportAgent()
        response = agent.process("Where can I park?", {})
        assert isinstance(response, AgentResponse)
        assert response.agent_name == "TransportAgent"

    @patch.object(TransportAgent, "_call_gemini")
    def test_process_classifies_parking_mode(self, mock_call_gemini):
        mock_call_gemini.return_value = "Parking garage on level 2."
        agent = TransportAgent()
        response = agent.process("Is there parking available?", {})
        assert response.metadata["transport_mode"] == "parking"

    @patch.object(TransportAgent, "_call_gemini")
    def test_process_classifies_transit_mode(self, mock_call_gemini):
        mock_call_gemini.return_value = "Train arrives every 10 minutes."
        agent = TransportAgent()
        response = agent.process("What train gets me to the stadium?", {})
        assert response.metadata["transport_mode"] == "transit"

    @patch.object(TransportAgent, "_call_gemini")
    def test_process_determines_arrival_direction(self, mock_call_gemini):
        mock_call_gemini.return_value = "Take exit 16W."
        agent = TransportAgent()
        response = agent.process("How do I get to the stadium?", {})
        assert response.metadata["direction"] == "arrival"

    @patch.object(TransportAgent, "_call_gemini")
    def test_process_determines_departure_direction(self, mock_call_gemini):
        mock_call_gemini.return_value = "Use Gate 4 for quickest exit."
        agent = TransportAgent()
        response = agent.process("I'm leaving the stadium, fastest route home?", {})
        assert response.metadata["direction"] == "departure"


class TestAllAgentsReturnAgentResponse:
    @pytest.mark.parametrize("agent_cls", [
        FanAgent, SecurityAgent, MedicalAgent, TransportAgent,
        OperationsAgent, AccessibilityAgent, VolunteerAgent, SustainabilityAgent,
    ])
    @patch("app.ai.agents.base_agent.GenerativeModel")
    @patch("app.ai.agents.base_agent.GenerationConfig")
    def test_all_agents_return_response(self, mock_config, mock_model_cls, agent_cls):
        mock_model = MagicMock()
        mock_model.generate_content.return_value.text = "Test response from agent."
        mock_model_cls.return_value = mock_model

        agent = agent_cls()
        response = agent.process("Test query", {})
        assert isinstance(response, AgentResponse)
        assert response.response_text is not None
        assert response.agent_name is not None
        assert 0.0 <= response.confidence <= 1.0
