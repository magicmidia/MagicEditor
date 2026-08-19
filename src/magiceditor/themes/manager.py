"""QSS theme manager for native chrome themes."""

from __future__ import annotations

from pathlib import Path

from magiceditor.paths import icons_dir, themes_dir
from magiceditor.themes.fonts import qss_font_family

NATIVE_THEMES: dict[str, str] = {
    "luminous_void": "Luminous Void",
    "clean_light": "Clean Light",
    "midnight_dark": "Midnight Dark",
    "darcula": "Darcula Mode",
    "cobalt_blue": "Cobalt Blue",
    "monokai_pro": "Monokai Pro",
    "tokyo_night": "Tokyo Night",
    "catppuccin_mocha": "Catppuccin Mocha",
    "nord": "Nord",
    "rose_pine": "Rosé Pine",
}


class ThemeManager:
    def __init__(self, themes_path: Path | None = None) -> None:
        self._themes_dir = themes_path or themes_dir()
        self._current = "luminous_void"

    @property
    def current(self) -> str:
        return self._current

    def list_themes(self) -> list[tuple[str, str]]:
        """Return (id, label) pairs."""
        return list(NATIVE_THEMES.items())

    def load_qss(self, theme_id: str) -> str:
        path = self._themes_dir / f"{theme_id}.qss"
        if not path.is_file():
            raise FileNotFoundError(f"Theme not found: {path}")
        return path.read_text(encoding="utf-8")

    def apply(self, app: object, theme_id: str) -> None:
        """Apply theme QSS to a QApplication-like object with setStyleSheet."""
        if theme_id not in NATIVE_THEMES:
            theme_id = "luminous_void"
        qss = self.load_qss(theme_id)
        # Inject Cascadia Code for chrome + editor (family only — never font-size on *).
        fam = qss_font_family()
        font_block = f"""
QWidget, QMenuBar, QMenu, QToolBar, QToolButton, QStatusBar, QLabel,
QTabBar, QTabWidget, QTreeView, QLineEdit, QPushButton, QCheckBox,
QDockWidget, QDialog, QMessageBox {{
  font-family: {fam};
}}
QPlainTextEdit, QTextEdit, QTextBrowser {{
  font-family: {fam};
}}
"""
        set_style = getattr(app, "setStyleSheet", None)
        if set_style is None:
            raise TypeError("app does not support setStyleSheet")
        # Clear first so residual rules from previous theme do not stack.
        set_style("")
        set_style(qss + font_block + _chrome_extras())
        self._current = theme_id


def _chrome_extras() -> str:
    """Checkbox checkmark + larger settings nav (all themes)."""
    check = icons_dir() / "app" / "check.svg"
    check_rule = ""
    if check.is_file():
        uri = check.resolve().as_posix()
        check_rule = f"""
QCheckBox::indicator {{
  width: 16px;
  height: 16px;
}}
QCheckBox::indicator:checked {{
  image: url("{uri}");
}}
"""
    return (
        check_rule
        + """
QDialog#settingsDialog QListWidget#settingsNav {
  font-size: 11pt;
}
QDialog#settingsDialog QListWidget#settingsNav::item {
  min-height: 40px;
  padding: 12px 16px;
}
QDialog#settingsDialog QGroupBox {
  font-size: 10.5pt;
  padding-top: 16px;
}
QDialog#settingsDialog QSpinBox,
QDialog#settingsDialog QComboBox,
QDialog#settingsDialog QSlider {
  min-height: 28px;
}
QDialog#settingsDialog QCheckBox {
  min-height: 22px;
  spacing: 10px;
}
"""
    )
