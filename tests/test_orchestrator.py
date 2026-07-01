import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.agents.orchestrator import classify_intent, route_and_respond, _get_suggested_actions
from app.utils.session import UserSession
from app.utils.observability import RequestMetrics


class TestClassifyIntent:

    def _make_session(self, active_intent="general_support"):
        session = UserSession(session_id="test-001", user_id=None)
        session.active_intent = active_intent
        return session

    def test_billing_keywords(self):
        session = self._make_session()
        assert classify_intent("Why is my bill so high?", session) == "billing_inquiry"
        assert classify_intent("I have a question about my billing", session) == "billing_inquiry"

    def test_dispute_keywords(self):
        session = self._make_session()
        result = classify_intent("I was overcharged this month", session)
        assert result == "billing_dispute"

    def test_plan_upgrade_keywords(self):
        session = self._make_session()
        result = classify_intent("I want to upgrade to unlimited", session)
        assert result == "plan_upgrade"

    def test_network_keywords(self):
        session = self._make_session()
        result = classify_intent("I have no signal at all", session)
        assert result == "network_issue"

    def test_slow_data_keywords(self):
        session = self._make_session()
        result = classify_intent("My internet is very slow and buffering", session)
        assert result == "slow_data"

    def test_ticket_status_keywords(self):
        session = self._make_session()
        result = classify_intent("What is the status of my ticket BIL-78231?", session)
        assert result == "ticket_status"

    def test_escalation_keywords(self):
        session = self._make_session()
        result = classify_intent("I want to speak to a human agent please", session)
        assert result == "escalation_request"

    def test_fallback_to_session_intent(self):
        session = self._make_session(active_intent="billing_inquiry")
        result = classify_intent("yes please", session)
        assert result == "billing_inquiry"

    def test_fallback_to_general_when_no_match(self):
        session = self._make_session(active_intent="general_support")
        result = classify_intent("zyxwvutsrqpo", session)
        assert result == "general_support"

    def test_case_insensitive(self):
        session = self._make_session()
        result_upper = classify_intent("MY BILL IS TOO HIGH", session)
        result_lower = classify_intent("my bill is too high", session)
        assert result_upper == result_lower

    def test_highest_score_wins(self):
        session = self._make_session()
        result = classify_intent("bill billing billing charge payment", session)
        assert result == "billing_inquiry"


class TestGetSuggestedActions:

    def test_billing_actions(self):
        actions = _get_suggested_actions("billing_inquiry")
        assert len(actions) > 0
        assert any("bill" in a.lower() or "autopay" in a.lower() or "billing" in a.lower() for a in actions)

    def test_escalation_actions(self):
        actions = _get_suggested_actions("escalation_request")
        assert any("agent" in a.lower() or "callback" in a.lower() for a in actions)

    def test_unknown_intent_returns_defaults(self):
        actions = _get_suggested_actions("unknown_xyz")
        assert len(actions) > 0

    def test_all_known_intents_have_actions(self):
        known_intents = [
            "billing_inquiry", "billing_dispute", "plan_upgrade", "plan_inquiry",
            "network_issue", "signal_problem", "slow_data", "escalation_request",
            "ticket_status", "account_information", "general_support", "troubleshooting",
        ]
        for intent in known_intents:
            actions = _get_suggested_actions(intent)
            assert len(actions) > 0, f"No actions for intent: {intent}"


class TestRouteAndRespond:

    @pytest.mark.asyncio
    async def test_returns_required_keys(self):
        session = UserSession(session_id="route-test-001", user_id=None)
        metrics = RequestMetrics(session_id="route-test-001")

        mock_rag_result = {
            "answer": "Your bill is higher due to data overage charges.",
            "sources": ["billing_faq"],
            "retrieved_count": 2,
        }

        with patch("app.agents.orchestrator.rag_pipeline") as mock_rag:
            mock_rag.generate = AsyncMock(return_value=mock_rag_result)
            result = await route_and_respond(
                user_message="Why is my bill high?",
                session=session,
                metrics=metrics,
            )

        assert "response" in result
        assert "intent" in result
        assert "agent_type" in result
        assert "suggested_actions" in result
        assert "requires_human" in result
        assert "sources" in result

    @pytest.mark.asyncio
    async def test_escalation_sets_requires_human(self):
        session = UserSession(session_id="route-test-002", user_id=None)
        metrics = RequestMetrics(session_id="route-test-002")

        with patch("app.agents.orchestrator.rag_pipeline") as mock_rag:
            mock_rag.generate = AsyncMock(return_value={
                "answer": "Connecting you with a specialist...",
                "sources": [],
                "retrieved_count": 0,
            })
            result = await route_and_respond(
                user_message="I want to speak to a human supervisor",
                session=session,
                metrics=metrics,
            )

        assert result["requires_human"] is True
        assert result["intent"] == "escalation_request"

    @pytest.mark.asyncio
    async def test_metrics_intent_updated(self):
        session = UserSession(session_id="route-test-003", user_id=None)
        metrics = RequestMetrics(session_id="route-test-003")

        with patch("app.agents.orchestrator.rag_pipeline") as mock_rag:
            mock_rag.generate = AsyncMock(return_value={
                "answer": "Network troubleshooting steps...",
                "sources": ["network_troubleshooting"],
                "retrieved_count": 1,
            })
            await route_and_respond(
                user_message="I have no signal",
                session=session,
                metrics=metrics,
            )

        assert metrics.intent in ["network_issue", "signal_problem"]
