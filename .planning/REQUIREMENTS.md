# Requirements: remmeh

**Defined:** 2026-03-26
**Core Value:** A keyboard-driven TUI where everything — model switching, session management, settings — is accessible without touching the mouse.

## v1 Requirements

### Core Chat

- [x] **CHAT-01**: User can type a message and receive a streamed LLM response token-by-token via OpenRouter
- [x] **CHAT-02**: LLM responses are rendered with full Markdown formatting (headers, lists, inline code, blockquotes, tables)
- [x] **CHAT-03**: Code blocks in responses are syntax-highlighted with language detection from fenced-code hints
- [x] **CHAT-04**: User can enter multi-line messages (3-line input panel, Enter=submit, Shift+Enter=newline) with scroll support
- [x] **CHAT-05**: API errors, rate limits, and timeouts are displayed inline in the chat thread — app does not crash
- [x] **CHAT-06**: OpenRouter API key is loaded from a `.env` file at startup

### Models

- [ ] **MODL-01**: App fetches available models dynamically from the OpenRouter `/models` endpoint
- [ ] **MODL-02**: User can switch models via the command palette without losing the current conversation
- [ ] **MODL-03**: User can configure a default model that persists across app restarts
- [ ] **MODL-04**: User can mark models as favorites, which appear at the top of the model picker list

### Sessions

- [ ] **SESS-01**: All conversations (messages, model, metadata, thinking blocks) are persisted locally in SQLite
- [ ] **SESS-02**: User can start a new session via command palette or keybind
- [ ] **SESS-03**: User can navigate to and resume a previous session via the session sidebar
- [ ] **SESS-04**: Session sidebar slides in and out from the right side via a keybind
- [ ] **SESS-05**: User can create named folders and organize sessions into them
- [ ] **SESS-06**: User can search/filter sessions by title or message content in the sidebar

### UI Layout

- [x] **UI-01**: Primary layout has a bottom input panel (3-line height, scrollable) and a main chat view
- [ ] **UI-02**: Command palette (Ctrl+P) provides access to all app actions: model switch, new session, navigate sessions, settings
- [ ] **UI-03**: Extended thinking blocks from supported models (e.g. Claude 3.7+) are stored in session and displayed as a distinct collapsible section in the chat view
- [ ] **UI-04**: User can rebind common hotkeys (model switch, new session, sidebar toggle) via a config file
- [x] **UI-05**: Current model name is always visible in the UI (status bar or header)

## v2 Requirements

### Discovery & Navigation

- **DISC-01**: Token and estimated cost indicator shown in status bar per-response
- **DISC-02**: User can export a session to a Markdown file

### Extended Capabilities (Phase 2+)

- **EXT-01**: User can search web pages and fetch web content in chat (Phase 2 per PROJECT.md)
- **EXT-02**: User can define and @-mention custom agent personalities (Phase 3 per PROJECT.md)
- **EXT-03**: User can split a conversation into a new session with a different agent (Phase 4 per PROJECT.md)
- **EXT-04**: User can edit previous messages to modify conversation outcome (Phase 4 per PROJECT.md)
- **EXT-05**: User can compare two conversations via LLM analysis (Phase 4 per PROJECT.md)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Cloud sync / backup | Single-user local tool by design; adds auth, network, privacy complexity |
| Multi-user / auth | Complete scope violation — personal tool |
| Plugin / extension system | Needs stable v1 API contracts first; premature complexity |
| Mouse-first UI | TUI users expect full keyboard control; mouse as bonus only |
| In-app settings screen | Config file + command palette achieves the same with less complexity |
| Voice input | Heavy platform-specific dependencies; out of scope for personal tool |
| Image / file attachments | Multimodal UX complex; OpenRouter model support inconsistent |
| Real-time sharing | Requires server infrastructure |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| CHAT-01 | Phase 1 | Complete |
| CHAT-02 | Phase 1 | Complete |
| CHAT-03 | Phase 1 | Complete |
| CHAT-04 | Phase 1 | Complete |
| CHAT-05 | Phase 1 | Complete |
| CHAT-06 | Phase 1 | Complete |
| MODL-01 | Phase 2 | Pending |
| MODL-02 | Phase 2 | Pending |
| MODL-03 | Phase 2 | Pending |
| MODL-04 | Phase 2 | Pending |
| SESS-01 | Phase 2 | Pending |
| SESS-02 | Phase 2 | Pending |
| SESS-03 | Phase 2 | Pending |
| SESS-04 | Phase 2 | Pending |
| SESS-05 | Phase 4 | Pending |
| SESS-06 | Phase 4 | Pending |
| UI-01 | Phase 1 | Complete |
| UI-02 | Phase 3 | Pending |
| UI-03 | Phase 3 | Pending |
| UI-04 | Phase 3 | Pending |
| UI-05 | Phase 1 | Complete |

**Coverage:**
- v1 requirements: 21 total
- Mapped to phases: 21
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-26*
*Last updated: 2026-03-26 after initial definition*
