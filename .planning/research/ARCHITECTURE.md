# Architecture Research

**Domain:** Textual TUI LLM chat application
**Researched:** 2026-03-26
**Confidence:** HIGH (sourced directly from official Textual documentation)

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         UI Layer (Textual)                               │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  RemmehApp (App subclass)                                        │   │
│  │  ┌──────────────────────────────────┐  ┌───────────────────────┐│   │
│  │  │  ChatScreen (Screen subclass)    │  │ SessionSidebar        ││   │
│  │  │  ┌────────────────────────────┐ │  │ (slide-in/out panel)  ││   │
│  │  │  │ ChatView (VerticalScroll)  │ │  │ ┌─────────────────┐   ││   │
│  │  │  │ ┌────────────────────────┐│ │  │ │ SessionList     │   ││   │
│  │  │  │ │ MessageWidget (×N)     ││ │  │ │ (ListView)      │   ││   │
│  │  │  │ │ Markdown + RichLog     ││ │  │ └─────────────────┘   ││   │
│  │  │  │ └────────────────────────┘│ │  └───────────────────────┘│   │
│  │  │  └────────────────────────────┘ │                           │   │
│  │  │  ┌────────────────────────────┐ │                           │   │
│  │  │  │ InputPanel (TextArea)      │ │                           │   │
│  │  │  └────────────────────────────┘ │                           │   │
│  │  └──────────────────────────────────┘                           │   │
│  │  ┌──────────────────────────────────────────────────────────┐   │   │
│  │  │  CommandPalette (built-in, extended with custom Provider) │   │   │
│  │  └──────────────────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Workers (async tasks, owned by App/Screen/Widget)              │   │
│  │  ┌──────────────────────┐  ┌──────────────────────────────┐    │   │
│  │  │ @work stream_response│  │ @work(thread=True) fetch_... │    │   │
│  │  └──────────────────────┘  └──────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │ calls (pure Python, no Textual)
┌────────────────────────────────▼────────────────────────────────────────┐
│                         Service Layer                                   │
│  ┌────────────────────┐  ┌──────────────────┐  ┌──────────────────┐   │
│  │  ChatService       │  │  ModelService    │  │  SessionService  │   │
│  │  (send / stream)   │  │  (list, favorite)│  │  (CRUD + folders)│   │
│  └─────────┬──────────┘  └───────┬──────────┘  └─────────┬────────┘   │
└────────────┼──────────────────────┼──────────────────────┬┼────────────┘
             │                      │                       ││
┌────────────▼──────────────────────▼───────────────────────▼▼───────────┐
│                 Integration + Storage Layers                            │
│  ┌───────────────────────────┐   ┌────────────────────────────────┐   │
│  │  OpenRouterClient         │   │  LocalStorage (SQLite/JSON)    │   │
│  │  (httpx async)            │   │  sessions/, messages, settings │   │
│  └───────────────────────────┘   └────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Textual Type |
|-----------|----------------|--------------|
| `RemmehApp` | App lifecycle, keybindings, command palette, screen management | `App` subclass |
| `ChatScreen` | Primary chat view layout, composes chat panel + input | `Screen` subclass |
| `ChatView` | Scrollable container holding all `MessageWidget`s | `VerticalScroll` or custom widget |
| `MessageWidget` | Renders a single message (user or assistant) with Markdown | Custom `Widget` subclass |
| `InputPanel` | 3-line input with scroll; captures Enter to send | `TextArea` or custom `Widget` |
| `SessionSidebar` | Slide-in/out right panel showing session list | Custom `Widget` with CSS `display: block/none` or `offset` animation |
| `SessionList` | Scrollable list of sessions; posts `SessionSelected` message | `ListView` or `OptionList` |
| `CommandPalette` | Built-in Textual palette, extended with `Provider` subclasses | Built-in (customized via `COMMANDS` class var) |
| `ChatService` | Formats messages, holds in-flight state, calls OpenRouterClient | Pure Python class |
| `ModelService` | Fetches model list, persists favorites/defaults | Pure Python class |
| `SessionService` | Creates, renames, deletes sessions and folders | Pure Python class |
| `OpenRouterClient` | httpx async client, streaming SSE responses | Pure Python, `httpx.AsyncClient` |
| `LocalStorage` | SQLite (via `aiosqlite`) or JSON file persistence | Pure Python |

---

## Recommended Project Structure

