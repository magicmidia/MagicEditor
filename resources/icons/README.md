# Icons

## Qlementine (default)

Bundled from [oclero/qlementine-icons](https://github.com/oclero/qlementine-icons)
([website](https://oclero.github.io/qlementine-icons/)).

- **License:** MIT (see `qlementine/LICENSE`)
- **Format:** SVG (16×16 design grid), recolored at runtime to match the theme chrome color
- **Path:** `resources/icons/qlementine/{category}/*.svg`

## Material Design (optional)

Loaded via [QtAwesome](https://github.com/spyder-ide/qtawesome) → Material Design Icons 6
(`mdi6.*`). Chosen in **Settings → Appearance → Icon pack**.

## Switching packs

`SessionState.icon_pack` = `qlementine` | `material`  
Persisted as `ui/icon_pack` in QSettings.
