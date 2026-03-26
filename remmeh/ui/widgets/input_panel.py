"""InputPanel widget — bottom 5-row input panel with Enter-to-submit behavior."""

from __future__ import annotations

import contextlib

from textual.app import ComposeResult
from textual.events import Key
from textual.message import Message as TextualMessage
from textual.widget import Widget
from textual.widgets import TextArea


class InputPanel(Widget):
    """Bottom 5-row input panel. Posts Submitted on Enter."""

    class Submitted(TextualMessage):
        """Posted when user submits a message."""

        def __init__(self, text: str) -> None:
            """Initialize with the submitted text."""
            self.text = text
            super().__init__()

    def __init__(
        self,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        """Initialize the input panel."""
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)

    def compose(self) -> ComposeResult:
        """Build the input panel widget tree."""
        yield TextArea(
            id="input-area",
            soft_wrap=True,
        )

    def on_mount(self) -> None:
        """Configure TextArea after mounting."""
        text_area = self.query_one("#input-area", TextArea)
        text_area.show_line_numbers = False
        # Set placeholder text via the TextArea attribute if available
        with contextlib.suppress(AttributeError):
            text_area.placeholder = "Message… (Enter to send, Shift+Enter for newline)"  # type: ignore[attr-defined]

    def on_key(self, event: Key) -> None:
        """Handle Enter key to submit, Shift+Enter to insert newline."""
        if event.key == "enter":
            # Prevent Enter from inserting a newline in the TextArea
            event.prevent_default()
            event.stop()
            text_area = self.query_one("#input-area", TextArea)
            text = text_area.text.strip()
            if text:
                text_area.clear()
                self.post_message(InputPanel.Submitted(text))
        # Shift+Enter (key == "shift+enter") falls through to TextArea default behavior

    def disable(self) -> None:
        """Disable input while streaming is active."""
        text_area = self.query_one("#input-area", TextArea)
        text_area.read_only = True
        self.add_class("disabled")

    def enable(self) -> None:
        """Re-enable input after streaming completes or errors."""
        text_area = self.query_one("#input-area", TextArea)
        text_area.read_only = False
        self.remove_class("disabled")