```
remmeh/
├── main.py                   # Entry point: instantiate App, call app.run()
├── app.py                    # RemmehApp (App subclass) — keybindings, SCREENS, COMMANDS
│
├── ui/
│   ├── __init__.py
│   ├── screens/
│   │   ├── __init__.py
│   │   └── chat.py           # ChatScreen (Screen subclass) — main chat layout
│   ├── widgets/
│   │   ├── __init__.py
│   │   ├── chat_view.py      # ChatView — scrollable message container
│   │   ├── message_widget.py # MessageWidget — single message renderer
│   │   ├── input_panel.py    # InputPanel — 3-line input with scroll
│   │   └── session_sidebar.py# SessionSidebar — slide-in session list
│   └── commands/
│       ├── __init__.py
│       ├── model_provider.py # CommandPalette Provider for model switching
│       └── session_provider.py # CommandPalette Provider for session actions
│
├── services/
│   ├── __init__.py
│   ├── chat.py               # ChatService — message formatting, session state
│   ├── models.py             # ModelService — model list, favorites, defaults
│   └── sessions.py           # SessionService — session and folder CRUD
│
├── integrations/
│   ├── __init__.py
│   └── openrouter.py         # OpenRouterClient — httpx, streaming SSE
│
├── storage/
│   ├── __init__.py
│   └── local.py              # LocalStorage — SQLite/JSON persistence
│
└── styles/
    └── app.tcss              # Textual CSS — all layout/style rules
```

### Structure Rationale

- **`ui/`:** All Textual-specific code. Widgets and screens are pure display — they call services, not storage directly.
- **`ui/commands/`:** `Provider` subclasses kept separate from widgets; they have their own lifecycle (startup/search/shutdown).
- **`services/`:** Business logic, zero Textual imports. Tested independently.
- **`integrations/`:** API client isolation. Swap OpenRouter for another provider without touching UI.
- **`storage/`:** Storage isolation. Migrate from JSON to SQLite without touching service logic.
- **`styles/app.tcss`:** All CSS in one file initially; split per-screen if it grows large.

---

## Architectural Patterns

### Pattern 1: Worker for Streaming LLM Responses

**What:** Use `@work(exclusive=True)` on an async coroutine that streams from OpenRouter via httpx, posting custom messages back to the UI on each chunk. Workers run on Textual's asyncio event loop.

**When to use:** Any time you make a network call. Without a worker, the UI freezes until the response completes.

**Trade-offs:** Workers run on the same asyncio loop — httpx async works natively. If you used a sync HTTP library (e.g. `requests`), you would need `thread=True` instead, plus `call_from_thread()` to update the UI safely.

**Example:**
```python
from textual import work
from textual.widget import Widget
from textual.worker import get_current_worker

class ChatView(Widget):

    @work(exclusive=True)
    async def stream_response(self, session_id: str, user_message: str) -> None:
        """Runs in background; posts chunk messages to self."""
        worker = get_current_worker()
        async for chunk in self.app.openrouter.stream(user_message):
            if worker.is_cancelled:
                break
            # post_message is thread-safe; safe to call from async worker too
            self.post_message(ChatView.ChunkReceived(chunk))

    class ChunkReceived(Message):
        def __init__(self, chunk: str) -> None:
            super().__init__()
            self.chunk = chunk

    def on_chat_view_chunk_received(self, event: ChunkReceived) -> None:
        """Called on the main thread — safe to update widgets."""
        self.query_one("#active-message", MessageWidget).append_chunk(event.chunk)
```

**Critical rule:** `exclusive=True` cancels any running stream before starting a new one — essential for preventing race conditions when the user sends a new message before the previous response finishes.

---

### Pattern 2: Reactive Attributes for UI State

**What:** Declare `reactive` attributes on App or Screen for app-level state (current session ID, active model). Textual automatically calls `watch_*` methods when they change, keeping the UI in sync without manual refresh calls.

**When to use:** For state that multiple widgets need to observe — the active model name shown in the footer, the current session title shown in the header, loading/streaming state.

**Trade-offs:** `reactive` on App is app-global — use `var` (non-refreshing reactive) when you don't need the smart-refresh side effect, only the watch callback.

**Example:**
```python
from textual.app import App
from textual.reactive import reactive

class RemmehApp(App):
    # Shown in footer; triggers watch → footer re-renders
    active_model: reactive[str] = reactive("", init=False)

    # Whether a response is being streamed; shown as loading indicator
    is_streaming: reactive[bool] = reactive(False)

    def watch_active_model(self, model: str) -> None:
        self.query_one(Footer).update_model_label(model)

    def watch_is_streaming(self, streaming: bool) -> None:
        self.query_one(LoadingIndicator).display = streaming
```

---

### Pattern 3: Custom Messages for Widget-to-Parent Communication

