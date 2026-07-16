# Bundled fonts

**Cascadia Code** (Microsoft) — SIL Open Font License 1.1  
Source: https://github.com/microsoft/cascadia-code

Files loaded at runtime (`magiceditor.ui.fonts`):

- `CascadiaCode-Regular.ttf` (required)
- `CascadiaCode-SemiBold.ttf`
- `CascadiaCode-Bold.ttf`

Also present for completeness (not auto-registered to avoid Qt variable-font issues):

- `CascadiaCode.ttf` (variable)
- `CascadiaCodeItalic.ttf`

Loaded via `QFontDatabase` for both UI chrome and the text editor.
