import time
import pytest
from app.utils.session import UserSession, SessionStore, ConversationTurn


class TestConversationTurn:

    def test_turn_creation(self):
        turn = ConversationTurn(role="user", content="Hello", intent="general_support")
        assert turn.role == "user"
        assert turn.content == "Hello"
        assert turn.intent == "general_support"
        assert turn.timestamp > 0

    def test_turn_default_metadata(self):
        turn = ConversationTurn(role="assistant", content="Hi there", intent="general_support")
        assert turn.metadata == {}


class TestUserSession:

    def setup_method(self):
        self.session = UserSession(session_id="test-uuid-001", user_id="user-123")

    def test_initial_state(self):
        assert self.session.session_id == "test-uuid-001"
        assert self.session.user_id == "user-123"
        assert self.session.active_intent == "general_support"
        assert len(self.session.conversation_history) == 0
        assert self.session.account_number is None

    def test_add_turn_user(self):
        self.session.add_turn(role="user", content="What is my balance?", intent="billing_inquiry")
        assert len(self.session.conversation_history) == 1
        assert self.session.conversation_history[0].role == "user"
        assert self.session.active_intent == "billing_inquiry"

    def test_add_turn_updates_last_active(self):
        before = self.session.last_active
        time.sleep(0.01)
        self.session.add_turn(role="user", content="Hello", intent="general_support")
        assert self.session.last_active >= before

    def test_add_turn_updates_active_intent(self):
        self.session.add_turn(role="user", content="Billing question", intent="billing_inquiry")
        assert self.session.active_intent == "billing_inquiry"
        self.session.add_turn(role="user", content="Network issue", intent="network_issue")
        assert self.session.active_intent == "network_issue"

    def test_history_truncation(self):
        for i in range(25):
            self.session.add_turn(role="user", content=f"Message {i}", intent="general_support")
            self.session.add_turn(role="assistant", content=f"Response {i}", intent="general_support")
        assert len(self.session.conversation_history) <= 20

    def test_get_history_for_prompt_empty(self):
        result = self.session.get_history_for_prompt()
        assert result == []

    def test_get_history_for_prompt_format(self):
        self.session.add_turn("user", "Hello", "general_support")
        self.session.add_turn("assistant", "Hi!", "general_support")
        history = self.session.get_history_for_prompt()
        assert len(history) == 2
        assert history[0] == {"role": "user", "content": "Hello"}
        assert history[1] == {"role": "assistant", "content": "Hi!"}

    def test_is_expired_false_when_recent(self):
        assert not self.session.is_expired()

    def test_is_expired_true_when_old(self):
        self.session.last_active = time.time() - 3600
        assert self.session.is_expired()

    def test_to_dict_contains_required_keys(self):
        d = self.session.to_dict()
        assert "session_id" in d
        assert "user_id" in d
        assert "active_intent" in d
        assert "turn_count" in d
        assert d["turn_count"] == 0

    def test_to_dict_turn_count_updates(self):
        self.session.add_turn("user", "Test", "general_support")
        self.session.add_turn("assistant", "Response", "general_support")
        d = self.session.to_dict()
        assert d["turn_count"] == 2


class TestSessionStore:

    def setup_method(self):
        self.store = SessionStore()

    def test_create_new_session(self):
        session = self.store.get_or_create()
        assert session is not None
        assert session.session_id is not None

    def test_get_existing_session(self):
        session = self.store.get_or_create(session_id="fixed-id-001")
        session2 = self.store.get_or_create(session_id="fixed-id-001")
        assert session.session_id == session2.session_id

    def test_get_nonexistent_returns_none(self):
        result = self.store.get("does-not-exist")
        assert result is None

    def test_delete_session(self):
        session = self.store.get_or_create(session_id="to-delete")
        self.store.delete("to-delete")
        assert self.store.get("to-delete") is None

    def test_active_count(self):
        assert self.store.active_count == 0
        self.store.get_or_create(session_id="s1")
        self.store.get_or_create(session_id="s2")
        assert self.store.active_count == 2

    def test_cleanup_expired(self):
        session = self.store.get_or_create(session_id="expiring")
        session.last_active = time.time() - 3600
        expired = self.store.cleanup_expired()
        assert expired == 1
        assert self.store.active_count == 0

    def test_expired_session_returns_new_on_get_or_create(self):
        session = self.store.get_or_create(session_id="reuse-id")
        session.last_active = time.time() - 3600
        new_session = self.store.get_or_create(session_id="reuse-id")
        assert new_session.session_id == "reuse-id"
        assert not new_session.is_expired()

    def test_user_id_assignment(self):
        session = self.store.get_or_create(user_id="user-xyz")
        assert session.user_id == "user-xyz"
