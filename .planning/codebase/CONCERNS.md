# Codebase Concerns

**Analysis Date:** 2026-03-26

## Tech Debt

**Project is a stub with no implementation:**
- Issue: The entire application is a placeholder. `main.py` contains only a `Hello from remmeh!` print statement. No modules, classes, services, or UI code exist yet.
- Files: `main.py`
- Impact: Nothing works. All features described in README.md are unimplemented.
- Fix approach: Begin Phase 1 implementation per README.md — establish module structure, integrate Textual, OpenRouter, and local session storage before anything else.

**`pyproject.toml` has no dependencies declared:**
- Issue: `dependencies = []` in `pyproject.toml` yet the project intends to use Textual, OpenRouter SDK, ruff, and ty (type checker). No dev dependencies section exists.
- Files: `pyproject.toml`
- Impact: No reproducible install. Any `uv sync` produces a bare environment with no runtime packages.
- Fix approach: Add `dependencies` (Textual, httpx or openai-compatible client) and `[dependency-groups]` for dev tools (ruff, ty, pytest) to `pyproject.toml`.

**`pyproject.toml` description is a placeholder:**
- Issue: `description = "Add your description here"` — boilerplate left from project init.
- Files: `pyproject.toml`
- Impact: Low. Cosmetic but unprofessional if published.
- Fix approach: Replace with the actual description from README.md: `"a TUI LLM chat and research tool"`.

**No entry point configured:**
- Issue: `pyproject.toml` has no `[project.scripts]` entry point. Running the tool requires `python main.py` rather than an installed CLI command.
- Files: `pyproject.toml`
- Impact: Poor developer and user experience. Not installable as a CLI tool.
- Fix approach: Add `[project.scripts]` e.g. `remmeh = "remmeh.main:main"` and restructure `main.py` into a proper package (`src/remmeh/` or `remmeh/`).

**Flat single-file structure not suitable for planned scope:**
- Issue: All code is in root-level `main.py`. The README describes multi-phase features: TUI, OpenRouter integration, local session/history persistence, command palette, hotkey config, web fetching, agent personalities, conversation splits. A flat file cannot sustain this.
- Files: `main.py`
- Impact: Will become unmaintainable rapidly as features are added. Import cycles, testing difficulty.
- Fix approach: Establish package structure before adding any features. Suggested: `remmeh/ui/`, `remmeh/api/`, `remmeh/storage/`, `remmeh/config/`, `tests/`.

## Known Bugs

No application code exists, so no runtime bugs are present. All concerns at this stage are structural/pre-implementation.

## Security Considerations

**No secrets management approach defined:**
- Risk: The planned OpenRouter integration requires an API key. No `.env` loading, config file, or keyring approach has been established.
- Files: `main.py`, `pyproject.toml`
- Current mitigation: None — no API key handling code exists yet.
- Recommendations: Before implementing OpenRouter calls, establish a secrets approach. Options: `python-dotenv` with `.env` (already in `.gitignore`), OS keyring via `keyring` package, or an XDG config directory file with restricted permissions. Ensure API key is never hardcoded or logged.

**Chat history stored locally — no encryption defined:**
- Risk: README states "Chat session history stored locally" and "All messages, including thinking blocks stored locally as well for debugging." LLM conversation data can be sensitive.
- Files: Not yet created
- Current mitigation: None — not implemented yet.
- Recommendations: Decide on storage location (XDG data home), use SQLite or structured JSON, and document whether encryption at rest is in scope. At minimum, ensure the storage directory has user-only permissions.

**No input sanitization strategy for web content (Phase 2):**
- Risk: Phase 2 plans to fetch web content and integrate with GitHub/PyPI. Malicious page content injected into LLM context could cause prompt injection.
- Files: Not yet created
- Current mitigation: None — not implemented yet.
- Recommendations: When implementing web fetching, strip/sanitize raw HTML before passing to LLM. Consider a content allowlist approach for trusted sources.

## Performance Bottlenecks

