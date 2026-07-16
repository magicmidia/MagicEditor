# Development

## Prerequisites
- Python **3.12+** (3.13 OK)
- [uv](https://github.com/astral-sh/uv) recommended; pip works
- Qt platform libs as required by PyQt6 on your OS
- Optional: display or `QT_QPA_PLATFORM=offscreen` for CI/UI tests

## Setup
```bash
# clone / enter repo
uv sync --all-extras
# or: python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
#     pip install -e ".[dev]"
```

## Run
```bash
uv run magiceditor
# or
uv run python -m magiceditor
```

## Quality loop
```bash
uv run ruff check src tests
uv run ruff format src tests
uv run mypy src/magiceditor
uv run pytest
uv run pytest --cov=magiceditor
```

### Windows (PowerShell) UI tests headless
```powershell
$env:QT_QPA_PLATFORM = "offscreen"
uv run pytest tests/ui -q
```

## Worktrees
```bash
git worktree add .worktrees/feature-foo -b feature/foo
cd .worktrees/feature-foo
uv sync --all-extras
```

## Ship Windows exe (each delivery)

Produce `MagicEditor.exe` at the **repository root**:

```powershell
pwsh -File scripts/build_exe.ps1
# or
scripts\build_exe.bat
```

Requirements: Python 3.12+, PyQt6, PyInstaller (`pip install -e ".[dev]"`).

The binary is windowed (no console), onefile, with `locales/` and `resources/` bundled.

## Project map
See root `AGENTS.md` and `docs/magiceditor-architecture.md`.