**What:** Define `Message` subclasses as inner classes of the widget that emits them. Parent widgets handle them by naming the handler `on_{WidgetClass}_{MessageClass}` or using `@on(Widget.MessageClass)`. Messages bubble up the DOM unless `bubble = False`.

**When to use:** Child-to-parent communication (e.g. `SessionList` → `ChatScreen` → `RemmehApp`). Avoids tight coupling — the child doesn't import the parent.

**Trade-offs:** Message bubbling is automatic, which is powerful but can be surprising if a message is handled too far up the tree. Use `stop()` on the event to prevent further bubbling when needed.

**Example:**
```python
from textual.message import Message
from textual.widget import Widget

class SessionList(Widget):

    class SessionSelected(Message):
        """Posted when the user selects a session."""
        def __init__(self, session_id: str) -> None:
            super().__init__()
            self.session_id = session_id

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        session_id = str(event.item.id)
        self.post_message(SessionList.SessionSelected(session_id))


# In ChatScreen or RemmehApp (whichever handles session switching):
class ChatScreen(Screen):
    def on_session_list_session_selected(
        self, event: SessionList.SessionSelected
    ) -> None:
        self.load_session(event.session_id)
```

---

### Pattern 4: Command Palette Provider for All App Actions

**What:** Extend `Provider` (from `textual.command`) to add custom commands to the built-in command palette. Add providers to `App.COMMANDS`. Use `get_system_commands` for simple callback-based commands.

**When to use:** Every user-facing action should be reachable from the command palette. Model switching, new session, session rename, open settings — all registered here.

**Trade-offs:** Two APIs exist: `get_system_commands` (simple, synchronous, yields `SystemCommand`) and `Provider` subclass (async `startup/search/discover/shutdown`, more powerful, supports fuzzy matching of dynamic data like model names). Use `get_system_commands` for static actions; use `Provider` for dynamic content (models, sessions).

**Example:**
```python
from textual.command import Provider, Hit, Hits, DiscoveryHit

class ModelSwitchProvider(Provider):

    async def startup(self) -> None:
        # Called once when palette opens — fetch models in background
        worker = self.app.run_worker(self.app.model_service.list_models, thread=True)
        self.models = await worker.wait()

    async def search(self, query: str) -> Hits:
        matcher = self.matcher(query)
        for model in self.models:
            score = matcher.match(model.display_name)
            if score > 0:
                yield Hit(
                    score,
                    matcher.highlight(model.display_name),
                    lambda m=model: self.app.switch_model(m.id),
                    help=f"Switch to {model.display_name}",
                )

    async def discover(self) -> AsyncGenerator[DiscoveryHit, None]:
        # Show top-5 favorited models immediately when palette opens
        for model in self.app.model_service.favorites[:5]:
            yield DiscoveryHit(model.display_name, ..., ...)
```

---

### Pattern 5: Screen Stack for Modal Dialogs

**What:** Use `app.push_screen(screen, callback)` to show a modal (e.g. confirm delete, settings). The callback receives the screen's return value when it's popped. Textual maintains a screen stack; only the top screen receives input.

**When to use:** Any destructive action confirmation, settings form, or any UI state that should obscure the main chat screen temporarily.

**Trade-offs:** Simple for blocking-style interaction. For non-modal overlays (like the session sidebar), use CSS positioning (`dock: right`, `display: none/block`) instead of the screen stack.

**Example:**
```python
from textual.screen import ModalScreen
from textual.widgets import Button, Label

class ConfirmDeleteScreen(ModalScreen[bool]):
    def compose(self) -> ComposeResult:
        yield Label("Delete this session?")
        yield Button("Delete", id="confirm", variant="error")
        yield Button("Cancel", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "confirm")

# Usage in parent:
async def delete_session(self, session_id: str) -> None:
    def on_confirm(confirmed: bool) -> None:
        if confirmed:
            self.session_service.delete(session_id)
            self.refresh_session_list()

    self.app.push_screen(ConfirmDeleteScreen(), on_confirm)
```

---

## Data Flow

### Primary Flow: User Sends Message

```
User presses Enter in InputPanel
    │
    ▼
InputPanel.on_key (Enter) → posts InputPanel.Submitted message
    │
    ▼
ChatScreen.on_input_panel_submitted(event)
    │  calls service synchronously to persist user message
    ▼
ChatService.add_user_message(text) → LocalStorage.save_message()
    │
    ▼
ChatView.stream_response(session_id, text)  ← @work(exclusive=True)
    │  starts async worker (non-blocking, returns immediately)
    ▼
[Worker runs in background on asyncio loop]
    │
    ├── OpenRouterClient.stream(messages) → httpx async SSE
    │       ↓ each chunk
    │   ChatView.post_message(ChunkReceived(chunk))  ← thread-safe
    │
    ▼
ChatView.on_chat_view_chunk_received(event)  ← main thread
    │  appends chunk to MessageWidget
    ▼
MessageWidget.append_chunk(chunk) → widget.update() → Textual refresh
    │
    ▼
[Stream ends: Worker state → SUCCESS]
    │
    ▼
ChatService.finalize_message(full_text) → LocalStorage.save_message()
```