**No async architecture decision made:**
- Problem: Textual is async-native. OpenRouter API calls are I/O-bound and must be non-blocking to keep the TUI responsive. No async patterns are in place.
- Files: `main.py`
- Cause: Not yet implemented.
- Improvement path: Design all I/O (API calls, file reads, web fetching) as `async` from the start. Use Textual's `call_after_refresh`, `run_worker`, or `work` decorator for background tasks. Retrofitting sync code into async later is costly.

**Streaming LLM responses not planned explicitly:**
- Problem: README mentions "thinking blocks" (likely Claude extended thinking). If responses are not streamed, the UI will freeze waiting for full responses on large outputs.
- Files: Not yet created
- Cause: Architectural decision not yet made.
- Improvement path: Implement OpenRouter calls with streaming (`stream=True`) from day one. Textual widgets can be updated incrementally via reactive attributes.

## Fragile Areas

**`main.py` as sole entry point:**
- Files: `main.py`
- Why fragile: Any refactor of the entry point breaks the only way to run the application. No package structure means imports will be messy.
- Safe modification: Establish `remmeh/` package directory with `__init__.py` and `__main__.py` before adding logic.
- Test coverage: None.

## Scaling Limits

**Local storage format not defined:**
- Current capacity: N/A — not implemented.
- Limit: If chat history is stored as flat JSON files, performance degrades with large numbers of sessions. Folder-based organization (per README) compounds this with filesystem limits.
- Scaling path: Use SQLite via `aiosqlite` for session/message storage. SQLite handles thousands of sessions efficiently and supports full-text search for future features.

## Dependencies at Risk

**No dependencies locked (empty `uv.lock`):**
- Risk: The `uv.lock` only contains the project itself with no resolved packages. First install will pull latest versions of everything without version constraints.
- Impact: Non-reproducible builds. Breaking changes in Textual, httpx, or other deps could go undetected.
- Migration plan: Add explicit version constraints to `pyproject.toml` and commit the populated `uv.lock` after first real install.

**Textual not yet added as dependency:**
- Risk: README specifies Textual as the UI framework but it is not in `pyproject.toml`. No version has been evaluated or tested.
- Impact: Blocks all UI development.
- Migration plan: Add `textual>=1.0` to dependencies. Review Textual changelog for breaking changes between versions before pinning.

## Missing Critical Features

**No test infrastructure:**
- Problem: README says "Well-designed test coverage" is a Phase 1 goal, but no test runner, config, or test files exist.
- Blocks: Cannot validate any functionality as it is built. No CI can run.
- Recommendation: Add `pytest` and `pytest-asyncio` to dev dependencies. Create `tests/` directory and `pyproject.toml` `[tool.pytest.ini_options]` section before writing first feature.

**No linting/formatting configuration:**
- Problem: README specifies ruff and ty as tools, but neither is configured in `pyproject.toml` and neither is installed.
- Blocks: Code style consistency from first commit.
- Recommendation: Add `[tool.ruff]` and `[tool.ruff.lint]` sections to `pyproject.toml`. Add `ty` (or `mypy`) config. Consider adding pre-commit hooks.

**No CI pipeline:**
- Problem: No `.github/workflows/` or other CI config exists.
- Blocks: Automated testing, linting, and type checking on PRs.
- Recommendation: Add a GitHub Actions workflow running `ruff check`, `ty check`, and `pytest` at minimum before the project grows.

**OpenRouter API client not chosen or integrated:**
- Problem: No HTTP client or OpenRouter SDK is installed. README plans automatic model fetching from OpenRouter endpoints.
- Blocks: All LLM functionality.
- Recommendation: Choose between `openai` Python SDK (OpenRouter is compatible), `httpx` with manual client, or a dedicated OpenRouter SDK. Add to `pyproject.toml` and implement an `api/` module.

## Test Coverage Gaps

**Entire application is untested:**
- What's not tested: Everything — no test files exist.
- Files: `main.py` (only source file)
- Risk: Any feature added has zero regression protection.
- Priority: High — establish test infrastructure before Phase 1 features are built.

---

*Concerns audit: 2026-03-26*
