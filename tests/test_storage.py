"""Tests for async SQLite storage layer — sessions and messages."""

from __future__ import annotations

import pytest

from remmeh.models import ChatSession, Message
from remmeh.storage import (
    append_message,
    create_session,
    get_session,
    init_db,
    list_sessions,
)


class TestInitDb:
    """Tests for init_db schema initialization."""

    @pytest.mark.asyncio
    async def test_init_db_creates_file(self, temp_db_path):
        """init_db creates the database file."""
        await init_db(str(temp_db_path))
        assert temp_db_path.exists()

    @pytest.mark.asyncio
    async def test_init_db_wal_mode(self, temp_db_path):
        """init_db enables WAL journal mode."""
        import aiosqlite

        await init_db(str(temp_db_path))
        async with aiosqlite.connect(str(temp_db_path)) as db:
            cursor = await db.execute("PRAGMA journal_mode")
            row = await cursor.fetchone()
            assert row[0] == "wal"

    @pytest.mark.asyncio
    async def test_init_db_creates_sessions_table(self, temp_db_path):
        """init_db creates the sessions table."""
        import aiosqlite

        await init_db(str(temp_db_path))
        async with aiosqlite.connect(str(temp_db_path)) as db:
            cursor = await db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'"
            )
            row = await cursor.fetchone()
            assert row is not None

    @pytest.mark.asyncio
    async def test_init_db_creates_messages_table(self, temp_db_path):
        """init_db creates the messages table."""
        import aiosqlite

        await init_db(str(temp_db_path))
        async with aiosqlite.connect(str(temp_db_path)) as db:
            cursor = await db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='messages'"
            )
            row = await cursor.fetchone()
            assert row is not None

    @pytest.mark.asyncio
    async def test_init_db_idempotent(self, temp_db_path):
        """init_db can be called multiple times without error."""
        await init_db(str(temp_db_path))
        await init_db(str(temp_db_path))  # Should not raise


class TestCreateSession:
    """Tests for create_session CRUD operation."""

    @pytest.mark.asyncio
    async def test_create_session_returns_session(self, temp_db_path):
        """create_session returns the session object."""
        await init_db(str(temp_db_path))
        session = ChatSession(name="Test Session")
        result = await create_session(str(temp_db_path), session)
        assert result.id == session.id
        assert result.name == session.name

    @pytest.mark.asyncio
    async def test_create_session_persisted(self, temp_db_path):
        """Created session can be retrieved from the database."""
        await init_db(str(temp_db_path))
        session = ChatSession(name="Persisted Session", model="openai/gpt-4o")
        await create_session(str(temp_db_path), session)

        retrieved = await get_session(str(temp_db_path), session.id)
        assert retrieved is not None
        assert retrieved.id == session.id
        assert retrieved.name == "Persisted Session"
        assert retrieved.model == "openai/gpt-4o"


