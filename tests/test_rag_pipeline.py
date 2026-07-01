import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from app.rag.pipeline import RAGPipeline
from app.utils.observability import RequestMetrics


class TestRAGPipeline:

    def setup_method(self):
        with patch("google.generativeai.GenerativeModel") as mock_model_cls:
            self.mock_model = MagicMock()
            mock_model_cls.return_value = self.mock_model
            with patch("google.generativeai.configure"):
                self.pipeline = RAGPipeline()
                self.pipeline._model = self.mock_model

    def test_format_history_empty(self):
        result = self.pipeline._format_history([])
        assert result == "No prior conversation."

    def test_format_history_with_turns(self):
        history = [
            {"role": "user", "content": "My bill is too high"},
            {"role": "assistant", "content": "I can help with that"},
        ]
        result = self.pipeline._format_history(history)
        assert "Customer: My bill is too high" in result
        assert "Nova: I can help with that" in result

    def test_format_history_truncates_to_six_turns(self):
        history = [{"role": "user", "content": f"Message {i}"} for i in range(10)]
        result = self.pipeline._format_history(history)
        turn_count = result.count("Customer:")
        assert turn_count <= 6

    def test_format_context_empty(self):
        result = self.pipeline._format_context([])
        assert "No relevant knowledge base content" in result

    def test_format_context_with_docs(self):
        docs = [
            {"content": "Billing FAQ content here", "source": "billing_faq", "relevance_score": 0.92},
            {"content": "Plan comparison data", "source": "plan_comparison", "relevance_score": 0.85},
        ]
        result = self.pipeline._format_context(docs)
        assert "billing_faq" in result
        assert "0.92" in result
        assert "Billing FAQ content here" in result

    def test_map_intent_to_category_billing(self):
        assert self.pipeline._map_intent_to_category("billing_inquiry") == "billing"
        assert self.pipeline._map_intent_to_category("billing_dispute") == "billing"
        assert self.pipeline._map_intent_to_category("payment_issue") == "billing"

    def test_map_intent_to_category_network(self):
        assert self.pipeline._map_intent_to_category("network_issue") == "network"
        assert self.pipeline._map_intent_to_category("signal_problem") == "network"
        assert self.pipeline._map_intent_to_category("slow_data") == "network"

    def test_map_intent_to_category_plan(self):
        assert self.pipeline._map_intent_to_category("plan_upgrade") == "plan"
        assert self.pipeline._map_intent_to_category("plan_inquiry") == "plan"

    def test_map_intent_to_category_unknown(self):
        assert self.pipeline._map_intent_to_category("general_support") is None
        assert self.pipeline._map_intent_to_category("nonexistent_intent") is None

    @pytest.mark.asyncio
    async def test_generate_returns_answer(self):
        mock_response = MagicMock()
        mock_response.text = "Your bill is higher due to a data overage charge."
        mock_response.usage_metadata = MagicMock()
        mock_response.usage_metadata.prompt_token_count = 500
        mock_response.usage_metadata.candidates_token_count = 80
        self.mock_model.generate_content = MagicMock(return_value=mock_response)

        with patch("app.rag.pipeline.knowledge_base") as mock_kb:
            mock_kb.retrieve.return_value = [
                {"content": "Data overage is $10/GB", "source": "billing_faq", "relevance_score": 0.91}
            ]
            metrics = RequestMetrics(session_id="test-session-001")
            result = await self.pipeline.generate(
                user_message="Why is my bill high?",
                intent="billing_inquiry",
                history=[],
                metrics=metrics,
            )

        assert "answer" in result
        assert result["answer"] == "Your bill is higher due to a data overage charge."
        assert "billing_faq" in result["sources"]
        assert result["retrieved_count"] == 1

    @pytest.mark.asyncio
    async def test_generate_records_token_counts(self):
        mock_response = MagicMock()
        mock_response.text = "Test response"
        mock_response.usage_metadata = MagicMock()
        mock_response.usage_metadata.prompt_token_count = 750
        mock_response.usage_metadata.candidates_token_count = 120
        self.mock_model.generate_content = MagicMock(return_value=mock_response)

        with patch("app.rag.pipeline.knowledge_base") as mock_kb:
            mock_kb.retrieve.return_value = []
            metrics = RequestMetrics(session_id="test-session-002")
            await self.pipeline.generate(
                user_message="Test question",
                intent="general_support",
                history=[],
                metrics=metrics,
            )

        assert metrics.token_count_input == 750
        assert metrics.token_count_output == 120
