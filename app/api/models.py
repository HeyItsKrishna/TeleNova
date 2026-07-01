from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="Customer's message")
    session_id: Optional[str] = Field(None, description="Existing session ID for multi-turn conversations")
    user_id: Optional[str] = Field(None, description="Optional customer identifier")
    account_number: Optional[str] = Field(None, description="Customer account number if known")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Why is my bill so high this month?",
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "customer_12345",
                "account_number": "TN-100001",
            }
        }


class ChatResponse(BaseModel):
    response: str
    session_id: str
    intent: str
    agent_type: str
    suggested_actions: list[str] = Field(default_factory=list)
    requires_human: bool = False
    sources: list[str] = Field(default_factory=list)
    observability: dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class WebhookRequest(BaseModel):
    detectIntentResponseId: Optional[str] = None
    intentInfo: Optional[dict] = None
    pageInfo: Optional[dict] = None
    sessionInfo: Optional[dict] = None
    fulfillmentInfo: Optional[dict] = None
    messages: Optional[list[dict]] = None
    text: Optional[str] = None

    def get_session_id(self) -> str:
        if self.sessionInfo:
            session = self.sessionInfo.get("session", "")
            return session.split("/")[-1] if "/" in session else session
        return ""

    def get_tag(self) -> str:
        if self.fulfillmentInfo:
            return self.fulfillmentInfo.get("tag", "")
        return ""

    def get_intent_display_name(self) -> str:
        if self.intentInfo:
            return self.intentInfo.get("displayName", "")
        return ""

    def get_parameters(self) -> dict:
        if self.sessionInfo:
            return self.sessionInfo.get("parameters", {})
        return {}

    def get_query_text(self) -> str:
        if self.messages:
            for msg in self.messages:
                if msg.get("type") == "CONVERSATION_SUCCESS":
                    return msg.get("text", "")
        return self.text or ""


class WebhookResponse(BaseModel):
    fulfillmentResponse: dict = Field(default_factory=dict)
    sessionInfo: Optional[dict] = None
    targetPage: Optional[str] = None

    @classmethod
    def from_text(cls, text: str, session_params: dict = None) -> "WebhookResponse":
        response = cls(
            fulfillmentResponse={
                "messages": [{"text": {"text": [text]}}]
            }
        )
        if session_params:
            response.sessionInfo = {"parameters": session_params}
        return response


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    knowledge_base_loaded: bool
    active_sessions: int
    database_connected: bool = True
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
