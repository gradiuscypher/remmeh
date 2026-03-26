"""Database initialization with WAL mode and schema creation."""

from __future__ import annotations

import aiosqlite


async def init_db(db_path: str) -> None:
    """Initialize DB with WAL mode and schema.

    WAL mode is set FIRST before any schema or data operations.
    Safe to call on an existing database (idempotent — uses CREATE TABLE IF NOT EXISTS).

    Args:
        db_path: Path to the SQLite database file.
    """
    async with aiosqlite.connect(db_path) as db:
        # WAL mode FIRST — before any schema or data operations
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                model TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL REFERENCES sessions(id),
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        await db.commit()
