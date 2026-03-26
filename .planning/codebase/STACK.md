# Technology Stack

**Analysis Date:** 2026-03-26

## Languages

**Primary:**
- Python 3.12 - All application code (enforced via `.python-version` and `pyproject.toml requires-python = ">=3.12"`)

## Runtime

**Environment:**
- CPython 3.12.3 (as configured in `.venv/pyvenv.cfg`)

**Package Manager:**
- `uv` 0.10.10 - Dependency management and virtual environment
- Lockfile: `uv.lock` present and committed

## Frameworks

**Core (planned per README):**
- Textual - TUI (terminal user interface) framework for all UI layout and interaction
  - Bottom input panel (3-line height with scroll)
  - Slide-in/out session list sidebar
  - Command palette for all configuration
  - Markdown formatting and coloring for chat messages

**Testing (planned per README):**
- Not yet configured - README states "well-designed test coverage" is a Phase 1 requirement
- pytest is the conventional choice for Python projects of this type

**Build/Dev (planned per README):**
- `ruff` - Linting and formatting (listed explicitly in README Phase 1 stack)
- `ty` - Type checking (listed explicitly in README Phase 1 stack)

## Key Dependencies

**Current (installed):**
- None — `pyproject.toml` has `dependencies = []` and `uv.lock` contains only the root package

**Planned (per README Phase 1):**
- `textual` - TUI framework for all UI components
- `ruff` - Linter/formatter (dev dependency)
- `ty` - Type checker (dev dependency)

**Planned (per README Phase 2):**
- HTTP client library (e.g., `httpx`) for OpenRouter API calls and web fetching
- Web content fetching utilities

## Configuration

**Environment:**
- `.env` file path listed in `.gitignore` — environment variables (e.g., API keys) will go here
- No environment configuration is currently implemented
- OpenRouter API key will be required (see INTEGRATIONS.md)

**Build:**
- `pyproject.toml` — project metadata and dependency declarations
- `uv.lock` — pinned dependency lockfile for reproducibility

## Platform Requirements

**Development:**
- Python 3.12+
- `uv` package manager (`pip install uv` or OS package)
- Virtual environment managed at `.venv/`
- Run entry point: `python main.py`

**Production:**
- Terminal-based application, no server deployment needed
- Local filesystem access required (chat history stored locally per README)
- OpenRouter API access required (internet connectivity)

---

*Stack analysis: 2026-03-26*
