"""App configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_MODEL = "anthropic/claude-3.5-sonnet"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_DB_PATH = str(Path.home() / ".local" / "share" / "remmeh" / "sessions.db")


@dataclass
class AppConfig:
    """Application configuration."""

    api_key: str
    model: str
    db_path: str


def load_config() -> AppConfig:
    """Load config from environment. Raises ValueError if OPENROUTER_API_KEY is missing."""
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY not set. Add it to .env or set the environment variable."
        )
    return AppConfig(
        api_key=api_key,
        model=os.environ.get("REMMEH_DEFAULT_MODEL", DEFAULT_MODEL),
        db_path=os.environ.get("REMMEH_DB_PATH", DEFAULT_DB_PATH),
    )
