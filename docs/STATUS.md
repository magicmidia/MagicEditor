# Project Status

**Updated:** 2026-07-16  
**Branch baseline:** `main`  
**Active worktree (optional):** `.worktrees/feature-bootstrap` → `feature/bootstrap`

## Current phase
**Editor MVP delivered** on `feature/editor-mvp` — modern UI + `MagicEditor.exe` pipeline.

## Done
- [x] Git repo + `.worktrees/` ignore
- [x] Architecture + AI harness + model routing
- [x] Piece table insert/delete, line index, encoding, document I/O
- [x] Modern MainWindow: tabs, sidebar, find/replace, gutter, zoom, preview, 5 themes, i18n
- [x] PyInstaller → root `MagicEditor.exe` via `scripts/build_exe.ps1`
- [x] Core tests green; ruff clean

## Delivery rule
Every feature delivery: run `pwsh -File scripts/build_exe.ps1` so `MagicEditor.exe` exists at repo root (~38–45 MB onefile).

## Next (suggested order)
1. [ ] Virtual viewport bound to piece table (huge files without full load)
2. [ ] Syntax highlighting (on-demand / visible range)
3. [ ] Search in files / directory
4. [ ] Clean print / PDF engine wiring
5. [ ] REVIEW (HIGH) before merge to main

## Blockers
- None (environment setup only)

## Handoff notes for agents
1. Read `AGENTS.md` → context routing
2. Product truth: `docs/magiceditor-architecture.md`
3. Do not start UI polish before core buffer works
4. Keep `core/` free of PyQt6
