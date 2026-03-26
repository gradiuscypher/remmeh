# External Integrations

**Analysis Date:** 2026-03-26

## APIs & External Services

**LLM Provider:**
- OpenRouter - LLM chat API; all model interactions route through OpenRouter endpoints
  - SDK/Client: HTTP client (to be added; `httpx` is conventional)
  - Auth: API key via environment variable (name TBD, likely `OPENROUTER_API_KEY`)
  - Models fetched dynamically from OpenRouter's model listing endpoint
  - README specifies: "Integration with OpenRouter endpoints, fetching the models automatically"

**Web Research (Phase 2, planned):**
- Generic web page fetching - Retrieve and display web content in the TUI
  - Auth: None (public URLs)
- GitHub - Custom integration for repository/issue browsing
  - Auth: Likely personal access token
- PyPI - Custom integration for package information
  - Auth: None (public API)
- Other "LLM-friendly search content" sources - TBD

## Data Storage

**Databases:**
- None — no database engine planned or configured

**File Storage:**
- Local filesystem - Chat session history and message content stored locally
  - Location: TBD (likely `~/.local/share/remmeh/` or `./data/` — not yet implemented)
  - Format: TBD (JSON or SQLite are both common for this use case)
  - README specifies: "Chat session history stored locally", "All messages, including thinking blocks stored locally as well for debugging"
  - Sessions can be organized into folders

**Caching:**
- None planned or configured

## Authentication & Identity

**Auth Provider:**
- None — this is a local CLI/TUI tool with no user accounts or identity system
- API key authentication only (OpenRouter API key stored in environment)

## Monitoring & Observability

**Error Tracking:**
- None planned or configured

**Logs:**
- Local file logging implied by README ("all messages, including thinking blocks stored locally as well for debugging")
- No structured logging framework configured yet

## CI/CD & Deployment

**Hosting:**
- Local terminal application — no server hosting required
- Distributed as a Python package (via `pyproject.toml`)

**CI Pipeline:**
- None configured (no `.github/`, no CI config files present)

## Environment Configuration

**Required env vars (planned):**
- OpenRouter API key (name TBD — likely `OPENROUTER_API_KEY`)
- Optionally: GitHub personal access token for Phase 2 GitHub integration

**Secrets location:**
- `.env` file (listed in `.gitignore`, will not be committed)
- No secrets management system configured

## Webhooks & Callbacks

**Incoming:**
- None — local TUI application, not reachable from external services

**Outgoing:**
- None — all communication is request/response (HTTP calls to OpenRouter and web sources)

---

*Integration audit: 2026-03-26*
