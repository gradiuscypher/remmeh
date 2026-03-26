# Coding Conventions

**Analysis Date:** 2026-03-26

## Project Status

This project is in initial scaffolding stage. Only `main.py` exists with a stub `main()` function. The README specifies the intended toolchain: **Python 3.12, uv, ruff, ty (type checker), Textual (TUI framework)**. Conventions below reflect the intended stack and should be enforced as code is added.

## Naming Patterns

**Files:**
- Use `snake_case` for all Python files (e.g., `chat_session.py`, `model_selector.py`)
- Test files: `test_<module>.py` or `<module>_test.py` in a `tests/` directory

**Functions:**
- Use `snake_case` (per PEP 8): `def send_message()`, `def fetch_models()`
- Private/internal functions: prefix with single underscore `_helper_fn()`

**Variables:**
- Use `snake_case` for local variables and module-level names
- Constants: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_MODEL`, `MAX_RETRIES`)

**Types/Classes:**
- Use `PascalCase` for classes: `ChatSession`, `ModelSelector`, `CommandPalette`
- Textual widgets follow Textual conventions (subclass `Widget`, `Screen`, `App`)

**Modules/Packages:**
- Use `snake_case` for package and module names

## Code Style

**Formatter:**
- **ruff format** (specified in README) — will replace black/isort
- Expected settings: line length 88–120, double quotes

**Linter:**
- **ruff** (specified in README) — replaces flake8/pylint
- Run: `uv run ruff check .`
- Auto-fix: `uv run ruff check --fix .`

**Type Checker:**
- **ty** (specified in README) — Astral's new type checker
- Run: `uv run ty check`
- Type annotations are expected on all function signatures

**Config location:**
- All tool config should live in `pyproject.toml` under `[tool.ruff]`, `[tool.ruff.format]`, `[tool.ty]`

> **Note:** No `pyproject.toml` tool sections exist yet. Add them before writing production code.

## Type Annotations

**All public functions must have type annotations:**
```python
def fetch_models(endpoint: str, api_key: str) -> list[Model]:
    ...

def send_message(session: ChatSession, content: str) -> Message:
    ...
```

**Use modern Python 3.12 union syntax:**
```python
def get_model(id: str) -> Model | None:   # NOT Optional[Model]
    ...
```

**Use built-in generics (Python 3.12+):**
```python
def get_history() -> list[Message]:       # NOT List[Message]
    ...
```

## Import Organization

**Order (enforced by ruff isort):**
1. Standard library imports
2. Third-party imports (textual, httpx, etc.)
3. Local application imports

**Example:**
```python
from __future__ import annotations

import json
from pathlib import Path

import httpx
from textual.app import App, ComposeResult
from textual.widgets import Input, RichLog

from remmeh.models import ChatSession, Message
```

**Path Aliases:**
- Not detected / not yet configured
- Use absolute package imports from project root (`from remmeh.services.openrouter import ...`)

## Error Handling

**Strategy:** Explicit exception handling with typed exceptions.

**Patterns to use:**
```python
# Raise specific exception types
class RemmehError(Exception): ...
class ModelFetchError(RemmehError): ...

# Catch specific exceptions, not bare except
try:
    response = await client.get(url)
    response.raise_for_status()
except httpx.HTTPStatusError as e:
    log.error(f"API error: {e.response.status_code}")
    raise ModelFetchError("Failed to fetch models") from e
```

**Never use:**
- Bare `except:` or `except Exception:` without re-raising or logging
- Swallowing exceptions silently

## Logging

**Framework:** Python `logging` module or Textual's built-in logging
- Textual apps use `self.log(...)` within widget/app context
- Use standard `logging.getLogger(__name__)` for non-UI code

**Patterns:**
- Log at appropriate levels: `debug` for trace, `info` for lifecycle, `warning` for recoverable issues, `error` for failures
- Include context in log messages: `log.debug(f"Fetching models from {endpoint}")`
- All messages including thinking blocks stored locally for debugging (per README)

## Comments

**When to Comment:**
- Public module, class, and function docstrings required
- Inline comments only for non-obvious logic
- No commented-out code in commits

**Docstrings:**
```python
def fetch_models(endpoint: str) -> list[Model]:
    """Fetch available models from the OpenRouter API.

    Args:
        endpoint: The OpenRouter base URL.

    Returns:
        List of available Model objects.

    Raises:
        ModelFetchError: If the API request fails.
    """
```

## Function Design

**Size:** Functions should do one thing; keep under ~30 lines where practical
**Parameters:** Prefer keyword arguments for functions with >2 params; use dataclasses/TypedDict for complex config
**Return Values:** Always annotate; prefer returning typed objects over raw dicts
**Async:** Use `async def` for all I/O operations (HTTP, file, Textual message handlers)

## Module Design

**Exports:** Explicit `__all__` in public module APIs
**Structure (planned):**
```
remmeh/
├── __init__.py
├── app.py              # Textual App entry point
├── models/             # Data models (ChatSession, Message, etc.)
├── services/           # External integrations (OpenRouter, storage)
├── widgets/            # Textual custom widgets
└── config.py           # App configuration
```

**Barrel Files:** Use sparingly; only at package boundaries for clean public APIs

## Textual-Specific Conventions

- Subclass `textual.app.App` for the root application
- Subclass `textual.widget.Widget` or `textual.screen.Screen` for UI components
- Use `compose()` method (not `__init__`) to build widget trees
- Use `on_<event>` naming for Textual message handlers: `on_button_pressed`
- CSS in `.tcss` files co-located with their screen/widget modules

---

*Convention analysis: 2026-03-26 — Project is pre-implementation. Conventions reflect intended stack from README.*
