---
phase: 01-foundation-core-chat
plan: "03"
subsystem: api
tags: [openrouter, httpx, streaming, sse, error-handling, config, tdd]
dependency_graph:
  requires:
    - remmeh package importable (01-01)
    - httpx[http2] installed (01-01)
  provides:
    - remmeh.config.AppConfig
    - remmeh.config.load_config
    - remmeh.api.OpenRouterClient with stream_chat() async generator
    - remmeh.api.OpenRouterError / RateLimitError / TimeoutError / NetworkError
    - Full SSE streaming with typed error classification
  affects:
    - Plan 05 (chat service uses OpenRouterClient)
    - Plan 04 (UI layer consumes stream tokens)
tech_stack:
  added:
    - httpx.AsyncClient with stream=True for SSE (already installed)
    - python-dotenv (already installed, load_config() reads env)
  patterns:
    - Async generator pattern for SSE streaming (async def ... yield)
    - Nested async with for httpx client + stream context (noqa SIM117)
    - TDD: RED test commit → GREEN implementation commit
    - Error hierarchy: typed exception subclasses with status_code attribute
key_files:
  created:
    - remmeh/config.py (AppConfig dataclass, load_config(), DEFAULT_MODEL constant)
    - remmeh/api/__init__.py (re-exports public API)
    - remmeh/api/openrouter.py (OpenRouterClient, error classes)
    - tests/test_openrouter.py (16 unit tests with mocked httpx)
  modified: []
decisions:
  - "Used nested async with (noqa SIM117) instead of combined form — inner context depends on outer's yielded value, which SIM117 doesn't understand"
  - "Suppressed SIM117 lint on outer `with` line — architecturally correct pattern for httpx streaming"
  - "Used AsyncGenerator mock pattern with MagicMock returning context manager chain — avoids AsyncMock return_value coroutine issues with aiter_lines"
metrics:
  duration_seconds: 270
  completed_date: "2026-03-26"
  tasks_completed: 2
  files_created: 4
  files_modified: 0
---

# Phase 01 Plan 03: OpenRouter API Client Summary

**One-liner:** Async SSE streaming OpenRouter client with typed error hierarchy (RateLimitError/TimeoutError/NetworkError), app config from env, and 16 unit tests with mocked httpx.

## What Was Built

### `remmeh/config.py`
- `AppConfig` dataclass: `api_key`, `model`, `db_path`
- `load_config()`: reads `OPENROUTER_API_KEY` from env, raises `ValueError` with actionable message if missing
- Constants: `DEFAULT_MODEL = "anthropic/claude-3.5-sonnet"`, `OPENROUTER_BASE_URL`, `DEFAULT_DB_PATH` (XDG pattern)
- Supports `REMMEH_DEFAULT_MODEL` and `REMMEH_DB_PATH` env overrides

### `remmeh/api/openrouter.py`
- `OpenRouterError(Exception)` — base error with `status_code: int | None`
- `RateLimitError(OpenRouterError)` — HTTP 429
- `TimeoutError(OpenRouterError)` — httpx.TimeoutException
- `NetworkError(OpenRouterError)` — httpx.ConnectError
- `OpenRouterClient.stream_chat(messages, model, timeout)` — async generator yielding string tokens
  - SSE parsing: `data: {json}` → extract `choices[0].delta.content`
  - Skips `data: [DONE]`, empty/None content, non-data SSE lines
  - Request headers: `Authorization: Bearer`, `HTTP-Referer`, `X-Title: remmeh`
  - Manual HTTP status check before streaming (avoids raise_for_status in stream context)

### `tests/test_openrouter.py`
16 unit tests covering:
- Happy path: token streaming, [DONE] skipping, empty delta skipping, non-data line filtering
- Error classification: 429→RateLimitError, 500→OpenRouterError, 401→OpenRouterError, TimeoutException→TimeoutError, ConnectError→NetworkError
- Error hierarchy: isinstance checks for all subclasses
- Request validation: correct headers and body structure sent

## Verification Results

```
uv run pytest tests/test_openrouter.py -v     ✓  16/16 tests passed
uv run ruff check remmeh/api/ remmeh/config.py ✓  All checks passed
uv run ty check remmeh/api/ remmeh/config.py   ✓  All checks passed
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Suppressed SIM117 lint rule for nested async with pattern**
- **Found during:** Task 2 verification (ruff check)
- **Issue:** ruff SIM117 suggested combining `async with httpx.AsyncClient(...) as http_client: async with http_client.stream(...) as response:` into a single `async with` statement. The combined form (`async with A, B(...) as x`) breaks here because the inner context manager (`http_client.stream(...)`) depends on the value yielded by the outer (`http_client`). Flattening severs this dependency.
- **Fix:** Reverted to nested `with` and added `# noqa: SIM117` on the outer statement with explanatory comment.
- **Files modified:** `remmeh/api/openrouter.py`
- **Commit:** e53b759

**2. [Rule 1 - Bug] Fixed async mock structure for httpx context manager chain**
- **Found during:** Task 2 TDD GREEN phase
- **Issue:** Initial tests used `AsyncMock(return_value=aiter_from_list(lines))` for `response.aiter_lines`, which made `aiter_lines` a coroutine (awaitable) rather than an async generator directly callable with `async for`. Also the mock chain needed to match `async with AsyncClient() as client: async with client.stream() as response`.
- **Fix:** Used `MagicMock` chain with explicit `__aenter__`/`__aexit__` `AsyncMock` at each level; `aiter_lines` set as a plain async generator function (not `AsyncMock`).
- **Files modified:** `tests/test_openrouter.py`
- **Commit:** e53b759

## Known Stubs

None — all exported symbols are fully implemented.

## Self-Check: PASSED
