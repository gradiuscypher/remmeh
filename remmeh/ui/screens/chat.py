"""ChatScreen — primary screen with StatusBar / ChatView / InputPanel layout."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen

from remmeh.config import DEFAULT_MODEL
from remmeh.ui.widgets.chat_view import ChatView
from remmeh.ui.widgets.input_panel import InputPanel
from remmeh.ui.widgets.status_bar import StatusBar


class ChatScreen(Screen[None]):
    """Primary screen: StatusBar / ChatView / InputPanel."""

    CSS_PATH = "../remmeh.tcss"

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", priority=True),
        Binding("ctrl+c", "quit", "Quit", priority=True, show=False),
        Binding("escape", "cancel_stream", "Cancel", show=False),
    ]

    def compose(self) -> ComposeResult:
        """Build the three-panel layout."""
        yield StatusBar(id="status-bar")
        yield ChatView(id="chat-view")
        yield InputPanel(id="input-panel")

    def on_mount(self) -> None:
        """Set initial model name in status bar after mounting."""
        status_bar = self.query_one("#status-bar", StatusBar)
        status_bar.update_model(DEFAULT_MODEL)

    def on_input_panel_submitted(self, event: InputPanel.Submitted) -> None:
        """Handle user message submission — wired to streaming in Plan 05."""
        self.app.log(f"Submitted: {event.text!r}")

    def action_cancel_stream(self) -> None:
        """Cancel active streaming worker — wired in Plan 05."""
        self.app.log("cancel_stream action (no-op in Plan 04)")
