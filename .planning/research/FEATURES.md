# Feature Research

**Domain:** TUI/CLI LLM Chat Tool (keyboard-first, multi-model, persistent sessions)
**Researched:** 2026-03-26
**Confidence:** HIGH (verified against Aider, llm CLI, AIChat, chatblade, OpenCode, and Textual ecosystem)

## Competitors Surveyed

| Tool | Stars | Type | Notable |
|------|-------|------|---------|
| OpenCode (anomalyco) | 130k | Full TUI agent | Tab-switch agents, LSP, client/server arch |
| Aider | 42k | Interactive CLI | Multi-LLM, git integration, streaming |
| llm CLI (simonw) | 11k | CLI + REPL | SQLite logging, plugin system, fragments |
| AIChat (sigoden) | 9.6k | CLI REPL | 20+ providers, sessions, roles, RAG, MCP |
| Chatblade (npiv) | 2.6k | CLI | **Archived** — recommend llm CLI instead |

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Send message → receive streamed response | Core loop — any LLM chat tool must do this | LOW | Must stream token-by-token, not wait for completion. Non-streaming feels broken. |
| Markdown rendering in responses | Every LLM outputs markdown; raw `**bold**` in terminal is terrible UX | MEDIUM | Need to handle inline code, headers, lists, blockquotes, tables. Textual's `Markdown` widget covers this. |
| Syntax-highlighted code blocks | Code in responses is useless without highlighting | MEDIUM | Must detect language from fenced-code hints. Rich/Textual syntax highlighting available. |
| Persistent session history | Users want to resume conversations after closing | MEDIUM | SQLite is the right choice; flat JSON files don't scale past ~100 sessions. |
| New conversation / clear context | Users need clean starts without restarting the app | LOW | Should be a keybind + command palette action. |
| Navigate between past sessions | Can't have persistent history without a way to browse it | MEDIUM | Needs a session list UI — sidebar or modal. |
| Model selection | Users switch models frequently to balance cost/quality | MEDIUM | Must show model name in UI at all times. Switching must not lose current conversation. |
| Configurable default model | Power users don't want to re-select every launch | LOW | Stored in config file, settable via command palette. |
| Multi-line input | Messages often span paragraphs; single-line input is a deal-breaker | LOW | Shift+Enter or similar. Textual's `TextArea` widget handles this natively. |
| Error handling with visible feedback | API errors, rate limits, timeouts must not silently fail | LOW | Show error inline in chat thread, not as a crash. |
| Keyboard-accessible navigation | TUI users expect full keyboard control | MEDIUM | Tab/arrow navigation between panels. No mouse required. |
| API key configuration via env | Standard pattern in the ecosystem — `.env` file or env var | LOW | All major tools use `OPENROUTER_API_KEY` / `.env`. Already in scope per PROJECT.md. |

---

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valuable.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Command palette as primary hub | Single discoverable entry point for all actions — no need to memorize hotkeys | MEDIUM | Textual has built-in `CommandPalette` widget (Ctrl+P pattern). This is remmeh's stated core differentiator. |
| Session folder organization | Users accumulate many sessions; flat list becomes unusable at 50+ | HIGH | Nested tree structure. Folder create/rename/delete. No competitor does this cleanly in a TUI. |
| Favorited / default model marking | Quick return to preferred models from a 400+ item list | LOW | Star/pin mechanism on model entries. Requires model metadata persistence. |
| Dynamic model list from API | Shows newly added models without app updates | MEDIUM | OpenRouter `/models` endpoint. Cache with TTL. Aider bakes in model lists; this is better. |
| Slide-in session sidebar | Spatial UI — sidebar context without losing the chat view | MEDIUM | Right-side sidebar that animates in/out. OpenCode does this well. Textual supports it. |
| Thinking block rendering | Preserves extended thinking (Claude 3.7+, etc.) as distinct collapsible section | MEDIUM | Required for models that expose chain-of-thought. No CLI tool currently renders these well. |
| Configurable hotkeys | Users have strong preferences; defaults will conflict with tmux/vim bindings | MEDIUM | Config file maps actions to keys. Common conflicts: `Ctrl+C`, `Ctrl+P`, `Esc`. |
| Token / cost indicator in UI | Users at OpenRouter want to monitor costs in real time | MEDIUM | Chatblade had a token count flag (`-t`). In a TUI this can be a persistent status bar element. |
| Session search / fuzzy filter | Useful at 20+ sessions; essential at 100+ | MEDIUM | Live-filter session list by title or message content. |