### Session Switch Flow

```
User selects session in SessionSidebar
    │
    ▼
SessionList posts SessionList.SessionSelected(session_id)
    │  message bubbles up DOM
    ▼
ChatScreen.on_session_list_session_selected(event)
    │
    ├── ChatService.cancel_streaming()         ← cancel any active worker
    ├── SessionService.load(session_id)        ← pure Python, synchronous ok for local storage
    │   or run_worker(SessionService.load, ...) if slow
    └── ChatView.render_session(session)       ← clear messages, mount MessageWidgets
```

### Model Switch Flow

```
User opens command palette (Ctrl+P) → types model name
    │
    ▼
ModelSwitchProvider.search(query) → yields Hit objects (fuzzy matched)
    │
    ▼
User selects → Hit callback: app.switch_model(model_id)
    │
    ▼
RemmehApp.switch_model(model_id)
    │
    ├── ModelService.set_active(model_id)      ← persists to storage
    └── self.active_model = model.display_name ← reactive → watch_active_model fires
         └── Footer re-renders with new model name
```

### Reactive State Flow

```
RemmehApp.is_streaming = True                  ← set when worker starts
    │ (reactive attribute, watch method fires)
    ▼
watch_is_streaming(new_value=True)
    │
    ▼
LoadingIndicator.display = True                ← widget becomes visible

RemmehApp.is_streaming = False                 ← set when worker ends
    │
    ▼
watch_is_streaming(new_value=False)
    │
    ▼
LoadingIndicator.display = False               ← widget hidden
```

---

## Suggested Build Order

Build in this order to avoid dependency direction problems:

1. **Storage layer** (`storage/local.py`) — pure Python, no dependencies on other layers. Define data models (Session, Message, Model).
2. **Integration layer** (`integrations/openrouter.py`) — pure Python, httpx. Can be tested standalone with mock responses.
3. **Service layer** (`services/`) — depends on storage + integration. Pure Python, testable without Textual.
4. **`RemmehApp` scaffold** (`app.py`) — minimal App subclass, wires services, defines keybindings and empty SCREENS.
5. **`InputPanel` widget** — simplest widget; demonstrates message → App flow.
6. **`MessageWidget`** — renders Markdown; test with hard-coded content first.
7. **`ChatView`** — container + worker integration; connect to `OpenRouterClient`.
8. **`ChatScreen`** — composes `ChatView` + `InputPanel`; wire submit → stream flow.
9. **`SessionSidebar`** — secondary panel; requires session storage to be complete.
10. **Command Palette providers** — requires services to be complete (model list, session list).

**Why this order:**
- Each step depends only on things built before it.
- The core chat send/receive loop (steps 1–8) is working before secondary features.
- Storage and services are testable without the UI layer, which speeds up iteration.

---

## CSS Patterns (Textual-specific)

### Layout: Docked Input Panel

The 3-line input panel docked to the bottom, chat view filling remaining space:

```css
/* app.tcss */
ChatScreen {
    layout: vertical;
}

ChatView {
    height: 1fr;       /* fills all available vertical space */
    overflow-y: auto;
}

InputPanel {
    height: 5;         /* 3 content lines + 1 border top + 1 border bottom */
    dock: bottom;
    border: solid $accent;
}
```

### Layout: Slide-In Sidebar

Session sidebar uses CSS `display` toggle (not the screen stack) for performance:

```css
SessionSidebar {
    width: 30;
    dock: right;
    display: none;     /* hidden by default */
    border-left: solid $panel;
}

SessionSidebar.visible {
    display: block;    /* toggled via add_class/remove_class */
}
```

Toggle in Python:
```python
def toggle_sidebar(self) -> None:
    sidebar = self.query_one(SessionSidebar)
    sidebar.toggle_class("visible")
```

### CSS File Strategy

Use a single `styles/app.tcss` file. Split per-screen only when it exceeds ~200 lines. Use `CSS_PATH` on the `App` class:

```python
class RemmehApp(App):
    CSS_PATH = "styles/app.tcss"
```

---

## Anti-Patterns

