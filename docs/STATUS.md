# Project Status

**Updated:** 2026-08-31  
**Branch:** `main`  
**Version:** 0.9.4 BETA

## Current phase
**Reengenharia J–N concluída** — Inventário de todos os IDs §11 contra o código enviado: **zero Aceites abertos** (2026-08-17).

J1 extrações + J2 camadas (`viewport_text`/`full_text`, sem `read_bytes` em `ui/`, I/O de tema em `services/theme_io`) + J3 `EditorSurface`.  
K10 `measure_packaging()`; K14 Ctrl+D via `line_text`; sort huge `c\\nb\\na\\n` → `a\\nb\\nc\\n`; K15 `SaveWorker`; K17 harness.  
L sanitização/assoc opt-in; M higiene; N testes + ADRs. Fora de §11 (macros, hex, plugins, MagicCloud) não é Aceite desta onda.

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
- [x] Bundled `resources/spell/{pt,en,es}.json.gz` so the onefile EXE actually knows common words + suggestions
- [x] Snippets module + word-completion setting
- [x] Last editor line padded above the status footer
- [x] Open files in the existing window as tabs (setting, default on)

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
- [x] CHANGELOG 0.9.1, version bump

### Onda M — Higiene (reengenharia)
- [x] `tmp/` gitignored e não versionado; ícones qlementine food/shopping/audio/instrument removidos
- [x] Matriz ROADMAP §1 alinhada a 0.9.1 (10 temas, spell, minimap, palette, compare)

### Onda J–N — Reengenharia
- [x] J1.4 settings: uma página = um módulo (`settings_pages/*`) + dialog shell
- [x] J1.3 mixin <900 LOC; controllers `spell_controller` / `workspace_actions` / `nav_palette`
- [x] J1.5–J1.7 tab bar, session_state/clamps, extensions.json
- [x] J2 camadas (Document em core, themes sem ui, EditorSurface, compare/quick-open I/O, viewport-only)
- [x] J3.1 protocolo `EditorSurface`; J3.2 attrs tipados, 0 `type: ignore[attr-defined]`
- [x] K2 `LineTokenCache` no paint; K3 spell debounce 60 ms, toggle sem `spell_force=True`
- [x] K4 `mono_advance`; K7 preview lazy; K11 QWidget sem background transparent
- [x] K15 save em chunks + `SaveWorker` ligado em `save_current`; K1, K5–K6, K8–K9, K12, K14, K16–K18
- [x] L1–L14 sanitize, assoc opt-in, regex cap, UPX off, extras removidos, docs QTextBrowser
- [x] M1–M10 higiene; ROADMAP §3 alinhado ao código
- [x] N2–N8 smoke `insert()`, huge-file, fail_under por pacote, ADR, dialogs, autosave/theme/split

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
- Virtual editor collaborators: `ui/virtual_paint.py`, `virtual_keys.py`, `virtual_find.py`, `virtual_undo.py`, `virtual_cursors.py`
- Prefer not growing `main_window.py` / `virtual_editor.py` further without extract
- Diagnostics: `MagicEditor.log` at repo root in dev; installed EXE uses `%LOCALAPPDATA%\MagicEditor\` (not Program Files)
- Crash fix: init `_file_watcher` **before** session restore (`watch_path`)
- Inno installer is `dist\MagicEditor-<ver>-win64-setup.exe` (not `.msi`; MSI is WiX)
