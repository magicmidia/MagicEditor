# GitHub Copilot — MagicEditor

Follow root `AGENTS.md` and `docs/ai/coding-standards.md`.

## Stack
- Python 3.12+, PyQt6, uv, ruff, pytest
- Pure engine in `src/magiceditor/core/` (no Qt imports)
- Thin UI in `src/magiceditor/ui/`; policy/I/O in `services/`

## Hard rules
- Files >50MB: mmap + piece table + virtual viewport — never full-file `str` / `QTextDocument`
- Prefer modules ≤300 LOC; do not further bloat `main_window.py` or `virtual_editor.py` — extract helpers
- i18n: translator keys + `locales/*.json`
- After edits: file-scoped `uv run ruff check` and targeted pytest
- AI commits: `Co-Authored-By: <model> <noreply@example.com>`

## Do not
- Put business rules in paint/event handlers
- Block the UI thread on search/disk for huge files
- Commit `dist/`, `.venv/`, secrets, or worktrees
