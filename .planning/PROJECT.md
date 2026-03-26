# remmeh

## What This Is

remmeh is a personal TUI LLM chat tool built around a keyboard-first experience. It integrates with OpenRouter to provide access to multiple LLMs in a single terminal application, with persistent local session history, full Markdown rendering, and a command palette that serves as the hub for all actions.

## Core Value

A keyboard-driven TUI where everything — model switching, session management, settings — is accessible without touching the mouse.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] User can send messages and receive LLM responses via OpenRouter
- [ ] User can switch between models fetched dynamically from OpenRouter
- [ ] User can mark models as default or favorited
- [ ] User can start new conversations and navigate between them
- [ ] Sessions are persisted locally in full, including thinking blocks
- [ ] Sessions can be organized into manually-created folders
- [ ] Responses are rendered with full Markdown formatting and syntax-highlighted code blocks
- [ ] All actions are accessible via a command palette
- [ ] Common actions (model switch, new chat) are accessible via configurable hotkeys
- [ ] UI layout: 3-line input panel at bottom with scroll, slide-in/out session sidebar on right

### Out of Scope

- Web search / web page fetching — Phase 2
- Custom agent personalities / @-mentions — Phase 3
- Conversation splitting and comparison — Phase 4
- OAuth or multi-user auth — single-user local tool, no auth needed
- Cloud sync — local storage only by design

## Context

- Project is at scaffold stage: `main.py` is a stub, no application code exists yet
- Stack is decided: Python 3.12, uv, Textual (TUI framework), ruff, ty
- OpenRouter API key will be loaded from a `.env` file (already gitignored)
- The codebase map exists at `.planning/codebase/` documenting intended architecture
- No existing capabilities to preserve — greenfield implementation

## Constraints

- **Tech stack**: Python 3.12 + Textual — already decided, no alternatives
- **Package manager**: uv — already in use, lockfile committed
- **Storage**: Local filesystem only — no server, no cloud
- **Type checking**: ty (not mypy) — explicitly chosen in README
- **Linting**: ruff — already in toolchain

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Textual for TUI | Python-native TUI framework with rich widget system | — Pending |
| OpenRouter for LLMs | Unified API for multiple models, dynamic model list | — Pending |
| Local file/SQLite storage | No server needed, portable, debugging-friendly | — Pending |
| Command palette as primary UI hub | Keyboard-first, discoverability without memorizing hotkeys | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-26 after initialization*
