"""Textual headless layout tests for RemmehApp.

Verifies that the TUI widget tree is correctly assembled without needing
a real terminal — uses App.run_test() in headless mode.

Note: Widgets are queried via app.screen.query_one() (not app.query_one())
because ChatScreen is pushed via push_screen(), which means it does not
inherit directly from the default screen layer.
"""

from __future__ import annotations

from remmeh.config import DEFAULT_MODEL
from remmeh.ui.app import RemmehApp
from remmeh.ui.screens.chat import ChatScreen
from remmeh.ui.widgets import ChatView, InputPanel, StatusBar

# ---------------------------------------------------------------------------
# app_mounts_chat_screen
# ---------------------------------------------------------------------------


async def test_app_mounts_chat_screen(monkeypatch):
    """App has a ChatScreen mounted after startup."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-fake-key")
    app = RemmehApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause(0.1)
        assert isinstance(app.screen, ChatScreen)


# ---------------------------------------------------------------------------
# chat_screen_has_status_bar
# ---------------------------------------------------------------------------


async def test_chat_screen_has_status_bar(monkeypatch):
    """query_one(StatusBar) on app.screen succeeds."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-fake-key")
    app = RemmehApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause(0.1)
        status_bar = app.screen.query_one(StatusBar)
        assert status_bar is not None


# ---------------------------------------------------------------------------
# chat_screen_has_chat_view
# ---------------------------------------------------------------------------


async def test_chat_screen_has_chat_view(monkeypatch):
    """query_one(ChatView) on app.screen succeeds."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-fake-key")
    app = RemmehApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause(0.1)
        chat_view = app.screen.query_one(ChatView)
        assert chat_view is not None


# ---------------------------------------------------------------------------
# chat_screen_has_input_panel
# ---------------------------------------------------------------------------


async def test_chat_screen_has_input_panel(monkeypatch):
    """query_one(InputPanel) on app.screen succeeds."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-fake-key")
    app = RemmehApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause(0.1)
        input_panel = app.screen.query_one(InputPanel)
        assert input_panel is not None


# ---------------------------------------------------------------------------
# status_bar_shows_model
# ---------------------------------------------------------------------------


async def test_status_bar_shows_model(monkeypatch):
    """StatusBar _model_name contains DEFAULT_MODEL."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-fake-key")
    app = RemmehApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause(0.1)
        status_bar = app.screen.query_one(StatusBar)
        assert DEFAULT_MODEL in status_bar._model_name
