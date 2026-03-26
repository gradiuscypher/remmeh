"""Integration tests for the chat submit→stream→persist chain.

Tests the ChatScreen's end-to-end flow using a mocked OpenRouterClient,
covering:
- User message display after submit
- Streaming token accumulation in MessageWidget
- RichLog → Markdown swap on stream completion
- SQLite persistence for user and assistant messages
- Error path: RateLimitError, TimeoutError, missing API key
- Cancel leaving partial response visible (no error widget)

Uses App.run_test() (headless) with InputPanel.Submitted posted directly
to trigger the chat flow — this bypasses TextArea key handling and tests
the ChatScreen message handler path reliably.
"""

from __future__ import annotations

import asyncio
from unittest.mock import patch

from remmeh.api.openrouter import RateLimitError
from remmeh.api.openrouter import TimeoutError as OpenRouterTimeoutError
from remmeh.storage import get_session, init_db, list_sessions
from remmeh.ui.app import RemmehApp
from remmeh.ui.widgets import InputPanel, MessageWidget

# ---------------------------------------------------------------------------
# Mock stream generators
# ---------------------------------------------------------------------------


async def mock_stream_hello(*args, **kwargs):
    """Yield two tokens simulating a normal stream."""
    yield "Hello"
    yield " world"


async def mock_stream_rate_limit(*args, **kwargs):
    """Raise RateLimitError immediately (async generator form)."""
    raise RateLimitError("429 rate limited")
    yield  # make it an async generator


async def mock_stream_timeout(*args, **kwargs):
    """Raise TimeoutError immediately (async generator form)."""
    raise OpenRouterTimeoutError("Request timed out")
    yield  # make it an async generator


async def mock_stream_partial(*args, **kwargs):
    """Yield one token then block — simulates slow stream that will be cancelled."""
    yield "Partial content"
    await asyncio.sleep(100)  # block until CancelledError is raised by worker


# ---------------------------------------------------------------------------
# submit_message_sends_to_chat
# ---------------------------------------------------------------------------


async def test_submit_message_sends_to_chat(api_key, temp_db_path, monkeypatch):
    """User message widget appears in chat view after submit."""
    monkeypatch.setenv("REMMEH_DB_PATH", str(temp_db_path))
    with patch("remmeh.ui.screens.chat.OpenRouterClient") as MockClient:
        MockClient.return_value.stream_chat = mock_stream_hello
        app = RemmehApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause(0.2)
            screen = app.screen
            input_panel = screen.query_one("#input-panel", InputPanel)
            input_panel.post_message(InputPanel.Submitted("Hello there"))
            await pilot.pause(0.5)
            await pilot.pause(0.5)
            messages = list(screen.query(MessageWidget))
            user_msgs = [m for m in messages if m.role == "user"]
            assert len(user_msgs) == 1
            assert "Hello there" in user_msgs[0].full_content


# ---------------------------------------------------------------------------
# streaming_tokens_accumulate
# ---------------------------------------------------------------------------


async def test_streaming_tokens_accumulate(api_key, temp_db_path, monkeypatch):
    """write_chunk() accumulates content in assistant widget."""
    monkeypatch.setenv("REMMEH_DB_PATH", str(temp_db_path))
    with patch("remmeh.ui.screens.chat.OpenRouterClient") as MockClient:
        MockClient.return_value.stream_chat = mock_stream_hello
        app = RemmehApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause(0.2)
            screen = app.screen
            input_panel = screen.query_one("#input-panel", InputPanel)
            input_panel.post_message(InputPanel.Submitted("Test message"))
            await pilot.pause(0.5)
            await pilot.pause(0.5)
            messages = list(screen.query(MessageWidget))
            asst_msgs = [m for m in messages if m.role == "assistant"]
            assert len(asst_msgs) == 1
            # Full accumulated content from both tokens
            assert asst_msgs[0].full_content == "Hello world"


# ---------------------------------------------------------------------------
# stream_completes_with_markdown_swap
# ---------------------------------------------------------------------------


async def test_stream_completes_with_markdown_swap(api_key, temp_db_path, monkeypatch):
    """After all chunks, the assistant widget has no active RichLog (swap occurred)."""
    monkeypatch.setenv("REMMEH_DB_PATH", str(temp_db_path))
    with patch("remmeh.ui.screens.chat.OpenRouterClient") as MockClient:
        MockClient.return_value.stream_chat = mock_stream_hello
        app = RemmehApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause(0.2)
            screen = app.screen
            input_panel = screen.query_one("#input-panel", InputPanel)
            input_panel.post_message(InputPanel.Submitted("Swap test"))
            await pilot.pause(0.5)
            await pilot.pause(0.5)
            messages = list(screen.query(MessageWidget))
            asst_msgs = [m for m in messages if m.role == "assistant"]
            assert len(asst_msgs) == 1
            # After swap_to_markdown(), _rich_log should be None and _streaming False
            assert asst_msgs[0]._rich_log is None
            assert not asst_msgs[0]._streaming


# ---------------------------------------------------------------------------
# user_message_saved_to_db
# ---------------------------------------------------------------------------


async def test_user_message_saved_to_db(api_key, temp_db_path, monkeypatch):
    """After submit, Message(role='user') exists in the temp DB."""
    monkeypatch.setenv("REMMEH_DB_PATH", str(temp_db_path))
    with patch("remmeh.ui.screens.chat.OpenRouterClient") as MockClient:
        MockClient.return_value.stream_chat = mock_stream_hello
        app = RemmehApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause(0.2)
            screen = app.screen
            input_panel = screen.query_one("#input-panel", InputPanel)
            input_panel.post_message(InputPanel.Submitted("Persist user msg"))
            await pilot.pause(0.5)
            await pilot.pause(0.5)

    # After app exits, verify DB
    session_db = str(temp_db_path)
    await init_db(session_db)
    sessions = await list_sessions(session_db)
    assert len(sessions) >= 1
    session = await get_session(session_db, sessions[0].id)
    assert session is not None
    user_msgs = [m for m in session.messages if m.role == "user"]
    assert len(user_msgs) >= 1
    assert user_msgs[0].content == "Persist user msg"


