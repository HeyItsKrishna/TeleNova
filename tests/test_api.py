import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from app.api.routes import app


@pytest.fixture
def client():
    with patch("app.api.routes._kb_loaded", True):
        with TestClient(app) as c:
            yield c


class TestHealthEndpoint:

    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_structure(self, client):
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "environment" in data
        assert "knowledge_base_loaded" in data
        assert "active_sessions" in data
        assert "timestamp" in data

    def test_health_status_value(self, client):
        response = client.get("/health")
        assert response.json()["status"] == "healthy"


class TestChatEndpoint:

    def _mock_route_result(self):
        return {
            "response": "Your bill is higher due to a 1 GB data overage charge of $10.",
            "intent": "billing_inquiry",
            "agent_type": "billing",
            "suggested_actions": ["View my bill", "Set up AutoPay"],
            "requires_human": False,
            "sources": ["billing_faq"],
        }

    def test_chat_basic_request(self, client):
        with patch("app.api.routes.route_and_respond", new_callable=AsyncMock) as mock_route:
            mock_route.return_value = self._mock_route_result()
            response = client.post("/chat", json={"message": "Why is my bill high?"})
        assert response.status_code == 200

    def test_chat_response_structure(self, client):
        with patch("app.api.routes.route_and_respond", new_callable=AsyncMock) as mock_route:
            mock_route.return_value = self._mock_route_result()
            response = client.post("/chat", json={"message": "Why is my bill high?"})
        data = response.json()
        assert "response" in data
        assert "session_id" in data
        assert "intent" in data
        assert "agent_type" in data
        assert "suggested_actions" in data
        assert "requires_human" in data
        assert "sources" in data
        assert "observability" in data
        assert "timestamp" in data

    def test_chat_observability_keys(self, client):
        with patch("app.api.routes.route_and_respond", new_callable=AsyncMock) as mock_route:
            mock_route.return_value = self._mock_route_result()
            response = client.post("/chat", json={"message": "Test message"})
        obs = response.json()["observability"]
        assert "request_id" in obs
        assert "session_id" in obs
        assert "latency_ms" in obs

    def test_chat_session_persistence(self, client):
        with patch("app.api.routes.route_and_respond", new_callable=AsyncMock) as mock_route:
            mock_route.return_value = self._mock_route_result()
            r1 = client.post("/chat", json={"message": "First message"})
            session_id = r1.json()["session_id"]

            r2 = client.post("/chat", json={"message": "Follow-up", "session_id": session_id})
            assert r2.json()["session_id"] == session_id

    def test_chat_empty_message_rejected(self, client):
        response = client.post("/chat", json={"message": ""})
        assert response.status_code == 422

    def test_chat_message_too_long_rejected(self, client):
        response = client.post("/chat", json={"message": "x" * 2001})
        assert response.status_code == 422

    def test_chat_with_account_number(self, client):
        with patch("app.api.routes.route_and_respond", new_callable=AsyncMock) as mock_route:
            mock_route.return_value = self._mock_route_result()
            response = client.post("/chat", json={
                "message": "Show me my bill",
                "account_number": "TN-100001",
            })
        assert response.status_code == 200

    def test_chat_error_returns_500(self, client):
        with patch("app.api.routes.route_and_respond", new_callable=AsyncMock) as mock_route:
            mock_route.side_effect = Exception("Simulated backend failure")
            response = client.post("/chat", json={"message": "Trigger error"})
        assert response.status_code == 500


class TestWebhookEndpoint:

    def _dialogflow_request(self, text="Why is my bill high?", intent="billing.inquiry", tag="billing_inquiry"):
        return {
            "detectIntentResponseId": "abc-123",
            "intentInfo": {"displayName": intent},
            "sessionInfo": {
                "session": "projects/test-project/locations/global/agents/test-agent/sessions/webhook-session-001",
                "parameters": {},
            },
            "fulfillmentInfo": {"tag": tag},
            "messages": [{"type": "CONVERSATION_SUCCESS", "text": text}],
        }

    def test_webhook_returns_200(self, client):
        with patch("app.api.routes.route_and_respond", new_callable=AsyncMock) as mock_route:
            mock_route.return_value = {
                "response": "Your bill breakdown is...",
                "intent": "billing_inquiry",
                "agent_type": "billing",
                "suggested_actions": [],
                "requires_human": False,
                "sources": [],
            }
            response = client.post("/webhook", json=self._dialogflow_request())
        assert response.status_code == 200

    def test_webhook_response_structure(self, client):
        with patch("app.api.routes.route_and_respond", new_callable=AsyncMock) as mock_route:
            mock_route.return_value = {
                "response": "Let me help with that.",
                "intent": "general_support",
                "agent_type": "support",
                "suggested_actions": [],
                "requires_human": False,
                "sources": [],
            }
            response = client.post("/webhook", json=self._dialogflow_request())
        data = response.json()
        assert "fulfillmentResponse" in data
        assert "messages" in data["fulfillmentResponse"]

    def test_webhook_with_session_params(self, client):
        payload = self._dialogflow_request()
        payload["sessionInfo"]["parameters"] = {"account_number": "TN-100001"}

        with patch("app.api.routes.route_and_respond", new_callable=AsyncMock) as mock_route:
            mock_route.return_value = {
                "response": "Account found.",
                "intent": "account_information",
                "agent_type": "support",
                "suggested_actions": [],
                "requires_human": False,
                "sources": [],
            }
            response = client.post("/webhook", json=payload)
        assert response.status_code == 200

    def test_webhook_handles_backend_error_gracefully(self, client):
        with patch("app.api.routes.route_and_respond", new_callable=AsyncMock) as mock_route:
            mock_route.side_effect = Exception("Simulated error")
            response = client.post("/webhook", json=self._dialogflow_request())
        assert response.status_code == 200
        data = response.json()
        assert "fulfillmentResponse" in data
        response_text = data["fulfillmentResponse"]["messages"][0]["text"]["text"][0]
        assert "specialist" in response_text.lower() or "error" in response_text.lower()
