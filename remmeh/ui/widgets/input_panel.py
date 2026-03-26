"""InputPanel widget — bottom 5-row input panel with Enter-to-submit behavior."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.events import Key
from textual.message import Message as TextualMessage
from textual.widget import Widget
from textual.widgets import TextArea


class _SubmitTextArea(TextArea):
    """TextArea subclass that intercepts Enter/Shift+Enter before default handling.

    TextArea consumes key events before they bubble to the parent widget, so
    Enter-to-submit must be handled here rather than in InputPanel.on_key.
    """

    def on_key(self, event: Key) -> None:
        """Intercept Enter (submit) and Shift+Enter (newline)."""
        if event.key == "enter":
            event.prevent_default()
            event.stop()
            text = self.text.strip()
            if text:
                self.clear()
                # Post Submitted on the parent InputPanel so ChatScreen can handle it
                self.post_message(InputPanel.Submitted(text))
        elif event.key == "shift+enter":
            # Insert a literal newline at the cursor position
            event.prevent_default()
            event.stop()
            self.insert("\n")


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
        yield _SubmitTextArea(
            id="input-area",
            soft_wrap=True,
        )

    def on_mount(self) -> None:
        """Focus the TextArea on mount so the user can type immediately."""
        self.query_one("#input-area", _SubmitTextArea).focus()

    def disable(self) -> None:
        """Disable input while streaming is active."""
        text_area = self.query_one("#input-area", _SubmitTextArea)
        text_area.read_only = True
        self.add_class("disabled")

    def enable(self) -> None:
        """Re-enable input after streaming completes or errors."""
        text_area = self.query_one("#input-area", _SubmitTextArea)
        text_area.read_only = False
        self.remove_class("disabled")
        text_area.focus()
