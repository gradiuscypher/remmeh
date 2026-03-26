# Project Research Summary

**Project:** remmeh
**Domain:** Python TUI LLM chat tool (Textual + OpenRouter)
**Researched:** 2026-03-26
**Confidence:** HIGH

## Executive Summary

remmeh is a keyboard-first, full-screen TUI chat application built on Textual and the OpenRouter API. Experts in this space (Aider, llm CLI, AIChat, OpenCode) converge on a few non-negotiable patterns: streaming responses rendered token-by-token, persistent session storage in SQLite, and a clean separation between UI widgets and business-logic services. The unique differentiator for remmeh — a Textual-native command palette as the primary action hub — is well-supported by Textual's built-in `CommandPalette` and `Provider` system, and represents a genuine gap in the competitive landscape where no existing CLI LLM tool offers this pattern.

The recommended approach is a layered architecture: a pure-Python storage + service layer (testable without Textual), an OpenRouter integration client using `httpx.AsyncClient`, and a Textual UI layer of widgets and screens that call services but never touch storage directly. All LLM API calls must be wrapped in Textual `@work(exclusive=True)` workers — this is the single most important architectural constraint. Failure to do so results in a frozen UI with no recovery path. The `openrouter` Python SDK (v0.7.11) is the right choice over the `openai` SDK for this project because it exposes OpenRouter-specific fields (thinking blocks, provider routing, native token counts).

The key risks are all Phase 1 concerns: event loop blocking, thread safety violations in workers, Markdown re-render jitter during streaming, and SQLite write contention from concurrent workers. All 10 documented pitfalls map to Phase 1 — meaning the foundation must be built correctly or retrofitting is expensive. The good news: every pitfall has a clear, well-documented prevention strategy. This project has unusually high implementation predictability for its scope.

---

## Key Findings

### Recommended Stack

The stack is deliberately lean: Python 3.12 + Textual 8.1.1 + `openrouter` SDK 0.7.11 + `sqlite3` stdlib. No ORM, no async database adapter for the single-user use case (the stdlib `sqlite3` is sufficient with WAL mode enabled). The `openrouter` SDK is pinned at a specific version because it is in beta and may have breaking changes between minors. `httpx` is a transitive dependency but should be declared explicitly if used directly for model-list fetching.

Testing is first-class: `pytest-asyncio` with `asyncio_mode = "auto"` and `pytest-textual-snapshot` for visual regression. These must be configured before writing the first test or async tests will silently pass without running. Dev tooling (`ruff`, `ty`) is already decided — no additions needed.

**Core technologies:**
- **Python 3.12**: Language runtime — improved asyncio, stdlib `tomllib`, better error messages
- **Textual 8.1.1**: TUI framework — native asyncio, built-in `Markdown` widget, `CommandPalette`, CSS-like layout
- **`openrouter` SDK 0.7.11**: LLM API client — type-safe, async, handles SSE framing and thinking blocks; **pin version** (beta SDK)
- **`httpx` 0.28.1**: HTTP client — transitive dep of `openrouter`; use directly for `/models` endpoint if needed
- **`sqlite3` (stdlib)**: Session/message persistence — zero deps, ACID-compliant, debuggable with any SQLite browser; enable WAL mode immediately
- **`python-dotenv` 1.2.2**: `.env` loading — load at module import time, before `App.__init__` runs
- **`pytest` 9.0.2 + `pytest-asyncio` 1.3.0 + `pytest-textual-snapshot` 1.1.0**: Testing — set `asyncio_mode = "auto"` from day one
- **`ruff` 0.15.7 + `ty` 0.0.25**: Linting/typing — already decided; don't add mypy or black

