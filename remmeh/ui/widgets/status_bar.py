"""StatusBar widget — 1-row status bar showing model name and app name."""

from __future__ import annotations

from textual.widgets import Static


class StatusBar(Static):
    """1-row status bar. Left: model name. Right: app name."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        """Initialize the status bar with default model name."""
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]
        self._model_name: str = ""
        self._streaming: bool = False

    def on_mount(self) -> None:
        """Render initial content after mounting."""
        self.update(self._render())

    def _render(self) -> str:
        """Build the status bar content string."""
        if self._streaming:
            prefix = "⠋ Streaming…  "
        else:
            prefix = ""
        model_part = (
            f"[bold $accent]Model:[/] {self._model_name}"
            if self._model_name
            else "[dim]No model[/]"
        )
        return f"{prefix}{model_part}  [dim]remmeh[/]"

    def update_model(self, model: str) -> None:
        """Update the model name label."""
        self._model_name = model
        self.update(self._render())

    def set_streaming(self, active: bool) -> None:
        """Show/hide streaming indicator in status bar."""
        self._streaming = active
        self.update(self._render())
