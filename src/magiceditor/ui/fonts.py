"""Load bundled Cascadia Code and expose UI/editor fonts."""

from __future__ import annotations

from PyQt6.QtGui import QFont, QFontDatabase

from magiceditor.paths import fonts_dir

FAMILY = "Cascadia Code"
_FALLBACKS = ("Cascadia Mono", "Consolas", "Courier New", "monospace")

# Module state (populated once per process after QGuiApplication exists)
_state: dict[str, object] = {"loaded": False, "family": FAMILY}


def load_bundled_fonts() -> str:
    """Register packaged Cascadia Code fonts. Returns the family name to use.

    Must be called after QApplication / QGuiApplication is created.
    """
    if _state["loaded"]:
        return str(_state["family"])

    directory = fonts_dir()
    # Static faces only — variable fonts have caused instability with Qt on some builds.
    candidates = [
        "CascadiaCode-Regular.ttf",
        "CascadiaCode-SemiBold.ttf",
        "CascadiaCode-Bold.ttf",
    ]
    registered_family: str | None = None
    for name in candidates:
        path = directory / name
        if not path.is_file():
            continue
        font_id = QFontDatabase.addApplicationFont(str(path))
        if font_id == -1:
            continue
        families = QFontDatabase.applicationFontFamilies(font_id)
        if families and registered_family is None:
            registered_family = families[0]

    if registered_family:
        _state["family"] = registered_family
    else:
        probe = QFont(FAMILY)
        if probe.exactMatch():
            _state["family"] = FAMILY
        else:
            for fb in _FALLBACKS:
                if QFont(fb).exactMatch():
                    _state["family"] = fb
                    break

    _state["loaded"] = True
    return str(_state["family"])


def font_family() -> str:
    if not _state["loaded"]:
        return load_bundled_fonts()
    return str(_state["family"])


def ui_font(point_size: int = 10) -> QFont:
    """Application / chrome font (Cascadia Code)."""
    f = QFont(font_family(), point_size)
    f.setStyleHint(QFont.StyleHint.Monospace)
    f.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
    return f


def editor_font(point_size: int = 12) -> QFont:
    """Editor buffer font (Cascadia Code, slightly larger)."""
    f = QFont(font_family(), point_size)
    f.setStyleHint(QFont.StyleHint.Monospace)
    f.setFixedPitch(True)
    f.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
    return f


def qss_font_family() -> str:
    """Quoted family name safe for QSS font-family rules."""
    return f'"{font_family()}", "Cascadia Code", "Consolas", monospace'
