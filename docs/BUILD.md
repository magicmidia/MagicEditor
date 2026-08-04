# Build & packaging (Windows)

Release artifacts are written to **`dist/`** and are **gitignored**. Never commit `.exe`, `.msi`, or portable `.zip`.

## Quick commands

```powershell
# From repo root — primary EXE lands at ./MagicEditor.exe
build.bat
# same as:
powershell -ExecutionPolicy Bypass -File scripts/build.ps1 -Exe

# Portable ZIP (includes EXE + README)
powershell -ExecutionPolicy Bypass -File scripts/build.ps1 -Exe -Portable

# MSI installer (needs WiX CLI)
powershell -ExecutionPolicy Bypass -File scripts/build.ps1 -Exe -Msi

# Inno Setup installer (needs Inno Setup 6 / ISCC)
powershell -ExecutionPolicy Bypass -File scripts/build.ps1 -Exe -Inno
# or only the setup from an existing dist EXE:
powershell -ExecutionPolicy Bypass -File scripts/build_inno.ps1

# Everything
powershell -ExecutionPolicy Bypass -File scripts/build.ps1 -All

# Full release kit (tests + All + SHA256SUMS.txt)
powershell -ExecutionPolicy Bypass -File scripts/build_release.ps1
powershell -ExecutionPolicy Bypass -File scripts/build_release.ps1 -SkipTests -Version 0.2.0

# Smoke dist EXE (offscreen)
powershell -ExecutionPolicy Bypass -File scripts/smoke_dist.ps1

# Regenerate app icon (.ico)
python scripts/generate_app_icon.py

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
| Onefile EXE (primary) | **`MagicEditor.exe`** (repo root) |
| Onefile EXE (packaging copy) | `dist/MagicEditor.exe` |
| Portable | `dist/MagicEditor-Portable-<ver>-win64.zip` |
| Installer (MSI / WiX) | `dist/MagicEditor-<ver>-win64.msi` |
| Installer (Inno Setup) | `dist/MagicEditor-<ver>-win64-setup.exe` |
| App icon source | `resources/icons/app/magiceditor.ico` |

The root EXE embeds `resources/icons/app/magiceditor.ico` (taskbar / Explorer).  
Both `*.exe` paths are **gitignored**.

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
- Start Menu + Desktop shortcuts  
- ProgID `MagicEditor.Document` + OpenWithProgids for text extensions  
- Context menu “Edit with MagicEditor”  
- Default Programs capabilities (subset of extensions)  
- Optional MSI properties `ME_LANG` / `ME_THEME` → HKCU install defaults  
- Extension list source of truth: `packaging/wix/file-associations.json` (+ `magiceditor.services.file_associations`)  
- MajorUpgrade enabled (stable `UpgradeCode`)

If `wix` is not on `PATH`, `-All` still produces EXE + Portable and **warns** that MSI was skipped.

## Inno Setup

Requires **Inno Setup 6** (`ISCC.exe`):

```powershell
winget install JRSoftware.InnoSetup
# optional: set ISCC_PATH if not on PATH
powershell -ExecutionPolicy Bypass -File scripts/build.ps1 -Exe -Inno
```

Source: `packaging/inno/MagicEditor.iss`  
Associations include: `packaging/inno/associations.issinc` (generated from `file-associations.json`).

| Feature | Detail |
|---------|--------|
| Install dir | `Program Files\MagicEditor\` |
| Shortcuts | Start Menu + optional Desktop |
| ProgID | `MagicEditor.Document` + open verb |
| Open with | `OpenWithProgids` for all listed extensions |
| Default open | Task **Associar extensões…** (optional, checked by default) |
| Context menu | **Editar com MagicEditor** on all files (+ folder) |
| Default Programs | `RegisteredApplications` + Capabilities |
| First-run prefs | Wizard page: **idioma** (pt_BR/en_US/es_ES) + **tema** → HKCU `Software\MagicEditor\MagicEditor\ui\*` |

If `ISCC` is missing, `-Inno` / `-All` **warns** and continues with other targets.

Code signing (optional): set `ME_SIGN_CERT` and run `build_release.ps1 -Sign`.

## What not to commit

See root `.gitignore`:

- `dist/`, `build/`
- `*.exe`, `*.msi`, `*.zip` (release archives)
- `.venv/`, `__pycache__/`, `tmp/`, `.worktrees/`

## Spec

PyInstaller config: `MagicEditor.spec` (windowed onefile, bundles `locales/` + `resources/` + QtAwesome fonts).
