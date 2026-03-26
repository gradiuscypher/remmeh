"""Shared pytest fixtures for remmeh test suite."""

from __future__ import annotations

import pytest


@pytest.fixture
def api_key(monkeypatch: pytest.MonkeyPatch) -> str:
    """Inject a fake OpenRouter API key for tests."""
    key = "sk-or-test-fake-key-12345"
    monkeypatch.setenv("OPENROUTER_API_KEY", key)
    return key


@pytest.fixture
def temp_db_path(tmp_path):
    """Provide a temporary SQLite database path."""
    return tmp_path / "remmeh_test.db"
