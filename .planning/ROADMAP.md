# Roadmap: remmeh

## Overview

remmeh is built in four phases that follow the natural dependency graph of a keyboard-first TUI chat tool. Phase 1 establishes the architectural foundation and core chat loop — all 10 documented pitfalls live here and must be resolved before building anything else. Phase 2 adds model selection and multi-session persistence, sharing the same SQLite and command palette infrastructure. Phase 3 completes the keyboard-first experience with full command palette providers, thinking block rendering, and configurable hotkeys. Phase 4 adds session organization and discovery features that are only worth building once the flat session list is stable.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundation & Core Chat** - Streaming LLM chat with Markdown rendering, working layout, and all async/storage pitfalls resolved
- [ ] **Phase 2: Model Selection & Sessions** - Dynamic model list, multi-session persistence, session sidebar, and command palette scaffold
- [ ] **Phase 3: Command Palette & Thinking Blocks** - Full command palette with providers, thinking block rendering, and configurable hotkeys
- [ ] **Phase 4: Session Organization & Discovery** - Session folders, fuzzy search, and session tree navigation

## Phase Details

### Phase 1: Foundation & Core Chat
**Goal**: User can send a message and receive a streamed, Markdown-rendered LLM response — with correct async architecture, SQLite storage, and error handling in place
**Depends on**: Nothing (first phase)
**Requirements**: CHAT-01, CHAT-02, CHAT-03, CHAT-04, CHAT-05, CHAT-06, UI-01, UI-05
**Success Criteria** (what must be TRUE):
  1. User can type a multi-line message in the 3-line input panel and submit it with Enter; Shift+Enter inserts a newline
  2. The LLM response streams token-by-token in the chat view without scroll-reset jitter or UI freezes
  3. Markdown formatting (headers, lists, code blocks with syntax highlighting) renders correctly in completed responses
  4. API errors, rate limits, and timeouts appear inline in the chat thread without crashing the app
  5. The current model name is visible in the status bar; the app loads the OpenRouter API key from `.env` at startup
**Plans**: 6 plans
Plans:
- [x] 01-01-PLAN.md — Project scaffold: pyproject.toml, package structure, ruff/ty/pytest config
- [x] 01-02-PLAN.md — Data models + async SQLite storage with WAL mode
- [x] 01-03-PLAN.md — App config + async OpenRouter streaming client with error classification
- [x] 01-04-PLAN.md — TUI layout skeleton: RemmehApp, ChatScreen, StatusBar, ChatView, InputPanel
- [ ] 01-05-PLAN.md — MessageWidget + streaming worker wired with SQLite persistence + error handling
- [ ] 01-06-PLAN.md — Integration tests + human verification checkpoint
**UI hint**: yes

### Phase 2: Model Selection & Sessions
**Goal**: User can switch models and manage multiple conversations — with sessions persisted in SQLite, the session sidebar accessible via keybind, and a working command palette scaffold
**Depends on**: Phase 1
**Requirements**: MODL-01, MODL-02, MODL-03, MODL-04, SESS-01, SESS-02, SESS-03, SESS-04
**Success Criteria** (what must be TRUE):
  1. User can open the command palette and switch to any model from a dynamically-fetched OpenRouter list without losing the current conversation
  2. User's default model and favorited models persist across app restarts; favorites appear at the top of the model picker
  3. User can start a new session via command palette or keybind; all sessions are saved to SQLite with full message history
  4. User can toggle the session sidebar open/closed with a keybind and navigate to any previous session to resume it
**Plans**: TBD
**UI hint**: yes

### Phase 3: Command Palette & Thinking Blocks
**Goal**: Every app action is accessible from the command palette; extended thinking blocks from Claude 3.7+ are stored and rendered as collapsible sections; hotkeys are configurable via config file
**Depends on**: Phase 2
**Requirements**: UI-02, UI-03, UI-04
**Success Criteria** (what must be TRUE):
  1. Pressing Ctrl+P opens the command palette with all app actions discoverable: model switch, new session, session navigation, and settings
  2. Extended thinking blocks from Claude 3.7+ responses appear as a distinct, collapsible section above the response content in the chat view
  3. User can rebind model switch, new session, and sidebar toggle hotkeys by editing a config file and restarting the app
**Plans**: TBD
**UI hint**: yes

### Phase 4: Session Organization & Discovery
**Goal**: User can organize sessions into named folders and quickly find any session via fuzzy search — making the app usable at 20+ sessions
**Depends on**: Phase 3
**Requirements**: SESS-05, SESS-06
**Success Criteria** (what must be TRUE):
  1. User can create named folders and drag or assign sessions into them; folder structure is persisted across restarts
  2. User can type in the session sidebar search box to filter sessions by title or message content in real time
**Plans**: TBD
**UI hint**: yes

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & Core Chat | 4/6 | In Progress|  |
| 2. Model Selection & Sessions | 0/? | Not started | - |
| 3. Command Palette & Thinking Blocks | 0/? | Not started | - |
| 4. Session Organization & Discovery | 0/? | Not started | - |
