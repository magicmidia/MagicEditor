# Project Status

**Updated:** 2026-07-30  
**Branch:** `main`  
**Version:** 0.9.1 BETA

## Current phase
**Roadmap B–I shipped (code)** — power editing, spell, navigation, workspace, UI first-run, performance APIs, Windows packaging with file associations.

## Done
### MVP + Onda A
- [x] Piece table, mmap, virtual viewport, huge files
- [x] Themes + Luminous Void, GPU/transparency
- [x] Session, drafts, recent, bookmarks, cursors
- [x] Find/replace, find-in-files, i18n, print/PDF, preview
- [x] Tab double-click, icons, About, encodings/catalog

### Onda B — Edição
- [x] Column selection (Alt+drag)
- [x] Multi-cursor Ctrl+D / Alt+F3 / Ctrl+click
- [x] Line ops, toggle comment, trim, tabs↔spaces
- [x] Brace match highlight + Ctrl+M

### Onda C–D — Navegação & workspace
- [x] Command palette (Ctrl+Shift+P); Preview → Ctrl+Shift+V
- [x] Goto Anything, symbols, reload (F5), minimap toggle
- [x] Reveal/copy path, compare, split view, autosave setting
- [x] Settings: font, tab, wrap, spell, minimap, autosave, a11y

### Onda G — Spell & texto
- [x] Viewport spell (pt_BR/en_US/es_ES), ignore/user dict, status
- [x] Snippets module + word-completion setting

### Onda F–E — UI & diferenciação
- [x] First-run language+theme wizard
- [x] Honest “Local only” status (no fake MagicCloud)
- [x] Performance dashboard, portable mode, theme export/import
- [x] Live HTML open in browser; search cancel flag

### Onda H — Performance
- [x] Cancelable async search + folder search progress hooks
- [x] Spell/minimap/viewport-scoped work; lazy preview unchanged

### Onda I — Release
- [x] `scripts/build_release.ps1`, `scripts/smoke_dist.ps1`
- [x] WiX MSI ProgID / OpenWith / context menu / Default Programs
- [x] `packaging/wix/file-associations.json`
- [x] CHANGELOG 0.2.0, version bump

## Delivery
```powershell
build.bat
# → MagicEditor.exe at repo root (+ dist\MagicEditor.exe)
powershell -ExecutionPolicy Bypass -File scripts/build.ps1 -All
powershell -ExecutionPolicy Bypass -File scripts/build_release.ps1
```
Primary EXE: **root `MagicEditor.exe`**. Packaging copies under **`dist/`**. Both gitignored.  
App icon: `resources/icons/app/magiceditor.ico`.

## Handoff
- Pure transforms: `core/line_ops`, `comment_rules`, `spell`, `document_edit`, …
- UI wiring: `ui/power_features.py` mixin on `MainWindow`
- Prefer not growing `main_window.py` / `virtual_editor.py` further without extract