**What NOT to use:** `requests` (sync, blocks event loop), `aiohttp` (heavier than httpx), `SQLAlchemy` (overkill for two-table schema), `MarkdownViewer` widget (TOC sidebar is wrong for chat), `rich` directly (use Textual's built-in widgets instead).

### Expected Features

The competitive landscape is clear: no CLI LLM tool currently combines a full-screen TUI, command palette as primary hub, and dynamic OpenRouter model list with favorites. remmeh has an unoccupied niche.

**Must have (table stakes) — v1:**
- Streamed responses rendered token-by-token — non-streaming feels broken
- Markdown + syntax-highlighted code block rendering — raw `**bold**` is unusable
- Multi-line input panel (3 lines, Enter=submit, Shift+Enter=newline)
- OpenRouter model selection via command palette — dynamically fetched, default persisted
- Persistent sessions in SQLite — start new, resume existing, navigate via sidebar
- Slide-in session sidebar (right panel, toggle with keybind)
- Command palette (Ctrl+P) — all actions discoverable from one place
- Favorite / default model marking — essential for a 400+ item model list
- Thinking block storage and rendering — Claude 3.7+ extended thinking
- Error display inline in chat thread — API errors, rate limits, timeouts must not crash

**Should have (competitive differentiators) — v1.x:**
- Session folder organization (tree structure) — unique in this tool category
- Session search / fuzzy filter — essential at 20+ sessions
- Token / cost indicator in status bar — OpenRouter usage data
- Configurable hotkeys — conflicts with tmux/vim are guaranteed to be reported

**Defer (v2+):**
- Web search / page fetching (Phase 2 per PROJECT.md)
- Custom agent personalities / @-mentions (Phase 3)
- Conversation branching / comparison (Phase 4)
- Image / file attachments — multimodal UX is complex, OpenRouter support inconsistent
- Plugin system — needs stable v1 API contracts first

**Anti-features to avoid building at all:** cloud sync, multi-user/auth, in-app settings form (use config file + `$EDITOR`), voice input, real-time conversation sharing.

### Architecture Approach

The architecture is a clean 3-tier design: **UI layer** (Textual widgets/screens, zero business logic) → **Service layer** (pure Python, no Textual imports, fully testable) → **Integration + Storage layer** (OpenRouter httpx client + SQLite). Workers bridge the UI and service layers for all async I/O. The build order strictly follows this dependency graph: Storage → Integration → Services → App scaffold → Widgets → Chat flow → Sidebar → Command Palette providers.

**Major components:**
1. **`RemmehApp`** — App lifecycle, keybindings, SCREENS registry, reactive state (`active_model`, `is_streaming`)
2. **`ChatScreen`** — Primary layout; composes `ChatView` + `InputPanel`; handles submit→stream flow
3. **`ChatView`** — `VerticalScroll` container holding `MessageWidget`s; owns the `@work(exclusive=True)` stream worker
4. **`MessageWidget`** — Renders a single message; uses `RichLog` during streaming, swaps to `Markdown` on completion
5. **`InputPanel`** — `TextArea` wrapper; posts `Submitted` message on Enter; consumes keys so app bindings don't fire while typing
6. **`SessionSidebar`** — CSS-docked right panel (`display: none/block` toggle via `toggle_class`); contains `SessionList` (`ListView`)
7. **`CommandPalette`** — Built-in Textual widget extended with `ModelSwitchProvider` and `SessionProvider` (async, fuzzy, dynamic)
8. **`ChatService` / `ModelService` / `SessionService`** — Pure Python business logic; no Textual imports; testable standalone
9. **`OpenRouterClient`** — `httpx.AsyncClient` wrapper; single shared client per app lifetime; streaming SSE with chunk-by-chunk parsing
10. **`LocalStorage`** — SQLite via `sqlite3` stdlib; WAL mode on; schema: `sessions` + `messages` tables; thinking blocks as JSON TEXT

**Key patterns:**
- `@work(exclusive=True)` for all streaming — cancels prior request automatically
- `reactive` attributes on `App` for shared UI state (model name, streaming indicator)
- Custom `Message` subclasses for widget-to-parent communication (no tight coupling)
- `RichLog` for streaming tokens → swap to `Markdown` on completion (avoids scroll-reset jitter)
- CSS `1fr` for `ChatView` height (not `height: auto` which collapses to 0)
- `exit_on_error=False` on all API workers (prevents app crash on transient errors)

### Critical Pitfalls

All 10 documented pitfalls map to Phase 1. Get these right before building anything else.

1. **Event loop blocking** — Never `await` a network call directly in a message handler. Always wrap in `@work(exclusive=True)`. Retrofit cost: HIGH (requires auditing every API call).

2. **Markdown re-render jitter during streaming** — `Markdown.update()` per chunk resets scroll and spikes CPU. Use `RichLog.write()` for in-progress streaming; render final `Markdown` once on completion. Retrofit cost: MEDIUM.

3. **Worker error crashes app** — Default `exit_on_error=True` means any 429 or network hiccup kills the TUI. Set `exit_on_error=False` on every `@work` decorator; handle `WorkerState.ERROR` to show inline error toast. Retrofit cost: LOW (easy fix, just must be done).

4. **SQLite concurrent write corruption** — Multiple workers writing to the same DB file without WAL mode produces `database is locked` errors. Enable `PRAGMA journal_mode=WAL` at startup; use a single shared connection. Retrofit cost: MEDIUM (requires migration).

5. **Silent async test failures** — Without `asyncio_mode = "auto"` in `pyproject.toml`, async tests silently never run (they appear to pass). Set this before writing the first test. Retrofit cost: LOW (config change, but previously "passing" tests will now fail — revealing real bugs).

6. **Hotkey conflicts with TextArea** — App-level bindings fire when focus is on the input widget. Design the binding table upfront; use `priority=True` only for quit-level bindings; route everything else through the command palette. Retrofit cost: MEDIUM (user-visible regressions, hard to test exhaustively).

---

## Implications for Roadmap

Based on combined research, the project maps naturally to 5 phases. All critical architectural decisions must be resolved in Phase 1 — the pitfalls research explicitly flags everything as "Phase 1 concern." Phases 2–4 are additive and relatively low-risk once the foundation is solid.

### Phase 1: Foundation & Core Chat Loop
**Rationale:** Every pitfall is a Phase 1 concern. Storage, async architecture, streaming display, test infrastructure, and keybinding design must all be correct before building features on top. The ARCHITECTURE.md build order (Storage → Integration → Services → App → Widgets) is the correct sequence within this phase.
**Delivers:** Working single-session LLM chat — send message, receive streamed markdown response, error handling — backed by SQLite with WAL mode, tested with `asyncio_mode = "auto"`.
**Addresses:** Streamed response, Markdown + code rendering, multi-line input, error display in chat thread, API key via env
**Avoids:** Event loop blocking, Markdown re-render jitter, worker crash, SQLite corruption, silent test failures, CSS layout collapse

### Phase 2: Model Selection & Sessions
**Rationale:** Once the core chat loop works, sessions and model switching are the next most valuable features. They share the same infrastructure (SQLite, command palette) and can be built together. Model list must be fetched in a background worker with a loading indicator — not at startup synchronously.
**Delivers:** Persistent multi-session chat with SQLite storage, dynamic OpenRouter model list via command palette (Ctrl+P), favorite/default model marking, slide-in session sidebar toggle.
**Addresses:** Persistent sessions, session navigation, model selection, configurable default model, favorite models
**Avoids:** Model list blocking startup (Pitfall 10), session load blocking UI

### Phase 3: Thinking Blocks & Command Palette Polish
**Rationale:** Thinking block rendering requires a streaming parser that discriminates `thinking` vs `content` blocks — this is non-trivial and should wait until streaming architecture is stable. Command palette providers for model switching and session navigation depend on Phase 2 services being complete.
**Delivers:** Extended thinking display (Claude 3.7+, stored + collapsible), full command palette with model switching provider and session navigation provider, complete keybinding table documented in config.
**Addresses:** Thinking block storage and rendering, command palette (model switch, session navigate, new session), configurable hotkeys foundation
**Avoids:** Thinking blocks mixed into regular content, command palette providers querying incomplete services

### Phase 4: Session Organization & Discovery
**Rationale:** Session folders and search require flat session list to be working and stable (Phase 2). Folder tree widget is complex enough to deserve its own phase. This phase also adds the cost/token indicator which depends on confirmed OpenRouter usage data availability.
**Delivers:** Session folder tree (create/rename/delete), fuzzy session search/filter, token/cost indicator in status bar, Markdown session export.
**Addresses:** Session folder organization, session search, token/cost indicator, Markdown export
**Uses:** Textual `Tree` widget for folder structure; SQLite FTS5 extension for content search

### Phase 5: Extended Capabilities (v2+)
**Rationale:** Phase 2+ items from FEATURES.md that require stable v1 to validate necessity. Web search requires complex HTTP + content parsing. Image attachments require multimodal UX design. These should not be committed to until Phase 1–4 are shipped and feedback is collected.
**Delivers:** Web search / page fetching integration (PROJECT.md Phase 2), custom agent personalities / @-mentions (PROJECT.md Phase 3), conversation branching (PROJECT.md Phase 4).
**Defers:** Plugin system (needs stable v1 API), voice input (platform-specific, heavy deps), real-time sharing (requires server infra)

### Phase Ordering Rationale

- **Pitfall-first ordering:** All 10 documented pitfalls are Phase 1 concerns. Building Phase 2+ on a broken foundation is expensive to fix — retrofitting async workers costs HIGH, retrofitting storage costs MEDIUM.
- **Service layer before UI:** The ARCHITECTURE.md build order is explicit: Storage → Integration → Services → UI. This enables testing services without Textual, which dramatically speeds up iteration.
- **Streaming before sessions:** Getting streaming right (Pitfalls 1, 3, 8) is harder than persistence and must be validated first. A working single-session streaming chat is more valuable than a multi-session non-streaming one.
- **Model list deferred from Phase 1:** While model selection is table-stakes, the background-fetch pattern (Pitfall 10) adds complexity. Phase 1 can hardcode a default model; Phase 2 adds the dynamic list with proper loading states.
- **Thinking blocks in Phase 3:** Requires a streaming parser on top of the Phase 1 streaming architecture. Adding it too early creates parser complexity before the underlying stream is stable.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3 (Thinking blocks):** The streaming parser for discriminating `thinking` vs `content` chunks from OpenRouter's API is model-specific. Needs validation against Claude 3.7+ response format before implementation.
- **Phase 4 (Session search):** SQLite FTS5 extension availability and indexing strategy for chat history content needs verification for the target deployment environment.
- **Phase 5 (Web search):** OpenRouter's web search integration (if any) vs external search API needs scoping; content extraction from arbitrary URLs is a large surface.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Foundation):** All patterns are explicitly documented in official Textual + OpenRouter docs. Research is complete and HIGH confidence.
- **Phase 2 (Model selection + sessions):** SQLite schema is simple and well-understood. OpenRouter `/models` endpoint is documented. Textual `CommandPalette` `Provider` pattern is documented.
- **Phase 4 (Folders + search):** Textual `Tree` widget is documented. SQLite FTS5 is stdlib. Standard patterns apply.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All versions verified via PyPI JSON API; Textual APIs verified against official docs; OpenRouter SDK verified against PyPI and openrouter.ai docs |
| Features | HIGH | 5 competitors surveyed (130k, 42k, 11k, 9.6k, 2.6k stars); feature gaps verified by absence in competitor README/docs |
| Architecture | HIGH | All patterns sourced directly from official Textual documentation (workers, reactivity, screens, events, command palette) — no inference |
| Pitfalls | HIGH | All critical pitfalls verified against official Textual docs and OpenRouter API docs; confirmed against existing CONCERNS.md |

**Overall confidence:** HIGH

### Gaps to Address

- **`openrouter` SDK beta stability:** The SDK is in beta (`0.7.11`). If it introduces breaking changes before implementation, the fallback is raw `httpx` + SSE parsing (documented in OpenRouter's Python streaming docs). Pin the version and monitor for changelog updates.
- **Thinking block API response format:** PITFALLS.md notes OpenRouter returns thinking as a distinct field "in some models" — the exact JSON structure needs verification against a live Claude 3.7+ streaming response before writing the parser. Address during Phase 3 planning.
- **`aiosqlite` vs `sqlite3`:** ARCHITECTURE.md mentions `aiosqlite` in the storage layer but STACK.md recommends `sqlite3` stdlib. The resolution: use `sqlite3` stdlib with synchronous operations in a `@work(thread=True)` worker (or keep writes serial via a single async worker). If async DB access is needed, add `aiosqlite` at that point. Flag for Phase 1 storage implementation.
- **`ty` type checker maturity:** `ty==0.0.25` is very early stage. If it proves too immature, `mypy` remains the fallback despite not being the stated preference. Monitor during Phase 1.

---

## Sources

### Primary (HIGH confidence)
- **https://textual.textualize.io/widgets/markdown/** — `Markdown` widget API, `get_stream()`, `append()`
- **https://textual.textualize.io/guide/workers/** — `@work` decorator, `exclusive=True`, thread safety, `call_from_thread()`
- **https://textual.textualize.io/guide/testing/** — `run_test()`, `pytest-asyncio`, `pytest-textual-snapshot`, `asyncio_mode = "auto"`
- **https://textual.textualize.io/guide/reactivity/** — `reactive` attributes, `watch_*` methods, `var`
- **https://textual.textualize.io/guide/screens/** — Screen stack, `ModalScreen`, `push_screen()` with callbacks
- **https://textual.textualize.io/guide/events/** — Custom `Message` subclasses, bubbling, `post_message()`
- **https://textual.textualize.io/guide/command_palette/** — `Provider` subclass, `startup/search/discover`, `DiscoveryHit`
- **https://openrouter.ai/docs/api/reference/streaming.mdx** — SSE format, `[DONE]` sentinel, keepalive comments, mid-stream errors
- **https://openrouter.ai/docs/sdks/python/overview.mdx** — Official Python SDK async API, `send_async()`, streaming pattern
- **https://pypi.org/project/openrouter/** — Beta status, httpx/pydantic deps, Python 3.9+ requirement
- **PyPI JSON API** — version numbers for all packages (fetched 2026-03-26)

### Secondary (MEDIUM confidence — competitor analysis)
- **https://github.com/Aider-AI/aider** (42k stars) — feature list, streaming implementation, model support
- **https://github.com/simonw/llm** (11k stars) — SQLite session logging, plugin system, fragment system
- **https://github.com/sigoden/aichat** (9.6k stars) — REPL guide, session/role features, provider support
- **https://github.com/anomalyco/opencode** (130k stars) — TUI layout patterns, keyboard navigation, agent tab-switching
- **https://github.com/npiv/chatblade** (2.6k stars, archived) — session options, streaming, token counting

### Tertiary (internal context)
- **`.planning/PROJECT.md`** — stated requirements, phase structure, scope constraints
- **`.planning/codebase/CONCERNS.md`** — identified gaps: no async architecture, streaming not planned, no test infra, no WAL mode decision

---
*Research completed: 2026-03-26*
*Ready for roadmap: yes*
