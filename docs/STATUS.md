# Project Status

**Updated:** 2026-07-17  
**Branch:** `feature/editor-mvp`

## Current phase
**MVP feature-complete** — daily-driver parity + session memory.

## Done
- [x] AI harness, model routing, Cascadia Code bundled
- [x] Modern MainWindow (themes, explorer optional, session restore, find modal)
- [x] Piece table, line index, document I/O
- [x] Syntax highlighting + Syntax menu (many languages)
- [x] Print / Export PDF (clean light styles)
- [x] Virtual viewport + mmap + incremental line index
- [x] Find in Files (workspace + open tabs) + regex
- [x] Go to Line, replace, undo/redo (virtual)
- [x] Soft wrap (virtual) + bookmarks
- [x] Session: open files, workspace, bookmarks, cursors
- [x] **Untitled draft recovery** (`session/drafts_json`)
- [x] **Recent files** menu
- [x] Encoding + EOL menu (Format)
- [x] Cut/Copy/Paste/Select All + indent/outdent/duplicate line
- [x] Close tab / others / all; double-click tab bar → new
- [x] Locales: pt_BR, en_US, es_ES
- [x] Luminous Void theme, GPU/transparency settings
- [x] Quick Open (Ctrl+E); Ctrl+P = Print
- [x] `MagicEditor.exe` pipeline at repo root

## Delivery rule
Every feature delivery: rebuild root exe:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build_exe.ps1
```

## Stretch / later
1. [ ] Multi-cursor / column selection
2. [ ] Tear-off tabs to new window
3. [x] Document outline (Markdown headings) — dialog Ctrl+Shift+O
4. [ ] Full Lucide SVG asset pack (optional)
5. [ ] REVIEW + merge to `main`

## Handoff
- Session keys: `open_files`, `active_file`, `bookmarks_json`, `cursors_json`, `drafts_json`, `recent_files`
- Drafts restore unsaved Untitled buffers (capped size)
- Only paths that still exist are restored for disk files
- UI smoke / session tests inject isolated `AppSettings`
