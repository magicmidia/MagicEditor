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
- [x] Find in Files (workspace)
- [x] Syntax on virtual viewport (visible lines only)
- [x] Go to Line (Ctrl+G)
- [x] Replace in virtual mode + find match highlight
- [x] Undo/Redo on virtual editor (Ctrl+Z / Ctrl+Y)
- [x] **Regex** find/replace (classic + virtual) and folder search
- [x] **Find in open tabs** (scope in Find in Files dialog)
- [x] `MagicEditor.exe` pipeline at repo root

## Delivery rule
Every feature delivery: rebuild root exe:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build_exe.ps1
```

## Next
1. [ ] Soft wrap for virtual editor (optional)
2. [ ] Bookmarks / multi-cursor (stretch)
3. [ ] REVIEW before merge to `main`

## Handoff
- `core/` stays Qt-free (`text_match`, syntax rules pure)
- Architecture: `docs/magiceditor-architecture.md`
- Design tokens: `docs/DESIGN.md`
- UI smoke tests must inject isolated `AppSettings` and clear modified flags
