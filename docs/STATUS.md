# Project Status

**Updated:** 2026-07-16  
**Branch:** `feature/editor-mvp`

## Current phase
**Feature expansion** — syntax highlighting + clean print/PDF on MVP UI.

## Done
- [x] AI harness, model routing, Cascadia Code bundled
- [x] Modern MainWindow (themes, explorer optional, session restore, find modal)
- [x] Piece table, line index, document I/O
- [x] **Syntax highlighting** (detect by extension + Syntax menu, QSyntaxHighlighter)
- [x] **Print / Export PDF** (clean light styles)
- [x] `MagicEditor.exe` pipeline at repo root

## Delivery rule
Every feature delivery: rebuild root exe:

```powershell
pwsh -File scripts/build_exe.ps1
```

## Next
1. [ ] Virtual viewport + mmap stream (huge files without full load into QTextDocument)
2. [ ] Search in folder / multi-file
3. [ ] Stronger lexers / theme-aware syntax palettes per QSS theme
4. [ ] REVIEW before merge to `main`

## Handoff
- `core/` stays Qt-free (syntax rules pure)
- Architecture: `docs/magiceditor-architecture.md`
- Design tokens: `docs/DESIGN.md`