---

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Mouse-driven UI | "More intuitive" for new users | Textual supports mouse, but a TUI that requires mouse defeats the terminal-first purpose. Creates two conflicting interaction models. | Full keyboard nav with discoverable command palette. Mouse can work as bonus, not primary. |
| In-app settings screen with forms | Users want a GUI settings editor | Adds enormous widget complexity for little gain. Breaks the "simple local tool" constraint. Config file + command palette achieve the same outcome. | Config file (`~/.config/remmeh/config.toml`) + palette command to open it in `$EDITOR`. |
| Plugin / extension system | Power users want to extend functionality | Premature architectural complexity. Plugin APIs require stable contracts before v1. Breaks "personal tool" scope. | Defer to v2+. Use a clean module boundary design that allows it later without requiring it now. |
| Cloud sync / backup | Users want access on multiple machines | Violates PROJECT.md constraint explicitly. Introduces auth, network, privacy concerns. | Document path to manual sync via `rclone` / `git` if users need it. |
| Multi-user / auth | "Share conversations with team" | Complete scope violation. Authentication complexity is enormous. | Single-user personal tool by design — this is the product positioning. |
| Real-time conversation sharing / export to HTML | "Share a session with a link" | Requires server infrastructure. Out of scope. | Export to Markdown file is the right alternative. Low complexity, zero infra. |
| Conversation branching (fork at message) | Power users love this concept | Extremely complex graph data model. Session storage becomes a DAG, not a list. UI to navigate branches is unsolved. | Defer to Phase 4 per PROJECT.md. Start new session is the v1 workaround. |
| Built-in shell command execution | "Run the command it suggests" | Serious security surface. Requires permission model, sandboxing, undo. aichat's shell assistant is a distinct product mode, not a chat feature. | Phase 2/3 feature at earliest, with explicit user confirmation flow. |
| Voice input | "Hands-free coding" | Platform-specific, requires microphone permissions, adds heavy dependencies (SpeechRecognition etc). Aider has it but it's experimental. | Not a chat tool feature — defer indefinitely for personal tool scope. |
| Image / file attachment in messages | Multimodal queries | Valid long-term, but current OpenRouter multimodal support is inconsistent across models. Complicates input UX significantly. | Phase 2 feature. Plan input API to support attachments without wiring UI now. |

---

## Feature Dependencies

```
Persistent Session History
    └──requires──> Session Storage (SQLite)
                       └──requires──> Session Schema (messages, model, metadata)

Session Folder Organization
    └──requires──> Persistent Session History
    └──requires──> Folder CRUD operations
    └──requires──> Tree widget in sidebar

Model Selection
    └──requires──> OpenRouter API (fetch model list)
    └──requires──> Model metadata persistence (favorites, default)

Command Palette
    └──requires──> All actions registered as palette commands
    └──requires──> Model switching action
    └──requires──> Session navigation action

Thinking Block Rendering
    └──requires──> Streaming response parser (detect thinking vs content)
    └──requires──> Collapsible/expandable widget

Configurable Hotkeys
    └──requires──> Config file loading
    └──enhances──> Command Palette (palette shows hotkey hints)

Token/Cost Indicator
    └──requires──> OpenRouter usage response fields
    └──requires──> Status bar widget

Session Search
    └──requires──> Persistent Session History
    └──enhances──> Session Sidebar (filter sidebar content)

Slide-in Sidebar
    └──requires──> Session list widget
    └──enhances──> Session navigation (shows context without modal)
```

