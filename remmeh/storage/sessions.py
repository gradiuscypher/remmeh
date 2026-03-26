"""Async CRUD operations for sessions and messages using aiosqlite."""

from __future__ import annotations

import aiosqlite

from remmeh.models import ChatSession, Message


async def create_session(db_path: str, session: ChatSession) -> ChatSession:
    """Insert a session into the database and return it.

    Args:
        db_path: Path to the SQLite database file.
        session: The ChatSession to persist.

    Returns:
        The persisted ChatSession (same object).
    """
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            INSERT INTO sessions (id, name, model, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                session.id,
                session.name,
                session.model,
                session.created_at.isoformat(),
                session.updated_at.isoformat(),
            ),
        )
        await db.commit()
    return session


async def get_session(db_path: str, session_id: str) -> ChatSession | None:
    """Retrieve a session by ID, with all messages loaded.

    Args:
        db_path: Path to the SQLite database file.
        session_id: The UUID of the session to retrieve.

    Returns:
        The ChatSession with messages, or None if not found.
    """
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, name, model, created_at, updated_at FROM sessions WHERE id = ?",
            (session_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None

        session = ChatSession.from_dict(
            {
                "id": row["id"],
                "name": row["name"],
                "model": row["model"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "messages": [],
            }
        )

        # Load messages ordered by created_at ASC
        msg_cursor = await db.execute(
            """
            SELECT id, session_id, role, content, created_at
            FROM messages
            WHERE session_id = ?
            ORDER BY created_at ASC
            """,
            (session_id,),
        )
        msg_rows = await msg_cursor.fetchall()
        for msg_row in msg_rows:
            message = Message.from_dict(
                {
                    "id": msg_row["id"],
                    "session_id": msg_row["session_id"],
                    "role": msg_row["role"],
                    "content": msg_row["content"],
                    "created_at": msg_row["created_at"],
                }
            )
            session.messages.append(message)

    return session


async def append_message(db_path: str, message: Message) -> Message:
    """Insert a message into the database.

    The message.session_id must be set before calling this function.

    Args:
        db_path: Path to the SQLite database file.
        message: The Message to persist (session_id must be set).

    Returns:
        The persisted Message (same object).
    """
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            INSERT INTO messages (id, session_id, role, content, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                message.id,
                message.session_id,
                message.role,
                message.content,
                message.created_at.isoformat(),
            ),
        )
        await db.commit()
    return message


async def list_sessions(db_path: str) -> list[ChatSession]:
    """Return all sessions ordered by updated_at DESC, without messages.

    Messages are NOT loaded for performance. Use get_session() to load
    a specific session with its messages.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        List of ChatSession objects ordered by updated_at DESC.
    """
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT id, name, model, created_at, updated_at
            FROM sessions
            ORDER BY updated_at DESC
            """
        )
        rows = await cursor.fetchall()

    sessions = []
    for row in rows:
        session = ChatSession.from_dict(
            {
                "id": row["id"],
                "name": row["name"],
                "model": row["model"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "messages": [],  # intentionally empty — use get_session() for messages
            }
        )
        sessions.append(session)

    return sessions
