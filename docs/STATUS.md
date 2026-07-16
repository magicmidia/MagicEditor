# Project Status

**Updated:** 2026-07-16  
**Branch baseline:** `main`  
**Active worktree (optional):** `.worktrees/feature-bootstrap` → `feature/bootstrap`

## Current phase
**AI harness + scaffolding** — agent docs, tooling, empty package layout. Product features not implemented yet.

## Done
- [x] Git repo + `.worktrees/` ignore
- [x] Architecture master doc → `docs/magiceditor-architecture.md`
- [x] `AGENTS.md` / `CLAUDE.md` / hierarchical `.memory/`
- [x] `pyproject.toml` (ruff, mypy, pytest, deps)
- [x] Package skeleton `src/magiceditor/**` by responsibility
- [x] Skills/MCP catalog → `docs/ai/skills-and-tools.md`

## Next (suggested order)
1. [ ] `uv sync --all-extras` / install dev deps locally
2. [ ] Implement `core/piece_table.py` + tests (TDD)
3. [ ] `core/mmap_source.py` + threshold policy (>50MB)
4. [ ] Minimal `MainWindow` + tab shell (no huge-file path yet)
5. [ ] Virtual viewport binding to piece table
6. [ ] Themes QSS (5 nativos) + i18n JSON
7. [ ] Preview MD/HTML; print engine; search worker

## Blockers
- None (environment setup only)

## Handoff notes for agents
1. Read `AGENTS.md` → context routing
2. Product truth: `docs/magiceditor-architecture.md`
3. Do not start UI polish before core buffer works
4. Keep `core/` free of PyQt6
