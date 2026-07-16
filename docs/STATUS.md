# Project Status

**Updated:** 2026-07-16  
**Branch baseline:** `main`  
**Active worktree (optional):** `.worktrees/feature-bootstrap` → `feature/bootstrap`

## Current phase
**Editor MVP in progress** on `feature/editor-mvp` + **model-routing harness**.

## Done
- [x] Git repo + `.worktrees/` ignore
- [x] Architecture master doc → `docs/magiceditor-architecture.md`
- [x] `AGENTS.md` / `CLAUDE.md` / hierarchical `.memory/`
- [x] `pyproject.toml` (ruff, mypy, pytest, deps)
- [x] Package skeleton `src/magiceditor/**` by responsibility
- [x] Skills/MCP catalog → `docs/ai/skills-and-tools.md`
- [x] **Model routing** HIGH/MEDIUM/LOW → `docs/ai/model-routing.md`, `.grok/{roles,agents,personas,rules}`
- [x] Piece table insert/delete, line index, encoding, document I/O (partial commit pending)
- [x] MainWindow shell with tabs/sidebar/themes/i18n/preview (partial commit pending)

## Next (suggested order)
1. [ ] VERIFY (LOW): ruff + pytest on pending MVP files; commit
2. [ ] Virtual viewport bound to piece table (BUILD medium)
3. [ ] Find/replace + search worker (BUILD medium)
4. [ ] Huge-file path without full decode to QTextEdit (PLAN high → BUILD)
5. [ ] REVIEW (HIGH) before merge to main

## Blockers
- None (environment setup only)

## Handoff notes for agents
1. Read `AGENTS.md` → context routing
2. Product truth: `docs/magiceditor-architecture.md`
3. Do not start UI polish before core buffer works
4. Keep `core/` free of PyQt6
