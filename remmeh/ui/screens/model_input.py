"""ModelInputScreen — minimal modal for typing a model name (pre-Phase 2 shim)."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, Label


class ModelInputScreen(ModalScreen[str | None]):
    """Simple modal screen that prompts the user to type a model string.

    Returns the entered model string, or None if cancelled.
    Phase 2 will replace this with a full command-palette provider backed
    by the OpenRouter /models endpoint.
    """

    CSS = """
    ModelInputScreen {
        align: center middle;
    }

    #dialog {
        width: 70;
        height: auto;
        padding: 1 2;
        background: $surface;
        border: round $accent;
    }

    #label {
        margin-bottom: 1;
        color: $text-muted;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    def __init__(self, current_model: str) -> None:
        """Initialize with the currently active model string."""
        super().__init__()
        self._current_model = current_model

    def compose(self) -> ComposeResult:
        """Build the modal layout."""
        with Vertical(id="dialog"):
            yield Label("Enter model (e.g. anthropic/claude-3.5-sonnet):", id="label")
            yield Input(value=self._current_model, id="model-input")

    def on_mount(self) -> None:
        """Focus the input and select all text on open."""
        inp = self.query_one("#model-input", Input)
        inp.focus()
        inp.action_select_all()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Return the entered model string on Enter."""
        value = event.value.strip()
        self.dismiss(value if value else None)

    def action_cancel(self) -> None:
        """Dismiss without changing the model."""
        self.dismiss(None)