### Dependency Notes

- **Session folders require sessions**: Folder organization is v1.x, not v1. Get flat session list working first.
- **Command palette requires action registry**: All features must register themselves as palette commands or hotkeys. Design the action system before wiring the palette.
- **Thinking blocks require streaming parser**: Can't just render the raw stream. The parser must discriminate `thinking` blocks from `content` blocks before Markdown rendering.
- **Model favorites require model storage**: Model list from API is ephemeral. To mark favorites/defaults, model metadata must be persisted locally.

---

## MVP Definition

### Launch With (v1)

Minimum viable product — what's needed to validate the concept.

- [ ] **Send message → streamed response** — Core loop. Not negotiable.
- [ ] **Markdown + syntax-highlighted code rendering** — Raw text output is unusable for a developer tool.
- [ ] **OpenRouter model selection** — Dynamically fetched list, select via command palette, default persisted.
- [ ] **Persistent sessions with local SQLite storage** — Start new, navigate existing, resume.
- [ ] **Command palette (Ctrl+P)** — Model switch, new session, navigate sessions — all actions in palette.
- [ ] **Slide-in session sidebar (right side)** — Toggle with keybind, shows session list.
- [ ] **3-line scrollable input panel (bottom)** — Multi-line input, submit on Enter/Ctrl+Enter.
- [ ] **Favorite / default model marking** — Surfaces preferred models to top of picker.
- [ ] **Thinking block storage and rendering** — Extended thinking from Claude 3.7+ preserved in session and shown in UI.
- [ ] **Error display in chat thread** — API errors shown inline, not as crashes.

### Add After Validation (v1.x)

Features to add once core is working.

- [ ] **Session folder organization** — Add when flat session list becomes visually cluttered (20+ sessions).
- [ ] **Session search / fuzzy filter** — Add when navigation becomes slow.
- [ ] **Token / cost indicator in status bar** — Add after confirming OpenRouter returns usage data reliably.
- [ ] **Configurable hotkeys** — Add when users report binding conflicts with their tmux/vim setup.
- [ ] **Markdown export of session** — Add when users need to share or archive sessions.

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] **Web search / web page fetching** — Explicit Phase 2 item in PROJECT.md. Complex HTTP + content parsing.
- [ ] **Custom agent personalities / @-mentions** — Phase 3 per PROJECT.md. Requires persona/system-prompt management.
- [ ] **Conversation branching and comparison** — Phase 4 per PROJECT.md. Requires graph data model.
- [ ] **Image / file attachments** — Multimodal UX is complex. OpenRouter model support is inconsistent.
- [ ] **Plugin system** — Needs stable v1 API contracts first.

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Streamed response | HIGH | LOW | P1 |
| Markdown + code rendering | HIGH | MEDIUM | P1 |
| Model selection (dynamic) | HIGH | MEDIUM | P1 |
| Persistent sessions (SQLite) | HIGH | MEDIUM | P1 |
| Command palette | HIGH | MEDIUM | P1 |
| Session sidebar (slide-in) | HIGH | MEDIUM | P1 |
| Multi-line input panel | HIGH | LOW | P1 |
| Default/favorite models | MEDIUM | LOW | P1 |
| Thinking block rendering | MEDIUM | MEDIUM | P1 |
| Error handling in chat | HIGH | LOW | P1 |
| Session folder organization | MEDIUM | HIGH | P2 |
| Session search | MEDIUM | MEDIUM | P2 |
| Token/cost indicator | MEDIUM | LOW | P2 |
| Configurable hotkeys | MEDIUM | MEDIUM | P2 |
| Markdown export | LOW | LOW | P2 |
| Web search integration | HIGH | HIGH | P3 |
| Image attachments | MEDIUM | HIGH | P3 |
| Plugin system | LOW | HIGH | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

---

## Competitor Feature Analysis

