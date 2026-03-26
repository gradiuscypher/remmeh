# Architecture

**Analysis Date:** 2026-03-26

## Pattern Overview

**Overall:** Single-file script (scaffold only — no application architecture implemented yet)

**Key Characteristics:**
- Project is in initial scaffold state: one entry-point file (`main.py`) with a stub `main()` function
- No packages, modules, or layers exist yet
- README defines the intended product: a TUI (terminal UI) LLM chat and research tool using Textual
- All architectural decisions below are inferred from README intent and toolchain choices

## Intended Architecture (from README)

The planned application is a TUI LLM chat client built with:
- **Textual** — Python TUI framework for the UI layer
- **OpenRouter** — LLM API provider, models fetched dynamically
- **Local storage** — Chat session history and message logs stored on disk

### Planned Layers (not yet implemented)

**UI Layer:**
- Purpose: Render TUI screens, panels, and widgets using Textual
- Location: `src/remmeh/ui/` or `remmeh/ui/` (to be determined)
- Contains: Textual `App`, `Screen`, and `Widget` subclasses
- Depends on: Service layer, state/session management

**Service Layer:**
- Purpose: Business logic — chat sessions, model management, message handling
- Location: `src/remmeh/services/` (to be determined)
- Contains: Session manager, model fetcher, message router
- Depends on: Integration layer (OpenRouter API)

**Integration Layer:**
- Purpose: External API calls to OpenRouter, web fetching (Phase 2)
- Location: `src/remmeh/integrations/` (to be determined)
- Contains: OpenRouter HTTP client, model list fetcher

**Storage Layer:**
- Purpose: Persist chat history, sessions, and thinking blocks locally
- Location: `src/remmeh/storage/` (to be determined)
- Contains: Session serialization, local file/DB reads and writes

## Current State

**Entry Point:**
- Location: `main.py`
- Current behavior: prints `"Hello from remmeh!"` — stub only
- Invoked via: `python main.py` or `uv run main.py`

**No layers implemented.** The project has zero application code beyond the stub.

## Data Flow (Intended)

**User Sends Message:**

1. User types in bottom input panel (Textual widget)
2. Input is captured by the Textual `App` and dispatched to the service layer
3. Service layer formats message, appends to session history, calls OpenRouter API
4. OpenRouter streams/returns response (including thinking blocks)
5. Response is stored locally (session file/DB) for persistence and debugging
6. Response is rendered in the main chat panel with Markdown formatting

**Session Management:**
- Sessions are organized in folders locally
- Right-side panel slides in/out to show session list

**Model Selection:**
- Model list is fetched dynamically from OpenRouter
- Models can be marked as default or favorited
- Selection available via command palette and hotkeys

## Key Abstractions (Planned)

**Chat Session:**
- Purpose: Represents a conversation with history, model, and metadata
- Examples: To be implemented in service/storage layer

**Message:**
- Purpose: A single unit of chat (user or assistant), including thinking blocks
- Stored locally in full for debugging

**Model:**
- Purpose: Represents an LLM model available via OpenRouter
- Includes default/favorited status

**Command Palette:**
- Purpose: Unified interface for all app functionality
- Expected to be a Textual overlay widget

## Error Handling

**Strategy:** Not yet defined — no implementation exists

**Patterns:**
- Expected to use Python exceptions with Textual's error handling conventions

## Cross-Cutting Concerns

**Logging:** Not yet implemented; README implies full message/thinking-block persistence to local files for debugging
**Validation:** Not yet implemented
**Authentication:** OpenRouter API key (environment variable expected, not yet wired)

---

*Architecture analysis: 2026-03-26*
