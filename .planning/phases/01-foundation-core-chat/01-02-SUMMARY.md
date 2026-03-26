---
phase: 01-foundation-core-chat
plan: "02"
subsystem: storage
tags: [models, storage, sqlite, aiosqlite, wal, dataclasses, tdd]
dependency_graph:
  requires:
    - remmeh package importable (01-01)
    - aiosqlite>=0.20 installed (01-01)
  provides:
    - Message dataclass with role/content/id/created_at/session_id
    - ChatSession dataclass with messages list and serialization
    - SQLite DB initialization with WAL mode
    - Async CRUD: create_session, get_session, append_message, list_sessions
    - remmeh.storage public API (re-exported via __init__.py)
  affects:
    - Plan 01-03 (OpenRouter client — consumes Message/ChatSession models)
    - Plan 01-04 (UI scaffold — will call storage layer)
    - Plan 01-05 (Chat send/receive — persists messages via storage)
tech_stack:
  added: []
  patterns:
    - aiosqlite connection-per-call pattern (async with aiosqlite.connect)
    - PRAGMA journal_mode=WAL set FIRST before any schema/data operations
    - CREATE TABLE IF NOT EXISTS for idempotent DB initialization
    - TDD red-green cycle: tests written first, then implementation
    - dataclass with __post_init__ for field validation
    - ISO 8601 strings for datetime serialization (naive UTC)
key_files:
  created:
    - remmeh/models.py (Message and ChatSession dataclasses)
    - remmeh/storage/__init__.py (public API re-exports)
    - remmeh/storage/db.py (init_db with WAL mode and schema)
    - remmeh/storage/sessions.py (CRUD operations)
    - tests/test_models.py (19 unit tests for models)
    - tests/test_storage.py (19 unit tests for storage)
  modified: []
decisions:
  - "Used connection-per-call pattern for aiosqlite (not a pool) — connection pooling is Phase 2+"
  - "Kept datetime.utcnow() per interface spec despite deprecation warning — timezone-aware migration is a future plan"
  - "list_sessions() intentionally omits messages for performance — callers use get_session() to load messages"
  - "Role validation in __post_init__ raises ValueError — consistent with Python idioms, no Pydantic needed"
metrics:
  duration_seconds: 222
  completed_date: "2026-03-26"
  tasks_completed: 2
  files_created: 6
  files_modified: 0
---

# Phase 01 Plan 02: Data Models & Storage Summary

**One-liner:** Message/ChatSession dataclasses with async aiosqlite SQLite storage, WAL mode enforced first, full CRUD with 38 passing TDD tests.

## What Was Built

Implemented the persistent data layer for remmeh from scratch using a TDD approach:

- **`remmeh/models.py`** — Two dataclasses:
  - `Message`: role/content/id (UUID4)/created_at (UTC datetime)/session_id fields; `__post_init__` validates role against `{"user", "assistant", "error"}`; `to_dict()`/`from_dict()` for ISO 8601 round-trip serialization
  - `ChatSession`: id (UUID4)/name/model/messages/created_at/updated_at; `add_message()` appends and updates `updated_at`; full serialization including nested messages

- **`remmeh/storage/db.py`** — `init_db(db_path)` enables `PRAGMA journal_mode=WAL` as the *first* DB operation, then creates `sessions` and `messages` tables with `CREATE TABLE IF NOT EXISTS` (idempotent)

- **`remmeh/storage/sessions.py`** — Four async CRUD functions using `async with aiosqlite.connect()`:
  - `create_session()` — inserts session row, returns session
  - `get_session()` — returns `None` for unknown IDs; loads session + messages (ordered by `created_at ASC`)
  - `append_message()` — inserts message row, returns message
  - `list_sessions()` — returns session metadata ordered by `updated_at DESC`, **without** messages (performance design)

- **`remmeh/storage/__init__.py`** — re-exports all five public functions

## Verification Results

```
uv run pytest tests/test_models.py tests/test_storage.py -v
  38 passed, 87 warnings in 0.60s

uv run ruff check remmeh/models.py remmeh/storage/
  All checks passed!

uv run ty check remmeh/models.py remmeh/storage/
  4 warnings (datetime.utcnow() deprecation — warnings only, no errors)
```

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all data flows are fully wired. `models.py` and `storage/` are complete implementations, not stubs.

## Self-Check: PASSED
