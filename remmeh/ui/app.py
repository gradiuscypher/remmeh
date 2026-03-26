"""Root Textual application for remmeh."""

from __future__ import annotations

from textual.app import App

from remmeh.ui.screens.chat import ChatScreen


class RemmehApp(App[None]):
    """remmeh — keyboard-first TUI LLM chat."""

    TITLE = "remmeh"
    SCREENS = {"chat": ChatScreen}

    def on_mount(self) -> None:
        """Push the chat screen on startup."""
        self.push_screen("chat")