class TestGetSession:
    """Tests for get_session retrieval."""

    @pytest.mark.asyncio
    async def test_get_session_unknown_id_returns_none(self, temp_db_path):
        """get_session returns None for an unknown session_id."""
        await init_db(str(temp_db_path))
        result = await get_session(str(temp_db_path), "nonexistent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_session_loads_messages(self, temp_db_path):
        """get_session loads messages ordered by created_at ASC."""
        await init_db(str(temp_db_path))
        session = ChatSession()
        await create_session(str(temp_db_path), session)

        msg1 = Message(role="user", content="first", session_id=session.id)
        msg2 = Message(role="assistant", content="second", session_id=session.id)
        await append_message(str(temp_db_path), msg1)
        await append_message(str(temp_db_path), msg2)

        retrieved = await get_session(str(temp_db_path), session.id)
        assert retrieved is not None
        assert len(retrieved.messages) == 2
        assert retrieved.messages[0].content == "first"
        assert retrieved.messages[1].content == "second"

    @pytest.mark.asyncio
    async def test_get_session_messages_are_message_objects(self, temp_db_path):
        """Retrieved session has Message objects, not dicts."""
        await init_db(str(temp_db_path))
        session = ChatSession()
        await create_session(str(temp_db_path), session)
        msg = Message(role="user", content="test", session_id=session.id)
        await append_message(str(temp_db_path), msg)

        retrieved = await get_session(str(temp_db_path), session.id)
        assert isinstance(retrieved.messages[0], Message)

    @pytest.mark.asyncio
    async def test_get_session_empty_messages(self, temp_db_path):
        """get_session returns empty messages list for session with no messages."""
        await init_db(str(temp_db_path))
        session = ChatSession()
        await create_session(str(temp_db_path), session)

        retrieved = await get_session(str(temp_db_path), session.id)
        assert retrieved is not None
        assert retrieved.messages == []


class TestAppendMessage:
    """Tests for append_message operation."""

    @pytest.mark.asyncio
    async def test_append_message_returns_message(self, temp_db_path):
        """append_message returns the inserted message."""
        await init_db(str(temp_db_path))
        session = ChatSession()
        await create_session(str(temp_db_path), session)

        msg = Message(role="user", content="hello", session_id=session.id)
        result = await append_message(str(temp_db_path), msg)
        assert result.id == msg.id
        assert result.content == "hello"

    @pytest.mark.asyncio
    async def test_append_message_persisted(self, temp_db_path):
        """Appended message is retrievable via get_session."""
        await init_db(str(temp_db_path))
        session = ChatSession()
        await create_session(str(temp_db_path), session)

        msg = Message(role="assistant", content="response", session_id=session.id)
        await append_message(str(temp_db_path), msg)

        retrieved = await get_session(str(temp_db_path), session.id)
        assert len(retrieved.messages) == 1
        assert retrieved.messages[0].role == "assistant"
        assert retrieved.messages[0].content == "response"

    @pytest.mark.asyncio
    async def test_append_message_preserves_id(self, temp_db_path):
        """append_message preserves the message's original id."""
        await init_db(str(temp_db_path))
        session = ChatSession()
        await create_session(str(temp_db_path), session)

        msg = Message(role="user", content="check id", session_id=session.id)
        original_id = msg.id
        await append_message(str(temp_db_path), msg)

        retrieved = await get_session(str(temp_db_path), session.id)
        assert retrieved.messages[0].id == original_id


class TestListSessions:
    """Tests for list_sessions ordering and behavior."""

    @pytest.mark.asyncio
    async def test_list_sessions_empty(self, temp_db_path):
        """list_sessions returns empty list when no sessions exist."""
        await init_db(str(temp_db_path))
        result = await list_sessions(str(temp_db_path))
        assert result == []

    @pytest.mark.asyncio
    async def test_list_sessions_returns_all(self, temp_db_path):
        """list_sessions returns all created sessions."""
        await init_db(str(temp_db_path))
        s1 = ChatSession(name="Session 1")
        s2 = ChatSession(name="Session 2")
        await create_session(str(temp_db_path), s1)
        await create_session(str(temp_db_path), s2)

        result = await list_sessions(str(temp_db_path))
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_list_sessions_ordered_by_updated_at_desc(self, temp_db_path):
        """list_sessions returns sessions ordered by updated_at DESC (most recent first)."""
        import asyncio

        await init_db(str(temp_db_path))

        s1 = ChatSession(name="Older Session")
        await create_session(str(temp_db_path), s1)
        await asyncio.sleep(0.01)  # ensure different timestamps

        s2 = ChatSession(name="Newer Session")
        await create_session(str(temp_db_path), s2)

        result = await list_sessions(str(temp_db_path))
        assert result[0].name == "Newer Session"
        assert result[1].name == "Older Session"

    @pytest.mark.asyncio
    async def test_list_sessions_no_messages_loaded(self, temp_db_path):
        """list_sessions does NOT load messages (empty messages list for performance)."""
        await init_db(str(temp_db_path))
        session = ChatSession()
        await create_session(str(temp_db_path), session)
        msg = Message(role="user", content="test", session_id=session.id)
        await append_message(str(temp_db_path), msg)

        result = await list_sessions(str(temp_db_path))
        assert result[0].messages == []

    @pytest.mark.asyncio
    async def test_list_sessions_are_chat_session_objects(self, temp_db_path):
        """list_sessions returns ChatSession instances."""
        await init_db(str(temp_db_path))
        await create_session(str(temp_db_path), ChatSession(name="Test"))

        result = await list_sessions(str(temp_db_path))
        assert isinstance(result[0], ChatSession)
