# Pitfalls Research

**Domain:** Python TUI + LLM API chat application (Textual + OpenRouter)
**Researched:** 2026-03-26
**Confidence:** HIGH — all critical pitfalls verified against official Textual docs and OpenRouter API docs

---

## Critical Pitfalls

### Pitfall 1: Blocking the Textual Event Loop with Synchronous API Calls

**What goes wrong:**
An `async def` message handler (e.g., `on_button_pressed`) directly `await`s an OpenRouter API call. The handler is technically async, but it still occupies the Textual event loop for the entire duration of the network request — usually 1–30 seconds. The UI freezes: no key presses are processed, no animations run, the input field won't even echo keystrokes.

**Why it happens:**
Python's `asyncio` is cooperative, not preemptive. If an `async def` handler doesn't yield control quickly (e.g., it `await`s a long network call without offloading to a worker), the event loop is blocked for that entire call. Developers see `async def` and assume the UI will remain responsive — it will not, because `async def` and `await` do not move work off the event loop.

**How to avoid:**
Use Textual's `@work` decorator (or `self.run_worker()`) for all OpenRouter API calls. This offloads the work to a managed asyncio task (or thread) that won't block the event loop. For streaming responses, use `@work(exclusive=True)` to cancel in-progress requests when a new message is sent.

```python
# WRONG — blocks the event loop
async def on_button_pressed(self, event: Button.Pressed) -> None:
    response = await httpx_client.post(OPENROUTER_URL, ...)
    self.update_display(response)

# CORRECT — offloads to a worker
@work(exclusive=True)
async def send_message(self, user_text: str) -> None:
    async with httpx.AsyncClient() as client:
        response = await client.post(OPENROUTER_URL, ...)
    self.post_message(ResponseReady(response))
```

**Warning signs:**
- Input field stops responding while an LLM request is in flight
- The cursor stops blinking or animations stall during API calls
- `textual` devtools shows the event loop processing nothing while a request is pending

**Phase to address:** Phase 1 (Core API integration) — this architecture decision must be made before writing any OpenRouter call. Retrofitting sync-to-worker later is costly.

---

### Pitfall 2: Updating Widgets from a Thread Worker (Thread Safety Violation)

**What goes wrong:**
A `@work(thread=True)` worker calls methods on Textual widgets directly (e.g., `my_widget.update(text)`). Textual's widget methods are **not thread-safe**. This produces race conditions: occasional crashes, partially-rendered state, or silent corruption.

