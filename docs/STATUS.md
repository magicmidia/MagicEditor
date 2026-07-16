# Project Status

**Updated:** 2026-07-16  
**Branch:** `feature/editor-mvp`

## Current phase
**Feature expansion** — huge-file virtual viewport + syntax + print.

## Done
- [x] AI harness, model routing, Cascadia Code bundled
- [x] Modern MainWindow (themes, explorer optional, session restore, find modal)
- [x] Piece table, line index, document I/O
- [x] Syntax highlighting + Syntax menu
- [x] Print / Export PDF (clean light styles)
- [x] **Virtual viewport** (`VirtualEditor`) for files >5MB; **mmap** >50MB
- [x] `MagicEditor.exe` pipeline at repo root

## Delivery rule
Every feature delivery: rebuild root exe:

```powershell
pwsh -File scripts/build_exe.ps1
```

## Next
1. [ ] Incremental line index on huge edits (avoid full rebuild)
2. [ ] Search in folder / multi-file
3. [ ] Syntax highlight on virtual viewport (visible lines only)
4. [ ] REVIEW before merge to `main`

## Handoff
- `core/` stays Qt-free (syntax rules pure)
- Architecture: `docs/magiceditor-architecture.md`
- Design tokens: `docs/DESIGN.md`
