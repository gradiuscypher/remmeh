---
phase: 01-foundation-core-chat
plan: "05"
subsystem: ui
tags: [streaming, chat-loop, message-widget, sqlite, error-handling]
dependency_graph:
  requires:
    - 01-02  # models.py, storage layer
    - 01-03  # OpenRouterClient, config
    - 01-04  # ChatView, InputPanel, StatusBar widgets
  provides:
    - MessageWidget with RichLog→Markdown streaming swap
    - ChatScreen with @work(exclusive=True) streaming worker
    - Full chat loop with SQLite persistence
    - Inline error handling for all API error types
  affects:
    - remmeh/ui/screens/chat.py
    - remmeh/ui/widgets/message_widget.py
    - remmeh/ui/widgets/__init__.py
tech_stack:
  added:
    - Textual @work decorator (exclusive=True, exit_on_error=False) for async streaming
    - RichLog.clear()+write() pattern for jitter-free token streaming
    - asyncio.CancelledError handling for Escape-key stream cancellation
  patterns:
    - Streaming swap: RichLog (during) → Markdown (complete) via call_after_refresh
    - Lazy config load with inline error reporting on missing API key
    - Background DB init worker (silent on config errors at startup)
key_files:
  created:
    - remmeh/ui/widgets/message_widget.py  # MessageWidget with streaming support
  modified:
    - remmeh/ui/screens/chat.py            # Full chat loop with @work worker
    - remmeh/ui/widgets/__init__.py        # Add MessageWidget export
decisions:
  - "Used RichLog.clear()+write(full_content) instead of write(chunk, end='') — end param not in Textual API; clear/rewrite avoids per-token line fragmentation without scroll jitter"
  - "MessageWidget merges role into CSS classes via __init__ (not overriding add_class) — simpler and compatible with Textual CSS selector pattern"
  - "DB init runs in background worker at mount (not blocking) — silent ValueError catch means missing API key doesn't prevent app launch"
  - "type: ignore[union-attr] on _client.stream_chat() — config validation guarantees non-None but ty can't flow-narrow past _get_config()"
metrics:
  duration_seconds: 267
  completed_date: "2026-03-26"
  tasks_completed: 2
  files_created: 1
  files_modified: 3
---

# Phase 01 Plan 05: Streaming Chat Loop — Summary

**One-liner:** Full streaming chat loop with `@work(exclusive=True)` LLM worker, `RichLog→Markdown` swap, and SQLite persistence for every exchange.

## What Was Built

This plan wires together all prior Phase 1 artifacts into a working streaming chat loop:

1. **`MessageWidget`** (`remmeh/ui/widgets/message_widget.py`) — renders user/assistant/error messages with streaming support. Assistant messages start in `RichLog` mode for token-by-token display; after completion, a `swap_to_markdown()` call replaces it with a rendered `Markdown` widget via `call_after_refresh`.

2. **`ChatScreen` streaming worker** (`remmeh/ui/screens/chat.py`) — `_submit_message()` is decorated with `@work(exclusive=True, exit_on_error=False)`. It:
   - Displays user message immediately
   - Appends to OpenRouter message history for multi-turn context
   - Saves user message to SQLite
   - Disables InputPanel + activates streaming state in StatusBar
   - Streams tokens to `MessageWidget.write_chunk()`
   - Handles all error types inline (no crashes)
   - Swaps RichLog → Markdown on success
   - Persists assistant response to SQLite
   - Re-enables InputPanel

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| `RichLog.clear()+write(full_content)` pattern | `end=` param not in Textual's `RichLog.write()` API; clear/rewrite avoids per-token line fragmentation with acceptable re-render cost |
| Role merged into CSS classes in `__init__` | Simpler than `add_class()`; works with Textual's CSS selector system |
| DB init as background worker (silent on ValueError) | Missing API key shouldn't prevent app launch; error surfaces on first message submit |
| `exit_on_error=False` on worker | Exceptions are handled inline; prevents unhandled exceptions from killing the TUI |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `RichLog.write()` has no `end=` parameter**
- **Found during:** Task 1 implementation
- **Issue:** Plan specified `self._rich_log.write(chunk, end="")` to concatenate tokens, but `RichLog.write()` signature is `(content, width, expand, shrink, scroll_end, animate)` — no `end` parameter
- **Fix:** Changed `write_chunk()` to use `clear() + write(full_content)` pattern — accumulate all tokens, rewrite RichLog with full content on each chunk. Same visual result, no fragmentation, no scroll jitter
- **Files modified:** `remmeh/ui/widgets/message_widget.py`
- **Commit:** 88abeb4

## Verification Results

```
uv run python -c "from remmeh.ui.app import RemmehApp; print('full app imports OK')"
# → full app imports OK

uv run ruff check remmeh/ui/
# → All checks passed!

uv run pytest tests/ -v
# → 54 passed, 87 warnings in 0.69s
```

## Known Stubs

None — all chat loop functionality is wired. The `MessageWidget`, streaming worker, error handling, and SQLite persistence are all active code paths (not stubs).

## Self-Check: PASSED
