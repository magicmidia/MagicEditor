---
name: me-ui
description: >
  MagicEditor PyQt6 UI work (main window, tabs, virtual viewport, dialogs).
  Use when editing src/magiceditor/ui/**, thin widgets, signals, or pytest-qt tests.
  Triggers: main_window, virtual_editor, tab_manager, dialog, QSS chrome, pytest-qt, thin UI.
---

# MagicEditor — Thin UI

## Non-negotiables
- **Thin widgets:** no piece-table math, no mmap open policy, no full-file I/O in paint/events
- Call `services/` / `core/` for policy and buffer ops
- Prefer signals/slots over direct cross-widget mutation
- Prefer ≤300 LOC modules; **do not grow** `main_window.py` / `virtual_editor.py` further — extract collaborators

## Key modules
| File | Role |
|------|------|
| `main_window.py` | Composition / menus / wiring only |
| `virtual_editor.py` | Visible-line viewport |
| `tab_manager.py` | Tab chrome, tear-off, double-click new |
| `text_editor.py` | Standard editor path |
| `editor_tab.py` | Per-tab shell |
| `*_dialog.py` | Modal flows |

## Patterns
- Live i18n: connect `TranslatorManager.language_changed` → `retranslate_ui()`
- Themes: chrome via QSS; syntax palette separate when needed
- Workers: `QThread` / `moveToThread`; never touch widgets from worker threads (signals only)
- Huge files: viewport paints visible range (+ small overscan) only

## Testing
```powershell
$env:QT_QPA_PLATFORM = "offscreen"
uv run pytest tests/ui/<file> -q
```

## Process
1. Read `src/magiceditor/ui/AGENTS.md`
2. Prefer new helper module over bloating god files
3. Wire actions in main window; implement behavior in focused classes
4. VERIFY file-scoped ruff + pytest-qt offscreen

## Anti-patterns
- `import PyQt6` inside `core/`
- Loading entire document into `QTextDocument` for >50MB
- Blocking GUI thread on folder search / disk scan
- Hardcoded PT/EN strings (use translator keys)
