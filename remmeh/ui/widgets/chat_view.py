"""ChatView widget — scrollable chat thread container."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widget import Widget
from textual.widgets import Static


class ChatView(VerticalScroll):
    """Scrollable chat thread container. Mounts MessageWidget instances."""

    def __init__(
        self,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        """Initialize the chat view with empty state tracking."""
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self._has_messages: bool = False

    def compose(self) -> ComposeResult:
        """Shows empty state until first message."""
        yield Static("Start a conversation", classes="empty-heading")
        yield Static(
            "Type a message below to begin chatting.",
            classes="empty-body",
        )

    def add_message_widget(self, widget: Widget) -> None:
        """Mount a new MessageWidget and scroll to end."""
        if not self._has_messages:
            # Remove the empty state widgets
            self._has_messages = True
            for child in list(self.children):
                child.remove()
        self.mount(widget)
        self.scroll_end(animate=False)

    def scroll_to_end(self) -> None:
        """Scroll to bottom without animation (per UI spec)."""
        self.scroll_end(animate=False)
