# Codebase Structure

**Analysis Date:** 2026-03-26

## Current Directory Layout

```
remmeh/
├── .git/               # Git repository metadata
├── .gitignore          # Standard Python + uv + ruff ignores
├── .planning/          # GSD planning documents
│   └── codebase/       # Codebase analysis docs (this file lives here)
├── .python-version     # Pins Python 3.12 (used by pyenv/uv)
├── .venv/              # Virtual environment (not committed)
├── LICENSE             # Project license
├── main.py             # Entry point (stub only)
├── pyproject.toml      # Project metadata and dependency config
├── README.md           # Feature roadmap and UI layout spec
└── uv.lock             # Dependency lockfile (committed)
```

## Directory Purposes

**`.planning/`:**
- Purpose: GSD planning and analysis documents
- Contains: Codebase maps, phase plans
- Key files: `.planning/codebase/ARCHITECTURE.md`, `.planning/codebase/STRUCTURE.md`
- Generated: No (manually authored by GSD tooling)
- Committed: Yes

**`.venv/`:**
- Purpose: Python virtual environment managed by uv
- Generated: Yes
- Committed: No (in `.gitignore`)

## Key File Locations

**Entry Points:**
- `main.py`: Application entry point — contains stub `main()` function

**Configuration:**
- `pyproject.toml`: Project name (`remmeh`), version (`0.1.0`), Python requirement (`>=3.12`), dependencies (none yet)
- `.python-version`: Pins Python version to `3.12`
- `uv.lock`: Dependency lockfile — currently only lists the project itself (no third-party deps yet)
- `.gitignore`: Comprehensive Python gitignore (covers uv, ruff, pyenv, venv, etc.)

**Documentation:**
- `README.md`: Feature roadmap across 4 phases; UI layout specification

## Naming Conventions

**Files:**
- `snake_case.py` for Python source files (standard Python convention)
- Entry point is `main.py` at project root

**Directories:**
- Lowercase with underscores for Python packages (standard convention)

## Where to Add New Code

**New Application Package:**
- Create `src/remmeh/` or `remmeh/` package directory with `__init__.py`
- Register as package in `pyproject.toml` under `[tool.setuptools.packages]` or equivalent

**New TUI Screen or Widget:**
- Implementation: `remmeh/ui/` (create directory)
- Follow Textual conventions: subclass `textual.app.App`, `textual.screen.Screen`, or `textual.widget.Widget`

**New Service (Business Logic):**
- Implementation: `remmeh/services/`
- One module per domain concern (e.g., `remmeh/services/session.py`, `remmeh/services/models.py`)

**New Integration (External API):**
- Implementation: `remmeh/integrations/`
- One module per provider (e.g., `remmeh/integrations/openrouter.py`)

**New Storage Module:**
- Implementation: `remmeh/storage/`
- One module per storage concern (e.g., `remmeh/storage/sessions.py`)

**Tests:**
- Location: `tests/` at project root (standard Python convention)
- Naming: `test_<module_name>.py` mirroring the source structure

**Utilities:**
- Shared helpers: `remmeh/utils/` or `remmeh/helpers/`

## Special Directories

**`.planning/`:**
- Purpose: GSD tooling documents — architecture maps, phase plans
- Generated: No
- Committed: Yes

**`.venv/`:**
- Purpose: Local Python virtual environment (uv-managed)
- Generated: Yes (via `uv sync`)
- Committed: No

## Project State Note

The project is in initial scaffold state. Beyond `main.py` (a 6-line stub), no source directories, packages, modules, or tests exist yet. All "where to add" guidance above reflects standard Python/Textual conventions consistent with the stated toolchain in README.md.

---

*Structure analysis: 2026-03-26*
