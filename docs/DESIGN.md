# MagicEditor — Design System (desktop)

Product UI for a **daily-driver code/text editor**. Design serves the product: calm, legible, dense-enough, not “marketing flashy”.

## Principles
- **Restrained palette:** neutrals + one accent (≤10% of chrome).
- **Spacing scale:** 4 / 8 / 12 / 16 (px). No random gaps.
- **Chrome vs canvas:** menubar/toolbar/status = slightly elevated surface; editor = deepest canvas.
- **Icons:** monochrome stroke on 24×24 grid, 1.75–2px stroke, round caps; same color as secondary text.

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
- UI: Segoe UI 10pt (system)
- Editor: Cascadia Code / Consolas 12pt

## Density
Visual density ~5/10 (daily app): tighter than marketing UI, looser than IDE “cockpit”.
