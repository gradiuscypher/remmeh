# Stack Research

**Domain:** Python TUI LLM chat tool (Textual + OpenRouter)
**Researched:** 2026-03-26
**Confidence:** HIGH (all versions verified via PyPI JSON API; all Textual APIs verified via official docs)

---

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.12 | Language runtime | Already decided. 3.12 gives better asyncio, `tomllib` stdlib, improved error messages. Match `.python-version` exactly. |
| Textual | 8.1.1 | TUI framework | Already decided. Native async (asyncio), built-in `Markdown` widget, `CommandPalette`, CSS-like layout. The only mature Python TUI with these capabilities. |
| uv | 0.10.10 | Package manager / venv | Already decided. Fastest Python package manager; lockfile committed; used throughout project. |

### HTTP Client & LLM Integration

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| `openrouter` | 0.7.11 (pin) | Official OpenRouter Python SDK | Auto-generated from OpenRouter's OpenAPI spec; type-safe with Pydantic; async support via `send_async()`; streams via `async for event in stream`; wraps httpx under the hood. Beta but actively maintained by OpenRouter team. **Pin version** — beta SDK may have breaking changes. |
| `httpx` | 0.28.1 | HTTP client (transitive, also direct) | The `openrouter` SDK depends on httpx≥0.28.1. Use `httpx.AsyncClient` directly for the `/models` endpoint if the SDK doesn't expose it cleanly. Native async, full streaming via `aiter_lines()`. Already the de-facto standard for async HTTP in Python. |

> **Why `openrouter` SDK over raw `httpx`?** The SDK gives typed response objects, handles SSE framing and the `[DONE]` sentinel, and tracks the API spec automatically. For a greenfield project this is worth the beta risk. The alternative — `openai` SDK pointed at `https://openrouter.ai/api/v1` — works but loses OpenRouter-specific features (provider routing params, thinking block access, etc.).

> **Why not `openai` SDK?** The `openai` package (2.30.0) works with OpenRouter via `base_url` override, but is typed for OpenAI's API surface only. You'd lose type safety on OpenRouter-specific fields like `provider`, `reasoning`, and `usage.native_tokens_prompt`. The official `openrouter` SDK is the right choice for a project that uses OpenRouter as its primary integration.

### Environment / Config

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| `python-dotenv` | 1.2.2 | Load `.env` file into `os.environ` | Standard for local dev `.env` files. The project already has `.env` in `.gitignore`. One call at startup (`load_dotenv()`), then read `os.getenv("OPENROUTER_API_KEY")`. No runtime dependency on `.env` existing (useful for CI). |

### Local Storage

**Decision: SQLite via Python's `sqlite3` stdlib — no ORM needed.**

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| `sqlite3` | stdlib | Session/message persistence | Zero new dependencies. SQLite is embedded, portable, ACID-compliant, debuggable with any DB browser. Handles thinking blocks as JSON-serialized TEXT columns. Supports full-text search later (FTS5 extension is bundled). |

