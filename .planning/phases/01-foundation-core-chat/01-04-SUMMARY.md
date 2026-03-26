---
phase: 01-foundation-core-chat
plan: "04"
subsystem: ui
tags: [tui, textual, widgets, layout, chat-screen]
dependency_graph:
  requires:
    - remmeh package importable (plan 01)
    - DEFAULT_MODEL constant in remmeh.config (plan 01-02/03)
  provides:
    - RemmehApp root Textual application
    - ChatScreen with StatusBar / ChatView / InputPanel layout
    - InputPanel with Enter=submit, Shift+Enter=newline behavior
    - ChatView scrollable container with empty state
    - StatusBar 1-row widget with model name and streaming indicator
    - remmeh.tcss layout stylesheet
  affects:
    - plan 05 (streaming worker wires into ChatScreen.on_input_panel_submitted)
    - plan 06 (session sidebar mounts into ChatScreen layout)
tech_stack:
  added:
    - textual.containers.VerticalScroll (base for ChatView)
    - textual.screen.Screen (base for ChatScreen)
    - textual.widgets.Static (base for StatusBar)
    - textual.widgets.TextArea (embedded in InputPanel)
    - textual.binding.Binding (priority=True for quit keybindings)
  patterns:
    - InputPanel.Submitted custom message for decoupled submit handling
    - on_key scoped to InputPanel to avoid TextArea binding conflicts (pitfall #9)
    - priority=True on Ctrl+Q/Ctrl+C bindings only (per UI spec)
    - compose() method builds widget tree (Textual convention)
    - CSS_PATH relative reference from Screen to co-located .tcss file
key_files:
  created:
    - remmeh/ui/widgets/__init__.py
    - remmeh/ui/widgets/status_bar.py
    - remmeh/ui/widgets/chat_view.py
    - remmeh/ui/widgets/input_panel.py
    - remmeh/ui/widgets/screens/__init__.py
    - remmeh/ui/screens/__init__.py
    - remmeh/ui/screens/chat.py
    - remmeh/ui/remmeh.tcss
  modified:
    - remmeh/ui/app.py (replaced stub with ChatScreen-wired RemmehApp)
decisions:
  - "Used VerticalScroll from textual.containers (not textual.widgets) — it was moved in Textual 1.x"
  - "Used typed __init__ parameters instead of *args/**kwargs passthrough — required for ty type checker compatibility"
  - "Renamed _render() to _build_content() in StatusBar — _render is a reserved Widget method name with incompatible signature"
  - "Placeholder text set via contextlib.suppress(AttributeError) — future-proofs against Textual version differences"
metrics:
  duration_seconds: 259
  completed_date: "2026-03-26"
  tasks_completed: 2
  files_created: 8
  files_modified: 1
---

# Phase 01 Plan 04: TUI Layout Skeleton Summary

**One-liner:** Complete Textual TUI layout with StatusBar/ChatView/InputPanel widgets, ChatScreen, RemmehApp, TCSS styling, and Enter/Shift+Enter keybinding behavior.

## What Was Built

Implemented the full TUI layout skeleton for remmeh — all UI components needed for the chat interface, wired together but without streaming logic (Plan 05):

- **`remmeh/ui/widgets/status_bar.py`** — `StatusBar(Static)` subclass showing model name on left and "remmeh" on right, with `update_model()` and `set_streaming()` API
- **`remmeh/ui/widgets/chat_view.py`** — `ChatView(VerticalScroll)` subclass with empty state ("Start a conversation"), `add_message_widget()` that removes empty state on first message
- **`remmeh/ui/widgets/input_panel.py`** — `InputPanel(Widget)` wrapping `TextArea`, consumes Enter via `on_key` to post `InputPanel.Submitted`, Shift+Enter falls through to TextArea newline behavior
- **`remmeh/ui/remmeh.tcss`** — Textual CSS: 1-row StatusBar, 1fr ChatView, 5-row InputPanel with `InputPanel:focus-within` accent border
- **`remmeh/ui/screens/chat.py`** — `ChatScreen(Screen)` with 3-panel `compose()`, `priority=True` Ctrl+Q/Ctrl+C bindings, stub `on_input_panel_submitted` and `action_cancel_stream`
- **`remmeh/ui/app.py`** — `RemmehApp(App)` with `SCREENS = {"chat": ChatScreen}` and `push_screen("chat")` on mount

## Verification Results

```
uv run python -c "from remmeh.ui.widgets import ChatView, InputPanel, StatusBar; print('widgets OK')"  ✓
uv run python -c "from remmeh.ui.app import RemmehApp; app = RemmehApp(); print('RemmehApp instantiates OK')"  ✓
uv run ruff check remmeh/ui/   ✓  All checks passed
uv run ty check remmeh/ui/     ✓  All checks passed
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] VerticalScroll import location changed in Textual 1.x**
- **Found during:** Task 1 verification
- **Issue:** `from textual.widgets import VerticalScroll` raised `ImportError` — widget moved to `textual.containers` in Textual 1.x
- **Fix:** Changed import to `from textual.containers import VerticalScroll`
- **Files modified:** `remmeh/ui/widgets/chat_view.py`
- **Commit:** 283a3cd

**2. [Rule 1 - Bug] `_render()` name conflicts with Widget internal method**
- **Found during:** Task 1 implementation
- **Issue:** Naming the helper method `_render` in `StatusBar` caused a `ty` error — `Widget._render()` is a reserved method with return type `Visual`, incompatible with `str`
- **Fix:** Renamed to `_build_content()`
- **Files modified:** `remmeh/ui/widgets/status_bar.py`
- **Commit:** e5bb032

**3. [Rule 1 - Bug] `*args/**kwargs` passthrough incompatible with `ty` type checker**
- **Found during:** Task 2 `ty check` run
- **Issue:** Using `*args: object, **kwargs: object` in widget `__init__` signatures caused 16 `ty` errors — `ty` validates argument types strictly even when passed through
- **Fix:** Replaced all widget `__init__` signatures with explicit typed parameters matching their base class
- **Files modified:** `remmeh/ui/widgets/status_bar.py`, `remmeh/ui/widgets/chat_view.py`, `remmeh/ui/widgets/input_panel.py`
- **Commit:** e5bb032

**4. [Rule 2 - Lint] ruff SIM105/SIM108 violations**
- **Found during:** Task 2 ruff check run
- **Issue:** `try/except/pass` for AttributeError (SIM105) and `if/else` block for ternary (SIM108)
- **Fix:** Used `contextlib.suppress(AttributeError)` and ternary operator
- **Files modified:** `remmeh/ui/widgets/input_panel.py`, `remmeh/ui/widgets/status_bar.py`
- **Commit:** e5bb032

## Known Stubs

| File | Stub | Reason |
|------|------|--------|
| `remmeh/ui/screens/chat.py` | `on_input_panel_submitted` only logs submitted text | Streaming worker wired in Plan 05 |
| `remmeh/ui/screens/chat.py` | `action_cancel_stream` is a no-op | Stream cancellation wired in Plan 05 |
| `remmeh/ui/widgets/chat_view.py` | Empty state body shows generic text (no model name) | Model name in empty state wired in Plan 05 after config loading |

These stubs are intentional — Plan 04 delivers layout skeleton only. Plan 05 wires the streaming logic.

## Self-Check: PASSED
