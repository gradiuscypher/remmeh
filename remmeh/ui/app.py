"""Root Textual application for remmeh."""

from __future__ import annotations

from textual.app import App
from textual.binding import Binding

from remmeh.ui.screens.chat import ChatScreen


class RemmehApp(App[None]):
    """remmeh — keyboard-first TUI LLM chat."""

    TITLE = "remmeh"
    SCREENS = {"chat": ChatScreen}

    # ctrl+q and ctrl+c defined at App level so they override Textual's
    # system-level ctrl+c binding (which shows a "how to quit" notification
    # in Textual 8 and cannot be overridden from a Screen).
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", priority=True),
        Binding("ctrl+c", "quit", "Quit", priority=True, show=False),
    ]

    def on_mount(self) -> None:
        """Push the chat screen on startup."""
        self.push_screen("chat")
