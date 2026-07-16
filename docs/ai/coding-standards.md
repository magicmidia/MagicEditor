# Coding Standards — MagicEditor

Complements `AGENTS.md` and `pyproject.toml` (ruff/mypy/pytest). Do not restate linter rules.

## Architecture layers
```
UI (PyQt6) → services → core (pure Python)
                ↓
            resources / locales / disk (mmap)
```

| Layer | May import | Must not |
|-------|------------|----------|
| `core/` | stdlib only (+ typing) | PyQt6, UI, paths to widgets |
| `services/` | `core`, stdlib, light deps | paint/event code |
| `ui/` | Qt, services, core (read-only use) | direct mmap policy; huge-file rules live in services/core |
| `themes/`, `i18n/`, `preview/` | own domain + Qt as needed | piece-table internals |

## Module responsibility
- One public concept per file (`piece_table.py`, `tab_manager.py`, `print_engine.py`)
- Prefer composition over god-objects (`MainWindow` wires; does not implement buffer math)
- Public API at package `__init__.py` only when stable; avoid star-imports
- Target ≤300 LOC/file; hard smell >400 LOC or >5 responsibilities

## Naming
| Kind | Convention |
|------|------------|
| Modules/files | `snake_case.py` |
| Classes | `PascalCase` |
| Functions/methods | `snake_case` |
| Qt signals | past tense / event: `tab_closed`, `language_changed` |
| Constants | `UPPER_SNAKE` |
| Tests | `test_<unit>_<behavior>` |

## Huge-file rules
1. Files **>50MB** → mmap source; no full `read()` into RAM
2. Edits go to piece table (add/original buffers), not in-place full rewrites
3. Viewport paints **only visible lines** (+ small overscan)
4. Search: worker thread + Boyer–Moore (or equivalent); progress/cancel signals
5. Syntax highlight: visible range only when size >20MB
6. Never block GUI thread on disk or full-file scan

## Qt / UI
- Prefer signals/slots over tight coupling
- `TranslatorManager` singleton (or app-scoped service) + `language_changed` for live i18n
- Themes: QSS files under `resources/themes/`; switch without restart
- Tear-off tabs / middle-click close: `ui/tab_manager.py`
- Preview: split view; debounce document updates
- Print/PDF: strip dark backgrounds (`services/print_engine.py`)

## Testing
| Kind | Where | Notes |
|------|-------|-------|
| Unit | `tests/core/` | No Qt; fast; piece table, mmap edge cases |
| Service | `tests/services/` | Mock FS when needed |
| UI | `tests/ui/` | pytest-qt; `QT_QPA_PLATFORM=offscreen` |
| Fixtures | `tests/fixtures/` | Small samples; generate huge files in tmp only |

- New `core/` behavior: failing test first (TDD)
- Assert complexity-sensitive invariants (piece spans, line index maps), not only snapshots
- Coverage gate: see `pyproject.toml` (`fail_under`)

## Errors & logging
- User-facing: status bar / dialogs; no raw tracebacks in UI
- Log with module logger (`logging.getLogger(__name__)`)
- Fail closed on encoding detection; allow manual override

## i18n & themes
- All user-visible strings via translator keys (not hardcoded PT/EN in widgets long-term)
- Locales: `locales/<lang>.json` only — no code change for new languages
- New theme = new QSS (+ optional syntax palette JSON), registered in theme manager

## Git
- Conventional commits preferred: `feat:`, `fix:`, `test:`, `docs:`, `chore:`, `refactor:`
- AI co-author trailer required (see `AGENTS.md`)
- Do not commit worktrees, venvs, tmp, huge fixtures
