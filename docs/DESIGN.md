# MagicEditor — Design System (desktop)

Product UI for a **daily-driver code/text editor**. Primary look: **Luminous Void** (see `tmp/DESIGN.md` + `tmp/screen.png` mockup).

## Principles
- **Void canvas + glass chrome:** deep `#0E0E0E` / `#131313` with translucent surfaces.
- **Flat yellow accent (`#FFD700`):** active tabs, caret, primary buttons, status accents (≤10% of chrome).
- **Spacing scale:** 4 / 8 / 12 / 16 (px). Toolbar ~36–40px.
- **Icons:** monochrome stroke on 24×24 grid; hover → light, active → yellow.
- **Settings:** View → Settings — GPU/OpenGL, MSAA, window opacity, glass chrome, translucent editor.

## Spacing (Qt chrome)
| Element | Spec |
|---------|------|
| MenuBar item padding | 5×10 |
| Menu panel padding | 4 |
| Menu item padding | 6×12 left / 6×28 right (check room) |
| Menu item margin | 1×4 |
| Toolbar padding | 6×8 |
| Toolbar button padding | 6 |
| Toolbar icon size | 18×18 |
| Tab padding | 8×14 |
| Status bar height | ~24, label pad 0×8 |

## Color roles (per theme)
| Role | Use |
|------|-----|
| `canvas` | Editor / tree background |
| `surface` | MenuBar, toolbar, status, menus |
| `border` | 1px separators |
| `text` | Primary UI text |
| `muted` | Secondary labels, inactive tabs |
| `accent` | Active tab underline, focus, checks |
| `select` | Text selection |

## Typography
- **UI + Editor:** Cascadia Code (bundled under `resources/fonts/`)
  - UI chrome: 10pt
  - Editor buffer: 12pt
  - Fallback: Consolas → Courier New → monospace
- Loaded at startup via `QFontDatabase` (`magiceditor.ui.fonts`)

## Density
Visual density ~5/10 (daily app): tighter than marketing UI, looser than IDE “cockpit”.
