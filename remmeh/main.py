"""Application entry point for remmeh."""

from __future__ import annotations

from dotenv import load_dotenv

# CRITICAL: load_dotenv() MUST run before App.__init__ — load at module import time
# so that os.environ is populated before Textual initializes (per pitfall #6 in CONCERNS.md)
load_dotenv()


def main() -> None:
    """Launch the remmeh TUI application."""
    # RemmehApp is imported here (after load_dotenv) to ensure env is ready
    from remmeh.ui.app import RemmehApp

    app = RemmehApp()
    app.run()
