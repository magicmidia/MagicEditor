# Project Status

**Updated:** 2026-07-16  
**Branch:** `feature/editor-mvp`

## Current phase
**Feature expansion** — daily-driver editing on classic + huge-file paths.

## Done
- [x] AI harness, model routing, Cascadia Code bundled
- [x] Modern MainWindow (themes, explorer optional, session restore, find modal)
- [x] Piece table, line index, document I/O
- [x] Syntax highlighting + Syntax menu
- [x] Print / Export PDF (clean light styles)
- [x] **Virtual viewport** (`VirtualEditor`) for files >5MB; **mmap** >50MB
- [x] Incremental line index on insert/delete
- [x] Find in Files (workspace + open tabs)
- [x] Syntax on virtual viewport (visible lines only)
- [x] Go to Line (Ctrl+G)
- [x] Replace + regex + find highlight (classic + virtual)
- [x] Undo/Redo on virtual editor (Ctrl+Z / Ctrl+Y)
- [x] **Soft wrap** on VirtualEditor (Alt+Z)
- [x] **Bookmarks** (Ctrl+F2 toggle, F2 / Shift+F2 next/prev)
- [x] `MagicEditor.exe` pipeline at repo root

## Delivery rule
Every feature delivery: rebuild root exe:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build_exe.ps1
```

## Next
1. [ ] Bookmark persistence in session (optional)
2. [ ] Multi-cursor / column selection (stretch)
3. [ ] REVIEW before merge to `main`

## Handoff
- `core/` stays Qt-free (`text_match`, `line_wrap`, syntax rules)
- Architecture: `docs/magiceditor-architecture.md`
- Design tokens: `docs/DESIGN.md`
- UI smoke tests must inject isolated `AppSettings` and clear modified flags
