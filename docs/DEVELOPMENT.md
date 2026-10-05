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

## AI-assisted development
See [`docs/ai/ai-setup.md`](ai/ai-setup.md) for skills, MCP, and multi-host config.

- Entry: root `AGENTS.md`
- Skills: `.agents/skills/` (e.g. `me-core`, `me-ui`, `me-feature`)
- Optional MCP: copy from `.mcp.example.json` or `.grok/mcp.example.toml`
- Never commit secrets or host-local `.mcp.json`

## Versioning

Product versions are [Semantic Versioning](VERSIONING.md). One number lives in
`src/magiceditor/version.py`, `pyproject.toml`, and the Inno script. Record
the change under `## [Unreleased]` or `## [x.y.z]` in `docs/CHANGELOG.md`.

```powershell
uv run python scripts/check_release_version.py
uv run python scripts/bump_version.py 0.9.9
```

A git tag `vX.Y.Z` pushed to GitHub builds the Windows installer and opens the
release. See [VERSIONING.md](VERSIONING.md). Ubuntu runners install the PyQt
libraries in `scripts/ci_qt_libs.sh` before pytest.

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
