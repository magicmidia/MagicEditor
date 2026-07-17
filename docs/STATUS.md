# Project Status

**Updated:** 2026-07-16  
**Branch:** `feature/editor-mvp`

## Current phase
**Feature expansion** — daily-driver editing + session memory.

## Done
- [x] AI harness, model routing, Cascadia Code bundled
- [x] Modern MainWindow (themes, explorer optional, session restore, find modal)
- [x] Piece table, line index, document I/O
- [x] Syntax highlighting + Syntax menu
- [x] Print / Export PDF (clean light styles)
- [x] Virtual viewport + mmap + incremental line index
- [x] Find in Files (workspace + open tabs) + regex
- [x] Go to Line, replace, undo/redo (virtual)
- [x] Soft wrap (virtual) + bookmarks
- [x] **Session persistence:** open files (absolute paths, order, active tab), workspace, bookmarks per file, cursor per file
- [x] `MagicEditor.exe` pipeline at repo root

## Delivery rule
Every feature delivery: rebuild root exe:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build_exe.ps1
```

## Done (recent)
- [x] Theme **Luminous Void** (mockup-aligned: void black + #FFD700)
- [x] Settings: GPU acceleration, MSAA, AA, window opacity, glass chrome, translucent editor
- [x] Sidebar mockup: Workspace header, Explorer/Search/Settings nav, Open Editors, Project Files
- [x] Quick Open (Ctrl+E) + toolbar search field; Ctrl+P = Print
- [x] Status accent "Sync Active: MagicCloud"

## Next
1. [ ] Multi-cursor / column selection (stretch)
2. [ ] Untitled buffer recovery (optional temp drafts)
3. [ ] REVIEW before merge to `main`

## Handoff
- Session keys: `session/open_files`, `session/active_file`, `session/bookmarks_json`, `session/cursors_json`
- Only **saved files on disk** are restored (unsaved Untitled tabs are not)
- UI smoke / session tests inject isolated `AppSettings` + clear modified before close
