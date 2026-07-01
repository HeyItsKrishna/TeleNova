import time
import uuid
from typing import Any, Optional
from collections import defaultdict
from dataclasses import dataclass, field
from app.config import get_settings

settings = get_settings()


@dataclass
class ConversationTurn:
    role: str
    content: str
    intent: str
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class UserSession:
    session_id: str
    user_id: Optional[str]
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    active_intent: str = "general_support"
    conversation_history: list[ConversationTurn] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    account_number: Optional[str] = None
    ticket_id: Optional[str] = None
    plan_type: Optional[str] = None

    def add_turn(self, role: str, content: str, intent: str, metadata: dict = None) -> None:
        turn = ConversationTurn(
            role=role,
            content=content,
            intent=intent,
            metadata=metadata or {},
        )
        self.conversation_history.append(turn)
        if len(self.conversation_history) > settings.max_history_turns * 2:
            self.conversation_history = self.conversation_history[-(settings.max_history_turns * 2):]
        self.last_active = time.time()
        self.active_intent = intent

    def get_history_for_prompt(self) -> list[dict[str, str]]:
        return [
            {"role": turn.role, "content": turn.content}
            for turn in self.conversation_history[-(settings.max_history_turns * 2):]
        ]

    def is_expired(self) -> bool:
        return (time.time() - self.last_active) > settings.session_ttl_seconds

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "last_active": self.last_active,
            "active_intent": self.active_intent,
            "account_number": self.account_number,
            "ticket_id": self.ticket_id,
            "plan_type": self.plan_type,
            "context": self.context,
            "turn_count": len(self.conversation_history),
        }


class SessionStore:
    def __init__(self):
        self._sessions: dict[str, UserSession] = {}

    def get_or_create(self, session_id: Optional[str] = None, user_id: Optional[str] = None) -> UserSession:
        if session_id and session_id in self._sessions:
            session = self._sessions[session_id]
            if not session.is_expired():
                session.last_active = time.time()
                return session
        new_id = session_id or str(uuid.uuid4())
        session = UserSession(session_id=new_id, user_id=user_id)
        self._sessions[new_id] = session
        return session

    def get(self, session_id: str) -> Optional[UserSession]:
        session = self._sessions.get(session_id)
        if session and session.is_expired():
            del self._sessions[session_id]
            return None
        return session

    def delete(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def cleanup_expired(self) -> int:
        expired = [sid for sid, s in self._sessions.items() if s.is_expired()]
        for sid in expired:
            del self._sessions[sid]
        return len(expired)

    @property
    def active_count(self) -> int:
        return len(self._sessions)


session_store = SessionStore()
