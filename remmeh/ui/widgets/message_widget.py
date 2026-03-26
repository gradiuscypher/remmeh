"""MessageWidget — renders a single chat turn with streaming support."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Markdown, RichLog, Static


class MessageWidget(Widget):
    """Renders a single chat message. Supports streaming via RichLog → Markdown swap."""

    DEFAULT_CSS = """
    MessageWidget {
        margin: 0 0 1 0;
        padding: 0 1;
    }
    MessageWidget.user {
        border-left: solid $primary;
        padding-left: 2;
    }
    MessageWidget.assistant {
        padding-left: 0;
    }
    MessageWidget.error {
        border-left: solid $error;
        padding-left: 2;
    }
    .message-header {
        text-style: bold;
        margin-bottom: 1;
    }
    .user .message-header {
        color: $primary;
    }
    .error .message-header {
        color: $error;
    }
    """

    def __init__(
        self,
        role: str,
        initial_content: str = "",
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        """Initialize a MessageWidget.

        Args:
            role: Message role — "user", "assistant", or "error".
            initial_content: Pre-existing content (non-streaming or completed messages).
            name: Widget name passed to Textual.
            id: Widget CSS id passed to Textual.
            classes: Additional CSS classes.
            disabled: Whether the widget starts disabled.
        """
        # Merge role into classes so CSS selectors work
        merged_classes = role if not classes else f"{role} {classes}"
        super().__init__(name=name, id=id, classes=merged_classes, disabled=disabled)
        self.role = role
        self._content = initial_content
        # Streaming mode: assistant widget with no initial content
        self._streaming = role == "assistant" and not initial_content
        self._rich_log: RichLog | None = None

    def compose(self) -> ComposeResult:
        """Build the widget tree based on role and streaming state."""
        if self.role == "user":
            yield Static("[bold]You:[/]", classes="message-header")
            yield Static(self._content)
        elif self.role == "assistant":
            yield Static("[bold]Assistant:[/]", classes="message-header")
            if self._streaming:
                # Streaming mode: RichLog for incremental writes (no scroll-reset jitter).
                # Do NOT use Markdown widget during streaming — it re-renders everything.
                rich_log = RichLog(id="stream-log", wrap=True, markup=False)
                self._rich_log = rich_log
                yield rich_log
            else:
                # Completed response: use Markdown for full rendering.
                yield Markdown(self._content)
        elif self.role == "error":
            yield Static("[bold $error]Error:[/]", classes="message-header")
            yield Static(self._content)

    def write_chunk(self, chunk: str) -> None:
        """Append a streaming token to the RichLog.

        Called per token during streaming. Writes to the RichLog with no end
        separator so chunks are concatenated visually.

        Args:
            chunk: A single text token from the LLM stream.
        """
        if self._rich_log is not None:
            self._rich_log.write(chunk, end="")
        self._content += chunk

    def swap_to_markdown(self) -> None:
        """Replace the RichLog with a Markdown widget on stream completion.

        Streaming swap pattern:
        - RichLog.write(chunk) per token during streaming
        - Replace with Markdown(full_text) on completion
        - Do NOT call Markdown.update() per chunk

        Uses call_after_refresh to avoid mid-render mutation.
        """
        if self._rich_log is not None:
            rich_log = self._rich_log
            self._rich_log = None
            self._streaming = False
            self.app.call_after_refresh(self._do_swap, rich_log)

    def _do_swap(self, rich_log: RichLog) -> None:
        """Remove the RichLog and mount a Markdown widget with the full response."""
        rich_log.remove()
        self.mount(Markdown(self._content))

    @property
    def full_content(self) -> str:
        """Return the full accumulated content of this message."""
        return self._content
