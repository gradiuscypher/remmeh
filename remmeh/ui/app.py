"""Root Textual application for remmeh."""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Label


class RemmehApp(App[None]):
    """Keyboard-first TUI LLM chat application."""

    TITLE = "remmeh"
    SUB_TITLE = "keyboard-first LLM chat"

    def compose(self) -> ComposeResult:
        """Build the initial widget tree."""
        yield Header()
        yield Label("Welcome to remmeh — press Ctrl+C to quit.")
        yield Footer()
