# MagicEditor — Agent Instructions

High-performance desktop text/code editor (Python 3.12+, PyQt6).
Canonical product/architecture: `docs/magiceditor-architecture.md`.

## Package Manager
Use **uv** when available, else **pip**:
- `uv sync --all-extras` or `pip install -e ".[dev]"`
- Run: `uv run magiceditor` / `python -m magiceditor`
- Prefer `uv run <cmd>` for tool isolation

## File-Scoped Commands
| Task | Command |
|------|---------|
| Lint file | `uv run ruff check path/to/file.py` |
| Format file | `uv run ruff format path/to/file.py` |
| Typecheck | `uv run mypy path/to/file.py` |
| Test file | `uv run pytest tests/path/test_x.py -q` |
| Test node | `uv run pytest tests/path/test_x.py::test_name -q` |
| Coverage | `uv run pytest --cov=magiceditor -q` |

## Layout (one responsibility per module)
```
src/magiceditor/
  core/     # piece table, mmap, search — no Qt imports
  ui/       # windows, tabs, viewport widgets — thin, no I/O policy
  themes/   # QSS load/switch
  i18n/     # TranslatorManager + locales
  preview/  # MD/HTML WebEngine preview
  services/ # print/PDF, config, sessions
tests/      # mirrors src; unit tests for core without Qt when possible
locales/    # pt_BR.json, en_US.json
resources/  # themes/*.qss, icons
```

## Non-Negotiables
- **Core pure:** `core/` must not import PyQt6
- **UI thin:** widgets call services/core; no business rules in paint/event handlers
- **Huge files:** never load whole file into `str`/`QTextDocument` for >50MB; use mmap + piece table + virtual viewport
- **Syntax on demand:** disable full-file lexers for >20MB; highlight visible range only
- **File size:** prefer ≤300 LOC/module; split before growing past ~400
- **No secrets** in repo; use env/local config only
- Worktrees: develop under `.worktrees/<name>` when isolated; keep ignored

## Context Routing (load only what you need)
| Area | Read first |
|------|------------|
| Product/UX/themes | `docs/magiceditor-architecture.md` |
| AI tooling/skills | `docs/ai/skills-and-tools.md` |
| Coding standards | `docs/ai/coding-standards.md` |
| Decisions | `.memory/decisions.md` |
| Patterns | `.memory/patterns.md` |
| Status handoff | `docs/STATUS.md` |
| Package root | `src/magiceditor/AGENTS.md` |
| Core engine | `src/magiceditor/core/AGENTS.md` |
| UI | `src/magiceditor/ui/AGENTS.md` |

## Workflow
1. Read root `AGENTS.md` → route table → only scoped files for the task
2. Prefer TDD for `core/` (pytest, no display)
3. UI changes: `pytest-qt` + `QT_QPA_PLATFORM=offscreen` when headless
4. After edits: ruff check/format on touched files, then relevant tests
5. New ADRs → `.memory/decisions.md`; reusable patterns → `.memory/patterns.md`

## Commit Attribution
AI commits MUST include:
```
Co-Authored-By: <agent-model-name> <noreply@example.com>
```

## Do Not
- Put long prose or skill catalogs in this file (see `docs/ai/`)
- Duplicate ruff/mypy rules here
- Block the UI thread with search/I/O on huge files
- Commit `.worktrees/`, `tmp/`, `.venv/`, or local secrets
