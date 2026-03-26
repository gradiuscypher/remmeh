---
phase: 01-foundation-core-chat
plan: "01"
subsystem: scaffold
tags: [bootstrap, dependencies, tooling, package-structure]
dependency_graph:
  requires: []
  provides:
    - remmeh package importable
    - uv.lock fully resolved
    - ruff linting configured
    - ty type checking configured
    - pytest test discovery configured
    - entry point script registered
  affects:
    - all subsequent plans (depend on this scaffold)
tech_stack:
  added:
    - textual>=1.0
    - httpx[http2]>=0.27
    - python-dotenv>=1.0
    - aiosqlite>=0.20
    - ruff>=0.4 (dev)
    - ty>=0.0.25 (dev)
    - pytest>=8.0 (dev)
    - pytest-asyncio>=0.24 (dev)
    - pytest-mock>=3.14 (dev)
  patterns:
    - uv package mode (tool.uv.package=true) for editable install with entry points
    - load_dotenv() at module import time before App.__init__
key_files:
  created:
    - pyproject.toml (rewritten with all deps, tooling config, entry point script)
    - uv.lock (431 lines, 31 resolved packages)
    - remmeh/__init__.py
    - remmeh/main.py
    - remmeh/ui/__init__.py
    - remmeh/ui/app.py
    - tests/__init__.py
    - tests/conftest.py
    - .env.example
  modified:
    - main.py (stub → delegates to remmeh.main:main)
decisions:
  - "Used tool.uv.package=true instead of hatchling build-system — simpler, avoids hatchling needing the package dir to exist before Task 2"
  - "Created stub remmeh/ui/app.py with minimal RemmehApp — required for entry point to not crash on import"
  - "Did NOT add openrouter SDK — plan explicitly excludes it; raw httpx will handle OpenRouter HTTP calls"
metrics:
  duration_seconds: 173
  completed_date: "2026-03-26"
  tasks_completed: 2
  files_created: 9
  files_modified: 2
---

# Phase 01 Plan 01: Project Scaffold Summary

**One-liner:** Full Python package scaffold with textual/httpx/aiosqlite/dotenv deps, ruff/ty/pytest tooling, and uv.lock resolved from empty stub.

## What Was Built

Bootstrapped the `remmeh` project from a 7-line stub `pyproject.toml` and a `print("Hello from remmeh!")` entry point into a real, installable Python package:

- **`pyproject.toml`** — complete with runtime deps, dev deps, `[project.scripts]`, ruff/ty/pytest config, and `tool.uv.package=true` for entry point registration
- **`uv.lock`** — fully resolved lockfile with 31 packages pinned
- **`remmeh/`** package — `__init__.py`, `main.py` (with `load_dotenv()` at import time), `ui/__init__.py`, `ui/app.py` (stub `RemmehApp`)
- **`tests/`** — `__init__.py` + `conftest.py` with `api_key` and `temp_db_path` fixtures
- **`.env.example`** — documents `OPENROUTER_API_KEY` env var

## Verification Results

```
uv sync                          ✓  31 packages resolved, 0 conflicts
python -c "import remmeh"        ✓  package importable
ruff check .                     ✓  All checks passed
ruff format --check .            ✓  7 files already formatted
ty check                         ✓  All checks passed
pytest --collect-only -q         ✓  no tests collected (expected — 0 test files yet)
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added stub remmeh/ui/app.py to prevent entry-point crash**
- **Found during:** Task 2 implementation
- **Issue:** `remmeh/main.py` imports `from remmeh.ui.app import RemmehApp` — this module didn't exist, so `uv run remmeh` would crash with `ModuleNotFoundError`. The must_haves require `uv run remmeh` to "launch without crashing".
- **Fix:** Created `remmeh/ui/__init__.py` and `remmeh/ui/app.py` with a minimal `RemmehApp(App)` subclass that renders a placeholder label. This will be replaced in a later plan (UI implementation).
- **Files modified:** `remmeh/ui/__init__.py`, `remmeh/ui/app.py`
- **Commit:** 6b85d8d

**2. [Rule 1 - Bug] Used tool.uv.package=true instead of hatchling build-system**
- **Found during:** Task 1 verification
- **Issue:** Adding `[build-system]` with hatchling failed (`Unable to determine which files to ship`) because the `remmeh/` package dir doesn't exist at Task 1 time.
- **Fix:** Used `[tool.uv]` `package = true` instead — achieves the same goal (entry point script registration) without requiring a build backend.
- **Files modified:** `pyproject.toml`
- **Commit:** 9896f19

## Known Stubs

| File | Stub | Reason |
|------|------|--------|
| `remmeh/ui/app.py` | `RemmehApp` renders placeholder label | Entry point scaffold only — real UI implemented in plan 01-04 (UI scaffold) |

## Self-Check: PASSED
