# Testing Patterns

**Analysis Date:** 2026-03-26

## Project Status

No tests exist yet. The README specifies **"Well-designed test coverage"** as a Phase 1 requirement. The intended toolchain is Python 3.12 + uv. Testing framework is not yet configured in `pyproject.toml`.

## Recommended Test Framework

**Runner:** pytest
- Industry standard for Python; integrates with uv
- Config: `pyproject.toml` under `[tool.pytest.ini_options]`
- Install: add `pytest` to `[dependency-groups]` in `pyproject.toml`

**For Textual UI testing:** `pytest-textual-snapshot` or Textual's built-in `App.run_test()` context manager

**Async support:** `pytest-asyncio` (required for async Textual handlers and HTTP client code)

**Assertion Library:** pytest built-in `assert` statements

**Run Commands:**
```bash
uv run pytest                  # Run all tests
uv run pytest --tb=short       # Shorter tracebacks
uv run pytest -x               # Stop on first failure
uv run pytest --cov=remmeh     # Coverage (requires pytest-cov)
uv run pytest -k "test_chat"   # Filter by name
```

**Recommended `pyproject.toml` additions:**
```toml
[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "pytest-cov>=5.0",
    "pytest-textual-snapshot>=0.4",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

## Test File Organization

**Location:**
- Dedicated `tests/` directory at project root (separate from source)
- Mirror the source package structure inside `tests/`

**Naming:**
- Test files: `test_<module>.py` (e.g., `test_chat_session.py`, `test_openrouter.py`)
- Test functions: `test_<what_it_does>` (e.g., `test_fetch_models_returns_list`)
- Test classes: `Test<Subject>` (e.g., `TestChatSession`, `TestOpenRouterClient`)

**Planned structure:**
```
tests/
├── conftest.py               # Shared fixtures
├── test_chat_session.py      # Unit tests for ChatSession model
├── test_openrouter.py        # Unit tests for OpenRouter integration
├── test_storage.py           # Unit tests for local history storage
├── ui/
│   ├── test_app.py           # Textual app-level tests
│   └── test_widgets.py       # Widget snapshot/interaction tests
└── integration/
    └── test_openrouter_live.py  # Live API tests (skipped in CI by default)
```

## Test Structure

**Suite Organization:**
```python
# tests/test_chat_session.py
import pytest
from remmeh.models import ChatSession, Message


class TestChatSession:
    def test_new_session_has_empty_history(self):
        session = ChatSession(name="test")
        assert session.messages == []

    def test_add_message_appends_to_history(self):
        session = ChatSession(name="test")
        msg = Message(role="user", content="hello")
        session.add_message(msg)
        assert len(session.messages) == 1
        assert session.messages[0].content == "hello"

    def test_session_serializes_to_json(self):
        session = ChatSession(name="test")
        data = session.to_dict()
        assert "name" in data
        assert "messages" in data
```

**Patterns:**
- `conftest.py` for shared fixtures (sessions, mock clients, temp directories)
- `@pytest.fixture` for reusable test data
- Arrange-Act-Assert structure within each test function
- One assertion concept per test (not one `assert` statement — one logical concept)

## Mocking

**Framework:** `unittest.mock` (stdlib) + `pytest-mock` (for `mocker` fixture convenience)

**Install:**
```toml
[dependency-groups]
dev = ["pytest-mock>=3.14"]
```

**Patterns:**
```python
# Mocking HTTP calls (httpx)
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_fetch_models_success(mocker):
    mock_response = mocker.AsyncMock()
    mock_response.json.return_value = {"data": [{"id": "gpt-4o"}]}
    mock_response.raise_for_status = mocker.Mock()

    mocker.patch("httpx.AsyncClient.get", return_value=mock_response)

    from remmeh.services.openrouter import fetch_models
    models = await fetch_models(api_key="test-key")
    assert len(models) == 1
    assert models[0].id == "gpt-4o"


# Mocking file system
@pytest.fixture
def temp_storage(tmp_path):
    """Fixture providing a temporary storage directory."""
    return tmp_path / "sessions"


def test_save_session(temp_storage):
    from remmeh.services.storage import save_session
    session = ChatSession(name="test")
    save_session(session, storage_dir=temp_storage)
    assert (temp_storage / "test.json").exists()