**Why it happens:**
Developers use `@work(thread=True)` for synchronous libraries (e.g., the `openai` SDK's non-async client) and then naturally call widget update methods from inside that thread, forgetting Textual's threading model.

**How to avoid:**
Use `self.call_from_thread(widget.update, value)` for any UI interaction from a thread worker. Alternatively, use `self.post_message(MyCustomMessage(...))` which **is** thread-safe — then handle the message in the main thread.

```python
@work(thread=True)
def fetch_models(self) -> None:
    models = openai_client.models.list()   # sync SDK call
    worker = get_current_worker()
    if not worker.is_cancelled:
        # CORRECT: call_from_thread for UI updates
        self.call_from_thread(self._populate_model_list, models)
```

**Warning signs:**
- Intermittent crashes or assertion errors inside Textual internals
- UI state that looks correct sometimes but corrupted other times
- Errors mentioning "not called from the event loop"

**Phase to address:** Phase 1 — decides whether to use async httpx or the sync openai SDK. If sync SDK is chosen, this becomes mandatory from the first API call.

---

### Pitfall 3: Streaming Responses Rendered as a Single Burst (No Incremental Display)

**What goes wrong:**
The LLM streaming API is called with `stream=True`, chunks are accumulated in a local buffer, and the widget is updated only once at the end. Users see a blank screen for 5–30 seconds then the full response appears instantly. This defeats the purpose of streaming and feels like a broken UI.

**Why it happens:**
Streaming is implemented at the API layer but not at the display layer. Developers accumulate chunks to parse complete Markdown before rendering, or call `widget.update()` in a loop but never yield control back to the event loop between chunks (calling `widget.update()` inside a tight `async for` loop without a brief `await` can also stall rendering if the chunk loop is fast enough to exhaust the render budget).

**How to avoid:**
- Call `widget.update()` (or use a `reactive` attribute) on **each chunk** as it arrives in the stream
- For Markdown display: either render raw text incrementally and re-parse Markdown only at completion, or use a `RichLog` widget for streaming and swap to a `Markdown` widget on completion
- Use `await asyncio.sleep(0)` sparingly if batching chunks prevents rendering

```python
@work(exclusive=True)
async def stream_response(self, messages: list) -> None:
    output = self.query_one("#response", RichLog)
    full_text = ""
    async with httpx.AsyncClient() as client:
        async with client.stream("POST", OPENROUTER_URL, json={...}) as resp:
            async for chunk in resp.aiter_lines():
                if chunk.startswith("data: "):
                    delta = parse_sse_chunk(chunk)
                    if delta:
                        full_text += delta
                        self.call_from_thread(output.write, delta)  # or output.write(delta) if async worker
```

**Warning signs:**
- LLM responses only appear after the full response is complete
- `stream=True` is set in the API call but no UI updates happen during streaming
- Widget update calls are all inside a `try/finally` block that runs after the stream loop

**Phase to address:** Phase 1 (streaming architecture must be decided upfront — retrofitting is painful).

---

### Pitfall 4: Hotkey Conflicts Between App Bindings and Focused Widget Bindings

**What goes wrong:**
An app-level binding (e.g., `ctrl+n` for new chat) fires when the user is typing in the `TextArea` input widget. The user presses Ctrl+N to type something, and instead triggers "New Chat", clearing their draft.

**Why it happens:**
Textual's binding resolution bubbles key events upward through the DOM: focused widget → parent containers → App. App-level `BINDINGS` without `priority=False` (the default) can intercept keys that the focused widget would also use. Some shortcuts that feel safe (Ctrl+N, Ctrl+W, Ctrl+S) are legitimate text-editing keystrokes in some terminals.

There is also the inverse problem: a TextArea widget consumes printable keys and arrow keys as text input, so bindings on parent widgets for those keys are silently swallowed.

**How to avoid:**
- Use `priority=True` only for bindings that **must** fire regardless of focus (e.g., Ctrl+Q to quit). Keep all other app bindings as `priority=False`.
- Prefer function keys (F1–F10), Ctrl+letter combinations not used for editing (Ctrl+P for palette, Ctrl+O for open, etc.), or Escape-based sequences for app-level actions.
- Route all commands through the Command Palette as the primary action mechanism — hotkeys as shortcuts, not as the sole access path.
- Run `textual keys` in the terminal to validate that chosen key combos are actually delivered to the app on the target terminal.

**Warning signs:**
- App-level action fires unexpectedly when the input box is focused
- Users report "pressing Ctrl+X deletes the whole conversation"
- Key bindings work in isolation but break when focus is on a text input widget

**Phase to address:** Phase 1 (Keybinding architecture) — design the binding table before implementing individual features, not after.

---

### Pitfall 5: `pytest-asyncio` Configuration Causing Silent Test Failures

**What goes wrong:**
Textual tests use `async with app.run_test() as pilot:` which requires async test functions. Without `asyncio_mode = "auto"` set in `pyproject.toml`, every async test must be decorated with `@pytest.mark.asyncio`. Tests written without the decorator appear to pass (pytest collects them as coroutine objects, not as test failures), but they never actually run — zero assertions are executed, zero bugs are caught.

**Why it happens:**
`pytest-asyncio` changed its default mode. In recent versions, the default `asyncio_mode = "strict"` requires explicit marking. Without it, async test functions are silently skipped rather than raising a configuration error.

**How to avoid:**
Set `asyncio_mode = "auto"` in `pyproject.toml` from the first test:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

Then verify by running `pytest -v` and confirming async tests show as `PASSED`/`FAILED` (not as `no tests ran`). Additionally, add at least one assertion-heavy test in each new module so silent passes are visible.

**Warning signs:**
- `pytest` reports `0 passed, 0 failed` or `no tests ran` despite test files existing
- Async test functions show `PASSED` in output but adding deliberate `assert False` doesn't cause failures
- CI reports 100% pass rate for a codebase with no test assertions

**Phase to address:** Phase 1 (test infrastructure setup) — must be configured before writing any tests.

---

### Pitfall 6: SQLite Write Corruption from Concurrent Workers

**What goes wrong:**
Multiple Textual workers (e.g., streaming a response while auto-saving session state) write to the same SQLite database concurrently without proper WAL mode or connection management. SQLite's default journal mode (`DELETE`) allows only one writer at a time; concurrent writes from different asyncio tasks produce `OperationalError: database is locked` or, worse, silently dropped writes.

**Why it happens:**
`aiosqlite` wraps SQLite in a thread, making it safe for asyncio use. But when multiple tasks open separate connections to the same database file concurrently, SQLite's per-file locking conflicts. Developers often open a new connection per operation rather than using a shared connection pool.

**How to avoid:**
- Use WAL mode (`PRAGMA journal_mode=WAL`) which allows concurrent reads and one writer without blocking
- Use a single shared `aiosqlite` connection (or connection pool) for the entire app lifetime
- Serialize all database writes through a single asyncio queue or Textual worker with `exclusive=True`

```python
# In app startup:
async def on_mount(self) -> None:
    self._db = await aiosqlite.connect(DB_PATH)
    await self._db.execute("PRAGMA journal_mode=WAL")
    await self._db.commit()
```

**Warning signs:**
- `OperationalError: database is locked` appearing in logs during heavy use
- Session data missing after app restart that was confirmed saved
- Two workers running simultaneously always produces a crash

**Phase to address:** Phase 1 (storage layer) — enable WAL mode from the first database migration.

---

### Pitfall 7: Textual CSS `height: auto` on Scrollable Chat Container

**What goes wrong:**
The main chat message container is given `height: auto` in TCSS, expecting it to grow with content. Instead, it collapses to zero height (no messages are visible), or it expands to fill the entire screen height and pushes the input panel offscreen.

**Why it happens:**
Textual CSS layout differs from web CSS. `height: auto` on a child inside a vertical layout means "size to fit content", but Textual uses fractional units (`1fr`) for proportional sizing. A container with `height: auto` inside a vertical layout has no guaranteed height and may get 0px or consume all remaining space depending on siblings.

**How to avoid:**
- Use `height: 1fr` for the chat container to consume all available space after fixed-height widgets (header, input panel)
- Use `min-height` to prevent collapse
- The input panel and sidebar should use explicit `height` values or `height: auto` only for single-line widgets where content size is deterministic
- Test layout with `textual run --dev` and use the inspector (`ctrl+i` in devtools) to visualize computed sizes

```tcss
/* WRONG — collapses or overflows */
#chat-history {
    height: auto;
    overflow-y: auto;
}

/* CORRECT — fills remaining space */
#chat-history {
    height: 1fr;
    overflow-y: auto;
}
```

**Warning signs:**
- Chat history area is invisible or collapsed to 0 rows
- Input panel is scrolled off-screen
- Layout looks correct in devtools preview but breaks when content is added

**Phase to address:** Phase 1 (UI layout implementation).

---

### Pitfall 8: Markdown Widget Re-render Causing Scroll Position Reset

**What goes wrong:**
During streaming, a `Markdown` widget is updated on every chunk (e.g., `markdown_widget.update(accumulated_text)`). Each `update()` call causes a full re-render, which resets the scroll position to the top. Users see the view jump to the beginning of the response on every chunk — several times per second.

**Why it happens:**
`Markdown.update()` replaces the widget's internal content tree and recalculates layout, which resets scroll position as a side effect. In a streaming loop, this runs ~10–50 times per second, causing severe visual jitter.

**How to avoid:**
- Use `RichLog.write()` for streaming tokens — `RichLog` appends content without re-rendering the entire widget and maintains scroll position
- Auto-scroll by calling `self.scroll_end(animate=False)` after each chunk
- Only use the `Markdown` widget for completed messages (render the final accumulated text once streaming finishes, then swap or replace)
- Alternatively, accumulate chunks client-side and update the `Markdown` widget at a throttled rate (every 100ms rather than every chunk)

**Warning signs:**
- Scroll position jumps to top during streaming
- CPU usage spikes during streaming (full Markdown parse per chunk is expensive)
- `Markdown.update()` is called inside the streaming loop

**Phase to address:** Phase 1 (chat display implementation).

---

### Pitfall 9: Worker Error Silently Crashing the App

**What goes wrong:**
An OpenRouter API worker raises an uncaught exception (network error, 429 rate limit, JSON parse error). With default settings, Textual exits the app and dumps the traceback to the terminal, leaving the user with a broken terminal state and no error message in the TUI.

**Why it happens:**
Textual workers have `exit_on_error=True` by default. This is good for development but catastrophic in production: a transient network error while streaming a response kills the entire application.

**How to avoid:**
- Use `@work(exclusive=True, exit_on_error=False)` for all API workers
- Handle `Worker.StateChanged` events to detect `WorkerState.ERROR` and display user-friendly error messages in the TUI
- Implement retry logic (with exponential backoff) for transient errors (429, 500, 503)
- Log errors to `textual`'s logging system (not `print`) so they appear in devtools without breaking the UI

```python
@work(exclusive=True, exit_on_error=False)
async def send_message(self, text: str) -> None:
    try:
        async with httpx.AsyncClient() as client:
            # ... API call
    except httpx.HTTPStatusError as e:
        self.post_message(APIError(f"HTTP {e.response.status_code}"))
    except Exception as e:
        self.post_message(APIError(str(e)))

def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
    if event.state == WorkerState.ERROR:
        self.notify(f"Request failed: {event.worker.error}", severity="error")
```

**Warning signs:**
- Any network hiccup exits the app entirely
- Users see a raw Python traceback instead of a TUI error message
- `exit_on_error` is not explicitly set on any worker

**Phase to address:** Phase 1 (API integration) — set from the first worker.

---

### Pitfall 10: OpenRouter Model List Fetched Synchronously at Startup

**What goes wrong:**
The app fetches the full model list from OpenRouter's API synchronously during `on_mount()` — before the UI has rendered. The app appears to hang for 1–3 seconds before showing anything. Alternatively, if fetch is done inside a non-worker async handler, the first screen is blank until the fetch completes.

**Why it happens:**
Startup sequence feels like a natural place to fetch initial data. Developers call `await fetch_models()` in `on_mount()` directly, which blocks the mount process.

**How to avoid:**
- Use a `@work` worker for the initial model fetch, triggered from `on_mount()`
- Show a loading state immediately (a `LoadingIndicator` widget or placeholder text)
- Cache the model list locally after first fetch (e.g., in a JSON file with a TTL)
- Populate the model selector incrementally as the fetch completes in the background

**Warning signs:**
- App shows a blank screen for several seconds on startup
- `await` is used inside `on_mount()` for any network operation
- Model list is not populated until the startup delay completes

**Phase to address:** Phase 1 (model switching feature).

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Accumulate full response, render once | Simpler code, clean Markdown render | No streaming UX, feels broken for long responses | Never — streaming is a core requirement |
| `print()` for debugging | Fast iteration | Corrupts TUI rendering (prints to stdout that Textual controls) | Never — use `textual.log()` or `self.log()` |
| Single global SQLite connection, no WAL | Simple setup | Deadlocks when workers write concurrently | Only if app guarantees strictly serial writes |
| Hardcode model IDs | Avoid API fetch complexity | Models change names/availability; breaks silently | Never — use the dynamic model list from day one |
| Flat JSON file for session history | Dead simple to implement | Degrades at ~50+ sessions; no atomic writes | MVP only, with a clear migration path to SQLite |
| Direct widget calls from thread workers | Shorter code | Race conditions, intermittent crashes | Never |
| `asyncio_mode = "strict"` (default) | No config needed | Async tests silently never run | Never — set `auto` from day one |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| OpenRouter streaming | Assuming SSE chunks always contain complete JSON | Parse `data: ` prefix, handle `[DONE]` sentinel, handle partial JSON across chunk boundaries |
| OpenRouter streaming | Not handling `stream=False` fallback for models that don't support streaming | Check model capabilities or catch non-streaming responses gracefully |
| OpenRouter model list | Fetching models inside a sync event handler | Use a `@work` worker; cache results with a TTL (models rarely change mid-session) |
| OpenRouter thinking blocks | Treating thinking content as regular assistant content | Store thinking blocks separately; don't include them in the visible chat thread by default; the API returns them as a distinct `thinking` field in some models |
| httpx async client | Creating a new `AsyncClient()` per request inside a worker | Share a single `httpx.AsyncClient` across the app lifetime (or at least per-session); creating clients per-request is expensive and leaks connections |
| aiosqlite | Opening separate connections per write operation | Use a shared connection opened at startup, with WAL mode enabled |
| `.env` loading | Loading `.env` after `App.__init__()` is called | Load environment variables at module import time (top of `main.py`) before any class is instantiated; Textual's `App.__init__` may be called before dotenv loads |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| `Markdown.update()` per streaming chunk | UI jitter, CPU spike, scroll reset | Use `RichLog` for streaming; `Markdown` for completed messages only | Immediately — every stream |
| `query_one()` in tight loops | Slow render on large session lists | Cache widget references in `on_mount()`; avoid querying in render-critical paths | At ~100+ messages per session |
| Loading all sessions into memory on startup | Slow startup as session count grows | Lazy-load session content; only load session metadata (title, timestamp) at startup | At ~200+ sessions |
| Re-rendering entire chat history on model switch | Perceptible lag when switching models | Model metadata lives in the session object; switching models doesn't touch the message history display | Immediately visible at 20+ messages |
| Throttle-less streaming widget updates | Excessive redraws on fast models (GPT-4o streams ~100 tokens/sec) | Batch chunk updates every 50ms or use `set_interval` to refresh the display buffer | On fast models with long responses |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Storing API key in `~/.remmeh/config.json` with 0644 permissions | Key readable by any user on the machine | Use `~/.config/remmeh/` with `chmod 600`; or load from `.env` file with restricted permissions |
| Logging `Authorization: Bearer <key>` headers in debug output | API key exposed in log files or devtools output | Redact headers in any debug logging; never pass the raw key through `self.log()` |
| Storing raw conversation content in world-readable files | Chat history with potentially sensitive content exposed | Store chat history in XDG data directory with user-only permissions (`~/.local/share/remmeh/`) |
| No input length validation before sending to OpenRouter | Accidentally sending massive context windows, incurring unexpected cost | Validate token estimates before sending; show user a warning if context is large |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No visual feedback during LLM request (no spinner) | User thinks the app is frozen; presses keys, triggers duplicate sends | Show a `LoadingIndicator` or status bar message immediately after send; disable the send button |
| Allowing second send while first is in progress | Duplicate requests; confused conversation state | Use `@work(exclusive=True)` to cancel the previous request; or disable input while streaming |
| No way to cancel an in-progress stream | User stuck waiting for a long response they don't want | Provide a "Stop generating" keybinding that calls `worker.cancel()` on the active stream worker |
| Auto-scroll to bottom disabled by default | New streaming content appears off-screen | Auto-scroll during streaming; stop auto-scroll if user manually scrolled up; resume on next message |
| Command palette not discoverable | Users don't know keyboard shortcuts exist | Show Command Palette hint on first launch; display `^P palette` in Footer from day one |
| Session list shows no metadata | Can't distinguish conversations | Show model name, timestamp, and first user message as session title |

---

## "Looks Done But Isn't" Checklist

- [ ] **Streaming:** Verify tokens appear incrementally, not all at once — send a long request (e.g., "write 500 words") and watch the display update in real time
- [ ] **Worker errors:** Kill network connectivity mid-stream — app should show an error toast, not crash or freeze
- [ ] **Hotkeys in input:** Focus the text area and press Ctrl+N (new chat), Ctrl+W — confirm they don't fire app actions while typing
- [ ] **Async tests:** Add `assert False` to one async test, run `pytest` — confirm it shows as `FAILED` (not silently ignored)
- [ ] **Model switch mid-session:** Switch models after 3 messages — confirm session history persists and new messages use the new model
- [ ] **Large session:** Generate 50+ messages — confirm scroll, performance, and persistence all work
- [ ] **Cold start:** Delete the database, start fresh — confirm model list loads, first session creates correctly
- [ ] **API key missing:** Start without a `.env` file — confirm a clear error message appears in the TUI, not a traceback

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Blocking event loop (sync API calls) | HIGH | Audit all `await` calls in message handlers; wrap each in `@work`; test with a slow API mock |
| Thread safety violations | MEDIUM | Replace all direct widget calls in thread workers with `call_from_thread()`; grep for `.update(`, `.append(`, `.write(` inside `@work(thread=True)` functions |
| No incremental streaming display | MEDIUM | Swap `Markdown` widget for `RichLog` in the streaming path; refactor to post-render Markdown only on completion |
| Silent async test failures | LOW | Add `asyncio_mode = "auto"` to `pyproject.toml`; re-run tests; expect previously "passing" tests to now fail (they were never running) |
| SQLite locking errors | MEDIUM | Enable WAL mode in a migration; consolidate to a single shared connection; may require a session format migration |
| App crash on worker error | LOW | Add `exit_on_error=False` to all `@work` decorators; add `on_worker_state_changed` handler |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Blocking event loop with sync API calls | Phase 1: Core API integration | Slow API mock shows UI stays responsive during request |
| Thread safety violations | Phase 1: Core API integration | Run concurrent send + model fetch; no crashes |
| No incremental streaming display | Phase 1: Chat display | Send long prompt; tokens appear within 200ms of first chunk |
| Hotkey conflicts with TextArea | Phase 1: Keybinding architecture | Focus input, test all app hotkeys manually and in automated pilot tests |
| Silent async test failures | Phase 1: Test infrastructure | `assert False` in one async test fails as expected |
| SQLite concurrent write corruption | Phase 1: Storage layer | Enable WAL mode in first migration; integration test with concurrent reads/writes |
| Markdown re-render on every chunk | Phase 1: Chat display | Profile render rate; confirm scroll doesn't reset during streaming |
| Worker error crashes app | Phase 1: API integration | Simulate 429 and network timeout; app shows error toast, stays open |
| Model list blocks startup | Phase 1: Model switching | Time startup; model list fetched in background, UI shows immediately |
| CSS layout collapse (`height: auto`) | Phase 1: UI layout | Devtools inspector shows computed heights; chat area is non-zero before first message |

---

## Sources

- Textual Workers guide: https://textual.textualize.io/guide/workers/ — confirmed sync-in-async and thread safety patterns
- Textual Testing guide: https://textual.textualize.io/guide/testing/ — `asyncio_mode = "auto"` requirement for pytest-asyncio
- Textual Input guide: https://textual.textualize.io/guide/input/ — binding priority model, focus-based key routing
- Textual FAQ: https://textual.textualize.io/FAQ/ — key combination terminal support, `WorkerDeclarationError`
- OpenRouter API docs: https://openrouter.ai/docs — model list endpoint, streaming via SSE, thinking blocks
- `.planning/codebase/CONCERNS.md` — identified: no async architecture, streaming not planned, no test infrastructure, no WAL mode decision
- `.planning/PROJECT.md` — requirements: streaming, thinking blocks, session persistence, configurable hotkeys, command palette

---
*Pitfalls research for: Python Textual TUI + OpenRouter LLM chat application*
*Researched: 2026-03-26*
