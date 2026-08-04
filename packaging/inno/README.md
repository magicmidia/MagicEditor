# Inno Setup packaging

## Build

```bat
REM One-shot (EXE + Inno installer) — preferred
scripts\setup_Install.bat
```

```powershell
# Same pipeline:
powershell -ExecutionPolicy Bypass -File scripts/build.ps1 -Exe -Inno

# Or only the setup from an existing dist\MagicEditor.exe:
powershell -ExecutionPolicy Bypass -File scripts/build_inno.ps1
```

Prerequisite: [Inno Setup 6](https://jrsoftware.org/isinfo.php) (`winget install JRSoftware.InnoSetup`).

Output: `dist/MagicEditor-<version>-win64-setup.exe`

## Files

| File | Role |
|------|------|
| `MagicEditor.iss` | Main installer script |
| `associations.issinc` | Generated registry lines for extensions |
| `../wix/file-associations.json` | Source of truth for extension list |

Regenerate associations after editing the JSON:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/generate_inno_associations.ps1
```

## Installer features

- **Language + theme** wizard page (written to HKCU QSettings)
- **File associations** (ProgID + Open with + optional default open)
- **Context menu** “Editar com MagicEditor” on files and folders
- **Default Programs** registration
- Start Menu / optional Desktop shortcuts
