# Build & packaging (Windows)

Release artifacts are written to **`dist/`** and are **gitignored**. Never commit `.exe`, `.msi`, or portable `.zip`.

## Quick commands

```powershell
# Default: onefile EXE → dist/MagicEditor.exe
powershell -ExecutionPolicy Bypass -File scripts/build.ps1

# Portable ZIP (includes EXE + README)
powershell -ExecutionPolicy Bypass -File scripts/build.ps1 -Exe -Portable

# MSI installer (needs WiX CLI)
powershell -ExecutionPolicy Bypass -File scripts/build.ps1 -Exe -Msi

# Everything
powershell -ExecutionPolicy Bypass -File scripts/build.ps1 -All

# Wrappers
scripts\build_exe.bat
scripts\build_all.bat
powershell -File scripts/build_portable.ps1
powershell -File scripts/build_msi.ps1
```

Optional flags:

| Flag | Meaning |
|------|---------|
| `-Version 0.2.0` | Override version (default: `pyproject.toml`) |
| `-SkipDeps` | Skip `pip install -e ".[dev]"` |
| `-KeepWork` | Keep `build/` PyInstaller workdir |

## Outputs

| Artifact | Path |
|----------|------|
| Onefile EXE | `dist/MagicEditor.exe` |
| Portable | `dist/MagicEditor-Portable-<ver>-win64.zip` |
| Installer | `dist/MagicEditor-<ver>-win64.msi` |

## Portable

- Single `MagicEditor.exe` + `README.txt` in a ZIP.
- No admin rights; extract and run.
- User settings still live in Windows `QSettings` (per-user), not inside the ZIP.

## MSI (WiX)

Requires **WiX Toolset v4+ CLI**:

```powershell
# Prerequisites
winget install Microsoft.DotNet.SDK.8   # if dotnet missing
dotnet tool install --global wix

# Build MSI only (reuses dist/MagicEditor.exe if present after -Exe)
powershell -ExecutionPolicy Bypass -File scripts/build.ps1 -Msi
```

Source: `packaging/wix/MagicEditor.wxs`  
- Installs to `Program Files\MagicEditor\`  
- Start Menu shortcut  
- MajorUpgrade enabled (stable `UpgradeCode`)

If `wix` is not on `PATH`, `-All` still produces EXE + Portable and **warns** that MSI was skipped.

## What not to commit

See root `.gitignore`:

- `dist/`, `build/`
- `*.exe`, `*.msi`, `*.zip` (release archives)
- `.venv/`, `__pycache__/`, `tmp/`, `.worktrees/`

## Spec

PyInstaller config: `MagicEditor.spec` (windowed onefile, bundles `locales/` + `resources/` + QtAwesome fonts).