| Feature | Aider | llm CLI | AIChat | OpenCode | remmeh approach |
|---------|-------|---------|--------|---------|-----------------|
| TUI layout | No — interactive CLI | No — pure CLI | No — REPL | Yes — full TUI | Yes — Textual full-screen TUI |
| Session persistence | File-based per session | SQLite (logs) | File-based per session | Yes | SQLite, all sessions in one DB |
| Session browsing | No | `llm logs` CLI | Named sessions | Tab-switch | Sidebar + command palette |
| Session organization | No | No | No | No | Folder tree (v1.x) |
| Model switching | `--model` flag | `-m` flag | `.model` command | Tab/modal | Command palette → model picker |
| Model favorites | No | Aliases | No | No | ★ marking, persisted |
| Dynamic model list | No (baked in) | Plugin-based | Config-based | Yes | OpenRouter `/models` API |
| Thinking blocks | Partial | No | No | Yes | Full store + render |
| Markdown rendering | Yes (Rich) | No (plain) | Yes (custom theme) | Yes | Textual Markdown widget |
| Syntax highlighting | Yes | No | Yes | Yes | Textual + Rich |
| Command palette | No | No | No | No | Ctrl+P (Textual built-in) |
| Configurable hotkeys | Limited | No | No | No | Config file |
| Folder organization | No | No | No | No | v1.x (unique differentiator) |
| Cost tracking | No | No | No | No | v1.x status bar |

---

## UX Patterns: Keyboard Navigation in TUI LLM Tools

*Synthesized from OpenCode and Textual ecosystem research.*

### Message Input Patterns

| Pattern | Tools Using It | remmeh recommendation |
|---------|---------------|----------------------|
| Enter = submit, Shift+Enter = newline | OpenCode, most chat apps | Use this. Most familiar for chat context. |
| Ctrl+Enter = submit, Enter = newline | Some editor-based tools | Avoid — users expect Enter=send in chat. |
| Multi-line area with scroll | OpenCode | Yes — 3-line height min, auto-scroll. |
| `!multi` / `!end` mode | llm CLI | No — modal text entry is bad UX in a TUI. |

### Session Navigation Patterns

| Pattern | Tools Using It | remmeh recommendation |
|---------|---------------|----------------------|
| Sidebar list | OpenCode | Yes — slide-in right sidebar. |
| CLI `--session` flag | llm CLI, chatblade | Skip — launch-time only, not in-app. |
| Named sessions via command | AIChat | Redundant if we have sidebar + palette. |
| Fuzzy search overlay | Not common in LLM TUIs, but standard in IDEs | v1.x addition — high value, low cost. |

### Command Palette Patterns

| Pattern | Tools Using It | remmeh recommendation |
|---------|---------------|----------------------|
| Ctrl+P trigger | VS Code, OpenCode, Textual apps | Yes — widely understood. |
| `/` slash commands | Many chat interfaces (Discord, Slack) | Use for in-input commands if needed. |
| `:` vim-style commands | AIChat REPL (`.model`, `.session`) | Skip — too niche, palette covers this. |
| All actions in palette | OpenCode, VS Code | Yes — the core design decision per PROJECT.md. |

---

## Sources

- **Aider** (42k stars): https://github.com/Aider-AI/aider — feature list, README
- **llm CLI** (11k stars): https://github.com/simonw/llm — docs, session/chat features
- **AIChat** (9.6k stars): https://github.com/sigoden/aichat — REPL guide, session/role features
- **Chatblade** (2.6k, archived): https://github.com/npiv/chatblade — session options, streaming
- **OpenCode** (130k stars): https://github.com/anomalyco/opencode — TUI layout, keyboard patterns, agent switching
- **Textual discussions**: https://github.com/Textualize/textual/discussions — Markdown widget performance discussion (#6414), copy/paste behavior (#2190)
- **OpenRouter API**: https://openrouter.ai/ — model list endpoint, usage fields

---
*Feature research for: Python TUI LLM chat tool (remmeh)*
*Researched: 2026-03-26*