> **Why SQLite over JSON files?** JSON files per-session hit filesystem limits at scale, have no query capability (can't list sessions by date/model without reading all files), and offer no atomic writes. SQLite gives `ORDER BY`, `FULL TEXT SEARCH`, foreign keys, and crash safety with zero server dependency. The "debugging-friendly" concern from PROJECT.md is satisfied — any SQLite browser (DB Browser, Datasette) can inspect the file.

> **Why no ORM (SQLAlchemy, tortoise-orm, etc.)?** An ORM adds a significant dependency and async complexity that isn't justified for a single-user local tool with a simple schema (conversations → messages). Raw `sqlite3` with dataclasses is sufficient and keeps the stack lean.

### Testing

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| `pytest` | 9.0.2 | Test runner | The standard. Textual's official docs and `pytest-textual-snapshot` both assume pytest. |
| `pytest-asyncio` | 1.3.0 | Async test support | Required for testing Textual (which is async). Set `asyncio_mode = "auto"` in `pyproject.toml` to avoid decorating every test. Textual's docs explicitly recommend this plugin. |
| `pytest-textual-snapshot` | 1.1.0 | Visual regression testing | Official Textual snapshot plugin (maintained by Textualize). Captures SVG screenshots and diffs. Use for layout tests (sidebar visibility, markdown rendering). Requires `--snapshot-update` on first run. |

### Dev Tools (Already Decided)

| Tool | Version | Purpose | Notes |
|------|---------|---------|-------|
| `ruff` | 0.15.7 | Linting + formatting | Replaces flake8, isort, black. One tool. Set as dev dependency. |
| `ty` | 0.0.25 | Type checking | Explicitly chosen (not mypy). Very fast Rust-based checker. Dev dependency. |

---

## Installation

```bash
# Runtime dependencies
uv add textual openrouter python-dotenv

# Dev dependencies
uv add --dev ruff ty pytest pytest-asyncio pytest-textual-snapshot
```

> Note: `httpx` is a transitive dependency of `openrouter` (requires `>=0.28.1`), so it will be present without explicit declaration. If you use `httpx.AsyncClient` directly in app code (e.g., for streaming model lists), add it as an explicit runtime dep: `uv add httpx`.

---

## Streaming LLM Responses in Textual — How It Works

This is the most critical integration point. The correct pattern:

```python
from textual import work
from textual.widgets import Markdown
from openrouter import OpenRouter

class ChatView(Widget):

    @work(exclusive=True)
    async def stream_response(self, messages: list[dict]) -> None:
        """Run in Textual worker — keeps UI responsive."""
        markdown_widget = self.query_one("#response", Markdown)
        stream = Markdown.get_stream(markdown_widget)  # Textual's streaming helper

        async with OpenRouter(api_key=os.getenv("OPENROUTER_API_KEY")) as client:
            response = await client.chat.send_async(
                model=self.current_model,
                messages=messages,
                stream=True,
            )
            try:
                async for chunk in response:
                    content = chunk.choices[0].delta.content if chunk.choices else None
                    if content:
                        await stream.write(content)
            finally:
                await stream.stop()
```

**Key facts verified from official docs:**
- `Markdown.get_stream()` is Textual's built-in streaming API — it rate-limits DOM updates to avoid exceeding ~20 appends/sec (documented in Textual 8.x docs)
- `@work(exclusive=True)` cancels any previous stream worker before starting a new one — correct for a chat tool where the user can abort
- `Markdown.append()` is the low-level alternative if `get_stream()` isn't available; `get_stream()` is preferred as it coalesces rapid updates
- OpenRouter SSE sends `: OPENROUTER PROCESSING` keepalive comments — the `openrouter` SDK handles these transparently
- Mid-stream errors come as SSE data events with `finish_reason: "error"` — check `chunk.choices[0].finish_reason` in the loop

---

## Markdown Rendering in Textual

Textual's built-in `Markdown` widget (since v0.11.0) handles:
- Typography (bold, italic, inline code)
- Headers (h1-h6)
- Lists (ordered and unordered)
- Tables
- Syntax-highlighted fenced code blocks
- Block quotes

**API:**
- `Markdown.update(str)` — replace entire content (use for completed messages)
- `Markdown.append(str)` — append fragment (use during streaming)
- `Markdown.get_stream(widget)` — returns `MarkdownStream` for rate-limited streaming
- `MarkdownViewer` — adds a TOC panel; don't use for chat (overkill, wrong UX)

**What it can't do (confirmed):** It does not render HTML embedded in Markdown. This is fine for LLM output.

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| `openrouter` SDK | `openai` SDK + base_url override | If you need OpenAI-specific tooling (evals, fine-tuning). Not applicable here. |
| `openrouter` SDK | Raw `httpx` + SSE parsing | If SDK proves too unstable (beta). Drop-in replacement: just copy the SSE parsing pattern from OpenRouter's Python streaming docs. |
| `sqlite3` stdlib | JSON files per session | If you need zero-schema portability / human-readable exports. Could add JSON export as a feature later without changing storage. |
| `sqlite3` stdlib | SQLAlchemy async | If the app grows to need complex queries, multiple concurrent writers, or migrations tooling. Overkill for a single-user local tool. |
| `pytest-textual-snapshot` | Manual testing only | For a tiny project with no layout complexity. Not recommended — snapshot tests catch regressions in the sidebar slide animation, markdown rendering, etc. |
| `pytest-asyncio` | `anyio` pytest plugin | If the project ever switches to Trio. Textual uses asyncio; stick with `pytest-asyncio`. |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `requests` | Synchronous — blocks the Textual event loop. The SSE example in OpenRouter's streaming docs uses `requests`, but it requires threading to avoid UI lock. | `openrouter` SDK (async) or `httpx.AsyncClient` |
| `aiohttp` | Heavier than httpx, different API style, no sync/async parity. The ecosystem has converged on httpx. | `httpx.AsyncClient` |
| `mypy` | Project explicitly chose `ty` (README + PROJECT.md). Don't add mypy. | `ty` |
| `black` / `isort` / `flake8` | Superseded by `ruff` which is already in toolchain. | `ruff` |
| `rich` directly | Rich is a transitive dependency of Textual. Use Textual's `Markdown` widget and `RichLog` instead of constructing Rich renderables directly. | `textual.widgets.Markdown`, `textual.widgets.RichLog` |
| `tortoise-orm` / `SQLAlchemy` | ORM complexity not justified for a single-user tool with a simple two-table schema (sessions + messages). | `sqlite3` stdlib |
| `MarkdownViewer` widget | Includes a TOC sidebar — wrong for chat, adds noise. | `Markdown` widget directly |

---

## Stack Patterns by Variant

**For the streaming worker pattern:**
- Use `@work(exclusive=True)` so sending a new message automatically cancels any in-progress stream
- Use `container.anchor()` on the scroll container before streaming starts — this locks scroll to the bottom as new content is added (documented Textual pattern)
- Use `Markdown.get_stream()` not bare `Markdown.append()` calls in a tight loop — `append()` at >20/sec causes UI lag

**For the SQLite schema:**
- Store message `content` as TEXT (full Markdown string)
- Store `thinking_blocks` as TEXT (JSON-serialized list) — OpenRouter returns thinking as a separate field
- Store `model_id` as TEXT on both sessions and messages (model can change mid-session in theory)
- Use `INTEGER` timestamps (Unix epoch), not ISO strings — easier to sort and range-query

**For testing Textual apps:**
- Use `async with app.run_test() as pilot:` for interaction tests (key presses, clicks)
- Use `snap_compare` fixture for layout/visual regression tests
- Set `asyncio_mode = "auto"` in `pytest.ini` or `pyproject.toml` `[tool.pytest.ini_options]` — avoids adding `@pytest.mark.asyncio` to every test

---

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| `textual==8.1.1` | `rich>=14.0.0` (transitive) | Textual pins its own rich version. Don't add rich separately. |
| `openrouter==0.7.11` | `httpx>=0.28.1`, `pydantic>=2.11.2` | Pin `openrouter` — beta SDK, breaking changes possible between minors |
| `pytest-textual-snapshot==1.1.0` | `textual>=0.28.0`, `pytest>=8.0.0` | Requires Textual 0.28+ (well below 8.x); requires pytest 8+ |
| `pytest-asyncio==1.3.0` | Python 3.9+ | Compatible with Python 3.12 ✓ |
| `ty==0.0.25` | Python 3.12 | Very early version; API may change. Pin it. |

---

## Sources

- **PyPI JSON API** — version numbers for all packages (fetched 2026-03-26, HIGH confidence)
- **https://textual.textualize.io/widgets/markdown/** — `Markdown` widget API, `get_stream()`, `append()` (HIGH confidence)
- **https://textual.textualize.io/guide/workers/** — `@work` decorator, `exclusive=True`, httpx async pattern (HIGH confidence)
- **https://textual.textualize.io/guide/testing/** — `run_test()`, `pytest-asyncio`, `pytest-textual-snapshot` (HIGH confidence)
- **https://openrouter.ai/docs/api/reference/streaming.mdx** — SSE format, `[DONE]` sentinel, keepalive comments, mid-stream errors (HIGH confidence)
- **https://openrouter.ai/docs/sdks/python/overview.mdx** — Official Python SDK async API, `send_async()`, streaming pattern (HIGH confidence)
- **https://www.python-httpx.org/async/** — `AsyncClient.stream()`, `aiter_lines()` (HIGH confidence)
- **https://pypi.org/project/openrouter/** — Beta status warning, httpx/pydantic deps, Python 3.9+ requirement (HIGH confidence)

---

*Stack research for: Python TUI LLM chat tool (remmeh)*
*Researched: 2026-03-26*
