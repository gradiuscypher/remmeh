"""Tests for Message and ChatSession data models."""

from __future__ import annotations

import time
from datetime import datetime

import pytest

from remmeh.models import ChatSession, Message


class TestMessage:
    """Tests for the Message dataclass."""

    def test_message_creation_defaults(self):
        """Message creates with UUID id and utcnow timestamp."""
        msg = Message(role="user", content="hello")
        assert msg.role == "user"
        assert msg.content == "hello"
        assert isinstance(msg.id, str)
        assert len(msg.id) == 36  # UUID4 format
        assert isinstance(msg.created_at, datetime)
        assert msg.session_id == ""

    def test_message_unique_ids(self):
        """Each Message gets a unique UUID id."""
        msg1 = Message(role="user", content="a")
        msg2 = Message(role="user", content="b")
        assert msg1.id != msg2.id

    def test_message_to_dict(self):
        """to_dict() returns all required keys with ISO string timestamp."""
        msg = Message(role="user", content="hello")
        d = msg.to_dict()
        assert set(d.keys()) == {"id", "role", "content", "created_at", "session_id"}
        assert d["role"] == "user"
        assert d["content"] == "hello"
        assert d["id"] == msg.id
        assert d["session_id"] == ""
        # created_at must be an ISO 8601 string
        assert isinstance(d["created_at"], str)
        parsed = datetime.fromisoformat(d["created_at"])
        assert isinstance(parsed, datetime)

    def test_message_from_dict_round_trip(self):
        """from_dict(msg.to_dict()) round-trips losslessly."""
        msg = Message(role="assistant", content="response text", session_id="sess-123")
        d = msg.to_dict()
        restored = Message.from_dict(d)
        assert restored.id == msg.id
        assert restored.role == msg.role
        assert restored.content == msg.content
        assert restored.session_id == msg.session_id
        assert restored.created_at == msg.created_at

    def test_message_all_valid_roles(self):
        """user, assistant, and error roles are all valid."""
        for role in ("user", "assistant", "error"):
            msg = Message(role=role, content="test")
            assert msg.role == role

    def test_message_invalid_role_raises_value_error(self):
        """Invalid role raises ValueError."""
        with pytest.raises(ValueError, match="role"):
            Message(role="system", content="test")

    def test_message_invalid_role_empty_raises(self):
        """Empty string role raises ValueError."""
        with pytest.raises(ValueError):
            Message(role="", content="test")

    def test_message_session_id_set(self):
        """session_id can be set at construction."""
        msg = Message(role="user", content="hi", session_id="my-session-id")
        assert msg.session_id == "my-session-id"
        d = msg.to_dict()
        assert d["session_id"] == "my-session-id"

    def test_message_error_role(self):
        """error role is valid and round-trips correctly."""
        msg = Message(role="error", content="Something went wrong")
        d = msg.to_dict()
        restored = Message.from_dict(d)
        assert restored.role == "error"


class TestChatSession:
    """Tests for the ChatSession dataclass."""

    def test_session_creation_defaults(self):
        """ChatSession creates with UUID id and empty messages list."""
        session = ChatSession()
        assert isinstance(session.id, str)
        assert len(session.id) == 36  # UUID4 format
        assert session.name == "New Chat"
        assert session.model == "anthropic/claude-3.5-sonnet"
        assert session.messages == []
        assert isinstance(session.created_at, datetime)
        assert isinstance(session.updated_at, datetime)

    def test_session_unique_ids(self):
        """Each ChatSession gets a unique UUID id."""
        s1 = ChatSession()
        s2 = ChatSession()
        assert s1.id != s2.id

    def test_add_message_appends(self):
        """add_message() appends to messages list."""
        session = ChatSession()
        msg = Message(role="user", content="hello")
        session.add_message(msg)
        assert len(session.messages) == 1
        assert session.messages[0] is msg

    def test_add_message_updates_updated_at(self):
        """add_message() updates session.updated_at."""
        session = ChatSession()
        original_updated_at = session.updated_at
        time.sleep(0.001)  # ensure time advances
        msg = Message(role="user", content="hello")
        session.add_message(msg)
        assert session.updated_at >= original_updated_at

    def test_add_multiple_messages(self):
        """Multiple add_message() calls accumulate messages."""
        session = ChatSession()
        for i in range(3):
            session.add_message(Message(role="user", content=f"msg {i}"))
        assert len(session.messages) == 3

    def test_session_to_dict(self):
        """to_dict() serializes all fields including messages."""
        session = ChatSession(name="My Chat", model="openai/gpt-4o")
        msg = Message(role="user", content="test")
        session.add_message(msg)
        d = session.to_dict()
        assert "id" in d
        assert d["name"] == "My Chat"
        assert d["model"] == "openai/gpt-4o"
        assert isinstance(d["created_at"], str)
        assert isinstance(d["updated_at"], str)
        assert isinstance(d["messages"], list)
        assert len(d["messages"]) == 1
        assert d["messages"][0]["content"] == "test"

    def test_session_from_dict_round_trip(self):
        """from_dict(session.to_dict()) round-trips losslessly."""
        session = ChatSession(name="Round Trip", model="openai/gpt-4o")
        msg1 = Message(role="user", content="hello")
        msg2 = Message(role="assistant", content="world")
        session.add_message(msg1)
        session.add_message(msg2)

        d = session.to_dict()
        restored = ChatSession.from_dict(d)

        assert restored.id == session.id
        assert restored.name == session.name
        assert restored.model == session.model
        assert restored.created_at == session.created_at
        assert restored.updated_at == session.updated_at
        assert len(restored.messages) == 2
        assert isinstance(restored.messages[0], Message)
        assert restored.messages[0].id == msg1.id
        assert restored.messages[0].role == msg1.role
        assert restored.messages[0].content == msg1.content
        assert restored.messages[1].id == msg2.id

    def test_session_from_dict_messages_are_message_objects(self):
        """Restored messages are Message instances, not plain dicts."""
        session = ChatSession()
        session.add_message(Message(role="user", content="test"))
        restored = ChatSession.from_dict(session.to_dict())
        assert isinstance(restored.messages[0], Message)

    def test_session_empty_messages_round_trip(self):
        """Session with no messages round-trips cleanly."""
        session = ChatSession()
        restored = ChatSession.from_dict(session.to_dict())
        assert restored.messages == []

    def test_session_custom_fields(self):
        """Custom name and model are preserved in round-trip."""
        session = ChatSession(name="Custom Name", model="google/gemini-pro")
        d = session.to_dict()
        assert d["name"] == "Custom Name"
        assert d["model"] == "google/gemini-pro"
