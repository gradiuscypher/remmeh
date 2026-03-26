<!-- GSD:project-start source:PROJECT.md -->
## Project

**remmeh**

remmeh is a personal TUI LLM chat tool built around a keyboard-first experience. It integrates with OpenRouter to provide access to multiple LLMs in a single terminal application, with persistent local session history, full Markdown rendering, and a command palette that serves as the hub for all actions.

**Core Value:** A keyboard-driven TUI where everything — model switching, session management, settings — is accessible without touching the mouse.

### Constraints

- **Tech stack**: Python 3.12 + Textual — already decided, no alternatives
- **Package manager**: uv — already in use, lockfile committed
- **Storage**: Local filesystem only — no server, no cloud
- **Type checking**: ty (not mypy) — explicitly chosen in README
- **Linting**: ruff — already in toolchain
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Languages
- Python 3.12 - All application code (enforced via `.python-version` and `pyproject.toml requires-python = ">=3.12"`)
## Runtime
- CPython 3.12.3 (as configured in `.venv/pyvenv.cfg`)
- `uv` 0.10.10 - Dependency management and virtual environment
- Lockfile: `uv.lock` present and committed
## Frameworks
- Textual - TUI (terminal user interface) framework for all UI layout and interaction
- Not yet configured - README states "well-designed test coverage" is a Phase 1 requirement
- pytest is the conventional choice for Python projects of this type
- `ruff` - Linting and formatting (listed explicitly in README Phase 1 stack)
- `ty` - Type checking (listed explicitly in README Phase 1 stack)
## Key Dependencies
- None — `pyproject.toml` has `dependencies = []` and `uv.lock` contains only the root package
- `textual` - TUI framework for all UI components
- `ruff` - Linter/formatter (dev dependency)
- `ty` - Type checker (dev dependency)
- HTTP client library (e.g., `httpx`) for OpenRouter API calls and web fetching
- Web content fetching utilities
## Configuration
- `.env` file path listed in `.gitignore` — environment variables (e.g., API keys) will go here
- No environment configuration is currently implemented
- OpenRouter API key will be required (see INTEGRATIONS.md)
- `pyproject.toml` — project metadata and dependency declarations
- `uv.lock` — pinned dependency lockfile for reproducibility
## Platform Requirements
- Python 3.12+
- `uv` package manager (`pip install uv` or OS package)
- Virtual environment managed at `.venv/`
- Run entry point: `python main.py`
- Terminal-based application, no server deployment needed
- Local filesystem access required (chat history stored locally per README)
- OpenRouter API access required (internet connectivity)
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Project Status
## Naming Patterns
- Use `snake_case` for all Python files (e.g., `chat_session.py`, `model_selector.py`)
- Test files: `test_<module>.py` or `<module>_test.py` in a `tests/` directory
- Use `snake_case` (per PEP 8): `def send_message()`, `def fetch_models()`
- Private/internal functions: prefix with single underscore `_helper_fn()`
- Use `snake_case` for local variables and module-level names
- Constants: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_MODEL`, `MAX_RETRIES`)
- Use `PascalCase` for classes: `ChatSession`, `ModelSelector`, `CommandPalette`
- Textual widgets follow Textual conventions (subclass `Widget`, `Screen`, `App`)
- Use `snake_case` for package and module names
## Code Style
- **ruff format** (specified in README) — will replace black/isort
- Expected settings: line length 88–120, double quotes
- **ruff** (specified in README) — replaces flake8/pylint
- Run: `uv run ruff check .`
- Auto-fix: `uv run ruff check --fix .`
- **ty** (specified in README) — Astral's new type checker
- Run: `uv run ty check`
- Type annotations are expected on all function signatures
- All tool config should live in `pyproject.toml` under `[tool.ruff]`, `[tool.ruff.format]`, `[tool.ty]`
## Type Annotations
## Import Organization
- Not detected / not yet configured
- Use absolute package imports from project root (`from remmeh.services.openrouter import ...`)
## Error Handling
- Bare `except:` or `except Exception:` without re-raising or logging
- Swallowing exceptions silently
## Logging
- Textual apps use `self.log(...)` within widget/app context
- Use standard `logging.getLogger(__name__)` for non-UI code
- Log at appropriate levels: `debug` for trace, `info` for lifecycle, `warning` for recoverable issues, `error` for failures
- Include context in log messages: `log.debug(f"Fetching models from {endpoint}")`
- All messages including thinking blocks stored locally for debugging (per README)
## Comments
- Public module, class, and function docstrings required
- Inline comments only for non-obvious logic
- No commented-out code in commits
## Function Design
## Module Design
## Textual-Specific Conventions
- Subclass `textual.app.App` for the root application
- Subclass `textual.widget.Widget` or `textual.screen.Screen` for UI components
- Use `compose()` method (not `__init__`) to build widget trees
- Use `on_<event>` naming for Textual message handlers: `on_button_pressed`
- CSS in `.tcss` files co-located with their screen/widget modules
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## Pattern Overview
- Project is in initial scaffold state: one entry-point file (`main.py`) with a stub `main()` function
- No packages, modules, or layers exist yet
- README defines the intended product: a TUI (terminal UI) LLM chat and research tool using Textual
- All architectural decisions below are inferred from README intent and toolchain choices
## Intended Architecture (from README)
- **Textual** — Python TUI framework for the UI layer
- **OpenRouter** — LLM API provider, models fetched dynamically
- **Local storage** — Chat session history and message logs stored on disk
### Planned Layers (not yet implemented)
- Purpose: Render TUI screens, panels, and widgets using Textual
- Location: `src/remmeh/ui/` or `remmeh/ui/` (to be determined)
- Contains: Textual `App`, `Screen`, and `Widget` subclasses
- Depends on: Service layer, state/session management
- Purpose: Business logic — chat sessions, model management, message handling
- Location: `src/remmeh/services/` (to be determined)
- Contains: Session manager, model fetcher, message router
- Depends on: Integration layer (OpenRouter API)
- Purpose: External API calls to OpenRouter, web fetching (Phase 2)
- Location: `src/remmeh/integrations/` (to be determined)
- Contains: OpenRouter HTTP client, model list fetcher
- Purpose: Persist chat history, sessions, and thinking blocks locally
- Location: `src/remmeh/storage/` (to be determined)
- Contains: Session serialization, local file/DB reads and writes
## Current State
- Location: `main.py`
- Current behavior: prints `"Hello from remmeh!"` — stub only
- Invoked via: `python main.py` or `uv run main.py`
## Data Flow (Intended)
- Sessions are organized in folders locally
- Right-side panel slides in/out to show session list
- Model list is fetched dynamically from OpenRouter
- Models can be marked as default or favorited
- Selection available via command palette and hotkeys
## Key Abstractions (Planned)
- Purpose: Represents a conversation with history, model, and metadata
- Examples: To be implemented in service/storage layer
- Purpose: A single unit of chat (user or assistant), including thinking blocks
- Stored locally in full for debugging
- Purpose: Represents an LLM model available via OpenRouter
- Includes default/favorited status
- Purpose: Unified interface for all app functionality
- Expected to be a Textual overlay widget
## Error Handling
- Expected to use Python exceptions with Textual's error handling conventions
## Cross-Cutting Concerns
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