# ---------------------------------------------------------------------------
# assistant_message_saved_to_db
# ---------------------------------------------------------------------------


async def test_assistant_message_saved_to_db(api_key, temp_db_path, monkeypatch):
    """After stream completes, Message(role='assistant') exists in the temp DB."""
    monkeypatch.setenv("REMMEH_DB_PATH", str(temp_db_path))
    with patch("remmeh.ui.screens.chat.OpenRouterClient") as MockClient:
        MockClient.return_value.stream_chat = mock_stream_hello
        app = RemmehApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause(0.2)
            screen = app.screen
            input_panel = screen.query_one("#input-panel", InputPanel)
            input_panel.post_message(InputPanel.Submitted("Persist assistant msg"))
            await pilot.pause(0.5)
            await pilot.pause(0.5)

    # After app exits, verify DB
    session_db = str(temp_db_path)
    await init_db(session_db)
    sessions = await list_sessions(session_db)
    assert len(sessions) >= 1
    session = await get_session(session_db, sessions[0].id)
    assert session is not None
    asst_msgs = [m for m in session.messages if m.role == "assistant"]
    assert len(asst_msgs) >= 1
    assert asst_msgs[0].content == "Hello world"


# ---------------------------------------------------------------------------
# rate_limit_error_shows_inline
# ---------------------------------------------------------------------------


async def test_rate_limit_error_shows_inline(api_key, temp_db_path, monkeypatch):
    """429/RateLimitError produces error MessageWidget with correct copy."""
    monkeypatch.setenv("REMMEH_DB_PATH", str(temp_db_path))
    with patch("remmeh.ui.screens.chat.OpenRouterClient") as MockClient:
        MockClient.return_value.stream_chat = mock_stream_rate_limit
        app = RemmehApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause(0.2)
            screen = app.screen
            input_panel = screen.query_one("#input-panel", InputPanel)
            input_panel.post_message(InputPanel.Submitted("Trigger rate limit"))
            await pilot.pause(0.5)
            await pilot.pause(0.5)
            messages = list(screen.query(MessageWidget))
            error_msgs = [m for m in messages if m.role == "error"]
            assert len(error_msgs) == 1
            assert "rate limit" in error_msgs[0].full_content.lower()


# ---------------------------------------------------------------------------
# timeout_error_shows_inline
# ---------------------------------------------------------------------------


async def test_timeout_error_shows_inline(api_key, temp_db_path, monkeypatch):
    """TimeoutError produces error MessageWidget with correct copy."""
    monkeypatch.setenv("REMMEH_DB_PATH", str(temp_db_path))
    with patch("remmeh.ui.screens.chat.OpenRouterClient") as MockClient:
        MockClient.return_value.stream_chat = mock_stream_timeout
        app = RemmehApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause(0.2)
            screen = app.screen
            input_panel = screen.query_one("#input-panel", InputPanel)
            input_panel.post_message(InputPanel.Submitted("Trigger timeout"))
            await pilot.pause(0.5)
            await pilot.pause(0.5)
            messages = list(screen.query(MessageWidget))
            error_msgs = [m for m in messages if m.role == "error"]
            assert len(error_msgs) == 1
            assert "timed out" in error_msgs[0].full_content.lower()


# ---------------------------------------------------------------------------
# missing_api_key_shows_inline
# ---------------------------------------------------------------------------


async def test_missing_api_key_shows_inline(temp_db_path, monkeypatch):
    """ValueError from load_config produces correct error copy in chat."""
    # Remove API key so config raises ValueError
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("REMMEH_DB_PATH", str(temp_db_path))
    app = RemmehApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause(0.2)
        screen = app.screen
        input_panel = screen.query_one("#input-panel", InputPanel)
        input_panel.post_message(InputPanel.Submitted("No key message"))
        await pilot.pause(0.5)
        messages = list(screen.query(MessageWidget))
        error_msgs = [m for m in messages if m.role == "error"]
        assert len(error_msgs) == 1
        # load_config raises: "OPENROUTER_API_KEY not set. Add it to .env..."
        assert "openrouter_api_key" in error_msgs[0].full_content.lower()


# ---------------------------------------------------------------------------
# cancel_leaves_partial_response
# ---------------------------------------------------------------------------


async def test_cancel_leaves_partial_response(api_key, temp_db_path, monkeypatch):
    """CancelledError leaves assistant widget with partial content, no error widget."""
    monkeypatch.setenv("REMMEH_DB_PATH", str(temp_db_path))
    with patch("remmeh.ui.screens.chat.OpenRouterClient") as MockClient:
        MockClient.return_value.stream_chat = mock_stream_partial
        app = RemmehApp()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause(0.2)
            screen = app.screen
            input_panel = screen.query_one("#input-panel", InputPanel)
            input_panel.post_message(InputPanel.Submitted("Cancel me"))
            # Wait for the first token to be received
            await pilot.pause(0.5)
            # Cancel stream with Escape
            await pilot.press("escape")
            await pilot.pause(0.5)
            messages = list(screen.query(MessageWidget))
            # No error widget should be present after cancellation
            error_msgs = [m for m in messages if m.role == "error"]
            assert len(error_msgs) == 0
            # Assistant widget with partial content should remain
            asst_msgs = [m for m in messages if m.role == "assistant"]
            assert len(asst_msgs) == 1
            assert "Partial content" in asst_msgs[0].full_content
