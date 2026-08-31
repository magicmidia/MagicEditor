# Changelog

## 0.9.4 BETA — Menus, auto-scroll, window raise, huge-file fixes

- Fix invalid application stylesheet: unquoted percent-encoded `url()` (non-ASCII
  install path, e.g. "Repositórios") made Qt reject the whole QSS — menus fell
  back to loose default metrics
- Compact menu rows (`QMenu::item` padding, no forced `min-width: 220px`);
  shortcuts keep right-aligned column; theme generator template synced
- Drag-select now auto-scrolls past the viewport top/bottom with speed
  proportional to distance; hit-test clamped (dragging above the top no longer
  jumps the caret to end-of-document)
- Huge files: minimap actually degrades (was a no-op `pass`); session collect no
  longer decodes file-backed tabs (up to 2MB per tab per persist)
- Opening a file from Explorer keeps the window maximized and brings it to the
  foreground (`AllowSetForegroundWindow` handoff from the forwarding instance)
- Hunspell pt_BR dictionary preload at startup; mmap threshold lowered to 5MB
- Tests: worker-based find-in-files cancel wiring, menu style isolation,
  drag auto-scroll coverage, line-index perf budgets

## 0.9.2 BETA — Footer, single instance, spell dictionaries

- Last editor line stays above the status footer (viewport pad + scroll range)
- Opening a file reuses the running editor as a new tab (Settings → General; default on)
- Bundle `resources/spell/{pt,en,es}.json.gz` so installed EXE recognizes common words and suggestions
- Installer still restores `.bat`/`.cmd` and clears Explorer FileExts leftovers

## 0.9.1 BETA — Inno Setup installer

- Inno Setup package: `packaging/inno/MagicEditor.iss` + `scripts/build_inno.ps1`
- Associations from `file-associations.json` (Open with, optional defaults, context menu)
- Installer wizard: default language + theme → QSettings
- Build: `scripts/build.ps1 -Exe -Inno`

## 0.9.1 BETA — Splash, settings depth, tab groups

- Centralized version module (`magiceditor.version`) — **0.9.1 BETA**
- Modern gradient splash screen (min. 5s, toggle in Settings)
- Version on status bar (bottom-left) and sidebar header
- Deep settings (tabs chrome, spell multi-lang, editor extras)
- Editor context menu, tab groups, compact tabs

## 0.2.0 — Roadmap waves B–I (excellence)

### Power editing (Onda B)
- Column / block selection (Alt+drag)
- Multi-cursor: Ctrl+D add next, Alt+F3 select all, Ctrl+click
- Line ops: move, sort, join, delete blank, trim trailing, tabs↔spaces
- Language-aware toggle comment (Ctrl+/)
- Matching brace highlight + jump (Ctrl+M)

### Navigation & workspace (Ondas C–D)
- Command palette (Ctrl+Shift+P); Preview rebinding to Ctrl+Shift+V
- Goto Anything (Ctrl+Shift+G)
- Symbol list, reload from disk (F5), minimap toggle
- Reveal in Explorer, copy path/dir, compare files, split view
- Settings: font, tab, wrap, spell, autosave, minimap, high contrast

### Spell & advanced text (Onda G)
- Viewport-aware spell check (pt_BR / en_US / es_ES), ignore/user dict
- Status bar spell indicator; default on for plaintext/markdown
- Snippets + word completion hooks (settings)

### UI / differentiation (Ondas F–E)
- First-run language + theme wizard
- Honest “Local only” status (no fake MagicCloud sync)
- Performance dashboard, portable mode detection
- Theme export/import; live HTML open in browser

### Performance (Onda H)
- Cancelable async search APIs; folder search progress/cancel hooks
- Lazy app version metadata; spell/minimap degrade on huge content
- Preview remains optional; WebEngine not required at cold start

### Release kit (Onda I)
- `scripts/build_release.ps1` → EXE + Portable + MSI + SHA256SUMS
- `scripts/smoke_dist.ps1`
- WiX MSI: ProgID, OpenWithProgids, context menu, Default Programs, ME_LANG/ME_THEME
- `packaging/wix/file-associations.json`

## 0.1.0 — MVP
- Piece table, mmap, virtual viewport, themes, i18n, session, find, print/PDF
