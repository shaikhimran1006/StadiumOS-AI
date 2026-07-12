"""Tests for GenerativeAI service."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def mock_vertex_ai():
    with patch("app.ai.services.generative_ai_service.vertexai") as mock_vertexai, \
         patch("app.ai.services.generative_ai_service.GenerativeModel") as mock_model_cls, \
         patch("app.ai.services.generative_ai_service.GenerationConfig") as mock_config_cls:
        mock_model = MagicMock()
        mock_model_cls.return_value = mock_model
        yield mock_model_cls


class TestGenerativeAIServiceInit:
    def test_initialization(self, mock_vertex_ai):
        from app.ai.services.generative_ai_service import GenerativeAIService
        service = GenerativeAIService()
        assert service._initialized is True
        assert service._model is not None

    def test_initialization_failure(self, mock_vertex_ai):
        with patch("app.ai.services.generative_ai_service.GenerativeModel", side_effect=Exception("Init failed")):
            from app.ai.services.generative_ai_service import GenerativeAIService
            service = GenerativeAIService()
            assert service._initialized is False


class TestGenerateResponse:
    @pytest.mark.asyncio
    async def test_generate_response_success(self, mock_vertex_ai):
        mock_model = MagicMock()
        mock_model.generate_content.return_value.text = "The match starts at 3pm."
        mock_vertex_ai.return_value = mock_model

        from app.ai.services.generative_ai_service import GenerativeAIService
        service = GenerativeAIService()
        service._model = mock_model

        result = await service.generate_response("What time is the match?")
        assert result == "The match starts at 3pm."

    @pytest.mark.asyncio
    async def test_generate_response_not_initialized(self, mock_vertex_ai):
        from app.ai.services.generative_ai_service import GenerativeAIService
        service = GenerativeAIService()
        service._initialized = False
        service._model = None

        with pytest.raises(RuntimeError, match="not initialized"):
            await service.generate_response("Test")

    @pytest.mark.asyncio
    async def test_generate_response_empty_text(self, mock_vertex_ai):
        mock_model = MagicMock()
        mock_model.generate_content.return_value.text = None
        mock_vertex_ai.return_value = mock_model

        from app.ai.services.generative_ai_service import GenerativeAIService
        service = GenerativeAIService()
        service._model = mock_model

        result = await service.generate_response("Test")
        assert result == ""


class TestGenerateWithContext:
    @pytest.mark.asyncio
    async def test_generate_with_context(self, mock_vertex_ai):
        mock_model = MagicMock()
        mock_model.generate_content.return_value.text = "Based on the docs, the answer is yes."
        mock_vertex_ai.return_value = mock_model

        from app.ai.services.generative_ai_service import GenerativeAIService
        service = GenerativeAIService()
        service._model = mock_model

        context = [
            {"content": "Stadium opens at 5pm", "source": "stadium_info"},
            {"content": "Gates close at 11pm", "source": "stadium_info"},
        ]

        result = await service.generate_with_context(
            query="What time does the stadium open?",
            context=context,
        )
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_generate_with_context_not_initialized(self, mock_vertex_ai):
        from app.ai.services.generative_ai_service import GenerativeAIService
        service = GenerativeAIService()
        service._initialized = False
        service._model = None

        with pytest.raises(RuntimeError, match="not initialized"):
            await service.generate_with_context(query="Test", context=[])


class TestGenerateStructuredOutput:
    @pytest.mark.asyncio
    async def test_generate_structured_output(self, mock_vertex_ai):
        mock_model = MagicMock()
        mock_model.generate_content.return_value.text = json.dumps({
            "answer": "The stadium opens at 5pm",
            "confidence": 0.95,
        })
        mock_vertex_ai.return_value = mock_model

        from app.ai.services.generative_ai_service import GenerativeAIService
        service = GenerativeAIService()
        service._model = mock_model

        schema = {
            "type": "object",
            "properties": {
                "answer": {"type": "string"},
                "confidence": {"type": "number"},
            },
        }

        result = await service.generate_structured_output(
            prompt="What time does the stadium open?",
            output_schema=schema,
        )
        assert isinstance(result, dict)
        assert "answer" in result


class TestParseJsonResponse:
    def test_parse_valid_json(self):
        from app.ai.services.generative_ai_service import GenerativeAIService
        service = GenerativeAIService()

        raw = '{"answer": "yes", "confidence": 0.9}'
        result = service._parse_json_response(raw, {})
        assert result["answer"] == "yes"
        assert result["confidence"] == 0.9

    def test_parse_json_with_markdown_fences(self):
        from app.ai.services.generative_ai_service import GenerativeAIService
        service = GenerativeAIService()

        raw = '```json\n{"answer": "yes"}\n```'
        result = service._parse_json_response(raw, {})
        assert result["answer"] == "yes"

    def test_parse_invalid_json(self):
        from app.ai.services.generative_ai_service import GenerativeAIService
        service = GenerativeAIService()

        raw = "This is not JSON at all"
        result = service._parse_json_response(raw, {})
        assert result.get("parse_error") is True

    def test_parse_non_object_json(self):
        from app.ai.services.generative_ai_service import GenerativeAIService
        service = GenerativeAIService()

        raw = '[1, 2, 3]'
        result = service._parse_json_response(raw, {})
        assert "raw_output" in result


class TestFormatContextBlock:
    def test_format_context(self):
        from app.ai.services.generative_ai_service import GenerativeAIService
        service = GenerativeAIService()

        context = [
            {"content": "Stadium opens at 5pm", "source": "info1"},
            {"content": "Gates close at 11pm"},
        ]
        block = service._format_context_block(context)
        assert "info1" in block
        assert "Document 2" in block
        assert "5pm" in block
        assert "11pm" in block