```

**What to Mock:**
- External HTTP calls (OpenRouter API)
- File system operations in unit tests (use `tmp_path` fixture instead)
- Environment variables (`monkeypatch.setenv`)
- Time-dependent code (`datetime.now`)

**What NOT to Mock:**
- Internal business logic / data models
- Pure functions with no side effects
- In integration tests: the actual external service (use real calls, mark with `@pytest.mark.integration`)

## Fixtures and Factories

**Test Data:**
```python
# tests/conftest.py
import pytest
from remmeh.models import ChatSession, Message


@pytest.fixture
def sample_message() -> Message:
    return Message(role="user", content="Hello, world!")


@pytest.fixture
def sample_session(sample_message) -> ChatSession:
    session = ChatSession(name="test-session")
    session.add_message(sample_message)
    return session


@pytest.fixture
def api_key(monkeypatch) -> str:
    key = "sk-or-test-key-12345"
    monkeypatch.setenv("OPENROUTER_API_KEY", key)
    return key
```

**Location:**
- Shared fixtures: `tests/conftest.py`
- Module-specific fixtures: local `conftest.py` inside test subdirectories

## Textual UI Testing

**Approach:** Use Textual's `App.run_test()` async context manager:
```python
# tests/ui/test_app.py
import pytest
from remmeh.app import RemmehApp


@pytest.mark.asyncio
async def test_app_starts_with_input_focused():
    app = RemmehApp()
    async with app.run_test() as pilot:
        # pilot.app gives access to the live app
        assert app.focused is not None


@pytest.mark.asyncio
async def test_send_message_updates_chat_log():
    app = RemmehApp()
    async with app.run_test() as pilot:
        await pilot.click("#input")
        await pilot.type("Hello")
        await pilot.press("enter")
        # Assert message appears in log
        chat_log = app.query_one("#chat-log")
        assert "Hello" in chat_log.renderable
```

**Snapshot tests** for visual regression:
```python
async def test_app_snapshot(snap_compare):
    assert await snap_compare("remmeh/app.py")
```

## Coverage

**Requirements:** "Well-designed test coverage" per README — target 80%+ for business logic
**Exclude:** UI snapshot tests, integration tests, `__main__` blocks

**Coverage config in `pyproject.toml`:**
```toml
[tool.coverage.run]
source = ["remmeh"]
omit = ["tests/*", "remmeh/__main__.py"]

[tool.coverage.report]
fail_under = 80
show_missing = true
```

**View Coverage:**
```bash
uv run pytest --cov=remmeh --cov-report=term-missing
uv run pytest --cov=remmeh --cov-report=html   # HTML report in htmlcov/
```

## Test Types

**Unit Tests:**
- Scope: Individual functions, classes, data models in isolation
- Location: `tests/test_*.py`
- Mock all external I/O
- Should be fast (<1s total per module)

**Integration Tests:**
- Scope: Real HTTP calls to OpenRouter API; real file system
- Location: `tests/integration/`
- Marked with `@pytest.mark.integration`
- Skipped by default in CI: `pytest -m "not integration"`
- Require real API key in environment

**UI / Snapshot Tests:**
- Framework: Textual's `run_test()` + `pytest-textual-snapshot`
- Location: `tests/ui/`
- Test widget composition, focus behavior, keyboard navigation

## Common Patterns

**Async Testing:**
```python
import pytest

@pytest.mark.asyncio
async def test_async_fetch():
    result = await some_async_function()
    assert result is not None
```

**Error Testing:**
```python
def test_raises_on_invalid_model():
    with pytest.raises(ModelFetchError, match="invalid model"):
        fetch_model("nonexistent-model-id")
```

**Parametrized Tests:**
```python
@pytest.mark.parametrize("role,expected", [
    ("user", True),
    ("assistant", True),
    ("system", True),
    ("invalid", False),
])
def test_message_role_validation(role, expected):
    msg = Message(role=role, content="test")
    assert msg.is_valid_role() == expected
```

**Environment Variables:**
```python
def test_reads_api_key_from_env(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    client = OpenRouterClient()
    assert client.api_key == "test-key"
```

---

*Testing analysis: 2026-03-26 — No tests exist yet. Patterns reflect README requirements and Python 3.12 + uv + Textual stack.*
