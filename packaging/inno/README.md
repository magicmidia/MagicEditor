# Inno Setup packaging

## Build

```powershell
# 1) Build the onefile EXE
powershell -ExecutionPolicy Bypass -File scripts/build.ps1 -Exe

# 2) Compile the installer (needs Inno Setup 6)
powershell -ExecutionPolicy Bypass -File scripts/build_inno.ps1
# or:
powershell -ExecutionPolicy Bypass -File scripts/build.ps1 -Exe -Inno
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