### Anti-Pattern 1: Blocking the Event Loop with Synchronous Network Calls

**What people do:** Call OpenRouter directly in an event handler with `await` but without a Worker.

```python
# BAD — blocks event loop until full response arrives
async def on_input_submitted(self, event: Input.Submitted) -> None:
    response = await openrouter_client.complete(event.value)  # freezes UI
    self.update_chat(response)
```

**Why it's wrong:** Textual runs on a single asyncio event loop. Awaiting a long network call in a message handler blocks ALL message processing — keyboard, mouse, render — until it completes. The app appears frozen.

**Do this instead:** Wrap in a `@work` decorated method. The worker runs on the same asyncio loop but Textual can process other messages between yields.

```python
# GOOD — UI stays responsive
def on_input_submitted(self, event: Input.Submitted) -> None:
    self.stream_response(event.value)  # returns immediately, starts worker

@work(exclusive=True)
async def stream_response(self, message: str) -> None:
    async for chunk in openrouter_client.stream(message):
        self.post_message(ChunkReceived(chunk))
```

---

### Anti-Pattern 2: Querying the DOM Before Mount

**What people do:** Call `self.query_one(Widget)` in `__init__` or in `on_load` before widgets are mounted.

**Why it's wrong:** `NoMatches` exception — the widget doesn't exist in the DOM yet. Textual's mount is asynchronous; composition happens in `compose()`, mounting completes before `on_mount()`.

**Do this instead:** DOM queries are safe in `on_mount` and all event handlers that fire after mount. Use `set_reactive` in constructors if you need to set initial reactive state without triggering watchers that query the DOM.

---

### Anti-Pattern 3: Using `self.app.query_one` from a Thread Worker

**What people do:** Update a widget directly from inside a `thread=True` worker.

```python
# BAD — not thread-safe
@work(thread=True)
def load_sessions(self) -> None:
    sessions = db.fetch_all()
    self.query_one(SessionList).refresh(sessions)  # race condition
```

**Why it's wrong:** Textual's widget methods are not thread-safe. Calling them from a thread worker causes unpredictable crashes or corrupted state.

**Do this instead:** Use `post_message()` (which IS thread-safe) to send a custom message back to the main thread, then update widgets in the handler.

```python
@work(thread=True)
def load_sessions(self) -> None:
    sessions = db.fetch_all()
    self.post_message(SessionsLoaded(sessions))  # thread-safe

def on_sessions_loaded(self, event: SessionsLoaded) -> None:
    self.query_one(SessionList).refresh(event.sessions)  # main thread, safe
```

---

### Anti-Pattern 4: Single Monolithic Screen

**What people do:** Put all UI logic (chat, sessions, settings, model picker) into one `App.compose()` with no `Screen` subclasses.

**Why it's wrong:** Becomes unwieldy quickly. Keybindings accumulate and conflict. Impossible to use screen stack for modals. Can't scope command palette commands to a specific screen via `Screen.COMMANDS`.

**Do this instead:** At minimum, one `ChatScreen` as the default screen. Add modal screens (`ModalScreen`) for destructive confirmations, settings overlays. Keep `App` as the thin top-level router.

---

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| OpenRouter API | `httpx.AsyncClient` with SSE streaming in async Worker | Use `@work(exclusive=True)` to cancel prior streams. Set `timeout=None` for streaming endpoints. |
| OpenRouter model list | Fetched once on startup via `@work`, cached in-memory + persisted locally | Refresh on command palette open via `Provider.startup()` |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Widget → Widget (child → parent) | Custom `Message` subclasses that bubble | Never import parent in child |
| Widget → Service | Direct method call (sync) or `run_worker(service.method)` | Services have no Textual imports |
| Worker → Widget | `post_message()` (thread-safe) | Only safe cross-thread communication path |
| Screen → Screen | `app.push_screen()` / `app.pop_screen()` with result callbacks | Use for modal dialogs only |
| App → global state | `reactive` attributes on `App` + `watch_*` methods | Propagates changes to any widget that queries App state |

---

## Sources

- Textual App Basics: https://textual.textualize.io/guide/app/
- Textual Workers: https://textual.textualize.io/guide/workers/
- Textual Reactivity: https://textual.textualize.io/guide/reactivity/
- Textual Screens: https://textual.textualize.io/guide/screens/
- Textual Events & Messages: https://textual.textualize.io/guide/events/
- Textual Command Palette: https://textual.textualize.io/guide/command_palette/
- All docs verified current as of 2026-03-26 (Textual latest)

---
*Architecture research for: Textual TUI LLM chat application (remmeh)*
*Researched: 2026-03-26*
