"""ChatScreen — primary screen with StatusBar / ChatView / InputPanel layout."""

from __future__ import annotations

import asyncio
from pathlib import Path

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen

from remmeh.api.openrouter import (
    NetworkError,
    OpenRouterClient,
    OpenRouterError,
    RateLimitError,
    TimeoutError,
)
from remmeh.config import DEFAULT_MODEL, load_config
from remmeh.models import ChatSession, Message
from remmeh.storage import append_message, create_session, init_db
from remmeh.ui.screens.model_input import ModelInputScreen
from remmeh.ui.widgets.chat_view import ChatView
from remmeh.ui.widgets.input_panel import InputPanel
from remmeh.ui.widgets.message_widget import MessageWidget
from remmeh.ui.widgets.status_bar import StatusBar


class ChatScreen(Screen[None]):
    """Primary screen: StatusBar / ChatView / InputPanel."""

    CSS_PATH = "../remmeh.tcss"

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", priority=True),
        Binding("ctrl+c", "quit", "Quit", priority=True, show=False),
        Binding("escape", "cancel_stream", "Cancel", show=False),
        Binding("ctrl+m", "switch_model", "Model", show=True),
    ]

    def __init__(self) -> None:
        """Initialize ChatScreen with lazy config and streaming state."""
        super().__init__()
        self._config = None
        self._client: OpenRouterClient | None = None
        self._session: ChatSession | None = None
        self._current_assistant_widget: MessageWidget | None = None
        # OpenRouter-format message history for multi-turn context
        self._stream_messages: list[dict] = []

    def compose(self) -> ComposeResult:
        """Build the three-panel layout."""
        yield StatusBar(id="status-bar")
        yield ChatView(id="chat-view")
        yield InputPanel(id="input-panel")

    def on_mount(self) -> None:
        """Set initial model name in status bar and initialize DB."""
        status_bar = self.query_one("#status-bar", StatusBar)
        status_bar.update_model(DEFAULT_MODEL)
        # Initialize SQLite DB at startup — runs in background worker
        self.run_worker(self._init_storage(), exclusive=False)

    async def _init_storage(self) -> None:
        """Initialize SQLite DB with WAL mode at startup.

        Runs as a background worker on mount. If config is missing (no API key),
        skips silently — the error will surface on first message submission.
        """
        try:
            cfg = self._get_config()
            Path(cfg.db_path).parent.mkdir(parents=True, exist_ok=True)
            await init_db(cfg.db_path)
        except ValueError:
            # API key not configured yet — silently skip DB init.
            # Error will be shown inline when user submits their first message.
            pass

    def _get_config(self):
        """Lazy config load. Raises ValueError with clear message if API key missing."""
        if self._config is None:
            self._config = load_config()
            self._client = OpenRouterClient(api_key=self._config.api_key)
            self.query_one("#status-bar", StatusBar).update_model(self._config.model)
        return self._config

    async def _ensure_session(self) -> ChatSession:
        """Create and persist a new ChatSession if none exists for this screen."""
        if self._session is None:
            cfg = self._get_config()
            session = ChatSession(model=cfg.model)
            self._session = await create_session(cfg.db_path, session)
        return self._session

    def on_input_panel_submitted(self, event: InputPanel.Submitted) -> None:
        """Handle user message submission."""
        text = event.text.strip()
        if not text:
            return
        self._submit_message(text)

    @work(exclusive=True, exit_on_error=False)
    async def _submit_message(self, text: str) -> None:
        """Streaming chat worker.

        Critical pitfalls addressed:
        1. @work(exclusive=True) — submitting a new message cancels any in-progress stream.
        3. exit_on_error=False — exceptions don't kill the TUI; handled inline via error widgets.
        """
        chat_view = self.query_one("#chat-view", ChatView)
        input_panel = self.query_one("#input-panel", InputPanel)
        status_bar = self.query_one("#status-bar", StatusBar)

        # --- Pre-flight: validate config (catches missing API key) ---
        try:
            cfg = self._get_config()
        except ValueError as exc:
            error_widget = MessageWidget(role="error", initial_content=str(exc))
            chat_view.add_message_widget(error_widget)
            return

        # --- Display user message immediately ---
        user_widget = MessageWidget(role="user", initial_content=text)
        chat_view.add_message_widget(user_widget)

        # --- Build OpenRouter message history for multi-turn context ---
        self._stream_messages.append({"role": "user", "content": text})

        # --- Persist user message to SQLite ---
        session = await self._ensure_session()
        user_msg = Message(role="user", content=text, session_id=session.id)
        await append_message(cfg.db_path, user_msg)

        # --- Disable input and activate streaming state in status bar ---
        input_panel.disable()
        status_bar.set_streaming(True)

        # --- Mount assistant widget in streaming mode (RichLog active) ---
        assistant_widget = MessageWidget(role="assistant")
        self._current_assistant_widget = assistant_widget
        chat_view.add_message_widget(assistant_widget)
        # Yield control so Textual can run compose() on the assistant widget
        # before we start writing chunks. Without this, swap_to_markdown() is
        # called before _rich_log is set by compose(), causing a silent no-op.
        await asyncio.sleep(0)

        # --- Stream tokens from OpenRouter ---
        full_response = ""
        try:
            async for chunk in self._client.stream_chat(  # type: ignore[union-attr]
                messages=self._stream_messages,
                model=cfg.model,
            ):
                assistant_widget.write_chunk(chunk)
                full_response += chunk
                chat_view.scroll_to_end()
        except RateLimitError:
            error_msg = "Rate limit reached. Wait a moment and try again."
            self._replace_with_error(assistant_widget, chat_view, error_msg)
            full_response = ""
        except TimeoutError:
            error_msg = "Request timed out. Check your connection and try again."
            self._replace_with_error(assistant_widget, chat_view, error_msg)
            full_response = ""
        except NetworkError:
            error_msg = "Connection error. Check your internet connection and try again."
            self._replace_with_error(assistant_widget, chat_view, error_msg)
            full_response = ""
        except OpenRouterError as exc:
            error_msg = f"Request failed: {exc}. Try again or check your API key."
            self._replace_with_error(assistant_widget, chat_view, error_msg)
            full_response = ""
        except asyncio.CancelledError:
            # Stream cancelled via Escape key — leave partial response visible.
            # No error widget — cancellation is intentional.
            pass
        else:
            # Stream completed successfully — swap RichLog → Markdown.
            assistant_widget.swap_to_markdown()
            # Update message history for multi-turn context
            if full_response:
                self._stream_messages.append({"role": "assistant", "content": full_response})

        # --- Persist assistant response to SQLite (if any content was received) ---
        if full_response:
            asst_msg = Message(role="assistant", content=full_response, session_id=session.id)
            await append_message(cfg.db_path, asst_msg)

        # --- Re-enable input and clear streaming state ---
        input_panel.enable()
        status_bar.set_streaming(False)
        self._current_assistant_widget = None

    def _replace_with_error(
        self,
        assistant_widget: MessageWidget,
        chat_view: ChatView,
        error_msg: str,
    ) -> None:
        """Replace a streaming assistant widget with an error widget.

        Args:
            assistant_widget: The in-progress streaming widget to remove.
            chat_view: The ChatView container.
            error_msg: Human-readable error text to display.
        """
        assistant_widget.remove()
        error_widget = MessageWidget(role="error", initial_content=error_msg)
        chat_view.add_message_widget(error_widget)

    def action_cancel_stream(self) -> None:
        """Cancel active streaming worker (Escape key binding)."""
        for worker in self.workers:
            if worker.is_running:
                worker.cancel()

    def action_switch_model(self) -> None:
        """Open the model input modal (Ctrl+M)."""
        current = self._config.model if self._config else DEFAULT_MODEL

        def _on_model_selected(new_model: str | None) -> None:
            if new_model and new_model != current:
                # Update config and client with the new model
                if self._config is None:
                    try:
                        self._config = load_config()
                    except ValueError:
                        return
                self._config = self._config.__class__(
                    api_key=self._config.api_key,
                    model=new_model,
                    db_path=self._config.db_path,
                )
                self._client = OpenRouterClient(api_key=self._config.api_key)
                self.query_one("#status-bar", StatusBar).update_model(new_model)

        self.app.push_screen(ModelInputScreen(current), _on_model_selected)
