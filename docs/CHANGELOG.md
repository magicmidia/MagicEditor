# Changelog

## 0.9.8 BETA — Recovery, preview, and editor options

- Unsaved tab text is snapshotted to a recovery file and restored after a power
  loss. The file on disk is not overwritten
- Markdown preview no longer shows the theme CSS as text. The Markdown view can
  be printed on its own
- Editor settings: line spacing, indent guides, auto-close brackets, right
  margin, occurrence highlight, Ctrl+wheel zoom, and the recovery interval
- Tools menu hashes the active file: MD5, SHA-1, SHA-256, SHA-384, SHA-512,
  BLAKE2b, or all of them
- Slightly shorter toolbar. About dialog lists what the editor actually does

## 0.9.7 BETA — Backspace and typing responsiveness

- Backspace and Delete remove a whole character (UTF-8, combining marks, emoji)
  from the raw bytes, so holding the key no longer leaves U+FFFD
- A click followed by holding Backspace no longer turns the caret move into a
  selection that skips deletes
- Typing and deleting at the end of the buffer keeps one piece-table span
  instead of one piece per keystroke
- The line index shifts only from the caret forward; spell check, minimap,
  syntax cache, and the tab title no longer redo all of their work on every key
- With word wrap on, breaking a line at the bottom of the viewport scrolls the
  new row above the status footer instead of painting it underneath

## 0.9.6 BETA — Filter Lines + Log Lens (roadmap §9.5, P1 e P6)

- Filter Lines (Tools): extract lines matching a pattern (substring/regex, case,
  invert) into a new tab, with original line numbers (`N: text`) — streaming
  worker (10k-line chunks), real progress + cancel, 1M-match cap with explicit
  truncation note; syntax off for results >20MB
- Log Lens: new `log` syntax language with severity highlighting
  (ERROR/FATAL/Traceback, WARN, INFO, DEBUG/TRACE) — word-boundary safe
  (`information` no longer lights up), colors tuned for dark and light themes;
  `.log` files auto-detect it
- Log summary dialog (Tools): per-level line counts on a worker thread plus
  "go to next" per level with wrap-around — works on huge files without
  materializing the document

## 0.9.5 BETA — Text transforms, document tools, editor perf

- Case conversion on selection: UPPERCASE, lowercase (Ctrl+U), Title, Sentence, Invert
- Base64 / URL encode-decode on selection; invalid decode warns and never destroys text
- Line ops: remove duplicate lines, remove consecutive duplicates, reverse line order,
  sort by length (same huge-file guardrails as existing line ops)
- Insert date/time submenu (ISO, local short, local date+time, Unix timestamp)
- File checksum dialog (MD5 / SHA-1 / SHA-256) on a worker thread with cancel;
  warns when hashing the on-disk file while the buffer is dirty
- Document statistics dialog (chars, words, lines, encoding/EOL); capped to the
  first 2MB on huge files with a visible "partial" note
- Save All (dirty tabs with paths); Always on top toggle; per-tab read-only mode
  with a 🔒 tab badge (blocks typing, paste, cut, undo/redo)
- Editor perf: O(1) mouse hit-test when wrap is off, O(N) monospace wrapping
  (no per-character font shaping), clipped painting of rows >300 chars,
  selection extents via the line index instead of full line materialization
- New pure core modules: `text_transform`, `checksum`, `text_stats`
  (streaming, split-CRLF-safe) with full unit coverage

## 0.9.4 BETA — Menus, auto-scroll, window raise, huge-file fixes

- Fix invalid application stylesheet: unquoted percent-encoded `url()` (non-ASCII
  install path, e.g. "Repositórios") made Qt reject the whole QSS — menus fell
  back to loose default metrics
- Compact menu rows with breathing room (`QMenu::item` padding, no forced
  `min-width: 220px`); shortcuts keep right-aligned column; generator synced
- Word wrap: scroll range now counts display rows — the last line renders fully,
  flush above the status bar (was clipped/hidden with wrapped tail lines)
- Toolbar slimmer (30px); tabs default 30px with fuller padding; tab corner
  buttons (◀ ▶ New) pinned to 22px and vertically centered (theme `QToolButton`
  min-size was overflowing the tab strip)
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
