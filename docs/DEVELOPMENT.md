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

## Ship Windows packages (each delivery)

Artifacts go to **`dist/`** (gitignored). Full guide: [`docs/BUILD.md`](BUILD.md).

```powershell
# EXE only → dist/MagicEditor.exe
powershell -ExecutionPolicy Bypass -File scripts/build.ps1 -Exe

# Portable ZIP
powershell -ExecutionPolicy Bypass -File scripts/build.ps1 -Exe -Portable

# MSI (needs: dotnet tool install -g wix)
powershell -ExecutionPolicy Bypass -File scripts/build.ps1 -Exe -Msi

# All of the above
powershell -ExecutionPolicy Bypass -File scripts/build.ps1 -All
# or: scripts\build_all.bat
```

Requirements: Python 3.12+, PyQt6, PyInstaller (`pip install -e ".[dev]"`).  
Optional for MSI: .NET SDK + WiX CLI (`wix`).

## Project map
See root `AGENTS.md` and `docs/magiceditor-architecture.md`.
