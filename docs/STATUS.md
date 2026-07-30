# Project Status

**Updated:** 2026-07-30  
**Branch:** `main`

## Current phase
**Design + competitive roadmap** — MVP solid; polish and next-wave features planned in `docs/ROADMAP.md`.

## Done (MVP core)
- [x] Piece table, mmap, virtual viewport, huge files
- [x] Themes (6) + Luminous Void, GPU/transparency settings
- [x] Session: open files, drafts Untitled, recent files, bookmarks, cursors
- [x] Find/replace, find-in-files, regex, goto, outline MD
- [x] Clipboard, indent, duplicate line, encoding/EOL Format menu
- [x] i18n pt_BR / en_US / es_ES
- [x] Print/PDF clean engine, preview MD/HTML
- [x] **Competitive ROADMAP** (`docs/ROADMAP.md`) — N++, Sublime, Brackets, VS Code, Notepad
- [x] **Tab bar double-click** → new file (event on QTabBar)
- [x] **Icons:** default **Qlementine** (oclero, MIT SVGs) + optional **Material Design outline** (QtAwesome) — switch in Settings
- [x] File-type / language icons on tabs + Syntax menu
- [x] **60+ encodings** in Format → Encoding; smarter BOM detection
- [x] **Expanded format catalog** (100+ extensions / basenames)
- [x] **About** premium dialog + message box QSS polish
- [x] `MagicEditor.exe` at repo root

## Next (from ROADMAP)
See full matrix in `docs/ROADMAP.md`. Immediate priorities:

1. **Fase B** — Column selection + multi-cursor (Ctrl+D)
2. **Fase C** — Command palette; rebind Preview
3. Line ops (sort/join/trim), comment toggle, brace match
4. Minimap, reload-on-disk, open-in-explorer
5. REVIEW + merge to `main` + tag v0.2.0

## Delivery rule
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build_exe.ps1
```

## AI harness (2026-07-30)
- Domain skills: `.agents/skills/me-*` + design-taste / superpowers / token-economy
- Slash commands: `/me-feature`, `/me-verify`, `/me-review`
- Multi-host: `.grok/`, `.claude/`, `.cursor/rules/`, `.github/copilot-instructions.md`
- MCP examples: `.mcp.example.json`, `.grok/mcp.example.toml` (opt-in, no secrets)
- Guide: `docs/ai/ai-setup.md` · package AGENTS under services/themes/i18n/preview

## Handoff
- Roadmap is the source of truth for feature backlog
- Double-click empty tab strip (not on a tab title) creates Untitled
- About: Help → Sobre (custom dialog, monogram M)
- Prefer extract modules over growing `main_window.py` / `virtual_editor.py`
